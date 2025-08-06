# Imports estándar
import base64
import os
import time
from typing import List, Optional
from pathlib import Path
from math import floor

# Imports de terceros
import requests
from fastapi import APIRouter, Depends, HTTPException, Path as FastPath, Query
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel
from dotenv import load_dotenv

# Imports internos
from app.db.database import SessionLocal
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.valoracion import Valoracion
from app.schemas.obra import ObraCreate, ObraOut, ObraSimple
from app.services.generador import generar_imagen
from app.utils.jwt import verificar_token
from app.utils.auth import get_current_user, get_current_user_optional

# Cargar variables de entorno
load_dotenv()

# Configuración del router
router = APIRouter()
oauth2_scheme = HTTPBearer()

# Base URL de la API (para devolver rutas correctas)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Esquemas de request
class ValoracionRequest(BaseModel):
    puntuacion: int

# Dependencia para obtener la sesión de la base de datos
async def get_db():
    async with SessionLocal() as session:
        yield session


# Endpoint: Generar una obra
@router.post("/generar")
async def generar_obra(
    obra: ObraCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    solo_generar: bool = Query(False, description="Si es true, solo genera la imagen sin guardarla en DB")
):
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    if not obra.imagen or not obra.imagen.startswith("data:image"):
        raise HTTPException(status_code=400, detail="Imagen inválida o ausente")

    # Extraer contenido base64 desde el string "data:image/jpeg;base64,..."
    try:
        header, b64data = obra.imagen.split(",", 1)
        base64.b64decode(b64data)  # Validar base64
    except Exception:
        raise HTTPException(status_code=400, detail="Base64 malformado o ilegible")

    if solo_generar:
        return {
            "mensaje": "Imagen generada temporalmente",
            "archivo": obra.imagen  # ya contiene el "data:image/jpeg;base64,..."
        }

    nueva = Obra(
        nombre=obra.nombre,
        descripcion=obra.descripcion,
        tipoArte=obra.tipoArte,
        archivoJPG=b64data,  # Guardamos solo el contenido sin el encabezado
        publicada=True,
        autor_id=usuario.id
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)

    return {
        "mensaje": "Obra generada y guardada",
        "archivo": f"data:image/jpeg;base64,{b64data}"
    }


# Endpoint: Obtener obras del usuario autenticado
@router.get("/mis-obras", response_model=List[ObraOut])
async def mis_obras(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            Obra,
            Usuario.userName,
            func.avg(Valoracion.puntuacion).label("promedio_valoracion"),
            func.count(Valoracion.id).label("cantidad_valoraciones")
        )
        .join(Usuario, Usuario.id == Obra.autor_id)
        .outerjoin(Valoracion, Valoracion.obra_id == Obra.id)
        .where(Obra.autor_id == current_user.id)
        .group_by(Obra.id, Usuario.userName)
    )

    result = await db.execute(stmt)

    obras = []
    for obra, autor_nombre, promedio, cantidad in result.all():
        promedio_truncado = floor(promedio * 100) / 100 if promedio is not None else None
        obras.append({
            **obra.__dict__,
            "archivoJPG": f"data:image/jpeg;base64,{obra.archivoJPG}",
            "autor_nombre": autor_nombre,
            "promedio_valoracion": promedio_truncado,
            "cantidad_valoraciones": cantidad
        })

    return obras

# Endpoint: Cambiar visibilidad de una obra
@router.patch("/{id}/publicar")
async def cambiar_visibilidad(id: str, body: dict, db: AsyncSession = Depends(get_db), usuario=Depends(get_current_user)):
    query = select(Obra).where(Obra.id == id, Obra.autor_id == usuario.id)
    result = await db.execute(query)
    obra = result.scalar_one_or_none()

    if not obra:
        raise HTTPException(status_code=404, detail="Obra no encontrada o no te pertenece")

    obra.publicada = body.get("publicada", True)
    await db.commit()
    await db.refresh(obra)

    return {"mensaje": "Visibilidad actualizada", "id": obra.id, "publicada": obra.publicada}


