"""
Servicio de Cloudinary para la gestión de fotos de evidencia del ERP.
Las credenciales se cargan desde las variables de entorno del archivo .env
"""
import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Configurar Cloudinary con las variables de entorno
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True  # Forzar HTTPS siempre
)


def upload_evidencia(file_bytes: bytes, id_ot: str, tipo_evidencia: str, epoch: int) -> dict:
    """
    Sube una foto de evidencia a Cloudinary.

    Args:
        file_bytes: Contenido binario del archivo.
        id_ot: ID de la Orden de Trabajo (ej. OT-2026-0001).
        tipo_evidencia: Tipo de evidencia ('Desplazamiento', 'Antes', 'Despues').
        epoch: Timestamp Unix para garantizar nombres únicos.

    Returns:
        dict con 'secure_url' y 'public_id' del archivo subido.

    Raises:
        Exception: Si la subida a Cloudinary falla.
    """
    # Sanitizar id_ot para usarlo como nombre de carpeta/archivo (quitar caracteres inválidos)
    id_ot_safe = id_ot.replace("/", "_").replace("\\", "_").replace(" ", "-")

    # Organizar en carpetas: erp-amazonas/evidencias/{id_ot}/
    folder = f"erp-amazonas/evidencias/{id_ot_safe}"

    # Nombre público del archivo (sin extensión, Cloudinary la maneja)
    public_id = f"{folder}/{tipo_evidencia}_{epoch}"

    result = cloudinary.uploader.upload(
        file_bytes,
        public_id=public_id,
        resource_type="image",
        overwrite=False,
        # Transformación automática: optimizar calidad y formato
        eager=[
            {"quality": "auto", "fetch_format": "auto"}
        ],
        eager_async=True,
    )

    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"],
    }


def delete_evidencia(public_id: str) -> bool:
    """
    Elimina una imagen de Cloudinary dado su public_id.

    Args:
        public_id: El identificador público de la imagen en Cloudinary.

    Returns:
        True si se eliminó correctamente, False en caso contrario.
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        return result.get("result") == "ok"
    except Exception:
        return False


def is_configured() -> bool:
    """
    Verifica que las credenciales de Cloudinary están configuradas.

    Returns:
        True si las 3 variables de entorno están presentes.
    """
    return all([
        os.environ.get("CLOUDINARY_CLOUD_NAME"),
        os.environ.get("CLOUDINARY_API_KEY"),
        os.environ.get("CLOUDINARY_API_SECRET"),
    ])
