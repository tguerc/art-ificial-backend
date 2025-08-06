import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    conn = await asyncpg.connect(
        user=os.getenv("user"),
        password=os.getenv("password"),
        database=os.getenv("dbname"),
        host=os.getenv("host"),
        port=os.getenv("port"),
        ssl="require"  # Fuerza SSL en Supabase
    )
    print("✅ Conectado correctamente a Supabase!")
    await conn.close()

asyncio.run(test())
