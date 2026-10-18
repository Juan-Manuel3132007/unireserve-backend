"""Configuracion de la aplicacion, leida exclusivamente de variables de entorno."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Aplicacion ---
    APP_NAME: str = "UniReserve API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # --- Base de datos ---
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/unireserve"

    # --- Seguridad / JWT ---
    JWT_SECRET: str = "cambiar-esta-clave-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Seed (solo entorno local) ---
    SEED_ADMIN_EMAIL: str = "admin@unireserve.com"
    SEED_ADMIN_PASSWORD: str = "Admin123!"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
