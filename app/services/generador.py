# Imports estándar
import os
import time
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

    initRes = requests.post(
        "https://stablehorde.net/api/v2/generate/async",
        headers=headers,
        json=payload,
    )

    raw = initRes.text
    if not initRes.ok:
        raise Exception(f"Stable Horde Error {initRes.status_code}: {raw}")

    request_id = initRes.json()["id"]
    print(f"✅ ID solicitud: {request_id}")

    # ⏳ Polling de estado
    status = None
    max_attempts = 120
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        time.sleep(3)
        
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
            break

    img = status.get("generations", [{}])[0].get("img")
    if not img:
        raise Exception("No se generó ninguna imagen en Stable Horde")

    if img.startswith("http"):
        print(f"✅ ¡Listo! {img}")
        return img

    raise Exception("Imagen en base64 no soportada")