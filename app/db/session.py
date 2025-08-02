# app/db/session.py

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal

# Context manager asincrónico para obtener una sesión de base de datos
@asynccontextmanager
async def get_db():
    async with SessionLocal() as session:
        yield session