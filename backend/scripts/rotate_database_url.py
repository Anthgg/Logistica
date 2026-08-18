"""Publica una versión nueva de `DATABASE_URL_PRODUCTION` tras rotar la contraseña.

La contraseña de la base la rota el panel de Supabase: el rol `postgres` no puede
cambiar la suya por SQL (`InsufficientPrivilege`). Lo que sí puede automatizarse es
todo lo demás, que es donde suelen ocurrir las filtraciones.

El valor nuevo se pide por entrada oculta y viaja en memoria hasta Secret Manager. No
pasa por la línea de comandos, ni por el historial del intérprete, ni por un fichero
temporal, ni por la pantalla. La estructura de la URL (usuario, host, puerto, base) se
toma de la versión vigente del secreto, así que no hay que reescribirla a mano.

Uso:
    python scripts/rotate_database_url.py
    python scripts/rotate_database_url.py --secret OTRO_SECRETO --project OTRO_PROYECTO
"""

from __future__ import annotations

import argparse
import getpass
import shutil
import subprocess
import sys
from urllib.parse import quote, urlsplit, urlunsplit

DEFAULT_SECRET = "DATABASE_URL_PRODUCTION"
DEFAULT_PROJECT = "gen-lang-client-0356667380"


def find_gcloud() -> str:
    """`gcloud` es un `.cmd` en Windows y no siempre resuelve por nombre."""
    for candidate in ("gcloud", "gcloud.cmd"):
        found = shutil.which(candidate)
        if found:
            return found
    print("FAIL: no se encontró gcloud en el PATH.", file=sys.stderr)
    raise SystemExit(2)


def run_gcloud(gcloud: str, args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    # check=False a propósito: cada llamada interpreta su propio fallo.
    return subprocess.run([gcloud, *args], capture_output=True, text=True, input=stdin, check=False)


def masked(host: str) -> str:
    head, _, tail = host.partition(".")
    return f"{head[:2]}***.{tail}" if tail else "***"


def main() -> int:
    parser = argparse.ArgumentParser(description="Publica una versión nueva del secreto de conexión.")
    parser.add_argument("--secret", default=DEFAULT_SECRET)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument(
        "--skip-connectivity-check",
        action="store_true",
        help="No comprobar la conexión antes de publicar (no recomendado).",
    )
    args = parser.parse_args()

    gcloud = find_gcloud()

    result = run_gcloud(
        gcloud,
        ["secrets", "versions", "access", "latest", f"--secret={args.secret}", f"--project={args.project}"],
    )
    current = result.stdout.strip()
    if not current.startswith("postgres"):
        print(f"FAIL: no se pudo leer {args.secret}.", file=sys.stderr)
        return 2

    parts = urlsplit(current)
    user = parts.username or "postgres"
    host = parts.hostname or ""
    port = parts.port or 5432
    database = parts.path.lstrip("/") or "postgres"
    old_password = parts.password or ""

    print(f"Secreto  : {args.secret}")
    print(f"Destino  : {user}@{masked(host)}:{port}/{database}")
    print("La estructura se reutiliza; solo cambia la contraseña.\n")

    new_password = getpass.getpass("Contraseña NUEVA (no se muestra): ")
    if not new_password:
        print("FAIL: contraseña vacía.", file=sys.stderr)
        return 2
    if getpass.getpass("Repite la contraseña: ") != new_password:
        print("FAIL: las dos entradas no coinciden.", file=sys.stderr)
        return 2
    if new_password == old_password:
        print("FAIL: es la misma contraseña que ya está publicada.", file=sys.stderr)
        return 2

    def dsn(password: str) -> str:
        return f"postgresql://{quote(user)}:{quote(password, safe='')}@{host}:{port}/{database}"

    if not args.skip_connectivity_check:
        try:
            import psycopg
        except ImportError:
            print("AVISO: psycopg no está disponible; se omite la comprobación de conexión.")
        else:
            try:
                with psycopg.connect(dsn(new_password), connect_timeout=20) as conn:
                    conn.execute("SELECT 1")
            except Exception as exc:  # noqa: BLE001 — se resume el tipo, nunca el valor
                # Publicar una credencial que no conecta deja producción sin base en
                # cuanto arranque la primera instancia nueva.
                print(f"FAIL: la contraseña nueva no conecta ({type(exc).__name__}). No se publica nada.", file=sys.stderr)
                return 1
            print("Conexión con la contraseña nueva ......................... OK")

    netloc = f"{quote(user)}:{quote(new_password, safe='')}@{host}:{port}"
    new_url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    result = run_gcloud(
        gcloud,
        ["secrets", "versions", "add", args.secret, f"--project={args.project}", "--data-file=-"],
        stdin=new_url,
    )
    if result.returncode != 0:
        print(f"FAIL: no se pudo publicar la versión nueva.\n{result.stderr.strip()[:200]}", file=sys.stderr)
        return 1
    print("Versión nueva del secreto publicada ...................... OK")

    if old_password:
        try:
            import psycopg

            with psycopg.connect(dsn(old_password), connect_timeout=20) as conn:
                conn.execute("SELECT 1")
        except ImportError:
            pass
        except Exception:  # noqa: BLE001 — cualquier fallo aquí significa lo mismo: ya no autentica
            print("La credencial anterior ya no autentica ................... OK")
        else:
            print("ATENCIÓN: la credencial anterior TODAVÍA autentica.")

    print("\nSiguiente paso: desplegar una revisión nueva de Cloud Run.")
    print("Una revisión en marcha conserva el valor que leyó al arrancar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
