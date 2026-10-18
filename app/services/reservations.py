"""Reglas de negocio de reservas.

Toda la logica vive aqui (no en los routers) para que sea testeable de forma
aislada y para que las reglas no se dupliquen entre endpoints.
"""
from datetime import date, time

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.enums import ReservationStatus, SpaceStatus, UserRole
from app.models.reservation import Reservation
from app.models.space import Space
from app.models.user import User
from app.schemas.reservation import ReservationCreate
from app.services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError

# Franja horaria en la que la universidad presta servicio.
HORA_APERTURA = time(6, 0)
HORA_CIERRE = time(22, 0)


def get_space_or_404(db: Session, space_id: int) -> Space:
    space = db.get(Space, space_id)
    if space is None:
        raise NotFoundError(f"El espacio {space_id} no existe.")
    return space


def get_reservation_or_404(db: Session, reservation_id: int) -> Reservation:
    reservation = db.get(Reservation, reservation_id)
    if reservation is None:
        raise NotFoundError(f"La reserva {reservation_id} no existe.")
    return reservation


def _validar_fecha(fecha: date) -> None:
    """Regla 7: no se permiten reservas en fechas pasadas."""
    hoy = date.today()
    if fecha < hoy:
        raise ValidationError("No se pueden crear reservas en fechas pasadas.")


def _validar_horario(hora_inicio: time, hora_fin: time) -> None:
    """Regla 3 (reforzada en servicio) + franja de apertura del campus."""
    if hora_fin <= hora_inicio:
        raise ValidationError("La hora de finalizacion debe ser posterior a la hora de inicio.")
    if hora_inicio < HORA_APERTURA or hora_fin > HORA_CIERRE:
        raise ValidationError(
            f"Las reservas solo se permiten entre {HORA_APERTURA:%H:%M} y {HORA_CIERRE:%H:%M}."
        )


def buscar_solapamientos(
    db: Session,
    space_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    excluir_reserva_id: int | None = None,
) -> list[Reservation]:
    """Regla 4: dos rangos [a1,a2) y [b1,b2) se solapan si a1 < b2 y b1 < a2.

    Solo se consideran reservas CONFIRMADAS; las canceladas liberan la franja.
    """
    condiciones = [
        Reservation.space_id == space_id,
        Reservation.fecha == fecha,
        Reservation.estado == ReservationStatus.CONFIRMADA,
        Reservation.hora_inicio < hora_fin,
        Reservation.hora_fin > hora_inicio,
    ]
    if excluir_reserva_id is not None:
        condiciones.append(Reservation.id != excluir_reserva_id)
    return list(db.scalars(select(Reservation).where(and_(*condiciones))).all())


def crear_reserva(db: Session, usuario: User, datos: ReservationCreate) -> Reservation:
    space = get_space_or_404(db, datos.space_id)

    # Regla 2: no se puede reservar un espacio que no esta disponible.
    if space.estado != SpaceStatus.DISPONIBLE:
        raise ConflictError(
            f"El espacio '{space.nombre}' esta en estado {space.estado.value} y no admite reservas.",
            code="space_unavailable",
        )

    _validar_fecha(datos.fecha)
    _validar_horario(datos.hora_inicio, datos.hora_fin)

    solapadas = buscar_solapamientos(db, space.id, datos.fecha, datos.hora_inicio, datos.hora_fin)
    if solapadas:
        conflicto = solapadas[0]
        raise ConflictError(
            f"El espacio ya esta reservado el {datos.fecha} de "
            f"{conflicto.hora_inicio:%H:%M} a {conflicto.hora_fin:%H:%M}.",
            code="reservation_overlap",
        )

    reserva = Reservation(
        user_id=usuario.id,
        space_id=space.id,
        fecha=datos.fecha,
        hora_inicio=datos.hora_inicio,
        hora_fin=datos.hora_fin,
        motivo=datos.motivo,
        estado=ReservationStatus.CONFIRMADA,
    )
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


def cancelar_reserva(db: Session, usuario: User, reservation_id: int) -> Reservation:
    reserva = get_reservation_or_404(db, reservation_id)

    # Regla 5 y 6: el estudiante solo cancela lo suyo; el administrador cancela todo.
    if usuario.rol != UserRole.ADMINISTRADOR and reserva.user_id != usuario.id:
        raise ForbiddenError("Solo puede cancelar sus propias reservas.")

    if reserva.estado == ReservationStatus.CANCELADA:
        raise ConflictError("La reserva ya estaba cancelada.", code="already_cancelled")

    reserva.estado = ReservationStatus.CANCELADA
    db.commit()
    db.refresh(reserva)
    return reserva


def disponibilidad_espacio(db: Session, space_id: int, fecha: date) -> dict:
    """Devuelve las franjas ocupadas de un espacio en una fecha concreta."""
    space = get_space_or_404(db, space_id)
    reservas = db.scalars(
        select(Reservation)
        .where(
            Reservation.space_id == space.id,
            Reservation.fecha == fecha,
            Reservation.estado == ReservationStatus.CONFIRMADA,
        )
        .order_by(Reservation.hora_inicio)
    ).all()
    return {
        "space_id": space.id,
        "fecha": fecha.isoformat(),
        "espacio_habilitado": space.estado == SpaceStatus.DISPONIBLE,
        "ocupado": [
            {
                "reservation_id": r.id,
                "hora_inicio": r.hora_inicio.strftime("%H:%M"),
                "hora_fin": r.hora_fin.strftime("%H:%M"),
            }
            for r in reservas
        ],
    }
