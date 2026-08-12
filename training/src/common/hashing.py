import hashlib
import json
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return sha256_bytes(payload)


def directory_fingerprint(path: str | Path) -> dict[str, str]:
    root = Path(path).resolve()
    if not root.exists():
        return {}
    return {
        item.relative_to(root).as_posix(): sha256_file(item)
        for item in sorted(root.rglob("*"))
        if item.is_file()
    }
