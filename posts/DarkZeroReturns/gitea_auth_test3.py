import requests
import gssapi
from requests_gssapi import HTTPSPNEGOAuth

# Check GSSAPI can see our ticket cache
try:
    creds = gssapi.Credentials(usage='initiate')
    print("GSSAPI sees credentials for:", creds.name)
except Exception as e:
    print("GSSAPI credential error:", e)

proxies = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080",
}

s = requests.Session()
s.proxies = proxies

try:
    r = s.get("http://dc02.darkzero.ext:3000/api/v1/user", auth=HTTPSPNEGOAuth())
    print(r.status_code)
except Exception as e:
    print("Request/auth error:", repr(e))
