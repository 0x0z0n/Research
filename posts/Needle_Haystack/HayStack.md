# Needle in a Haystack


We have got intelligence that one our developers at Ack-Me Corp is working on a weekend side-project where he is vibe coding an internal knowledge-base chatbot for our company, where he put all of our customer records and sensitive data inside it.

Your mission, if you choose to accept it - is to track down the website and obtain the secret flag.

Start by investigating ackme-corp.net online presence and dig deep into their infrastructure, this includes going beyond the scope of the shell.




The prompt gives us two massive clues:

1. **"Going beyond the scope of the shell"**: This means the answer isn't just sitting on a running web server waiting to be exploited. We need to look at public records, source code repositories, and DNS history.

2. **"Weekend side-project" & "Vibe coding"**: This strongly implies a developer pushed code to a public repository (like GitHub or GitLab) or deployed it to a modern PaaS platform (like Vercel, Netlify, or Render) outside of the company's official infrastructure.

Here is our tactical recon plan to track down this hidden chatbot.

### Phase 1: Passive Subdomain Enumeration
Before we go looking for rogue deployments, let's see if the developer accidentally mapped this project to the main corporate domain. We want to look for subdomains containing keywords like `chat`, `kb`, `bot`, `dev`, or `test`.

Run these from your terminal:
* **Query Certificate Transparency Logs (crt.sh):**
```bash
user@monthly-challenge:~$ curl -s "https://crt.sh/?q=%25.ackme-corp.net&output=json" | jq -r '.[].name_value' | sort -u
user@monthly-challenge:~$ subfinder -d ackme-corp.net -all -silent
mail.app.ackme-corp.net
ackme-corp.net
app.ackme-corp.net
interactsh.ackme-corp.net
www.ackme-corp.net
ns2.app.ackme-corp.net
ns1.app.ackme-corp.net
user@monthly-challenge:~$ 
    ```

The `subfinder` output just gave us some very interesting threads to pull. 

Let's break down what we found:
* `app`, `www`, `mail`, `ns1`, `ns2`: These are standard corporate infrastructure. `app` is definitely worth a closer look.
* **`interactsh.ackme-corp.net`**: This is a massive anomaly. `interactsh` is a tool used by security researchers for Out-of-Band (OOB) vulnerability testing (like a self-hosted Burp Collaborator). The fact that this exists means either the developers are doing security testing, or this is a hint for a blind vulnerability (like SSRF or blind RCE) we might need later. Keep it in your back pocket.

However, none of these explicitly say "chatbot" or "knowledge-base," which aligns with the hint: *"going beyond the scope of the shell."*

Here is your two-pronged attack plan for Phase 2:

### 1. Probe the Live Infrastructure (Inside the Shell)
Let's see which of these subdomains are actually hosting a web server and what they look like. If you have `httpx` installed in your CTF environment, run this to get the status codes, titles, and technologies:

