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
    import datetime
    partes = nombre_completo.strip().split()
    year = datetime.datetime.now().year
    if len(partes) >= 2:
        inicial = partes[0][0].upper()
        apellido = partes[1].capitalize()
        return f"{inicial}{apellido}{year}"
    elif len(partes) == 1:
        return f"{partes[0].capitalize()}{year}"
    else:
        return f"Usuario{year}"


def generate_email_from_name(nombre_completo: str, domain: str = "mantenimiento-amazonas.pe") -> str:
    import datetime
    import unicodedata
    import re

    def normalize(s: str) -> str:
        """Elimina tildes y caracteres especiales."""
        nfkd = unicodedata.normalize('NFKD', s)
        return re.sub(r'[^\w]', '', nfkd.encode('ascii', 'ignore').decode('ascii'))

    partes = nombre_completo.strip().split()
    year = datetime.datetime.now().year
    
    if len(partes) >= 2:
        inicial = partes[0][0].upper()
        apellido = partes[1].capitalize()
        credencial = f"{inicial}{apellido}{year}"
    elif len(partes) == 1:
        credencial = f"{partes[0].capitalize()}{year}"
    else:
        credencial = f"Usuario{year}"
        
    return normalize(credencial)

