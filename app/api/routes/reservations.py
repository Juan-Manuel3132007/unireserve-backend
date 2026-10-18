from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.enums import ReservationStatus, UserRole
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.common import Page
from app.schemas.reservation import ReservationCreate, ReservationRead, ReservationUpdate
from app.services import reservations as service
from app.services.errors import ConflictError, ForbiddenError

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("", response_model=Page[ReservationRead], summary="Listar reservas")
def list_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    estado: ReservationStatus | None = None,
    space_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[ReservationRead]:
    """Regla 6: el administrador ve todas las reservas; el estudiante solo las suyas.

    El filtro se aplica en la consulta SQL, no ocultando datos en el frontend.
    """
    stmt = select(Reservation).options(
        selectinload(Reservation.space), selectinload(Reservation.user)
    )
    if current_user.rol != UserRole.ADMINISTRADOR:
        stmt = stmt.where(Reservation.user_id == current_user.id)
    if estado is not None:
        stmt = stmt.where(Reservation.estado == estado)
    if space_id is not None:
        stmt = stmt.where(Reservation.space_id == space_id)
    if desde is not None:
        stmt = stmt.where(Reservation.fecha >= desde)
    if hasta is not None:
        stmt = stmt.where(Reservation.fecha <= hasta)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Reservation.fecha.desc(), Reservation.hora_inicio.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return Page[ReservationRead](
        items=[ReservationRead.model_validate(r) for r in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, -(-total // size)),
    )


@router.get("/{reservation_id}", response_model=ReservationRead, summary="Detalle de una reserva")
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Reservation:
    reserva = service.get_reservation_or_404(db, reservation_id)
    if current_user.rol != UserRole.ADMINISTRADOR and reserva.user_id != current_user.id:
        raise ForbiddenError("Solo puede consultar sus propias reservas.")
    return reserva


@router.post(
    "",
    response_model=ReservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una reserva (requiere autenticacion)",
)
def create_reservation(
    datos: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Reservation:
    return service.crear_reserva(db, current_user, datos)


@router.put("/{reservation_id}", response_model=ReservationRead, summary="Modificar una reserva")
def update_reservation(
    reservation_id: int,
    datos: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Reservation:
    reserva = service.get_reservation_or_404(db, reservation_id)
    es_admin = current_user.rol == UserRole.ADMINISTRADOR
    if not es_admin and reserva.user_id != current_user.id:
        raise ForbiddenError("Solo puede modificar sus propias reservas.")
    if reserva.estado == ReservationStatus.CANCELADA:
        raise ConflictError("No se puede modificar una reserva cancelada.", code="already_cancelled")

    cambios = datos.model_dump(exclude_unset=True)
    nueva_fecha = cambios.get("fecha", reserva.fecha)
    nueva_inicio = cambios.get("hora_inicio", reserva.hora_inicio)
    nueva_fin = cambios.get("hora_fin", reserva.hora_fin)

    # Si cambia el horario se revalidan las mismas reglas que en la creacion.
    if {"fecha", "hora_inicio", "hora_fin"} & cambios.keys():
        service._validar_fecha(nueva_fecha)
        service._validar_horario(nueva_inicio, nueva_fin)
        solapadas = service.buscar_solapamientos(
            db, reserva.space_id, nueva_fecha, nueva_inicio, nueva_fin, excluir_reserva_id=reserva.id
        )
        if solapadas:
            conflicto = solapadas[0]
            raise ConflictError(
                f"El espacio ya esta reservado el {nueva_fecha} de "
                f"{conflicto.hora_inicio:%H:%M} a {conflicto.hora_fin:%H:%M}.",
                code="reservation_overlap",
            )

    for campo, valor in cambios.items():
        setattr(reserva, campo, valor)
    db.commit()
    db.refresh(reserva)
    return reserva


@router.delete("/{reservation_id}", response_model=ReservationRead, summary="Cancelar una reserva")
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Reservation:
    return service.cancelar_reserva(db, current_user, reservation_id)
