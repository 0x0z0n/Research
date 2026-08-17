import gssapi
import requests
import base64

proxies = {
    "http": "socks5h://127.0.0.1:1080",
    "https": "socks5h://127.0.0.1:1080",
}

target_name = gssapi.Name('HTTP@dc02.darkzero.ext', gssapi.NameType.hostbased_service)
ctx = gssapi.SecurityContext(name=target_name, usage='initiate')

token = ctx.step()
auth_header = "Negotiate " + base64.b64encode(token).decode()

s = requests.Session()
s.proxies = proxies
r = s.get("http://dc02.darkzero.ext:3000/api/v1/user",
          headers={"Authorization": auth_header})
print(r.status_code)
print(r.text[:2000])
