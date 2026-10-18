"""Dependencias de FastAPI: sesion de BD, usuario autenticado y control de rol."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.base import get_db
from app.models.enums import UserRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token invalido o sesion expirada.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Regla 1: sin token valido no hay acceso a los endpoints protegidos."""
    if credentials is None or not credentials.credentials:
        raise CREDENCIALES_INVALIDAS

    payload = decode_access_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise CREDENCIALES_INVALIDAS

    user = db.scalar(select(User).where(User.correo == payload["sub"]))
    if user is None:
        raise CREDENCIALES_INVALIDAS
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="La cuenta esta desactivada."
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Autorizacion por rol verificada en el backend, no solo en la UI."""
    if current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta operacion requiere rol ADMINISTRADOR.",
        )
    return current_user
