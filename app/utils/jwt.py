from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.dependency import get_db
from app.models.usuario import Usuario
from datetime import datetime, timedelta
from uuid import UUID


security = HTTPBearer()

# Clave secreta para firmar el JWT (en producción usar variable de entorno)
SECRET_KEY = "clave-super-secreta"
ALGORITHM = "HS256"
EXPIRACION_MINUTOS = 60 * 24  # 1 día

def crear_token(user: Usuario):
    data = {
        "sub": user.email,  # <- usar email
        "userName": user.userName
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

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