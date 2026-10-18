from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ReservationStatus


class ReservationCreate(BaseModel):
    space_id: int = Field(gt=0)
    fecha: date
    hora_inicio: time
    hora_fin: time
    motivo: str = Field(min_length=3, max_length=255)

    @model_validator(mode="after")
    def _validar_rango(self):
        # Regla 3: la hora de fin debe ser posterior a la de inicio.
        if self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora de finalizacion debe ser posterior a la hora de inicio.")
        return self


class ReservationUpdate(BaseModel):
    fecha: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    motivo: str | None = Field(default=None, min_length=3, max_length=255)
    estado: ReservationStatus | None = None


class ReservationUserMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    correo: str


class ReservationSpaceMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    ubicacion: str


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    space_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    estado: ReservationStatus
    motivo: str
    created_at: datetime
    updated_at: datetime
    user: ReservationUserMini | None = None
    space: ReservationSpaceMini | None = None
