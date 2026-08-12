"""Live probe & connection verification script for Google Cloud Run deployment."""

import json
import sys
import urllib.request
import urllib.error

# Set UTF-8 encoding for Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

URLS = [
    "https://autenticacion-continua-api-177686674468.southamerica-west1.run.app",
    "https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app",
]

endpoints = [
    "/health",
    "/live",
    "/ready",
    "/api/health",
    "/api/logistics/health",
]


def test_endpoint(base_url: str, path: str):
    url = f"{base_url}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-Probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status_code = resp.getcode()
            body = resp.read().decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = body[:100]
            print(f"[OK] [{base_url.split('//')[1]}] {path} -> HTTP {status_code} | Output: {data}")
            return True, status_code, data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[FAIL] [{base_url.split('//')[1]}] {path} -> HTTP {e.code} | Error: {body}")
        return False, e.code, body
    except Exception as ex:
        print(f"[ERROR] [{base_url.split('//')[1]}] {path} -> Exception: {ex}")
        return False, 500, str(ex)


def main():
    print("=== TESTING LIVE GOOGLE CLOUD RUN PROBES & CONNECTIONS ===")
    total_passed = 0
    total_tests = 0
    for base_url in URLS:
        print(f"\n--- Testing Base URL: {base_url} ---")
        for path in endpoints:
            total_tests += 1
            ok, code, data = test_endpoint(base_url, path)
            if ok:
                total_passed += 1

    print(f"\nLive Probes Summary: {total_passed}/{total_tests} passed.")


if __name__ == "__main__":
    main()
