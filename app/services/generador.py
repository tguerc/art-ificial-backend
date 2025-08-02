# Imports estándar
from shutil import copyfile
from uuid import uuid4
from pathlib import Path

# Genera una imagen duplicando un archivo existente (robot.jpg) y devuelve la ruta relativa
def generar_imagen(prompt: str) -> str:
    base_dir = Path(__file__).resolve().parents[2]  # Llega a la raíz del proyecto
    origen = base_dir / "output" / "robot.jpg"

    if not origen.exists():
        raise FileNotFoundError(f"La imagen de origen no existe en: {origen}")

    nombre_archivo = f"{uuid4()}.jpg"
    destino_rel = f"/output/{nombre_archivo}"
    destino_abs = base_dir / "output" / nombre_archivo

    try:
        copyfile(origen, destino_abs)
    except Exception as e:
        raise RuntimeError(f"Error al copiar la imagen: {e}")

    return destino_rel