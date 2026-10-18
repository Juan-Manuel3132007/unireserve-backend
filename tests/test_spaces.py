"""Pruebas de CRUD de espacios y su autorizacion."""


def test_listar_espacios_es_publico(client, espacio):
    respuesta = client.get("/spaces")
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1


def test_filtrar_espacios_por_tipo(client, espacio, espacio_deshabilitado):
    respuesta = client.get("/spaces", params={"tipo": "SALA_ESTUDIO"})
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1


def test_filtrar_espacios_por_capacidad_minima(client, espacio, espacio_deshabilitado):
    respuesta = client.get("/spaces", params={"capacidad_min": 20})
    assert respuesta.json()["total"] == 1
    assert respuesta.json()["items"][0]["nombre"] == "Aula 305"


def test_detalle_de_espacio_inexistente(client):
    assert client.get("/spaces/9999").status_code == 404


def test_estudiante_no_puede_crear_espacio(client, auth_estudiante):
    respuesta = client.post(
        "/spaces",
        headers=auth_estudiante,
        json={
            "nombre": "Sala pirata",
            "ubicacion": "Bloque X",
            "capacidad": 10,
            "tipo": "SALA_ESTUDIO",
        },
    )
    assert respuesta.status_code == 403


def test_crear_espacio_sin_token(client):
    respuesta = client.post(
        "/spaces",
        json={"nombre": "Sala anonima", "ubicacion": "Bloque X", "capacidad": 10, "tipo": "AULA"},
    )
    assert respuesta.status_code == 401


def test_admin_crea_espacio(client, auth_admin):
    respuesta = client.post(
        "/spaces",
        headers=auth_admin,
        json={
            "nombre": "Laboratorio de Redes",
            "descripcion": "20 equipos",
            "ubicacion": "Bloque 4 - Piso 1",
            "capacidad": 20,
            "tipo": "LABORATORIO",
        },
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "DISPONIBLE"


def test_no_se_permiten_espacios_con_nombre_duplicado(client, auth_admin, espacio):
    respuesta = client.post(
        "/spaces",
        headers=auth_admin,
        json={
            "nombre": "Sala de estudio 101",
            "ubicacion": "Otro bloque",
            "capacidad": 5,
            "tipo": "SALA_ESTUDIO",
        },
    )
    assert respuesta.status_code == 409


def test_capacidad_debe_ser_positiva(client, auth_admin):
    respuesta = client.post(
        "/spaces",
        headers=auth_admin,
        json={"nombre": "Sala vacia", "ubicacion": "Bloque 1", "capacidad": 0, "tipo": "AULA"},
    )
    assert respuesta.status_code == 422


def test_admin_edita_espacio(client, auth_admin, espacio):
    respuesta = client.put(f"/spaces/{espacio.id}", headers=auth_admin, json={"capacidad": 12})
    assert respuesta.status_code == 200
    assert respuesta.json()["capacidad"] == 12


def test_admin_deshabilita_espacio(client, auth_admin, espacio):
    respuesta = client.delete(f"/spaces/{espacio.id}", headers=auth_admin)
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "DESHABILITADO"
