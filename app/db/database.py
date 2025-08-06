import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno
load_dotenv()

# Usar siempre la URL externa
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"🔗 Conectando a la base de datos externa en Render")

# Crear motor asincrónico
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Mostrar logs SQL en consola
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