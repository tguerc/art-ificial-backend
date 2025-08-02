from fastapi import FastAPI
from app.routers import usuarios, obras
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

app = FastAPI()

# Incluir routers
app.include_router(usuarios.router, prefix="/usuarios")
app.include_router(obras.router, prefix="/obras")

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio de salida
output_path = Path(__file__).resolve().parents[1] / "output"
os.makedirs(output_path, exist_ok=True)

# ✅ Montar carpeta estática para servir imágenes
app.mount("/imagenes", StaticFiles(directory=output_path), name="imagenes")

# 🚀 Ejecutar con: uvicorn app.main:app --reload