import asyncio
from datetime import datetime
from app.db.database import Base, engine
from app.models.usuario import Usuario
from app.models.obra import Obra
from app.models.valoracion import Valoracion
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

async def init_db():
    async with engine.begin() as conn:
        print("🧨 Borrando y recreando tablas (modo desarrollo)...")
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("📥 Precargando datos de ejemplo...")

    async with AsyncSession(engine) as session:
        usuario_id = str(uuid.uuid4())
        obra_id = str(uuid.uuid4())

        nuevo_usuario = Usuario(
            id=usuario_id,
            email="ejemplo@ia.com",
            password="hashed-no-importa",  # en producción, usar hash real
            userName="Tomás G."
        )

        nueva_obra = Obra(
            id=obra_id,
            nombre="Robot visionario",
            descripcion="Primera obra generada por IA",
            tipoArte="Futurista",
            archivoJPG="/imagenes/robot.jpg",  # asegurate que exista en /output/
            publicada=True,
            fecha=datetime.utcnow(),
            autor_id=usuario_id
        )

        session.add_all([nuevo_usuario, nueva_obra])
        await session.commit()

    print("✅ Base cargada con una obra de ejemplo.")

if __name__ == "__main__":
    asyncio.run(init_db())