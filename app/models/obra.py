# Imports estándar
from datetime import datetime
import uuid

# Imports de terceros
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

# Imports internos
from app.db.database import Base

# Modelo de la tabla "obras"
class Obra(Base):
    __tablename__ = "obras"

    # Columnas de la tabla
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String)
    descripcion = Column(String)
    tipoArte = Column(String)
    archivoJPG = Column(String)
    publicada = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    autor_id = Column(String, ForeignKey("usuarios.id"))

    # Relaciones con otras tablas
    autor = relationship("Usuario", back_populates="obrasPropias")
    valoraciones = relationship("Valoracion", back_populates="obra", cascade="all, delete")