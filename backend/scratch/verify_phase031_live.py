import sys
import urllib.request

# Force UTF-8 output for Windows terminals
sys.stdout.reconfigure(encoding='utf-8')

base_url = "https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app"

probes = [
    "/live",
    "/ready",
    "/api/health",
    "/api/logistics/health",
    "/api/logistics/cost-centers/",
    "/api/logistics/procurement/requisitions/",
]

print("=== PHASE 031 CLOUD RUN LIVE VERIFICATION ===")
for path in probes:
    url = base_url + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ProbeClient/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")[:200]
            print(f"[OK] HTTP {status} {path}")
            print(f"     Response: {body}")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print(f"[OK-AUTH] HTTP {e.code} {path} - endpoint exists & protected by RBAC (expected)")
        elif e.code == 404:
            print(f"[INFO] HTTP {e.code} {path} - not found")
        else:
            print(f"[ERR] HTTP {e.code} {path} - {e}")
    except Exception as e:
        print(f"[ERR] {path} - {e}")

print()
print("=== PHASE 031 CLOUD RUN VERIFICATION COMPLETE ===")
