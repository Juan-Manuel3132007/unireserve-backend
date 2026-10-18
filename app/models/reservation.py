from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReservationStatus


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("hora_fin > hora_inicio", name="ck_reservations_rango_horario"),
        # Indice compuesto: la consulta mas frecuente es "reservas de un espacio en una fecha".
        Index("ix_reservations_space_fecha", "space_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    estado: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"),
        default=ReservationStatus.CONFIRMADA,
        index=True,
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="reservations")  # noqa: F821
    space: Mapped["Space"] = relationship(back_populates="reservations")  # noqa: F821
