from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.db.base import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import UserCreateAdmin, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserRead], summary="Listar usuarios (solo ADMINISTRADOR)")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    rol: UserRole | None = None,
    activo: bool | None = None,
    buscar: str | None = Query(default=None, description="Filtra por nombre, apellido o correo"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[UserRead]:
    stmt = select(User)
    if rol is not None:
        stmt = stmt.where(User.rol == rol)
    if activo is not None:
        stmt = stmt.where(User.activo == activo)
    if buscar:
        patron = f"%{buscar.lower()}%"
        stmt = stmt.where(
            func.lower(User.nombre).like(patron)
            | func.lower(User.apellido).like(patron)
            | func.lower(User.correo).like(patron)
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(User.id).offset((page - 1) * size).limit(size)).all()
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, -(-total // size)),
    )


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario desde el panel administrativo",
)
def create_user(
    datos: UserCreateAdmin, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> User:
    if db.scalar(select(User).where(User.correo == datos.correo.lower())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya esta registrado.")
    user = User(
        nombre=datos.nombre.strip(),
        apellido=datos.apellido.strip(),
        correo=datos.correo.lower(),
        contrasena_hash=hash_password(datos.password),
        rol=datos.rol,
        activo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead, summary="Detalle de un usuario")
def get_user(
    user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> User:
    # Un estudiante solo puede consultar su propio perfil.
    if current_user.rol != UserRole.ADMINISTRADOR and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso no autorizado.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return user


@router.put("/{user_id}", response_model=UserRead, summary="Actualizar un usuario")
def update_user(
    user_id: int,
    datos: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    es_admin = current_user.rol == UserRole.ADMINISTRADOR
    if not es_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso no autorizado.")

    cambios = datos.model_dump(exclude_unset=True)
    # Cambiar rol o estado de la cuenta es exclusivo del administrador.
    if not es_admin:
        cambios.pop("rol", None)
        cambios.pop("activo", None)
    for campo, valor in cambios.items():
        setattr(user, campo, valor)

    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    response_model=UserRead,
    summary="Desactivar un usuario (borrado logico, solo ADMINISTRADOR)",
)
def deactivate_user(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="No puede desactivar su propia cuenta."
        )
    # Borrado logico: las reservas historicas se conservan para trazabilidad.
    user.activo = False
    db.commit()
    db.refresh(user)
    return user
