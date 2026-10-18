"""Enumeraciones del dominio compartidas por modelos y schemas."""
import enum


class UserRole(str, enum.Enum):
    ESTUDIANTE = "ESTUDIANTE"
    ADMINISTRADOR = "ADMINISTRADOR"


class SpaceType(str, enum.Enum):
    SALA_ESTUDIO = "SALA_ESTUDIO"
    LABORATORIO = "LABORATORIO"
    SALA_REUNIONES = "SALA_REUNIONES"
    AUDITORIO = "AUDITORIO"
    AULA = "AULA"


class SpaceStatus(str, enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    DESHABILITADO = "DESHABILITADO"
    MANTENIMIENTO = "MANTENIMIENTO"


class ReservationStatus(str, enum.Enum):
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
