from pydantic import BaseModel # type: ignore
from uuid import UUID
from datetime import datetime
from typing import Optional

class ObraCreate(BaseModel):
    nombre: str
    descripcion: str
    tipoArte: str
    prompt: str
    imagen: Optional[str] = None
    
class ObraSimple(BaseModel):
    id: str
    nombre: str
    descripcion: str
    tipoArte: str
    archivoJPG: str
    publicada: bool
    fecha: datetime
    autor_id: str

    class Config:
        from_attributes = True

class ObraOut(BaseModel):
    id: str
    nombre: str
    descripcion: str
    tipoArte: str
    archivoJPG: str
    publicada: bool
    fecha: datetime
    autor_id: str
    autor_nombre: str
    promedio_valoracion: Optional[float] = None
    cantidad_valoraciones: Optional[int] = 0
    ya_valorada: Optional[bool] = False  # 👈 nuevo campo para controlar el frontend

    class Config:
        from_attributes = True
