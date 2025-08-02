# Imports de terceros
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

# Imports internos
from app.db.database import Base

# Imports estándar
import uuid


# Modelo de la tabla "usuarios"
class Usuario(Base):
    __tablename__ = "usuarios"

    # Columnas de la tabla
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)
    userName = Column(String, nullable=False)


# Relaciones con otras tablas
Usuario.obrasPropias = relationship("Obra", back_populates="autor")
Usuario.valoraciones = relationship("Valoracion", back_populates="usuario", cascade="all, delete")