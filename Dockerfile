# ---------------------------------------------------------------------------
# Imagen del backend (FastAPI + Uvicorn)
#
# Multi-stage: la etapa `builder` compila las dependencias en un virtualenv y
# la etapa final solo copia ese venv. Asi la imagen de ejecucion no arrastra
# compiladores ni cabeceras de desarrollo.
# ---------------------------------------------------------------------------

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


# --------------------------------------------------------------- imagen final
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# libpq5 es la unica biblioteca de sistema que psycopg necesita en ejecucion.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY . .

# El proceso no corre como root: requisito para desplegar en Kubernetes con
# securityContext restringido.
RUN useradd --create-home --uid 1000 unireserve \
    && chown -R unireserve:unireserve /app
USER unireserve

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
