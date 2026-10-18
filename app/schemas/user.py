import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole

PASSWORD_RULE = (
    "La contrasena debe tener al menos 8 caracteres, una mayuscula, "
    "una minuscula y un numero."
)


def validar_password(valor: str) -> str:
    if len(valor) < 8:
        raise ValueError(PASSWORD_RULE)
    if not re.search(r"[A-Z]", valor) or not re.search(r"[a-z]", valor) or not re.search(r"\d", valor):
        raise ValueError(PASSWORD_RULE)
    return valor


class UserBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    apellido: str = Field(min_length=2, max_length=80)
    correo: EmailStr


class UserRegister(UserBase):
    """Registro publico: el rol SIEMPRE es ESTUDIANTE, no se acepta del cliente."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_fuerte(cls, v: str) -> str:
        return validar_password(v)


class UserCreateAdmin(UserRegister):
    """Creacion desde el panel administrativo: aqui si se puede fijar el rol."""

    rol: UserRole = UserRole.ESTUDIANTE


class UserUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    apellido: str | None = Field(default=None, min_length=2, max_length=80)
    activo: bool | None = None
    rol: UserRole | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rol: UserRole
    activo: bool
    created_at: datetime
    updated_at: datetime
