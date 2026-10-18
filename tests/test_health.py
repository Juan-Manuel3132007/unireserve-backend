def test_health(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "ok"


def test_readiness_verifica_la_base_de_datos(client):
    respuesta = client.get("/health/ready")
    assert respuesta.status_code == 200
    assert respuesta.json()["database"] == "up"


def test_openapi_se_genera(client):
    respuesta = client.get("/openapi.json")
    assert respuesta.status_code == 200
    assert "/reservations" in respuesta.json()["paths"]
