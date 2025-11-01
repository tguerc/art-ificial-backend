# Imports estándar
import os
import time
import asyncio
from pathlib import Path

# Imports de terceros
import requests

# 🔥 Generar imagen usando Stable Horde con opción NSFW
async def generar_imagen(
    prompt: str,
    nsfw: bool = False,
    model: str = "stable_diffusion"
) -> str:
    headers = {
        "Content-Type": "application/json",
        "apikey": os.getenv("STABLE_HORDE_API_KEY", "S-Dgg1Hs9fKjhuuxX2-qBw"),
        "Client-Agent": "Art-ificial:1.0:debug",
    }

    payload = {
        "prompt": prompt,
        "params": {"steps": 22, "width": 512, "height": 512},
        "models": [model],
        "nsfw": nsfw,
        "censor_nsfw": False,
    }

    print(f"🚀 Enviando a Stable Horde: {prompt[:50]}...")
    
    initRes = requests.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers=headers,
        json=payload,
    )

    if not initRes.ok:
        raise Exception(f"Stable Horde Error {initRes.status_code}: {initRes.text}")

    request_id = initRes.json()["id"]
    print(f"✅ ID solicitud: {request_id}")

    # ⏳ Polling de estado
    max_attempts = 120
    attempt = 0
    status = None
    
    while attempt < max_attempts:
        attempt += 1
        await asyncio.sleep(5)  # Aumentar a 5s para evitar rate limit
        
        pollRes = requests.get(
            f"https://stablehorde.net/api/v2/generate/status/{request_id}",
            headers=headers,
        )
        
        # Si rate limit, esperar más
        if pollRes.status_code == 429:
            print(f"⚠️ Rate limit, esperando...")
            await asyncio.sleep(10)
            continue
        
        if not pollRes.ok:
            print(f"⚠️ Error {pollRes.status_code}: {pollRes.text}")
            continue
            
        status = pollRes.json()
        print(f"📊 Estado completo: {status}")  # Ver qué devuelve realmente
        
        if status.get("queue_position"):
            print(f"📋 Cola: {status['queue_position']}")
        
        if status.get("is_processing"):
            print(f"🎨 Procesando... {attempt * 5}s")
        
        if status.get("done") and status.get("generations"):
            print("✅ ¡Terminado!")
            break
        
        if status.get("faulted"):
            raise Exception(f"Generación falló: {status.get('faulted_reason', 'Desconocido')}")

    if not status or not status.get("generations"):
        raise Exception(f"No se generó ninguna imagen. Estado final: {status}")

    img = status["generations"][0].get("img")
    if not img:
        raise Exception(f"No hay URL en generations: {status['generations']}")

    if img.startswith("http"):
        print(f"✅ ¡URL final! {img}")
        return img

    raise Exception("Imagen en base64 no soportada") 