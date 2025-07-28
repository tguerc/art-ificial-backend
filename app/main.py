from fastapi import FastAPI # type: ignore
from app.routers import usuarios, obras  # agregá obras si no está
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path


app = FastAPI()

app.include_router(usuarios.router, prefix="/usuarios")
app.include_router(obras.router, prefix="/obras")

output_path = Path(__file__).resolve().parents[1] / "output"

# Montar carpeta output como servidor de imágenes
os.makedirs("output", exist_ok=True)  # Asegura que la carpeta exista
app.mount("/imagenes", StaticFiles(directory="output"), name="imagenes")
app.mount("/output", StaticFiles(directory=output_path), name="output")




logging.basicConfig(level=logging.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o ["http://localhost:3000"] para más seguro
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  uvicorn app.main:app --reload    