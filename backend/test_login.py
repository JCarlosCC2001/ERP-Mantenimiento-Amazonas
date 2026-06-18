import urllib.request
import json

url = "http://localhost:8000/api/auth/login"
data = json.dumps({"email": "alfonso.curi@mantenimiento-amazonas.pe", "password": "ACuri#Amazonas"}).encode()

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        print("LOGIN OK:", json.loads(resp.read()))
except urllib.error.HTTPError as e:
    print("ERROR", e.code, e.read().decode())
