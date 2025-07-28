# app/models/valoracion.py
from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid

class Valoracion(Base):
    __tablename__ = "valoraciones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    puntuacion = Column(Integer, nullable=False)

    obra_id = Column(String, ForeignKey("obras.id"))
    usuario_id = Column(String, ForeignKey("usuarios.id"))

    obra = relationship("Obra", back_populates="valoraciones")
    usuario = relationship("Usuario", back_populates="valoraciones")

    __table_args__ = (UniqueConstraint("obra_id", "usuario_id", name="una_valoracion_por_usuario"),)