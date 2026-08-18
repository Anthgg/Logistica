"""Verificación de solo lectura del esquema desplegado (Fase 005.2).

Comprueba, contra la base a la que apunta ``DATABASE_URL``, que el release de
migraciones dejó el estado esperado. **No escribe nada**: todas las consultas son
``SELECT``. Sirve tanto de comprobación previa (``--verify-only``, para saber en qué
revisión está la base sin tocarla) como de verificación posterior a ``alembic upgrade``.

Nunca imprime la cadena de conexión: el destino se muestra enmascarado, para que la
salida pueda pegarse en un log de CI sin filtrar credenciales.

Uso:
    python scripts/verify_production_schema.py --expected-revision jl480110048dk
    python scripts/verify_production_schema.py --verify-only
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

#: Lo único que se imprime cuando el destino no se puede descomponer con seguridad.
UNPARSEABLE_TARGET = "<destino no interpretable>"

#: Tablas que cada fase debe haber dejado en la base.
REQUIRED_TABLES: dict[str, tuple[str, ...]] = {
    "F004": ("logistics_organizations", "logistics_branches", "warehouses"),
    "F004.5": ("geo_departments", "geo_provinces", "geo_districts"),
    "F005.1": ("entity_code_counters",),
}

#: Conteos canónicos del catálogo UBIGEO (INEI).
EXPECTED_GEO_COUNTS: dict[str, int] = {
    "geo_departments": 25,
    "geo_provinces": 196,
    "geo_districts": 1893,
}

#: Tablas introducidas por F004.5/F005.1 que deben tener RLS habilitado.
RLS_REQUIRED_TABLES: tuple[str, ...] = (
    "entity_code_counters",
    "geo_departments",
    "geo_provinces",
    "geo_districts",
)

#: Tipo de entidad, prefijo de código y tabla donde viven esos códigos.
CODE_ENTITIES: tuple[tuple[str, str, str], ...] = (
    ("organization", "ORG", "logistics_organizations"),
    ("branch", "SED", "logistics_branches"),
    ("warehouse", "ALM", "warehouses"),
)


@dataclass
class Report:
    """Resultado acumulado. ``failures`` vacío significa verificación superada."""

    target: str
    revision: str | None = None
    lines: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def ok(self, message: str) -> None:
        self.lines.append(f"  PASS  {message}")

    def fail(self, message: str) -> None:
        self.lines.append(f"  FAIL  {message}")
        self.failures.append(message)

    def note(self, message: str) -> None:
        self.lines.append(f"  ----  {message}")


def masked_target(url: str) -> str:
    """Host y base, sin usuario ni contraseña.

    A prueba de fallos: si la URL no se puede descomponer en host y base, se devuelve
    una constante. Nunca se emite nada derivado del valor crudo — un destino mal
    formado no debe convertirse en una fuga de credenciales en el log.
    """
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return UNPARSEABLE_TARGET

    if not host:
        return UNPARSEABLE_TARGET

    # Solo el inicio del host: identifica el proveedor sin publicar el proyecto entero.
    head, _, tail = host.partition(".")
    masked_host = f"{head[:4]}***.{tail}" if tail else "***"

    database = (parts.path or "").lstrip("/")
    if not database or "/" in database:
        return f"{masked_host}/<base no interpretable>"
    return f"{masked_host}/{database}"


def normalized_url(raw: str) -> str:
    """Fuerza el driver psycopg, que es el que trae la imagen del backend."""
    if raw.startswith("postgresql+"):
        return raw
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw[len("postgresql://") :]
    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://") :]
    return raw


def table_exists(engine: Engine, table: str) -> bool:
    with engine.connect() as conn:
        found = conn.execute(
            text("SELECT to_regclass(:qualified)"), {"qualified": f"public.{table}"}
        ).scalar()
    return found is not None


def check_revision(engine: Engine, report: Report, expected: str | None) -> None:
    if not table_exists(engine, "alembic_version"):
        report.fail("no existe alembic_version: la base no ha sido migrada nunca")
        return

    with engine.connect() as conn:
        revisions = [
            row[0] for row in conn.execute(text("SELECT version_num FROM alembic_version"))
        ]

    if len(revisions) != 1:
        report.fail(f"alembic_version tiene {len(revisions)} filas; se espera exactamente 1")
        return

    report.revision = revisions[0]
    if expected is None:
        report.note(f"revisión actual: {report.revision}")
    elif report.revision == expected:
        report.ok(f"revisión = {expected}")
    else:
        report.fail(f"revisión = {report.revision}; se esperaba {expected}")


def check_tables(engine: Engine, report: Report) -> None:
    for phase, tables in REQUIRED_TABLES.items():
        missing = [name for name in tables if not table_exists(engine, name)]
        if missing:
            report.fail(f"{phase}: faltan tablas {', '.join(missing)}")
        else:
            report.ok(f"{phase}: {len(tables)} tabla(s) presentes")


def check_geo_counts(engine: Engine, report: Report) -> None:
    for table, expected in EXPECTED_GEO_COUNTS.items():
        if not table_exists(engine, table):
            report.fail(f"{table}: ausente, no se puede contar")
            continue
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
        if count == expected:
            report.ok(f"{table}: {count}")
        else:
            # Drift de datos: se reporta, nunca se corrige desde aquí.
            report.fail(
                f"{table}: {count}; se esperaban {expected} "
                "(drift de datos, NO corregir automáticamente)"
            )


def check_rls(engine: Engine, report: Report) -> None:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT relname, relrowsecurity FROM pg_class "
                "WHERE relkind = 'r' AND relname = ANY(:names)"
            ),
            {"names": list(RLS_REQUIRED_TABLES)},
        ).all()

    seen = {name: enabled for name, enabled in rows}
    for table in RLS_REQUIRED_TABLES:
        if table not in seen:
            report.fail(f"RLS {table}: tabla ausente")
        elif seen[table]:
            report.ok(f"RLS {table}: habilitado")
        else:
            report.fail(f"RLS {table}: DESHABILITADO")


def check_code_counters(engine: Engine, report: Report) -> None:
    """El contador debe ir por delante de los códigos ya emitidos.

    Es la comprobación que impide el peor fallo posible de F005.1: que una base con
    entidades preexistentes empiece a emitir códigos que ya están en uso.
    """
    if not table_exists(engine, "entity_code_counters"):
        report.fail("entity_code_counters ausente: no se puede evaluar colisión")
        return

    with engine.connect() as conn:
        counters = dict(
            conn.execute(text("SELECT entity_type, next_value FROM entity_code_counters")).all()
        )
    report.note(f"contadores: {counters or 'ninguno'}")

    for entity_type, prefix, table in CODE_ENTITIES:
        if not table_exists(engine, table):
            report.fail(f"colisión {entity_type}: {table} ausente")
            continue

        next_value = counters.get(entity_type)
        if next_value is None:
            report.fail(f"colisión {entity_type}: sin fila de contador")
            continue

        # Solo los códigos con la forma que emite F005.1 (prefijo + 6 dígitos) compiten
        # con la secuencia; los códigos manuales antiguos tienen otra forma.
        pattern = f"^{prefix}[0-9]{{6}}$"
        with engine.connect() as conn:
            highest = conn.execute(
                text(
                    f"SELECT max(substring(code from 4)::bigint) FROM {table} "
                    "WHERE code ~ :pattern"
                ),
                {"pattern": pattern},
            ).scalar()

        if highest is None:
            report.ok(f"colisión {entity_type}: sin códigos generados aún (next={next_value})")
        elif next_value > highest:
            report.ok(f"colisión {entity_type}: next={next_value} > máximo emitido={highest}")
        else:
            report.fail(
                f"colisión {entity_type}: next={next_value} <= máximo emitido={highest} "
                "— la próxima alta reutilizaría un código existente"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verificación de solo lectura del esquema desplegado."
    )
    parser.add_argument(
        "--expected-revision",
        default=None,
        help="Revisión Alembic exigida. Si se omite, solo se informa la actual.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Solo conectividad y revisión actual; omite la verificación de esquema.",
    )
    args = parser.parse_args()

    raw_url = os.environ.get("DATABASE_URL", "").strip()
    if not raw_url:
        print("FAIL: DATABASE_URL no está definida en el entorno.", file=sys.stderr)
        return 2

    report = Report(target=masked_target(raw_url))
    print(f"Destino: {report.target}")

    try:
        engine = create_engine(normalized_url(raw_url), pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — se resume el tipo, nunca la URL
        print(f"FAIL: no se pudo conectar ({type(exc).__name__}).", file=sys.stderr)
        return 2

    report.ok("conectividad")
    check_revision(engine, report, args.expected_revision)

    if not args.verify_only:
        check_tables(engine, report)
        check_geo_counts(engine, report)
        check_rls(engine, report)
        check_code_counters(engine, report)

    print("\n".join(report.lines))
    print(f"\nREVISION={report.revision or 'UNKNOWN'}")

    if report.failures:
        print(f"RESULTADO=FAIL ({len(report.failures)} comprobación/es)")
        return 1
    print("RESULTADO=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
