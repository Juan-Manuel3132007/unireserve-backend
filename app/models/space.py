from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SpaceStatus, SpaceType


class Space(Base):
    __tablename__ = "spaces"
    __table_args__ = (CheckConstraint("capacidad > 0", name="ck_spaces_capacidad_positiva"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ubicacion: Mapped[str] = mapped_column(String(160), nullable=False)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo: Mapped[SpaceType] = mapped_column(Enum(SpaceType, name="space_type"), index=True, nullable=False)
    estado: Mapped[SpaceStatus] = mapped_column(
        Enum(SpaceStatus, name="space_status"), default=SpaceStatus.DISPONIBLE, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    reservations: Mapped[list["Reservation"]] = relationship(  # noqa: F821
        back_populates="space", cascade="all, delete-orphan"
    )
