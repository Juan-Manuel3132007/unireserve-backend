"""Agrega todos los routers bajo un unico APIRouter."""
from fastapi import APIRouter

from app.api.routes import auth, health, reservations, spaces, stats, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(spaces.router)
api_router.include_router(reservations.router)
api_router.include_router(stats.router)
