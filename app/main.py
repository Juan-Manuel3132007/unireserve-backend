"""Punto de entrada de la API de UniReserve."""
import logging
import time
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.errors import DomainError

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("unireserve")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API REST de UniReserve: gestion y reserva de espacios universitarios. "
        "Documentacion interactiva en /docs y esquema OpenAPI en /openapi.json."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Asigna un request_id y registra cada peticion como log estructurado."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    inicio = time.perf_counter()
    response = await call_next(request)
    duracion_ms = round((time.perf_counter() - inicio) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duracion_ms,
        },
    )
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    """Traduce las excepciones de dominio a una respuesta JSON uniforme."""
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail, "code": exc.code}
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Devuelve los errores de validacion en un formato estable para el frontend."""
    errores = [
        {"campo": ".".join(str(p) for p in err["loc"][1:]) or "body", "mensaje": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Los datos enviados no son validos.",
            "code": "validation_error",
            "errores": errores,
        },
    )


app.include_router(api_router)


@app.get("/", tags=["health"], summary="Informacion basica del servicio")
def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
