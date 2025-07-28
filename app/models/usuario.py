from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
import uuid

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)
    userName = Column(String, nullable=False)

    

Usuario.obrasPropias = relationship("Obra", back_populates="autor")
Usuario.valoraciones = relationship("Valoracion", back_populates="usuario", cascade="all, delete")
