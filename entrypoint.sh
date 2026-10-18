#!/usr/bin/env sh
# ---------------------------------------------------------------------------
# Arranque del backend dentro del contenedor.
#
# 1. Espera a que PostgreSQL acepte conexiones.
# 2. Aplica las migraciones de Alembic.
# 3. Carga el seed solo si RUN_SEED=true (nunca en produccion).
# 4. Cede el control al comando recibido (uvicorn por defecto).
# ---------------------------------------------------------------------------
set -e

echo "[entrypoint] Esperando a PostgreSQL..."
python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
for intento in range(1, 31):
    try:
        create_engine(url).connect().execute(text("SELECT 1"))
        print(f"[entrypoint] PostgreSQL disponible (intento {intento}).")
        sys.exit(0)
    except Exception as exc:
        print(f"[entrypoint] Intento {intento}/30 fallido: {type(exc).__name__}")
        time.sleep(2)

print("[entrypoint] PostgreSQL no respondio a tiempo.", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] Aplicando migraciones de Alembic..."
alembic upgrade head

if [ "${RUN_SEED}" = "true" ]; then
  echo "[entrypoint] Cargando datos de prueba (RUN_SEED=true)..."
  python -m app.db.seed
fi

echo "[entrypoint] Iniciando la aplicacion: $*"
exec "$@"
