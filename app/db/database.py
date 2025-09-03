# app/db/database.py
import os
import ssl
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------
# Cargar variables de entorno
# ---------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _normalize_url(url: str) -> str:
    if not url:
        raise RuntimeError("DATABASE_URL no está definida")
    # Si llega con el prefijo viejo, normalizar a asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    # Asegurar SSL para asyncpg (Render lo exige)
    if "ssl=" not in url and "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "ssl=true"
    return url

# ---------------------------------------------------------------------
# Configuración DB
# ---------------------------------------------------------------------
raw_url = os.getenv("DATABASE_URL", "")
DATABASE_URL = _normalize_url(raw_url)

print("🔗 Conectando a la base de datos externa en Render")

# Contexto TLS explícito (verifica CA y hostname)
_ssl_ctx = ssl.create_default_context()

# Motor asincrónico SQLAlchemy + asyncpg
engine = create_async_engine(
    DATABASE_URL,
    echo=True,                      # logs SQL en consola
    connect_args={"ssl": _ssl_ctx}, # <- clave para Render + asyncpg
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)

# Session factory asincrónica
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base para modelos ORM
Base = declarative_base()
