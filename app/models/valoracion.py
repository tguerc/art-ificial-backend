# Imports de terceros
from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

# Imports internos
from app.db.database import Base

# Imports estándar
import uuid


# Modelo de la tabla "valoraciones"
class Valoracion(Base):
    __tablename__ = "valoraciones"

    # Columnas de la tabla
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    puntuacion = Column(Integer, nullable=False)
    obra_id = Column(String, ForeignKey("obras.id"))
    usuario_id = Column(String, ForeignKey("usuarios.id"))

    # Relaciones con otras tablas
    obra = relationship("Obra", back_populates="valoraciones")
    usuario = relationship("Usuario", back_populates="valoraciones")

    # Restricciones únicas
    __table_args__ = (
        UniqueConstraint("obra_id", "usuario_id", name="una_valoracion_por_usuario"),
    )