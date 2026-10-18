"""Carga de datos iniciales para el entorno LOCAL.

Es idempotente: se puede ejecutar varias veces sin duplicar registros.
Uso:  python -m app.db.seed
"""
import logging
from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import SessionLocal
from app.models.enums import ReservationStatus, SpaceStatus, SpaceType, UserRole
from app.models.reservation import Reservation
from app.models.space import Space
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")

ESTUDIANTES = [
    ("Juan", "Restrepo", "juan.restrepo@unireserve.com", "Estudiante123!"),
    ("Maria", "Gomez", "maria.gomez@unireserve.com", "Estudiante123!"),
    ("Carlos", "Vasquez", "carlos.vasquez@unireserve.com", "Estudiante123!"),
    ("Laura", "Mejia", "laura.mejia@unireserve.com", "Estudiante123!"),
]

ESPACIOS = [
    {
        "nombre": "Sala de estudio 101",
        "descripcion": "Sala para trabajo en grupo con tablero y tomas de corriente.",
        "ubicacion": "Bloque 1 - Piso 1",
        "capacidad": 8,
        "tipo": SpaceType.SALA_ESTUDIO,
        "estado": SpaceStatus.DISPONIBLE,
    },
    {
        "nombre": "Sala de estudio 102",
        "descripcion": "Sala silenciosa para estudio individual o en parejas.",
        "ubicacion": "Bloque 1 - Piso 1",
        "capacidad": 6,
        "tipo": SpaceType.SALA_ESTUDIO,
        "estado": SpaceStatus.DISPONIBLE,
    },
    {
        "nombre": "Laboratorio de Sistemas",
        "descripcion": "30 equipos con entorno de desarrollo y acceso a servidores.",
        "ubicacion": "Bloque 4 - Piso 2",
        "capacidad": 30,
        "tipo": SpaceType.LABORATORIO,
        "estado": SpaceStatus.DISPONIBLE,
    },
    {
        "nombre": "Sala de reuniones A",
        "descripcion": "Sala con videoproyector y videoconferencia.",
        "ubicacion": "Bloque 2 - Piso 3",
        "capacidad": 12,
        "tipo": SpaceType.SALA_REUNIONES,
        "estado": SpaceStatus.DISPONIBLE,
    },
    {
        "nombre": "Auditorio principal",
        "descripcion": "Auditorio para eventos academicos y sustentaciones.",
        "ubicacion": "Bloque 5 - Piso 1",
        "capacidad": 200,
        "tipo": SpaceType.AUDITORIO,
        "estado": SpaceStatus.DISPONIBLE,
    },
    {
        "nombre": "Aula 305",
        "descripcion": "Aula en mantenimiento electrico. Sirve para probar la Regla 2.",
        "ubicacion": "Bloque 3 - Piso 5",
        "capacidad": 40,
        "tipo": SpaceType.AULA,
        "estado": SpaceStatus.MANTENIMIENTO,
    },
]


def _obtener_o_crear_usuario(
    db: Session, nombre: str, apellido: str, correo: str, password: str, rol: UserRole
) -> User:
    user = db.scalar(select(User).where(User.correo == correo))
    if user:
        return user
    user = User(
        nombre=nombre,
        apellido=apellido,
        correo=correo,
        contrasena_hash=hash_password(password),
        rol=rol,
        activo=True,
    )
    db.add(user)
    db.flush()
    logger.info("Usuario creado: %s (%s)", correo, rol.value)
    return user


def _obtener_o_crear_espacio(db: Session, datos: dict) -> Space:
    space = db.scalar(select(Space).where(Space.nombre == datos["nombre"]))
    if space:
        return space
    space = Space(**datos)
    db.add(space)
    db.flush()
    logger.info("Espacio creado: %s", datos["nombre"])
    return space


def _crear_reserva_si_libre(
    db: Session, user: User, space: Space, fecha: date, inicio: time, fin: time, motivo: str
) -> None:
    existente = db.scalar(
        select(Reservation).where(
            Reservation.space_id == space.id,
            Reservation.fecha == fecha,
            Reservation.hora_inicio == inicio,
        )
    )
    if existente:
        return
    db.add(
        Reservation(
            user_id=user.id,
            space_id=space.id,
            fecha=fecha,
            hora_inicio=inicio,
            hora_fin=fin,
            motivo=motivo,
            estado=ReservationStatus.CONFIRMADA,
        )
    )
    logger.info("Reserva creada: %s el %s %s-%s", space.nombre, fecha, inicio, fin)


def run() -> None:
    db = SessionLocal()
    try:
        admin = _obtener_o_crear_usuario(
            db,
            "Administrador",
            "UniReserve",
            settings.SEED_ADMIN_EMAIL,
            settings.SEED_ADMIN_PASSWORD,
            UserRole.ADMINISTRADOR,
        )
        estudiantes = [
            _obtener_o_crear_usuario(db, n, a, c, p, UserRole.ESTUDIANTE)
            for n, a, c, p in ESTUDIANTES
        ]
        espacios = [_obtener_o_crear_espacio(db, datos) for datos in ESPACIOS]

        manana = date.today() + timedelta(days=1)
        pasado = date.today() + timedelta(days=2)
        _crear_reserva_si_libre(
            db, estudiantes[0], espacios[0], manana, time(9, 0), time(10, 0), "Preparacion de parcial"
        )
        _crear_reserva_si_libre(
            db, estudiantes[1], espacios[0], manana, time(10, 0), time(11, 30), "Trabajo en grupo"
        )
        _crear_reserva_si_libre(
            db, estudiantes[2], espacios[2], manana, time(14, 0), time(16, 0), "Practica de laboratorio"
        )
        _crear_reserva_si_libre(
            db, estudiantes[0], espacios[3], pasado, time(8, 0), time(9, 0), "Reunion de proyecto"
        )
        _crear_reserva_si_libre(
            db, admin, espacios[4], pasado, time(17, 0), time(19, 0), "Sustentacion de grado"
        )

        db.commit()
        logger.info("Seed completado.")
        logger.info("Administrador: %s / %s", settings.SEED_ADMIN_EMAIL, settings.SEED_ADMIN_PASSWORD)
        logger.info("Estudiante de prueba: %s / %s", ESTUDIANTES[0][2], ESTUDIANTES[0][3])
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
