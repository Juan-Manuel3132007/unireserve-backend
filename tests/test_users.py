"""Pruebas de usuarios y de autorizacion por rol."""


def test_estudiante_no_puede_listar_usuarios(client, auth_estudiante):
    respuesta = client.get("/users", headers=auth_estudiante)
    assert respuesta.status_code == 403


def test_admin_puede_listar_usuarios(client, auth_admin, estudiante):
    respuesta = client.get("/users", headers=auth_admin)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] >= 2
    assert {"items", "total", "page", "size", "pages"} <= cuerpo.keys()


def test_listar_usuarios_sin_token(client):
    assert client.get("/users").status_code == 401


def test_admin_puede_crear_usuario_con_rol(client, auth_admin):
    respuesta = client.post(
        "/users",
        headers=auth_admin,
        json={
            "nombre": "Nuevo",
            "apellido": "Admin",
            "correo": "admin2@test.com",
            "password": "Segura123",
            "rol": "ADMINISTRADOR",
        },
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["rol"] == "ADMINISTRADOR"


def test_estudiante_consulta_su_propio_perfil(client, auth_estudiante, estudiante):
    respuesta = client.get(f"/users/{estudiante.id}", headers=auth_estudiante)
    assert respuesta.status_code == 200


def test_estudiante_no_consulta_perfil_ajeno(client, auth_estudiante, otro_estudiante):
    respuesta = client.get(f"/users/{otro_estudiante.id}", headers=auth_estudiante)
    assert respuesta.status_code == 403


def test_estudiante_no_puede_ascenderse_a_admin(client, auth_estudiante, estudiante):
    """Aunque envie el campo rol, el backend lo descarta."""
    respuesta = client.put(
        f"/users/{estudiante.id}", headers=auth_estudiante, json={"rol": "ADMINISTRADOR"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "ESTUDIANTE"


def test_admin_desactiva_usuario(client, auth_admin, estudiante):
    respuesta = client.delete(f"/users/{estudiante.id}", headers=auth_admin)
    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is False


def test_admin_no_puede_desactivarse_a_si_mismo(client, auth_admin, admin):
    respuesta = client.delete(f"/users/{admin.id}", headers=auth_admin)
    assert respuesta.status_code == 409