# Endpoint: Muro público con obras publicadas ordenadas por fecha
@router.get("/muro", response_model=List[ObraOut])
async def muro_publico(
    db: AsyncSession = Depends(get_db),
    usuario: Optional[Usuario] = Depends(get_current_user_optional)
):
    stmt = (
        select(
            Obra,
            Usuario.userName,
            func.avg(Valoracion.puntuacion).label("promedio_valoracion"),
            func.count(Valoracion.id).label("cantidad_valoraciones")
        )
        .join(Usuario, Usuario.id == Obra.autor_id)
        .outerjoin(Valoracion, Valoracion.obra_id == Obra.id)
        .where(Obra.publicada == True)
        .group_by(Obra.id, Usuario.userName)
        .order_by(Obra.fecha.desc())
    )

    result = await db.execute(stmt)

    obras = []
    for obra, autor_nombre, promedio, cantidad in result.all():
        ya_valorada = False
        puntuacion_usuario = None

        if usuario:
            valoracion_user = await db.execute(
                select(Valoracion).where(
                    Valoracion.obra_id == obra.id,
                    Valoracion.usuario_id == usuario.id
                )
            )
            valoracion = valoracion_user.scalar_one_or_none()
            if valoracion:
                ya_valorada = True
                puntuacion_usuario = valoracion.puntuacion

        promedio_truncado = floor(promedio * 100) / 100 if promedio is not None else None

        obras.append({
            **obra.__dict__,
            "archivoJPG": f"data:image/jpeg;base64,{obra.archivoJPG}",
            "autor_nombre": autor_nombre,
            "promedio_valoracion": promedio_truncado,
            "cantidad_valoraciones": cantidad,
            "ya_valorada": ya_valorada,
            "puntuacion_usuario": puntuacion_usuario
        })

    return obras


# Endpoint: Eliminar obra
@router.delete("/{obra_id}")
async def eliminar_obra(obra_id: str, db: AsyncSession = Depends(get_db), usuario_actual: Usuario = Depends(get_current_user)):
    result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.autor_id == usuario_actual.id)
    )
    obra = result.scalar_one_or_none()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra no encontrada o no autorizada")
    await db.delete(obra)
    await db.commit()
    return {"detail": "Obra eliminada"}


# Endpoint: Valorar una obra
@router.post("/{obra_id}/valorar")
async def valorar_obra(
    obra_id: str,
    data: ValoracionRequest,
    db: AsyncSession = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user)
):
    puntuacion = data.puntuacion
    if puntuacion < 1 or puntuacion > 5:
        raise HTTPException(status_code=400, detail="Puntuación inválida")

    result = await db.execute(
        select(Valoracion).where(
            Valoracion.obra_id == obra_id,
            Valoracion.usuario_id == usuario_actual.id
        )
    )
    valoracion_existente = result.scalar_one_or_none()

    if valoracion_existente:
        raise HTTPException(status_code=400, detail="Ya valoraste esta obra")

    nueva_valoracion = Valoracion(
        puntuacion=puntuacion,
        obra_id=obra_id,
        usuario_id=usuario_actual.id
    )
    db.add(nueva_valoracion)
    await db.commit()
    return {"detail": "Valoración registrada"}


# Endpoint: Obtener todas las obras ordenadas por fecha
@router.get("/obras/todas", response_model=List[ObraSimple])
async def obtener_todas_las_obras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Obra).order_by(Obra.fecha.desc()))
    obras = result.scalars().all()
    return obras


# Endpoint: Servir imágenes desde output con CORS habilitado
@router.get("/imagenes/{nombre}")
async def obtener_imagen(nombre: str):
    BASE_DIR = Path(__file__).resolve().parents[2]
    file_path = BASE_DIR / "output" / nombre

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return FileResponse(file_path, media_type="image/jpeg", headers={"Access-Control-Allow-Origin": "*"})
