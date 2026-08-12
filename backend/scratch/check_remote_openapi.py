import json
import urllib.request

url = "https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/openapi.json"
req = urllib.request.Request(url, headers={"User-Agent": "ProbeClient/1.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode("utf-8"))

paths = sorted(list(data.get("paths", {}).keys()))
print(f"Total OpenAPI paths on Cloud Run: {len(paths)}")
print("All paths under /api/logistics:")
for p in paths:
    if p.startswith("/api/logistics"):
        print(" -", p)
