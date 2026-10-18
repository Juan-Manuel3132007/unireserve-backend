"""Metricas agregadas que alimentan el dashboard. Se calculan en la BD."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.enums import ReservationStatus, SpaceStatus, UserRole
from app.models.reservation import Reservation
from app.models.space import Space
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", summary="Metricas del dashboard segun el rol")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    hoy = date.today()

    if current_user.rol == UserRole.ADMINISTRADOR:
        return {
            "rol": current_user.rol.value,
            "total_usuarios": db.scalar(select(func.count(User.id))) or 0,
            "usuarios_activos": db.scalar(select(func.count(User.id)).where(User.activo.is_(True))) or 0,
            "total_espacios": db.scalar(select(func.count(Space.id))) or 0,
            "espacios_disponibles": db.scalar(
                select(func.count(Space.id)).where(Space.estado == SpaceStatus.DISPONIBLE)
            )
            or 0,
            "total_reservas": db.scalar(select(func.count(Reservation.id))) or 0,
            "reservas_confirmadas": db.scalar(
                select(func.count(Reservation.id)).where(
                    Reservation.estado == ReservationStatus.CONFIRMADA
                )
            )
            or 0,
            "reservas_hoy": db.scalar(
                select(func.count(Reservation.id)).where(
                    Reservation.fecha == hoy, Reservation.estado == ReservationStatus.CONFIRMADA
                )
            )
            or 0,
        }

    base = select(func.count(Reservation.id)).where(Reservation.user_id == current_user.id)
    return {
        "rol": current_user.rol.value,
        "total_reservas": db.scalar(base) or 0,
        "reservas_confirmadas": db.scalar(
            base.where(Reservation.estado == ReservationStatus.CONFIRMADA)
        )
        or 0,
        "reservas_proximas": db.scalar(
            base.where(
                Reservation.fecha >= hoy, Reservation.estado == ReservationStatus.CONFIRMADA
            )
        )
        or 0,
        "espacios_disponibles": db.scalar(
            select(func.count(Space.id)).where(Space.estado == SpaceStatus.DISPONIBLE)
        )
        or 0,
    }
