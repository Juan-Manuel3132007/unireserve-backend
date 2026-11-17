# UniReserve Backend (API REST)

[![Backend CI](https://github.com/Juan-Manuel3132007/unireserve-backend/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Juan-Manuel3132007/unireserve-backend/actions/workflows/backend-ci.yml)

API REST para la gestión y reserva de espacios universitarios de **UniReserve**, construida con FastAPI, SQLAlchemy 2.0, PostgreSQL 16 y Pydantic v2.

---

## 🛠️ Tecnologías

- **Python**: 3.12+
- **Framework Web**: FastAPI 0.115 + Uvicorn 0.34
- **ORM & DB**: SQLAlchemy 2.0, PostgreSQL 16, psycopg3
- **Migraciones**: Alembic 1.14
- **Pruebas y Calidad**: Pytest 8.3, HTTPX, Ruff (linter/formatter)
- **Contenedores**: Docker (Multi-stage build runtime no-root)

---

## ⚙️ Variables de Entorno

| Variable | Tipo / Valor por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/unireserve` | Cadena de conexión a PostgreSQL |
| `JWT_SECRET` | *Requerido en producción* (ej. `clave-secreta-segura`) | Clave simétrica para firma de tokens JWT HS256 |
| `JWT_ALGORITHM` | `HS256` | Algoritmo criptográfico para JWT |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Tiempo de vida del token de acceso |
| `RUN_SEED` | `false` (en local/compose: `true`) | Cargar datos semilla al iniciar el contenedor |
| `TEST_DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/unireserve_test` | Base de datos real para pruebas con Pytest |

---

## 🧪 Ejecución de Pruebas y Linter

### 1. Entorno virtual y dependencias
```bash
python -m venv .venv
# En Windows:
.\.venv\Scripts\Activate.ps1
# En Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Base de datos para pruebas
Pytest corre contra una base de datos PostgreSQL **real** (no SQLite en memoria), asegurando compatibilidad estricta con Enums, tipos y constraints nativos.
```bash
docker run -d --name unireserve-test-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=unireserve_test \
  -p 5432:5432 postgres:16-alpine
```

### 3. Ejecutar Linter y Pruebas
```bash
# Linter con Ruff
ruff check .

# Suite completa de 56 pruebas con reporte XML JUnit
pytest -v --junitxml=junit-report.xml
```

---

## 🐳 Construcción y Ejecución de la Imagen Docker

La imagen utiliza multi-stage build y corre como usuario sin privilegios `unireserve` (UID 1000):

```bash
# Construir imagen localmente
docker build -t juanma313/unireserve-backend:v1.0.0 .

# Ejecutar contenedor
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://usuario:password@host:5432/unireserve \
  -e JWT_SECRET=supersecreto \
  juanma313/unireserve-backend:v1.0.0
```

---

## 🔄 CI/CD Automatizado

El workflow `.github/workflows/backend-ci.yml` ejecuta automáticamente:
1. Concurrencia con cancelación de builds obsoletas.
2. Contenedor de servicio PostgreSQL 16 con verificación de salud (`pg_isready`).
3. Verificación de estilo y estándares con `ruff check .`.
4. Ejecución de las 56 pruebas con `pytest` y publicación de reporte JUnit como artefacto.
5. Verificación de construcción de la imagen Docker.
6. Publicación a DockerHub (`juanma313/unireserve-backend`) con etiquetas OCI (`sha-<hash>`, semver y `latest`) condicionado al éxito del job de pruebas.
