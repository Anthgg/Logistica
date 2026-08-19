"""Pre-UAT Runtime Identity Guard.

Validates that:
1. Expected Candidate Git SHA matches local HEAD.
2. Docker backend container is running and healthy on port 8000.
3. Docker bind-mounts point exclusively to the active worktree with 0 references to other tracks.
4. Active Python runtime in container contains expected feature patches.
5. Live health and authenticated endpoints respond with HTTP 200.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
import http.cookiejar


def run_cmd(cmd: list[str]) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def verify_runtime(expected_sha: str, expected_worktree_substr: str, forbidden_worktree_substr: str):
    print("=== 1. VERIFYING GIT WORKTREE SHA ===")
    local_sha = run_cmd(["git", "rev-parse", "HEAD"])
    print(f"Local Git SHA: {local_sha}")
    if local_sha != expected_sha:
        print(f"[FAIL] Expected SHA {expected_sha}, found {local_sha}")
        sys.exit(1)
    print("[PASS] Git SHA matches expected candidate.")

    print("\n=== 2. VERIFYING DOCKER CONTAINER MOUNTS ===")
    inspect_out = run_cmd(["docker", "inspect", "continuous-authentication-backend-1"])
    data = json.loads(inspect_out)[0]
    mounts = data.get("Mounts", [])
    has_expected_mount = False
    forbidden_mounts = []
    for m in mounts:
        src = m.get("Source", "")
        if expected_worktree_substr.lower() in src.lower():
            has_expected_mount = True
        if forbidden_worktree_substr.lower() in src.lower():
            forbidden_mounts.append(src)
        print(f" - {m.get('Type')}: {src} -> {m.get('Destination')}")

    if not has_expected_mount:
        print(f"[FAIL] Missing expected worktree mount for {expected_worktree_substr}")
        sys.exit(1)
    if forbidden_mounts:
        print(f"[FAIL] Found forbidden mounts to {forbidden_worktree_substr}: {forbidden_mounts}")
        sys.exit(1)
    print("[PASS] Docker mounts point strictly to active worktree (0 forbidden references).")

    print("\n=== 3. VERIFYING AUDIT SERVICE PATCH IN CONTAINER RUNTIME ===")
    check_code = (
        "import inspect\n"
        "from app.modules.logistics.audit.service import AuditService\n"
        "src = inspect.getsource(AuditService.list)\n"
        "assert 'category: str | None = None' in src\n"
        "assert 'organization_id: UUID | None = None' in src\n"
        "print('PATCH_OK')\n"
    )
    patch_out = run_cmd(["docker", "exec", "continuous-authentication-backend-1", "python", "-c", check_code])
    if "PATCH_OK" not in patch_out:
        print("[FAIL] Audit service patch not detected in runtime container.")
        sys.exit(1)
    print("[PASS] Audit service patch verified inside running container.")

    print("\n=== 4. VERIFYING HEALTH AND AUTHENTICATED ENDPOINTS ===")
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # CSRF & Login
    csrf_res = opener.open("http://127.0.0.1:8000/api/auth/csrf")
    csrf_token = json.loads(csrf_res.read().decode("utf-8")).get("csrf_token")
    login_data = json.dumps({"email": "usuario@example.com", "password": "Admin123!"}).encode("utf-8")
    login_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf_token},
    )
    login_res = opener.open(login_req)
    assert login_res.status == 200

    # Logistics Health
    health_req = urllib.request.Request("http://127.0.0.1:8000/api/logistics/health")
    health_res = opener.open(health_req)
    health_body = json.loads(health_res.read().decode("utf-8"))
    assert health_res.status == 200
    assert health_body.get("status") == "ok"
    print(f"Health check: {health_body}")

    # Audit Events
    audit_req = urllib.request.Request("http://127.0.0.1:8000/api/logistics/audit-events?page=1&page_size=20")
    audit_res = opener.open(audit_req)
    audit_body = json.loads(audit_res.read().decode("utf-8"))
    assert audit_res.status == 200
    print(f"Audit events total: {audit_body.get('total')}, page items: {len(audit_body.get('items', []))}")

    print("\n=== ALL RUNTIME IDENTITY CHECKS PASSED SUCCESSFULLY ===")


if __name__ == "__main__":
    verify_runtime(
        expected_sha="8134eddf616abc85f1c7bac000b076092448b030",
        expected_worktree_substr="Logistica-F003",
        forbidden_worktree_substr="logistica-history",
    )
