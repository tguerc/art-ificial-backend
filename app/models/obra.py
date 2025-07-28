from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.database import Base

class Obra(Base):
    __tablename__ = "obras"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String)
    descripcion = Column(String)
    tipoArte = Column(String)
    archivoJPG = Column(String)
    publicada = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    autor_id = Column(String, ForeignKey("usuarios.id"))

    autor = relationship("Usuario", back_populates="obrasPropias")
    valoraciones = relationship("Valoracion", back_populates="obra", cascade="all, delete")