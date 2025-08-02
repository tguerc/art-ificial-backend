# app/db/database.py

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la base de datos desde .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./artificial.db")

# Motor asincrónico de SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

# Sesión de base de datos asincrónica
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base declarativa para los modelos
Base = declarative_base()