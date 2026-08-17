import gssapi
import requests
import base64

target_name = gssapi.Name('HTTP@dc02.darkzero.ext', gssapi.NameType.hostbased_service)
ctx = gssapi.SecurityContext(name=target_name, usage='initiate')

token1 = ctx.step()
auth_header = "Negotiate " + base64.b64encode(token1).decode()

s = requests.Session()
r1 = s.get("http://dc02.darkzero.ext:3000/api/v1/user",
           headers={"Authorization": auth_header})

print("Round 1 status:", r1.status_code)
www_auth = r1.headers.get("Www-Authenticate", "")
print("WWW-Authenticate:", www_auth[:80], "...")

if www_auth.startswith("Negotiate "):
    server_token_b64 = www_auth.split(" ", 1)[1]
    server_token = base64.b64decode(server_token_b64)

    token2 = ctx.step(server_token)
    if token2:
        auth_header2 = "Negotiate " + base64.b64encode(token2).decode()
        r2 = s.get("http://dc02.darkzero.ext:3000/api/v1/user",
                    headers={"Authorization": auth_header2},
                    cookies=r1.cookies)
        print("Round 2 status:", r2.status_code)
        print(r2.text[:1000])
    else:
        print("Context complete after step 2, no further token generated.")
        print("ctx.complete:", ctx.complete)
else:
    print("No continuation token found; server_token missing.")
