# Imports estándar
from datetime import datetime, timedelta
from uuid import UUID
import os

# Imports de terceros
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

# Imports internos
from app.db.dependency import get_db
from app.models.usuario import Usuario

# Cargar variables de entorno
load_dotenv()

# Configuración de seguridad
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "clave-super-secreta")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRACION_MINUTOS = int(os.getenv("EXPIRACION_MINUTOS", 60 * 24))  # Por defecto 1 día


# Crea un token JWT para un usuario con expiración
def crear_token(user: Usuario):
    expiracion = datetime.utcnow() + timedelta(minutes=EXPIRACION_MINUTOS)
    data = {
        "sub": user.email,        # Identificador principal
        "userName": user.userName,
        "exp": expiracion         # Fecha de expiración del token
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


# Verifica y decodifica un token JWT
def verificar_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# Obtiene el usuario autenticado a partir de un token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    token = credentials.credentials

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
