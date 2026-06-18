"""
Utilidades de seguridad: hashing de contraseñas con bcrypt.
Buenas prácticas:
  - Las contraseñas NUNCA se almacenan en texto plano.
  - Se usa bcrypt con factor de trabajo 12 (suficientemente lento para resistir ataques de fuerza bruta).
  - Las funciones son independientes del gestor de BD para mayor modularidad.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """Genera un hash bcrypt seguro a partir de una contraseña en texto plano."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con el hash almacenado."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def generate_password_from_name(nombre_completo: str) -> str:
    """
    Genera una contraseña inicial a partir del nombre y apellido del personal.
    
    Reglas:
    - Toma la primera letra del nombre en mayúscula.
    - Usa el primer apellido completo con primera letra en mayúscula.
    - Añade el sufijo '#Amazonas' para fortalecerla.
    
    Ejemplo: "Juan Carlos Perez Gomez" -> "JPerez#Amazonas"
    Si solo tiene un nombre: "Juan" -> "Juan#Amazonas"
    """
    partes = nombre_completo.strip().split()
    if len(partes) >= 2:
        inicial_nombre = partes[0][0].upper()
        apellido = partes[1].capitalize()
        return f"{inicial_nombre}{apellido}#Amazonas"
    elif len(partes) == 1:
        return f"{partes[0].capitalize()}#Amazonas"
    else:
        return "Amazonas#2026"


def generate_email_from_name(nombre_completo: str, domain: str = "mantenimiento-amazonas.pe") -> str:
    """
    Genera un email corporativo limpio a partir del nombre completo.
    
    Ejemplo: "Juan Carlos Perez Gomez" -> "jcarlos.perez@mantenimiento-amazonas.pe"
    """
    import unicodedata
    import re

    def normalize(s: str) -> str:
        """Elimina tildes y caracteres especiales."""
        nfkd = unicodedata.normalize('NFKD', s)
        return re.sub(r'[^\w]', '', nfkd.encode('ascii', 'ignore').decode('ascii')).lower()

    partes = nombre_completo.strip().split()
    if len(partes) == 0:
        return f"usuario@{domain}"

    if len(partes) == 1:
        return f"{normalize(partes[0])}@{domain}"

    # "Juan Carlos Perez Gomez" -> nombre="Juan Carlos", apellido="Perez"
    # Asumiendo formato: NOMBRE(S) APELLIDO(S)
    # Tomamos el primer nombre (si hay 2+ partes) y primer apellido
    nombre_part = normalize(partes[0])
    apellido_part = normalize(partes[1]) if len(partes) > 1 else ""

    if apellido_part:
        return f"{nombre_part}.{apellido_part}@{domain}"
    else:
        return f"{nombre_part}@{domain}"
