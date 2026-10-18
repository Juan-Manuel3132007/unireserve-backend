"""Pruebas de registro, login y proteccion de endpoints (Reglas 1 y 8)."""


def test_registro_crea_estudiante_y_devuelve_token(client):
    respuesta = client.post(
        "/auth/register",
        json={
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "correo": "nuevo@test.com",
            "password": "Segura123",
        },
    )
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["user"]["rol"] == "ESTUDIANTE"
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["access_token"]


def test_registro_ignora_el_rol_enviado_por_el_cliente(client):
    """Nadie puede autoproclamarse ADMINISTRADOR desde el registro publico."""
    respuesta = client.post(
        "/auth/register",
        json={
            "nombre": "Intruso",
            "apellido": "Malicioso",
            "correo": "intruso@test.com",
            "password": "Segura123",
            "rol": "ADMINISTRADOR",
        },
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["user"]["rol"] == "ESTUDIANTE"


def test_registro_rechaza_correo_duplicado(client, estudiante):
    respuesta = client.post(
        "/auth/register",
        json={
            "nombre": "Copia",
            "apellido": "Duplicada",
            "correo": "estudiante@test.com",
            "password": "Segura123",
        },
    )
    assert respuesta.status_code == 409


def test_registro_rechaza_contrasena_debil(client):
    respuesta = client.post(
        "/auth/register",
        json={"nombre": "Ana", "apellido": "Perez", "correo": "ana@test.com", "password": "1234"},
    )
    assert respuesta.status_code == 422


def test_contrasena_no_se_guarda_en_texto_plano(client, db):
    """Regla 8: en la BD solo debe existir el hash."""
    from sqlalchemy import select

    from app.models.user import User

    client.post(
        "/auth/register",
        json={"nombre": "Hash", "apellido": "Test", "correo": "hash@test.com", "password": "Segura123"},
    )
    user = db.scalar(select(User).where(User.correo == "hash@test.com"))
    assert user.contrasena_hash != "Segura123"
    assert user.contrasena_hash.startswith("$2b$")


def test_login_correcto(client, estudiante):
    respuesta = client.post(
        "/auth/login", json={"correo": "estudiante@test.com", "password": "Estudiante123!"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["user"]["correo"] == "estudiante@test.com"


def test_login_con_contrasena_incorrecta(client, estudiante):
    respuesta = client.post(
        "/auth/login", json={"correo": "estudiante@test.com", "password": "Incorrecta1"}
    )
    assert respuesta.status_code == 401


def test_login_de_usuario_inexistente(client):
    respuesta = client.post("/auth/login", json={"correo": "nadie@test.com", "password": "Cualquiera1"})
    assert respuesta.status_code == 401


def test_me_sin_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_token_invalido(client):
    respuesta = client.get("/auth/me", headers={"Authorization": "Bearer token.falso.aqui"})
    assert respuesta.status_code == 401


def test_me_con_token_valido(client, auth_estudiante):
    respuesta = client.get("/auth/me", headers=auth_estudiante)
    assert respuesta.status_code == 200
    assert respuesta.json()["correo"] == "estudiante@test.com"


def test_usuario_desactivado_no_puede_iniciar_sesion(client, db, estudiante):
    estudiante.activo = False
    db.commit()
    respuesta = client.post(
        "/auth/login", json={"correo": "estudiante@test.com", "password": "Estudiante123!"}
    )
    assert respuesta.status_code == 403
