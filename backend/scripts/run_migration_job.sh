#!/bin/sh
# Punto de entrada del Cloud Run Job de migraciones (Fase 005.2).
#
# Se ejecuta fuera de banda: ninguna instancia del servicio web migra. Por eso el Job
# sobreescribe el ENTRYPOINT de la imagen, que arranca uvicorn.
#
# Modos (variable MIGRATION_MODE):
#   upgrade      (por defecto) comprueba, migra y verifica
#   verify-only  solo diagnostica; no escribe nada en la base
#
# Nunca imprime DATABASE_URL ni ningún secreto: los pasos que podrían revelarla se
# apoyan en verify_production_schema.py, que enmascara el destino.

set -eu

export PYTHONPATH="${PYTHONPATH:-/app}"

MODE="${MIGRATION_MODE:-upgrade}"
EXPECTED_HEAD="${EXPECTED_ALEMBIC_HEAD:-}"

echo "=== MIGRATION JOB START ==="
echo "mode=${MODE}"

if [ -z "${DATABASE_URL:-}" ]; then
  echo "FAIL: DATABASE_URL no está inyectada en el Job." >&2
  exit 2
fi

# --- Estado antes de tocar nada -------------------------------------------------
echo "--- alembic current ---"
CURRENT="$(alembic current 2>/dev/null | tail -1 | awk '{print $1}')"
echo "CURRENT=${CURRENT:-<ninguna>}"

echo "--- alembic heads ---"
HEADS_OUTPUT="$(alembic heads 2>/dev/null || true)"
HEADS_COUNT="$(printf '%s\n' "$HEADS_OUTPUT" | grep -c '(head)' || true)"
TARGET="$(printf '%s\n' "$HEADS_OUTPUT" | head -1 | awk '{print $1}')"
echo "TARGET=${TARGET:-<ninguna>}"
echo "HEADS=${HEADS_COUNT}"

# Varias cabezas en producción significa que el grafo se bifurcó sin que nadie lo
# resolviera. Migrar así deja la base en un estado que nadie eligió.
if [ "$HEADS_COUNT" != "1" ]; then
  echo "FAIL: se esperaba exactamente 1 head y hay ${HEADS_COUNT}." >&2
  exit 3
fi

# Cinturón de seguridad opcional: si quien lanza el release declara qué head espera,
# se comprueba que la imagen sea realmente esa y no una más antigua o más nueva.
if [ -n "$EXPECTED_HEAD" ] && [ "$TARGET" != "$EXPECTED_HEAD" ]; then
  echo "FAIL: head de la imagen (${TARGET}) != head esperado (${EXPECTED_HEAD})." >&2
  exit 4
fi

if [ "$MODE" = "verify-only" ]; then
  echo "--- verificación (sin escribir) ---"
  python scripts/verify_production_schema.py --verify-only
  echo "=== MIGRATION JOB END (verify-only) ==="
  exit 0
fi

# --- Migración ------------------------------------------------------------------
if [ "$CURRENT" = "$TARGET" ]; then
  echo "DATABASE_ALREADY_CURRENT=TRUE"
else
  echo "DATABASE_ALREADY_CURRENT=FALSE"
fi

echo "--- alembic upgrade head ---"
alembic upgrade head
echo "MIGRATION_RESULT=SUCCESS"

# --- Estado final ----------------------------------------------------------------
FINAL="$(alembic current 2>/dev/null | tail -1 | awk '{print $1}')"
echo "FINAL=${FINAL:-<ninguna>}"

echo "--- verificación de esquema ---"
python scripts/verify_production_schema.py --expected-revision "$TARGET"

echo "=== MIGRATION JOB END ==="
