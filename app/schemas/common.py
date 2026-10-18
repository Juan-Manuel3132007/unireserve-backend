from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Message(BaseModel):
    detail: str


class Page(BaseModel, Generic[T]):
    """Respuesta paginada consistente para los listados."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
