#!/bin/sh
set -eu

export PYTHONPATH="${PYTHONPATH:-/app}"

python scripts/wait_for_database.py \
  --timeout-seconds "${DATABASE_WAIT_TIMEOUT_SECONDS:-90}"

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  alembic upgrade heads
fi

if [ "${VALIDATE_MODELS_ON_STARTUP:-false}" = "true" ]; then
  python scripts/validate_model_artifacts.py
fi

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-*}"
