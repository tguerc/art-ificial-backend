# Imports estándar
import os
from typing import Optional
from uuid import UUID

# Imports de terceros
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

# Imports internos
from app.db.database import SessionLocal
from app.models.usuario import Usuario

# Cargar variables de entorno
load_dotenv()

# Configuración de seguridad
security = HTTPBearer()  # Requerido para endpoints protegidos
security_optional = HTTPBearer(auto_error=False)  # No lanza error si no hay token
SECRET_KEY = os.getenv("SECRET_KEY", "clave-super-secreta")  # Desde .env o valor por defecto
ALGORITHM = os.getenv("ALGORITHM", "HS256")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependencia para obtener la sesión de base de datos
async def get_db():
    async with SessionLocal() as session:
        yield session


# Verifica y decodifica el token JWT
def verificar_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# Obtiene el usuario autenticado a partir del token (requiere token válido)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    token = credentials.credentials

    # Validar token vacío o inválido explícitamente
    if not token or token.lower() in ["null", "undefined"]:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    result = await db.execute(select(Usuario).where(Usuario.email == user_email))
    usuario = result.scalar_one_or_none()

    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario


# Obtiene el usuario autenticado de manera opcional (si no hay token válido, devuelve None)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[Usuario]:
    # Si no hay credenciales o el token es "null"/"undefined", devolver None sin error
    if not credentials or not credentials.credentials or credentials.credentials.lower() in ["null", "undefined"]:
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
