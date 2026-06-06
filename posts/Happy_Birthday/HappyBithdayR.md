# Vulnerability Report: SNS Subscription Bypass and S3 Object Disclosure via Lambda Path Traversal

## Executive Summary

The application exposed a chain of vulnerabilities that allowed an attacker to receive invitation tokens, invoke an internal Lambda function, and retrieve unintended objects from a private S3 bucket.

The attack relied on two primary weaknesses:

1. Improper SNS subscription restrictions that validated only the subscription endpoint string rather than the protocol.
2. Unsafe path construction within the Lambda function, allowing access to arbitrary S3 objects through path traversal logic.

By combining these issues, an attacker could obtain a valid registration token and abuse the Lambda function to read sensitive files stored outside the intended templates directory.

---

## Affected Components

### Public Web Application

* Birthday invitation website
* API Gateway endpoints
* Static S3-hosted content

### AWS Services

* Amazon SNS
* AWS Lambda
* Amazon S3

---

## Vulnerability 1: SNS Subscription Restriction Bypass

### Description

The SNS topic policy attempted to restrict subscriptions to company email addresses by validating that the subscription endpoint matched:

```
*@cloudsecuritychampionship.com
```

However, the policy failed to restrict the subscription protocol.

As a result, an attacker could subscribe an HTTP or HTTPS endpoint whose URL path ended with:

```
@cloudsecuritychampionship.com
```

Example:

```
https://attacker.example.com/webhook@cloudsecuritychampionship.com
```

Since SNS evaluates the endpoint string and not the protocol semantics, the subscription request satisfied the policy condition.

### Impact

An attacker could:

* Subscribe arbitrary HTTPS endpoints.
* Receive all future SNS notifications.
* Intercept invitation tokens.
* Learn internal application metadata.

### Risk

High

---

## Vulnerability 2: Information Disclosure via SNS Notifications

### Description

After triggering the invitation workflow, the application published registration data to the SNS topic.

The notification contained:

```json
{
  "message": "You're invited to the S3 Birthday Party!",
  "registration_url": "...",
  "token": "...",
  "expires_in": "1 hour",
  "generated_by": "GenerateBirthdayCard"
}
```

This exposed:

* Registration token
* Registration URL
* Internal Lambda function name

### Impact

An attacker who successfully subscribed to the SNS topic could obtain valid registration tokens and internal infrastructure information.

### Risk

Medium

---

## Vulnerability 3: Public Lambda Invocation

### Description

The Lambda function resource policy permitted invocation from any principal.

Example:

```json
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "lambda:InvokeFunction"
}
```

Because the function accepted user-controlled input and relied solely on possession of a valid token, an attacker could invoke it directly after obtaining a token.

### Impact

An attacker could bypass the intended application workflow and interact directly with backend logic.

### Risk

High

---

## Vulnerability 4: S3 Object Disclosure via Path Traversal

### Description

The Lambda function constructed S3 object keys using:

```python
template_key = os.path.join(
    "templates",
    f"{template}.txt"
)
```

The application attempted to prevent traversal using:

```python
if ".." in template:
    return None
```

However, supplying an absolute path bypassed the intended restriction.

Example:

```python
template = "/flag"
```

Result:

```python
os.path.join("templates", "/flag.txt")
```

Produces:

```text
/flag.txt
```

The leading slash causes the previous path component to be discarded.

Consequently, the application accessed:

```text
flag.txt
```

instead of:

```text
templates/flag.txt
```

### Impact

An attacker could retrieve arbitrary objects from the private S3 bucket, provided the Lambda execution role had permission to read them.

Potentially exposed data includes:

* Secrets
* Configuration files
* Internal templates
* Challenge flags
* Sensitive application content

### Risk

Critical

---

## Attack Chain

### Step 1

Enumerate public assets:

* S3 bucket name
* API Gateway endpoints
* SNS topic name

### Step 2

Construct SNS Topic ARN.

### Step 3

Subscribe an attacker-controlled HTTPS endpoint.

### Step 4

Trigger invitation generation.

### Step 5

Receive SNS notification containing:

* Registration token
* Lambda function name

### Step 6

Invoke Lambda directly using the valid token.

### Step 7

Abuse path traversal through the template parameter.

### Step 8

Retrieve sensitive S3 objects outside the templates directory.

---

## Root Cause Analysis

### SNS Layer

Insufficient validation of subscriber protocols.

### Lambda Layer

Unsafe use of:

```python
os.path.join()
```

with user-controlled input.

### Application Layer

Sensitive information included in SNS notifications.

### IAM Layer

Overly permissive Lambda invocation permissions.

---

## Remediation

### Restrict SNS Protocols

Require email-only subscriptions.

Example:

```json
{
  "StringEquals": {
    "sns:Protocol": "email"
  }
}
```

### Remove Sensitive Data from Notifications

Do not include:

* Tokens
* Internal resource names
* Function names

### Restrict Lambda Invocation

Replace:

```json
"Principal": "*"
```

with specific trusted principals.

### Secure Path Handling

Use an allowlist:

```python
ALLOWED_TEMPLATES = [
    "default_balloon",
    "birthday",
    "invite"
]
```

Reject all other values.

### Normalize and Validate Paths

Ensure generated paths remain inside the templates directory.

### Least-Privilege IAM

Limit S3 access to:

```text
templates/*
```

rather than the entire bucket.

---

## Severity

| Vulnerability              | Severity |
| -------------------------- | -------- |
| SNS Subscription Bypass    | High     |
| SNS Information Disclosure | Medium   |
| Public Lambda Invocation   | High     |
| S3 Path Traversal          | Critical |
| Combined Attack Chain      | Critical |

## Conclusion

A combination of SNS subscription bypass, information disclosure, public Lambda invocation, and unsafe path handling enabled unauthorized access to sensitive S3 objects. The vulnerabilities were individually significant and, when chained together, resulted in complete compromise of the intended trust boundary protecting private bucket contents.
