# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    async with SessionLocal() as session:
        yield session