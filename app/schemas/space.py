from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SpaceStatus, SpaceType


class SpaceBase(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)
    ubicacion: str = Field(min_length=3, max_length=160)
    capacidad: int = Field(gt=0, le=5000)
    tipo: SpaceType
    estado: SpaceStatus = SpaceStatus.DISPONIBLE


class SpaceCreate(SpaceBase):
    pass


class SpaceUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)
    ubicacion: str | None = Field(default=None, min_length=3, max_length=160)
    capacidad: int | None = Field(default=None, gt=0, le=5000)
    tipo: SpaceType | None = None
    estado: SpaceStatus | None = None


class SpaceRead(SpaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class OccupiedSlot(BaseModel):
    reservation_id: int
    hora_inicio: str
    hora_fin: str


class AvailabilityRead(BaseModel):
    space_id: int
    fecha: str
    espacio_habilitado: bool
    ocupado: list[OccupiedSlot]
