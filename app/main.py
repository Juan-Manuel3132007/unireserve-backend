from fastapi import FastAPI

app = FastAPI(title="UniReserve API")


@app.get("/")
def hola_mundo() -> dict:
    return {"mensaje": "Hola mundo desde el backend de UniReserve"}