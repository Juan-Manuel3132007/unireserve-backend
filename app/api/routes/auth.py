from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.base import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


def _emitir_token(user: User) -> Token:
    return Token(
        access_token=create_access_token(subject=user.correo, role=user.rol.value),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Registro publico (siempre crea un ESTUDIANTE)",
)
def register(datos: UserRegister, db: Session = Depends(get_db)) -> Token:
    existente = db.scalar(select(User).where(User.correo == datos.correo.lower()))
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe una cuenta con ese correo."
        )

    user = User(
        nombre=datos.nombre.strip(),
        apellido=datos.apellido.strip(),
        correo=datos.correo.lower(),
        contrasena_hash=hash_password(datos.password),
        rol=UserRole.ESTUDIANTE,  # el rol nunca se toma del cliente
        activo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _emitir_token(user)


@router.post("/login", response_model=Token, summary="Inicio de sesion")
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(User).where(User.correo == datos.correo.lower()))
    # Mismo mensaje para usuario inexistente y clave incorrecta: no se filtra
    # que correos estan registrados.
    if user is None or not verify_password(datos.password, user.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contrasena incorrectos."
        )
    if not user.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La cuenta esta desactivada.")
    return _emitir_token(user)


@router.get("/me", response_model=UserRead, summary="Perfil del usuario autenticado")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
