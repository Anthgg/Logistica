"""Detector de secretos en texto y ficheros (Fase 005.3).

Nace de un incidente concreto: durante F005.2, un comando de auditoría imprimió la
cadena de conexión productiva completa, y el enmascarado de un script falló ante una
URL con comillas y acabó volcando el valor crudo. Ambas cosas eran evitables.

Se usa de dos formas:

- como filtro de salida: ``... | python scripts/scan_for_secrets.py --stdin``
- como auditoría de ficheros: ``python scripts/scan_for_secrets.py .github docs``

Nunca imprime el valor encontrado: solo el fichero, la línea y qué clase de secreto
parece. Un detector que cita lo que encuentra es otra fuga.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

#: Extensiones que se revisan al recorrer directorios.
SCANNED_SUFFIXES = frozenset(
    {".yml", ".yaml", ".md", ".py", ".sh", ".json", ".toml", ".ini", ".env", ".txt", ""}
)

#: Directorios que nunca aportan señal y sí mucho ruido.
SKIPPED_DIRS = frozenset({".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"})


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


RULES: tuple[Rule, ...] = (
    Rule("cadena de conexión PostgreSQL con credenciales", re.compile(r"postgres(?:ql)?(?:\+\w+)?://[^\s\"'<>]*:[^\s\"'<>@]+@")),
    Rule("SECRET_KEY con valor literal", re.compile(r"SECRET_KEY\s*[:=]\s*[\"']?(?!\$\{)(?![A-Z_]*PRODUCTION)[^\s\"',}]{8,}")),
    Rule("JWT_SECRET con valor literal", re.compile(r"JWT_SECRET\s*[:=]\s*[\"']?(?!\$\{)[^\s\"',}]{8,}")),
    Rule("password con valor literal", re.compile(r"(?i)pass(?:word|wd)\s*[:=]\s*[\"']?(?!\$\{)(?!\*)[^\s\"',}]{8,}")),
    Rule("service role key de Supabase", re.compile(r"(?i)service[_-]role[_-]key\s*[:=]\s*[\"']?[A-Za-z0-9._-]{20,}")),
    Rule("JSON Web Token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")),
    Rule("clave privada PEM", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    Rule("clave de API de Google", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
)

#: Una credencial contra la máquina local no es un secreto productivo: son las bases
#: efímeras de CI y de desarrollo.
LOCAL_HOSTS = ("@localhost", "@127.0.0.1", "@postgres:", "@db:", "@host.docker.internal")

#: `NOMBRE:latest` es una referencia a Secret Manager — justo el patrón seguro que esta
#: fase introduce. Marcarlo convertiría la buena práctica en un fallo.
SECRET_REFERENCE = re.compile(r"[A-Z][A-Z0-9_]*\s*[:=]\s*[A-Z][A-Z0-9_]*:(?:latest|\d+)")

#: Marcadores que indican que la línea es un ejemplo, no un secreto real. Sin esto, la
#: propia documentación de esta fase se denunciaría a sí misma.
PLACEHOLDER_MARKERS = (
    "example",
    "ejemplo",
    "placeholder",
    "<",
    "***",
    "REDACTED",
    "change-me",
    "changeme",
    "your-",
    "xxx",
    "dummy",
    "fake",
    "development-only",
    "replace-with",
    "test-only",
)


def looks_like_placeholder(line: str) -> bool:
    lowered = line.lower()
    if any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS):
        return True
    if any(host in lowered for host in LOCAL_HOSTS):
        return True
    return bool(SECRET_REFERENCE.search(line))


def scan_text(text: str, origin: str) -> list[str]:
    """Devuelve un hallazgo por línea sospechosa, **sin** incluir el valor."""
    findings: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if looks_like_placeholder(line):
            continue
        for rule in RULES:
            if rule.pattern.search(line):
                findings.append(f"{origin}:{number}: {rule.name}")
                break
    return findings


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIPPED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Busca secretos en texto o ficheros.")
    parser.add_argument("paths", nargs="*", type=Path, help="Ficheros o directorios a revisar.")
    parser.add_argument("--stdin", action="store_true", help="Revisar la entrada estándar.")
    args = parser.parse_args()

    if not args.stdin and not args.paths:
        parser.error("indica rutas o usa --stdin")

    findings: list[str] = []

    if args.stdin:
        findings.extend(scan_text(sys.stdin.read(), "<stdin>"))

    for root in args.paths:
        if not root.exists():
            print(f"FAIL: no existe {root}", file=sys.stderr)
            return 2
        for path in iter_files(root):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            findings.extend(scan_text(content, str(path)))

    if findings:
        print(f"SECRET_LEAKS={len(findings)}")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print("SECRET_LEAKS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
