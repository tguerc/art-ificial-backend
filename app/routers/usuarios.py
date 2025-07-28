from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from app.db.dependency import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate
from app.utils.security import hashear_password
from app.utils.jwt import crear_token

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    credential: str

# 📌 Registro tradicional (opcional)
@router.post("/registrar")
async def registrar_usuario(usuario: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    resultado = await db.execute(select(Usuario).where(Usuario.email == usuario.email))
    existente = resultado.scalar_one_or_none()

    if existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    nuevo = Usuario(
        email=usuario.email,
        userName=usuario.userName,
        password=hashear_password(usuario.password)
    )
    db.add(nuevo)
    await db.commit()
    await db.refresh(nuevo)

    return {"mensaje": "Usuario registrado con éxito", "id": nuevo.id}

# 📌 Login de prueba (solo email)
@router.post("/login")
async def login(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    token = crear_token(usuario)  # ✅ Pasa el objeto Usuario completo
    return {
        "token": token,
        "user": {
            "id": usuario.id,
            "email": usuario.email,
            "userName": usuario.userName
        }
    }

@router.post("/google-login")
async def google_login(data: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            data.credential,
            requests.Request(),
            audience="470836904892-cpj8gpmd6q3n94dk2ndqio5jhd8t726t.apps.googleusercontent.com"
        )

        email = idinfo['email']
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        result = await db.execute(select(Usuario).where(Usuario.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = Usuario(email=email, userName=name)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # ✅ Este token está bien
        token = crear_token(user)

        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "userName": user.userName,
                "picture": picture
            }
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido")