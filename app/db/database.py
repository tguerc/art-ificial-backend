import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno
load_dotenv()

# Detectar entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "local").lower()

if ENVIRONMENT == "render":
    DATABASE_URL = os.getenv("DATABASE_URL_INTERNAL")
    print("🔗 Usando DATABASE_URL interna (Render)")
else:
    DATABASE_URL = os.getenv("DATABASE_URL_EXTERNAL")
    print("🔗 Usando DATABASE_URL externa (Local)")

# Crear motor asincrónico
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

# Base declarativa para modelos
Base = declarative_base()