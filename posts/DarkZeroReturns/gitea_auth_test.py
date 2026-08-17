import requests
from requests_gssapi import HTTPSPNEGOAuth

proxies = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080",
}

s = requests.Session()
s.proxies = proxies
r = s.get("http://dc02.darkzero.ext:3000/api/v1/user", auth=HTTPSPNEGOAuth())
print(r.status_code)
print(r.text[:500])
