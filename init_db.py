import asyncio
from datetime import datetime
from app.db.database import Base, engine
from app.models.usuario import Usuario
from app.models.obra import Obra
from app.models.valoracion import Valoracion
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def init_db():
    async with engine.begin() as conn:
        print("🛠️ Verificando y creando tablas si no existen...")
        await conn.run_sync(Base.metadata.create_all)  # ✅ Solo crea si no existen

    print("📥 Verificando datos iniciales...")

    async with AsyncSession(engine) as session:
        # Verificar si ya hay usuarios en la base
        result = await session.execute(select(Usuario))
        usuario_existente = result.scalar_one_or_none()

        if usuario_existente:
            print("✅ La base ya contiene datos, no se insertaron ejemplos.")
            return

        # Si está vacía, precargar datos iniciales
        usuario_id = str(uuid.uuid4())
        obra_id = str(uuid.uuid4())

        nuevo_usuario = Usuario(
            id=usuario_id,
            email="ejemplo@ia.com",
            password="hashed-no-importa",  # En producción usar hash real
            userName="Tomás G."
        )

        nueva_obra = Obra(
            id=obra_id,
            nombre="Robot visionario",
            descripcion="Primera obra generada por IA",
            tipoArte="Futurista",
            archivoJPG="/imagenes/robot.jpg",  # Ruta válida en producción
            publicada=True,
            fecha=datetime.utcnow(),
            autor_id=usuario_id
        )

        session.add_all([nuevo_usuario, nueva_obra])
        await session.commit()

        print("✅ Base inicializada con un usuario y obra de ejemplo.")

if __name__ == "__main__":
    asyncio.run(init_db())