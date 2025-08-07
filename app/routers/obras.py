# Imports estándar
import os
import time
from typing import List, Optional
from math import floor

# Imports de terceros
import cloudinary
import cloudinary.uploader
import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
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

# Cloudinary configuración
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

router = APIRouter()
oauth2_scheme = HTTPBearer()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ValoracionRequest(BaseModel):
    puntuacion: int


async def get_db():
    async with SessionLocal() as session:
        yield session


# 🚀 Generar y subir imagen
@router.post("/generar")
async def generar_obra(
    obra: ObraCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    solo_generar: bool = Query(False)
):
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    # Obtener imagen desde URL
    if not obra.imagen or not obra.imagen.strip().startswith("http"):
        raise HTTPException(status_code=400, detail="Debe enviarse una URL válida")

    try:
        response = requests.get(obra.imagen)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar la imagen")

        # Subir a Cloudinary con timestamp
        timestamp = int(time.time())
        nombre_cloud = f"obra_{timestamp}"

        result = cloudinary.uploader.upload(
            response.content,
            public_id=nombre_cloud,
            resource_type="image",
            folder="artificial",
            overwrite=True
        )
        image_url = result["secure_url"]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo a Cloudinary: {e}")

    if solo_generar:
        return {"mensaje": "Imagen generada temporalmente", "archivo": image_url}

    nueva = Obra(
        nombre=obra.nombre,
        descripcion=obra.descripcion,
        tipoArte=obra.tipoArte,
        archivoJPG=image_url,
        publicada=True,
        autor_id=usuario.id
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)

    return {"mensaje": "Obra generada y guardada", "archivo": image_url}


@router.get("/mis-obras", response_model=List[ObraOut])
async def mis_obras(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    filas = result.all()

    obras = []
    for obra, autor_nombre, promedio, cantidad in filas:
        promedio_truncado = floor(promedio * 100) / 100 if promedio is not None else None
        obra_dict = {
            **obra.__dict__,
            "archivoJPG": obra.archivoJPG,
            "autor_nombre": autor_nombre,
            "promedio_valoracion": promedio_truncado,
            "cantidad_valoraciones": cantidad
        }
        obras.append(obra_dict)
    return obras


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


@router.get("/muro", response_model=List[ObraOut])
async def muro_publico(db: AsyncSession = Depends(get_db), usuario: Optional[Usuario] = Depends(get_current_user_optional)):
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
            "archivoJPG": obra.archivoJPG,
            "autor_nombre": autor_nombre,
            "promedio_valoracion": promedio_truncado,
            "cantidad_valoraciones": cantidad,
            "ya_valorada": ya_valorada,
            "puntuacion_usuario": puntuacion_usuario
        })

    return obras


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


@router.post("/{obra_id}/valorar")
async def valorar_obra(obra_id: str, data: ValoracionRequest, db: AsyncSession = Depends(get_db), usuario_actual: Usuario = Depends(get_current_user)):
    if data.puntuacion < 1 or data.puntuacion > 5:
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
        puntuacion=data.puntuacion,
        obra_id=obra_id,
        usuario_id=usuario_actual.id
    )
    db.add(nueva_valoracion)
    await db.commit()
    return {"detail": "Valoración registrada"}


@router.get("/obras/todas", response_model=List[ObraSimple])
async def obtener_todas_las_obras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Obra).order_by(Obra.fecha.desc()))
    obras = result.scalars().all()
    return obras


@router.get("/imagenes/{nombre}")
async def redirigir_a_cloudinary(nombre: str):
    return RedirectResponse(f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/artificial/{nombre}")


@router.delete("/obras/eliminar-todas")
async def eliminar_todas_las_obras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Obra))
    obras = result.scalars().all()

    for obra in obras:
        await db.delete(obra)
    await db.commit()

    return {"mensaje": f"Se eliminaron {len(obras)} obras correctamente."}
