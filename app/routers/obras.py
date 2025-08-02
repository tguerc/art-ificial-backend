import base64
import os
import requests
import time
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from app.db.database import SessionLocal
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.valoracion import Valoracion
from app.schemas.obra import ObraCreate, ObraOut, ObraSimple
from app.services.generador import generar_imagen
from app.utils.jwt import verificar_token
from app.utils.auth import get_current_user, get_current_user_optional
from fastapi.responses import FileResponse


router = APIRouter()
oauth2_scheme = HTTPBearer()

class ValoracionRequest(BaseModel):
    puntuacion: int

async def get_db():
    async with SessionLocal() as session:
        yield session





from fastapi import Query

@router.post("/generar")
async def generar_obra(
    obra: ObraCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
    solo_generar: bool = Query(False, description="Si es true, solo genera la imagen sin guardarla en DB")
):
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    print("📥 Datos recibidos:", obra.dict())
    print("🎯 solo_generar:", solo_generar)

    # ✅ Subir dos niveles desde app/routers hasta la raíz del proyecto
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    output_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = int(time.time())
    file_name = f"obra_{timestamp}.jpg"
    file_path = os.path.join(output_dir, file_name)

    # Manejo de imagen
    if obra.imagen and obra.imagen.strip():
        if obra.imagen.startswith("data:image"):
            print("🖼️ Guardando imagen desde Base64")
            header, b64data = obra.imagen.split(",", 1)
            image_bytes = base64.b64decode(b64data)
            with open(file_path, "wb") as f:
                f.write(image_bytes)

        elif obra.imagen.startswith("http"):
            if "localhost:8000/output/" in obra.imagen:
                print("📂 Copiando imagen local directamente (sin HTTP)")
                local_name = obra.imagen.split("/output/")[-1]
                local_path = os.path.join(output_dir, local_name)
                if not os.path.exists(local_path):
                    raise HTTPException(status_code=404, detail="Imagen local no encontrada")
                with open(local_path, "rb") as src, open(file_path, "wb") as dest:
                    dest.write(src.read())
            else:
                print("🌐 Descargando imagen externa:", obra.imagen)
                response = requests.get(obra.imagen)
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="No se pudo descargar la imagen desde la URL")
                with open(file_path, "wb") as f:
                    f.write(response.content)
    else:
        print("⚠️ Usando robot.jpg por defecto")
        robot_path = os.path.join(output_dir, "robot.jpg")
        if not os.path.exists(robot_path):
            raise HTTPException(status_code=404, detail="robot.jpg no encontrado en output")
        file_name = "robot.jpg"
        file_path = robot_path

    archivo = f"/output/{file_name}"

    # ✅ Si solo queremos generar, devolvemos la URL y no guardamos en DB
    if solo_generar:
        print("🛑 Solo generando imagen, no guardando en DB.")
        return {"mensaje": "Imagen generada temporalmente", "archivo": f"http://localhost:8000{archivo}"}

    # ✅ Si es publicación normal, guardar en DB
    nueva = Obra(
        nombre=obra.nombre,
        descripcion=obra.descripcion,
        tipoArte=obra.tipoArte,
        archivoJPG=archivo,
        publicada=True,
        autor_id=usuario.id
    )
    db.add(nueva)
    await db.commit()
    await db.refresh(nueva)

    print("✅ Obra guardada con archivo:", archivo)
    return {"mensaje": "Obra generada y guardada", "archivo": f"http://localhost:8000{archivo}"}



@router.get("/mis-obras", response_model=List[ObraOut])
async def mis_obras(current_user: Usuario = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    print("USUARIO AUTENTICADO:", current_user.email, current_user.id)

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
    print(f"OBRAS ENCONTRADAS: {len(filas)}")

    obras = []
    for obra, autor_nombre, promedio, cantidad in filas:
        obra_dict = {
            **obra.__dict__,
            "autor_nombre": autor_nombre,
            "promedio_valoracion": round(promedio, 2) if promedio else None,
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
async def muro_publico(
    db: AsyncSession = Depends(get_db),
    usuario: Optional[Usuario] = Depends(get_current_user)  # 👈 opcional
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
    )

    result = await db.execute(stmt)

    obras = []
    for obra, autor_nombre, promedio, cantidad in result.all():
        ya_valorada = False
        if usuario:
            subq = await db.execute(
                select(Valoracion).where(
                    Valoracion.obra_id == obra.id,
                    Valoracion.usuario_id == usuario.id
                )
            )
            ya_valorada = subq.scalar_one_or_none() is not None

        obra_dict = {
            **obra.__dict__,
            "autor_nombre": autor_nombre,
            "promedio_valoracion": round(promedio, 2) if promedio else None,
            "cantidad_valoraciones": cantidad,
            "ya_valorada": ya_valorada  # 👈 se devuelve al frontend
        }
        obras.append(obra_dict)

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


@router.get("/obras/todas", response_model=List[ObraSimple])
async def obtener_todas_las_obras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Obra).order_by(Obra.fecha.desc()))
    obras = result.scalars().all()
    return obras

# 📌 Servir imágenes desde output con CORS habilitado
@router.get("/imagenes/{nombre}")
async def obtener_imagen(nombre: str):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    file_path = os.path.join(BASE_DIR, "output", nombre)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return FileResponse(file_path, media_type="image/jpeg", headers={"Access-Control-Allow-Origin": "*"})