# Imports estándar
import os
import logging
from pathlib import Path

# Imports de terceros
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import cloudinary

# Imports internos
from app.routers import usuarios, obras
from app.db.database import engine, Base

# Cargar variables de entorno desde .env
load_dotenv()

# Inicialización de la aplicación FastAPI
app = FastAPI()

# Incluir routers
app.include_router(usuarios.router, prefix="/usuarios")
app.include_router(obras.router, prefix="/obras")

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

cloudinary.config(secure=True)

# Configuración de CORS
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://art-ificial-frontend-v2.vercel.app"
).split(",")

@app.on_event("startup")
async def crear_tablas_si_no_existen():
    async with engine.begin() as conn:
        print("🛠️ Creando tablas si no existen...")
        await conn.run_sync(Base.metadata.create_all)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],  # Limpiar espacios
    allow_credentials=True,
    allow_methods=["*"],  # Permitir GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Permitir todos los encabezados (incluido Authorization)
)

# Directorio de salida para imágenes generadas
output_path = Path(__file__).resolve().parents[1] / "output"
os.makedirs(output_path, exist_ok=True)

# Montar carpeta estática para servir imágenes
app.mount("/imagenes", StaticFiles(directory=output_path), name="imagenes")

# Ejecutar con: uvicorn app.main:app --reload