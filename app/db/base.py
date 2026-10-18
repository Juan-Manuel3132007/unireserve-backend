"""Motor de SQLAlchemy, sesion y clase Base declarativa."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: abre una sesion por request y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
