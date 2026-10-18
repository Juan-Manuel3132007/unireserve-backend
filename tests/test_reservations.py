"""Pruebas de las reglas de negocio de reservas (Reglas 1 a 7)."""
from datetime import date, timedelta

MANANA = (date.today() + timedelta(days=1)).isoformat()
AYER = (date.today() - timedelta(days=1)).isoformat()


def _payload(space_id, inicio="09:00", fin="10:00", fecha=MANANA, motivo="Estudio"):
    return {
        "space_id": space_id,
        "fecha": fecha,
        "hora_inicio": inicio,
        "hora_fin": fin,
        "motivo": motivo,
    }


def test_regla_1_sin_autenticacion_no_hay_reserva(client, espacio):
    respuesta = client.post("/reservations", json=_payload(espacio.id))
    assert respuesta.status_code == 401


def test_reserva_valida_se_crea(client, auth_estudiante, espacio):
    respuesta = client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id))
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "CONFIRMADA"


def test_regla_2_espacio_deshabilitado(client, auth_estudiante, espacio_deshabilitado):
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio_deshabilitado.id)
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "space_unavailable"


def test_regla_3_hora_fin_anterior_a_inicio(client, auth_estudiante, espacio):
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "11:00", "10:00")
    )
    assert respuesta.status_code == 422


def test_regla_3_horas_iguales(client, auth_estudiante, espacio):
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "10:00", "10:00")
    )
    assert respuesta.status_code == 422


def test_regla_4_solapamiento_parcial(client, auth_estudiante, espacio):
    """Existe 09:00-10:00; 09:30-10:30 debe rechazarse."""
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00"))
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:30", "10:30")
    )
    assert respuesta.status_code == 409
    assert respuesta.json()["code"] == "reservation_overlap"


def test_regla_4_reserva_contenida(client, auth_estudiante, espacio):
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "12:00"))
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "10:00", "11:00")
    )
    assert respuesta.status_code == 409


def test_regla_4_franjas_contiguas_si_se_permiten(client, auth_estudiante, espacio):
    """09:00-10:00 y 10:00-11:00 no se solapan: el limite es exclusivo."""
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00"))
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "10:00", "11:00")
    )
    assert respuesta.status_code == 201


def test_regla_4_mismo_horario_en_espacio_distinto_si_se_permite(
    client, auth_estudiante, espacio, db
):
    from app.models.enums import SpaceStatus, SpaceType
    from app.models.space import Space

    otro = Space(
        nombre="Sala de estudio 102",
        ubicacion="Bloque 1",
        capacidad=6,
        tipo=SpaceType.SALA_ESTUDIO,
        estado=SpaceStatus.DISPONIBLE,
    )
    db.add(otro)
    db.commit()
    db.refresh(otro)

    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00"))
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(otro.id, "09:00", "10:00")
    )
    assert respuesta.status_code == 201


def test_una_reserva_cancelada_libera_la_franja(client, auth_estudiante, espacio):
    creada = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00")
    ).json()
    client.delete(f"/reservations/{creada['id']}", headers=auth_estudiante)
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00")
    )
    assert respuesta.status_code == 201


def test_regla_7_fecha_pasada(client, auth_estudiante, espacio):
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, fecha=AYER)
    )
    assert respuesta.status_code == 422


def test_fuera_de_la_franja_de_apertura(client, auth_estudiante, espacio):
    respuesta = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "04:00", "05:00")
    )
    assert respuesta.status_code == 422


def test_regla_5_estudiante_no_cancela_reserva_ajena(
    client, auth_estudiante, auth_otro_estudiante, espacio
):
    creada = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id)
    ).json()
    respuesta = client.delete(f"/reservations/{creada['id']}", headers=auth_otro_estudiante)
    assert respuesta.status_code == 403


def test_regla_5_estudiante_cancela_su_propia_reserva(client, auth_estudiante, espacio):
    creada = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id)
    ).json()
    respuesta = client.delete(f"/reservations/{creada['id']}", headers=auth_estudiante)
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "CANCELADA"


def test_regla_6_admin_cancela_cualquier_reserva(client, auth_estudiante, auth_admin, espacio):
    creada = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id)
    ).json()
    respuesta = client.delete(f"/reservations/{creada['id']}", headers=auth_admin)
    assert respuesta.status_code == 200


def test_regla_6_admin_ve_todas_las_reservas(client, auth_estudiante, auth_admin, espacio):
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id))
    assert client.get("/reservations", headers=auth_admin).json()["total"] == 1


def test_estudiante_solo_ve_sus_reservas(
    client, auth_estudiante, auth_otro_estudiante, espacio
):
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00"))
    respuesta = client.get("/reservations", headers=auth_otro_estudiante)
    assert respuesta.json()["total"] == 0


def test_no_se_cancela_dos_veces(client, auth_estudiante, espacio):
    creada = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id)
    ).json()
    client.delete(f"/reservations/{creada['id']}", headers=auth_estudiante)
    respuesta = client.delete(f"/reservations/{creada['id']}", headers=auth_estudiante)
    assert respuesta.status_code == 409


def test_reserva_en_espacio_inexistente(client, auth_estudiante):
    respuesta = client.post("/reservations", headers=auth_estudiante, json=_payload(9999))
    assert respuesta.status_code == 404


def test_disponibilidad_muestra_franjas_ocupadas(client, auth_estudiante, espacio):
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00"))
    respuesta = client.get(f"/spaces/{espacio.id}/availability", params={"fecha": MANANA})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["espacio_habilitado"] is True
    assert cuerpo["ocupado"] == [
        {"reservation_id": 1, "hora_inicio": "09:00", "hora_fin": "10:00"}
    ]


def test_editar_reserva_respeta_el_solapamiento(client, auth_estudiante, espacio):
    client.post("/reservations", headers=auth_estudiante, json=_payload(espacio.id, "09:00", "10:00"))
    segunda = client.post(
        "/reservations", headers=auth_estudiante, json=_payload(espacio.id, "11:00", "12:00")
    ).json()
    respuesta = client.put(
        f"/reservations/{segunda['id']}",
        headers=auth_estudiante,
        json={"hora_inicio": "09:30", "hora_fin": "10:30"},
    )
    assert respuesta.status_code == 409
