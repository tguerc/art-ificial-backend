# Imports estándar
import os
import logging
from pathlib import Path

# Imports de terceros
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv  # Para leer .env

# Imports internos
from app.routers import usuarios, obras

# Cargar variables de entorno desde .env
load_dotenv()

# Inicialización de la aplicación FastAPI
app = FastAPI()

# Incluir routers
app.include_router(usuarios.router, prefix="/usuarios")
app.include_router(obras.router, prefix="/obras")

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Configuración de CORS con variable de entorno
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio de salida para imágenes generadas
output_path = Path(__file__).resolve().parents[1] / "output"
os.makedirs(output_path, exist_ok=True)

# Montar carpeta estática para servir imágenes
app.mount("/imagenes", StaticFiles(directory=output_path), name="imagenes")

# Ejecutar con: uvicorn app.main:app --reload
