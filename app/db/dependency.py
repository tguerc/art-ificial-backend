# app/db/dependency.py

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal

# Dependencia para obtener una sesión de base de datos asincrónica
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session