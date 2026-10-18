from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.base import get_db
from app.models.enums import SpaceStatus, SpaceType
from app.models.space import Space
from app.models.user import User
from app.schemas.common import Page
from app.schemas.space import AvailabilityRead, SpaceCreate, SpaceRead, SpaceUpdate
from app.services.reservations import disponibilidad_espacio

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.get("", response_model=Page[SpaceRead], summary="Listar espacios (publico)")
def list_spaces(
    db: Session = Depends(get_db),
    tipo: SpaceType | None = None,
    estado: SpaceStatus | None = None,
    capacidad_min: int | None = Query(default=None, ge=1),
    buscar: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[SpaceRead]:
    stmt = select(Space)
    if tipo is not None:
        stmt = stmt.where(Space.tipo == tipo)
    if estado is not None:
        stmt = stmt.where(Space.estado == estado)
    if capacidad_min is not None:
        stmt = stmt.where(Space.capacidad >= capacidad_min)
    if buscar:
        patron = f"%{buscar.lower()}%"
        stmt = stmt.where(
            func.lower(Space.nombre).like(patron) | func.lower(Space.ubicacion).like(patron)
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(Space.nombre).offset((page - 1) * size).limit(size)).all()
    return Page[SpaceRead](
        items=[SpaceRead.model_validate(s) for s in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, -(-total // size)),
    )


@router.get("/{space_id}", response_model=SpaceRead, summary="Detalle de un espacio")
def get_space(space_id: int, db: Session = Depends(get_db)) -> Space:
    space = db.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espacio no encontrado.")
    return space


@router.get(
    "/{space_id}/availability",
    response_model=AvailabilityRead,
    summary="Franjas ocupadas de un espacio en una fecha",
)
def get_availability(
    space_id: int,
    fecha: date = Query(description="Fecha a consultar en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> dict:
    return disponibilidad_espacio(db, space_id, fecha)


@router.post(
    "",
    response_model=SpaceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear espacio (solo ADMINISTRADOR)",
)
def create_space(
    datos: SpaceCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> Space:
    if db.scalar(select(Space).where(func.lower(Space.nombre) == datos.nombre.lower())):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe un espacio con ese nombre."
        )
    space = Space(**datos.model_dump())
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


@router.put("/{space_id}", response_model=SpaceRead, summary="Editar espacio (solo ADMINISTRADOR)")
def update_space(
    space_id: int,
    datos: SpaceUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Space:
    space = db.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espacio no encontrado.")

    cambios = datos.model_dump(exclude_unset=True)
    nuevo_nombre = cambios.get("nombre")
    if nuevo_nombre:
        duplicado = db.scalar(
            select(Space).where(func.lower(Space.nombre) == nuevo_nombre.lower(), Space.id != space_id)
        )
        if duplicado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Ya existe un espacio con ese nombre."
            )
    for campo, valor in cambios.items():
        setattr(space, campo, valor)

    db.commit()
    db.refresh(space)
    return space


@router.delete(
    "/{space_id}", response_model=SpaceRead, summary="Deshabilitar espacio (solo ADMINISTRADOR)"
)
def disable_space(space_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Space:
    space = db.get(Space, space_id)
    if space is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espacio no encontrado.")
    # Borrado logico: eliminar el espacio destruiria el historial de reservas.
    space.estado = SpaceStatus.DESHABILITADO
    db.commit()
    db.refresh(space)
    return space
