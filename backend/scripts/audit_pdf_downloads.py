"""Audit the PDF download contract across the logistics backend.

Reads the OpenAPI schema (from the local app by default, or from a running
instance with ``--base-url``) and reports, for every operation that advertises
``application/pdf``:

* whether it is a preview (``inline``) or a download (``attachment``);
* whether every preview has a download counterpart;
* optionally, the live response headers for endpoints that can be probed.

No credentials are embedded. Probing a protected endpoint without a session is
expected to return 401 and is reported as such rather than treated as an error.

Usage::

    python scripts/audit_pdf_downloads.py
    python scripts/audit_pdf_downloads.py --base-url http://127.0.0.1:8000 --probe
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

PDF_MEDIA_TYPE = "application/pdf"

# Suffix pairs that mark a preview route and the download that must accompany it.
DOWNLOAD_SUFFIXES = ("/pdf", ".pdf", "/download")


BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_schema(base_url: str | None) -> dict:
    if base_url:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/openapi.json", timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    # Running a script puts scripts/ on sys.path, not the backend root, so make
    # the import work regardless of the working directory the caller used.
    if BACKEND_ROOT not in sys.path:
        sys.path.insert(0, BACKEND_ROOT)
    from app.main import app  # imported lazily so --base-url works without deps

    return app.openapi()


def pdf_operations(schema: dict) -> list[tuple[str, str, dict]]:
    found = []
    for path, operations in schema.get("paths", {}).items():
        for method, operation in operations.items():
            if not isinstance(operation, dict):
                continue
            for response in (operation.get("responses") or {}).values():
                if PDF_MEDIA_TYPE in (response.get("content") or {}):
                    found.append((method.upper(), path, operation))
                    break
    return sorted(found, key=lambda row: (row[1], row[0]))


def is_preview(path: str) -> bool:
    return path.endswith(("/preview", "/document-preview"))


def expected_downloads(path: str) -> list[str]:
    """Candidate download routes for a given preview route."""
    if path.endswith("/preview"):
        return [path + ".pdf", path.rsplit("/preview", 1)[0] + "/pdf"]
    if path.endswith("/document-preview"):
        return [path + ".pdf"]
    return []


def probe(base_url: str, method: str, path: str) -> str:
    """Probe an endpoint without credentials; 401 is the expected good outcome."""
    if "{" in path:
        return "SKIPPED (templated path)"
    url = f"{base_url.rstrip('/')}{path}"
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            ctype = response.headers.get("Content-Type", "")
            disposition = response.headers.get("Content-Disposition", "")
            nosniff = response.headers.get("X-Content-Type-Options", "")
            return f"{response.status} {ctype} | {disposition} | nosniff={nosniff}"
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return f"{exc.code} (auth enforced, as expected)"
        return f"{exc.code}"
    except urllib.error.URLError as exc:  # pragma: no cover - environment dependent
        return f"UNREACHABLE ({exc.reason})"


def routes_returning_pdf(app_root: str) -> int:
    """Count route handlers that build a PDF response, straight from the source.

    Compared against the OpenAPI declarations so a PDF route can never be added
    without also advertising ``application/pdf``.
    """
    import ast

    total = 0
    for dirpath, dirnames, filenames in os.walk(app_root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as handle:
                src = handle.read()
            if "build_pdf_" not in src:
                continue
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                body = ast.get_source_segment(src, node) or ""
                if "build_pdf_download_response(" not in body and (
                    "build_pdf_preview_response(" not in body
                ):
                    continue
                for dec in node.decorator_list:
                    if (
                        isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr in ("get", "post", "put", "patch")
                    ):
                        total += 1
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", help="Probe a running instance instead of importing the app")
    parser.add_argument("--probe", action="store_true", help="Issue unauthenticated requests")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero on any preview without a download or undeclared PDF route",
    )
    parser.add_argument(
        "--min-operations",
        type=int,
        default=0,
        help="Fail if fewer than this many PDF operations are declared",
    )
    parser.add_argument(
        "--app-root",
        default=os.path.join(BACKEND_ROOT, "app"),
        help="Source root scanned to cross-check declarations (default: <backend>/app)",
    )
    args = parser.parse_args()

    schema = load_schema(args.base_url)
    operations = pdf_operations(schema)
    paths = {path for _, path, _ in operations}

    print(f"PDF operations declaring {PDF_MEDIA_TYPE}: {len(operations)}")
    print()

    previews = [(m, p) for m, p, _ in operations if is_preview(p)]
    downloads = [(m, p) for m, p, _ in operations if not is_preview(p)]
    print(f"  preview endpoints : {len(previews)}")
    print(f"  download endpoints: {len(downloads)}")
    print()

    missing: list[str] = []
    for _, path in previews:
        candidates = expected_downloads(path)
        if not any(c in paths for c in candidates):
            missing.append(path)

    print("Preview endpoints without a download counterpart:", len(missing))
    for path in missing:
        print("  MISSING DOWNLOAD:", path)
    print()

    if args.probe:
        if not args.base_url:
            print("--probe requires --base-url", file=sys.stderr)
            return 2
        print("Unauthenticated probes (401/403 is the expected result):")
        for method, path, _ in operations:
            print(f"  {method:5} {path}\n        -> {probe(args.base_url, method, path)}")
        print()

    for method, path, operation in operations:
        kind = "PREVIEW " if is_preview(path) else "DOWNLOAD"
        print(f"  {kind} {method:5} {path}")
        summary = operation.get("summary")
        if summary:
            print(f"           {summary}")

    failures = []
    if missing:
        failures.append(f"PREVIEW_WITHOUT_DOWNLOAD={len(missing)}")

    if args.check:
        in_source = routes_returning_pdf(args.app_root)
        undeclared = in_source - len(operations)
        print()
        print(f"PDF routes in source     : {in_source}")
        print(f"PDF operations declared  : {len(operations)}")
        print(f"INVALID_PDF_OPENAPI      : {max(undeclared, 0)}")
        if undeclared > 0:
            failures.append(f"INVALID_PDF_OPENAPI={undeclared}")
        if args.min_operations and len(operations) < args.min_operations:
            failures.append(
                f"PDF_OPERATIONS={len(operations)} < min {args.min_operations}"
            )

    if failures:
        print()
        for failure in failures:
            print("FAIL:", failure, file=sys.stderr)
        return 1

    print()
    print("PDF audit: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
