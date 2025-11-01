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
    
    while attempt < max_attempts:
        attempt += 1
        await asyncio.sleep(3)
        
        pollRes = requests.get(
            f"https://stablehorde.net/api/v2/generate/status/{request_id}",
            headers=headers,
        )
        status = pollRes.json()
        
        if status.get("queue_position"):
            print(f"📋 Cola: {status['queue_position']}")
        
        if status.get("is_processing"):
            print(f"🎨 Procesando... {attempt}s")
        
        if status.get("done"):
            print("✅ ¡Terminado!")
            break

    img = status.get("generations", [{}])[0].get("img")
    if not img:
        raise Exception("No se generó ninguna imagen en Stable Horde")

    if img.startswith("http"):
        print(f"✅ ¡URL final! {img}")
        return img

    raise Exception("Imagen en base64 no soportada")