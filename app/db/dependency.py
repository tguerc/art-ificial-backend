# app/db/dependency.py
from app.db.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session