from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.models.usuario import Usuario
from sqlalchemy import select
from uuid import UUID
from typing import Optional

security = HTTPBearer()


import os

# Simulamos un secreto (en producción usá uno fuerte y guardado en env)
SECRET_KEY = "clave-super-secreta"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_db():
    async with SessionLocal() as session:
        yield session

def verificar_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        print("TOKEN INVÁLIDO:", e)
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    token = credentials.credentials
    print("🟠 TOKEN RECIBIDO:", token)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("🟢 PAYLOAD DECODIFICADO:", payload)
        user_email: str = payload.get("sub")  # 👈 ahora usamos el email
        if not user_email:
            print("❌ No hay 'sub' en el token")
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError as e:
        print("🔴 ERROR AL DECODIFICAR TOKEN:", e)
        raise HTTPException(status_code=401, detail="Token inválido")

    print("🔵 BUSCANDO USUARIO CON EMAIL:", user_email)
    result = await db.execute(select(Usuario).where(Usuario.email == user_email))
    usuario = result.scalar_one_or_none()

    if usuario is None:
        print("🔴 USUARIO NO ENCONTRADO CON EMAIL:", user_email)
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    print("✅ USUARIO AUTENTICADO:", usuario.email)
    return usuario

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[Usuario]:
    if not credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            return None
    except JWTError:
        return None

    result = await db.execute(select(Usuario).where(Usuario.email == user_email))
    return result.scalar_one_or_none()