```bash
echo -e "ackme-corp.net\napp.ackme-corp.net\nmail.app.ackme-corp.net\ninteractsh.ackme-corp.net\nwww.ackme-corp.net" | httpx -silent -title -tech-detect -status-code
```
*(If you don't have `httpx`, just do a quick `curl -I https://app.ackme-corp.net` to see the headers).*

Ah, the classic `Could not resolve host` error. That is actually a fantastic piece of information. 

It tells us that those subdomains are either dead DNS records, strictly internal, or just pure distractions. The flag is *not* sitting on the main corporate infrastructure.

This brings us right back to the scenario description: a developer is **"vibe coding a weekend side-project."** Just like in a classic HTB OSINT machine, when the main infrastructure goes cold, we turn to source code repositories. Developers love to push their weekend projects to public GitHub repos and deploy them to platforms like Vercel or Render.

### Phase 2: The GitHub Hunt (Outside the Shell)

You need to step outside your web terminal for this one. Open up a new tab in your regular web browser and go to **[GitHub.com/search](https://github.com/search)**.

We are going to use specific "dorks" to find the rogue developer's repository. Make sure you select the **"Code"** tab in the GitHub search results so we are searching the actual source code, not just repository names.

Try these exact queries one by one:

1. https://github.com/search?q=%22ackme-corp.net%22&type=code
2. https://github.com/search?q=%22Ack-Me+Corp%22+chatbot&type=code
3. https://github.com/search?q=%22ackme-corp%22+API_KEY&type=code (Since they are vibe-coding an AI chatbot, they likely leaked an API key or an environment variable).


https://github.com/alejandro-pigeon/just-testing-stuff-thanks/commits/main/

Revision,Removed (-),Added (+)
Rev 1,docs.staging.chase.io,sphinxdocs.pyansys.co
Rev 2,sphinxdocs.pyansys.co,morpheus-docs.dev.vtg.paramount.tech
Rev 3,morpheus-docs.dev.vtg.paramount.tech,testing.internal.hacme-corp.net
Rev 4,testing.internal.hacme-corp.net,testing.internal.ackme-corp.net
Rev 5,testing.internal.ackme-corp.net,testing.internal.ackme-corp.com
Rev 6,testing.internal.ackme-corp.com,testing.internal.ackme-corp.net

**What are you looking for?**
You want to find any public repository that contains these strings. Once you find it, look for a `README.md`, a `package.json`, or a `.env` file. We are hunting for a staging URL (like `something.vercel.app`) or hardcoded credentials.

Ah, the classic developer cover-up! Alejandro realized he leaked something and tried to scrub the repository clean, leaving only a "hello" and a `CNAME` file. 

But Git never forgets. If the code isn't in the current view, it is hiding in one of two places. 

Here is how we pull the deleted code from the void using the GitHub web interface:

### 1. Check the Hidden Branches (The `gh-pages` trick)
By default, GitHub shows you the `main` or `master` branch. But when developers deploy to GitHub Pages, the actual code is often pushed to a separate, automatically generated branch. 
* On the repository page, look for the button that says **`main`** or **`master`** (usually on the left side, above the file list). 
* Click it to open the dropdown. 
* Do you see a branch named **`gh-pages`**, **`dev`**, or **`build`**? If you do, click it! The entire chatbot source code might be sitting right there.

### 2. Time Travel through the Commit History
If there are no other branches, Alejandro definitely committed the code and then deleted it in a subsequent commit. We can literally travel back in time to the exact moment the code existed.
* On the main repository page (where it says `Update README.md · 7 months ago`), look to the right side for a button that says something like **`3 Commits`** (the number might be different, accompanied by a little clock icon). 
* Click that to view the repository's entire timeline.
* Scroll down to the **oldest commits** at the bottom of the list. Look for names like *"Initial commit"*, *"first draft"*, or *"added chatbot"*.
* Click the `< >` button (View repository at this point in history) next to those old commits. 



Mission accepted. Here is the detailed, step-by-step technical write-up for the Ack-Me Corp internal knowledge-base investigation, formatted for clarity and scannability.

***

# Technical Investigation Report: Ack-Me Corp Internal Chatbot

## Objective
Track down the "vibe-coded" internal knowledge-base chatbot hosted by an Ack-Me Corp developer and obtain the secret flag by circumventing authentication controls.

---

## Phase 1: Initial Reconnaissance

The investigation begins with analyzing the online presence of the primary domain, `ackme-corp.net`. 

### 1. GitHub Repository Discovery
A search on GitHub for the domain reveals a repository of interest. 
* The repository contains a GitHub Pages deployment with several intriguing subdomains.
* Currently, the live page hosts no interesting content.

### 2. CNAME Version History Analysis
Reviewing the version control history of the `CNAME` file reveals a timeline of previous domains:
1.  `docs.staging.chase.io` (Inactive, no snapshots)
2.  `sphinxdocs.pyansys.co` (Inactive, no snapshots)
3.  `morpheus-docs.dev.vtg.paramount.tech` (Hosted the current GitHub Pages content in March of this year)
4.  `testing.internal.hacme-corp.net`

### 3. Certificate Transparency Search
Investigating the `testing.internal.hacme-corp.net` domain via `crt.sh` reveals subdomains specified in the SSL certificate:
* **Target Subdomain:** `vibe.coding.internal.test.hacme-corp.net` matches the "vibe coding" intelligence. While currently inactive, archived snapshots from a few days prior are available via Recorded Future.
* **Pivot Domain:** `vibecodeawebsitetoday.com` was identified. (This will be utilized later in the exploit chain).
* **Current Target:** `testing.internal.ackme-corp.com` mirrors the subdomains of the GitLab Pages deployment. 

---

## Phase 2: Subdomain Enumeration

Given the presence of wildcard subdomains in the certificates for both `hacme-corp.net` and `ackme-corp.net`, deep enumeration is required. The current GitHub Pages deployment sits at `testing.internal.ackme-corp.net`.

Using the provided 5,000-word list at `/opt/wordlists/subdomain-wordlist.txt`, we utilized **ffuf** to fuzz the domain.

**Attempt 1: Standard Fuzzing**
```bash
ffuf -u http://FUZZ.testing.internal.ackme-corp.net -w /opt/wordlists/subdomain-wordlist.txt -mc 200,301,302 -s
```
*Result: No hits.*

**Attempt 2: Nested Subdomain Fuzzing (Pattern Matching)**
Assuming a nested structure combining the keyword "coding" (discovered in Phase 1):
```bash
ffuf -u http://FUZZ.REDACTED.testing.internal.ackme-corp.net -w /opt/wordlists/subdomain-wordlist.txt -mc 200,301,302
```
*Result: No hits.*

**Attempt 3: Alternate Nested Subdomain Fuzzing**
```bash
ffuf -u http://REDACTED.FUZZ.testing.internal.ackme-corp.net -w /opt/wordlists/subdomain-wordlist.txt -mc 200,301,302 -s
```
*Result: Success. The endpoint returned an HTTP 200 OK, revealing a hosted login portal.*

---

## Phase 3: Portal Analysis & Client-Side Bypass

### 1. Login Portal Behavior
Investigating the newly discovered login portal reveals strict access controls. Attempting to log in with an email that does not end in `@ackme-corp.net` fails to generate a network request.

Inspecting the page's source code reveals a **client-side validation** vulnerability:
```javascript
// Client-side validation: Only allow @ackme-corp.net emails
if (!email.toLowerCase().endsWith('@ackme-corp.net')) {
    showError('Access restricted to Ack-Me Corp employees only (@ackme-corp.net emails)');
    return;
}
```
Further inspection shows the actual login API call, meaning we can bypass the UI and hit the endpoint directly if we obtain valid credentials:
```javascript
try {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    });
```

### 2. Investigating the Pivot Domain
Navigating to the previously discovered `vibecodeawebsitetoday.com` reveals a fictional "VibeCode" service landing page. 
* The page is static; buttons do not trigger network requests.
* Fuzzing the directory structure with the `api-objects.txt` wordlist yields a breakthrough:

```bash
ffuf -u https://vibecodeawebsitetoday.com/FUZZ -w /opt/wordlists/api-objects.txt -mc 200,301,302 -s
```
*Result: Discovered live API documentation (Swagger/OpenAPI UI).*

---

## Phase 4: API Exploitation & Authentication

### 1. API Registration
The API documentation requires an `app_id` to execute authentication endpoints. By reviewing the source code of our target login portal, the specific `app_id` is extracted.

Attempting to register via the API with an `@ackme-corp.net` email fails:
```json
{
  "status": "error",
  "message": "Registration failed. Ack-Me Corp employees should use the internal portal for authentication."
}
```

However, registering with an external email (`testing@email.net`) and password (`testing123`) using the documentation's execution feature succeeds:
```json
{
  "status": "success",
  "message": "Registration successful. You can now login with your credentials.",
  "app_id": "REDACTED",
  "verified": true,
  "dev_note": "Account auto-verified for immediate access"
}
```

### 2. Token Generation
Logging into the API documentation portal with the newly created `testing@email.net` credentials yields a valid JWT:
```json
{
  "status": "success",
  "token": "REDACTED",
  "message": "Login successful!",
  "app_id": "REDACTED"
}
```

---

## Phase 5: Target App Exploitation & LLM Jailbreak

Discovering the `/openapi.json` file on the target application maps out the internal routing:
* `/login` → Login UI
* `/api/auth/login` → Authentication endpoint
* `/chat` → Chat interface
* `/api/chat` → Chatbot endpoint
* `/api/health` → Health check

### 1. Bypassing the Target Authentication
Using the credentials created on the VibeCode API, we manually send a POST request to the target app's login endpoint, bypassing the client-side JavaScript restriction entirely.

**Variable Setup:**
```bash
APP='http://coding.pprod.testing.internal.ackme-corp.net'
EMAIL='testing@email.net'
PASS='testing123'
```

**cURL Execution:**
```bash
curl -isS -H 'content-type: application/json' -X POST "$APP/api/auth/login" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}"
```

**Response:**
```http
HTTP/1.1 200 OK
Server: nginx/1.29.1
Date: Mon, 29 Sep 2025 21:45:07 GMT
Content-Type: application/json
Content-Length: 39
Connection: keep-alive
set-cookie: session_token=6EEVbQ55QcgsUqRnJDHOWHuKmCg2qYje42dOvHWLad4; HttpOnly; Max-Age=86400; Path=/; SameSite=lax
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block

{"status":"success","redirect":"/chat"}
```

### 2. Final Stage: Console Scripting
With the `session_token` successfully set as an HTTP-only cookie, direct interactions with the `/chat` endpoint are authorized. 

To automate the extraction of the flag from the vibe-coded LLM, a custom script is written and executed directly within the browser's developer console. This script iterates through a series of LLM jailbreak prompts, passing the authenticated session to the chatbot until the sensitive data (the secret flag) is successfully extracted.