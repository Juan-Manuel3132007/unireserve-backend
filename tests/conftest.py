"""Fixtures de pytest.

Los tests corren contra una base de datos PostgreSQL REAL y separada
(TEST_DATABASE_URL), no contra SQLite: asi las pruebas ejercitan los mismos
tipos, enums y constraints que produccion. El esquema se crea y se destruye
en cada sesion de pruebas.
"""
import os

os.environ.setdefault("JWT_SECRET", "clave-de-pruebas")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import SpaceStatus, SpaceType, UserRole  # noqa: E402
from app.models.space import Space  # noqa: E402
from app.models.user import User  # noqa: E402

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/unireserve_test",
)

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _crear_esquema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _limpiar_tablas():
    """Cada test arranca con las tablas vacias para que sean independientes."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE reservations, spaces, users RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _get_test_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------- datos base


@pytest.fixture
def admin(db) -> User:
    user = User(
        nombre="Admin",
        apellido="Test",
        correo="admin@test.com",
        contrasena_hash=hash_password("Admin123!"),
        rol=UserRole.ADMINISTRADOR,
        activo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def estudiante(db) -> User:
    user = User(
        nombre="Estu",
        apellido="Diante",
        correo="estudiante@test.com",
        contrasena_hash=hash_password("Estudiante123!"),
        rol=UserRole.ESTUDIANTE,
        activo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def otro_estudiante(db) -> User:
    user = User(
        nombre="Otro",
        apellido="Alumno",
        correo="otro@test.com",
        contrasena_hash=hash_password("Estudiante123!"),
        rol=UserRole.ESTUDIANTE,
        activo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def espacio(db) -> Space:
    space = Space(
        nombre="Sala de estudio 101",
        descripcion="Sala de prueba",
        ubicacion="Bloque 1",
        capacidad=8,
        tipo=SpaceType.SALA_ESTUDIO,
        estado=SpaceStatus.DISPONIBLE,
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


@pytest.fixture
def espacio_deshabilitado(db) -> Space:
    space = Space(
        nombre="Aula 305",
        ubicacion="Bloque 3",
        capacidad=40,
        tipo=SpaceType.AULA,
        estado=SpaceStatus.DESHABILITADO,
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


# ------------------------------------------------------------------ helpers


def _token(client, correo: str, password: str) -> str:
    respuesta = client.post("/auth/login", json={"correo": correo, "password": password})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


@pytest.fixture
def auth_admin(client, admin) -> dict:
    return {"Authorization": f"Bearer {_token(client, 'admin@test.com', 'Admin123!')}"}


@pytest.fixture
def auth_estudiante(client, estudiante) -> dict:
    return {"Authorization": f"Bearer {_token(client, 'estudiante@test.com', 'Estudiante123!')}"}


@pytest.fixture
def auth_otro_estudiante(client, otro_estudiante) -> dict:
    return {"Authorization": f"Bearer {_token(client, 'otro@test.com', 'Estudiante123!')}"}
