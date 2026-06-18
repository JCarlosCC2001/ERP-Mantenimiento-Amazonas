import os
import sys
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import Any, Optional

# Asegurar que el directorio actual esté en la ruta para poder importar sheets_service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_service import sheets_service
from main import map_row_to_elemento, map_row_to_ot
from security import hash_password, generate_email_from_name, generate_password_from_name

# Cargar dotenv
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def test_and_get_db_connection():
    if not DATABASE_URL or "xxxxxx" in DATABASE_URL or "[YOUR-PASSWORD]" in DATABASE_URL:
        print("\n[ERROR] Por favor, configura tu contraseña y host reales de Supabase en DATABASE_URL dentro del archivo backend/.env.")
        print("Ejemplo: DATABASE_URL=postgresql://postgres:mi_contraseña_real@db.ofqmfptmqjdywvpszmim.supabase.co:5432/postgres\n")
        sys.exit(1)
        
    try:
        uri = DATABASE_URL
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
            
        conn = psycopg2.connect(uri, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"\n[ERROR] No se pudo conectar a la base de datos de Supabase: {e}")
        print("Por favor, verifica que tu contraseña y los datos en backend/.env sean correctos.\n")
        sys.exit(1)

def inicializar_tablas(conn):
    print("Inicializando tablas en Supabase recreándolas...")
    with conn.cursor() as cur:
        # Forzar la recreación para actualizar el esquema limpio
        cur.execute("DROP TABLE IF EXISTS ordenes_trabajo CASCADE;")
        cur.execute("DROP TABLE IF EXISTS elementos CASCADE;")
        
        # Tabla elementos expandida
        cur.execute("""
            CREATE TABLE elementos (
                id_elemento VARCHAR(100) PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                tipo VARCHAR(50) CHECK(tipo IN ('Nodo', 'IAO', 'Hotspot')) NOT NULL,
                pendiente VARCHAR(255),
                categoria VARCHAR(255),
                dependencia VARCHAR(255),
                provincia VARCHAR(255),
                distrito VARCHAR(255),
                localidad VARCHAR(255),
                latitud VARCHAR(100),
                longitud VARCHAR(100)
            );
        """)
        # Tabla ordenes_trabajo
        cur.execute("""
            CREATE TABLE ordenes_trabajo (
                id_ot VARCHAR(100) PRIMARY KEY,
                id_elemento VARCHAR(100) NOT NULL REFERENCES elementos(id_elemento) ON DELETE RESTRICT ON UPDATE CASCADE,
                prioridad VARCHAR(50) CHECK(prioridad IN ('Alta', 'Media', 'Baja')) NOT NULL,
                diagnostico_inicial TEXT,
                hora_recepcion TIMESTAMP NOT NULL,
                hora_despacho TIMESTAMP,
                hora_llegada TIMESTAMP,
                hora_cierre TIMESTAMP,
                estado VARCHAR(50) CHECK(estado IN ('Abierta', 'Despachada', 'En Sitio', 'Cerrada')) DEFAULT 'Abierta'
            );
        """)
        # Tabla personal con hashing de contraseñas (buenas prácticas)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS personal (
                id_personal SERIAL PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                cargo VARCHAR(100),
                cm VARCHAR(100),
                estado VARCHAR(50) CHECK(estado IN ('Activo', 'Inactivo')) DEFAULT 'Activo',
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_personal_email ON personal(email);")
    conn.commit()
    print("Tablas listas.")

def parse_iso_datetime(dt_str: Any) -> Optional[datetime]:
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    try:
        clean_str = str(dt_str).strip()
        if clean_str.endswith("Z"):
            clean_str = clean_str[:-1]
        return datetime.fromisoformat(clean_str)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue
    return None

def migrar_datos():
    conn = test_and_get_db_connection()
    inicializar_tablas(conn)
    
    print("\nObteniendo datos desde Google Sheets...")
    try:
        raw_elementos = sheets_service.obtener_datos_red()
        raw_ots = sheets_service.obtener_datos_master()
    except Exception as e:
        print(f"[ERROR] Error al leer Google Sheets: {e}")
        conn.close()
        sys.exit(1)
        
    print(f"Leídos {len(raw_elementos)} elementos y {len(raw_ots)} OTs desde Google Sheets.")

    # --- PROCESAR ELEMENTOS ---
    print("\nProcesando e insertando elementos en Supabase...")
    elementos_procesados = {}
    
    for row in raw_elementos:
        if not any(row.values()):
            continue
            
        el = map_row_to_elemento(row)
        id_el = el["id_elemento"]
        nombre = el["nombre"]
        tipo = el["tipo"]
        
        if not id_el:
            continue
            
        original_id = id_el
        sufijo = 1
        while id_el in elementos_procesados:
            sufijo += 1
            id_el = f"{original_id}-{sufijo}"
            
        if id_el != original_id:
            print(f"  [Aviso] ID de elemento duplicado detectado. Renombrando '{original_id}' a '{id_el}'")
            
        elementos_procesados[id_el] = {
            "id_elemento": id_el,
            "nombre": nombre,
            "tipo": tipo,
            "pendiente": el.get("pendiente"),
            "categoria": el.get("categoria"),
            "dependencia": el.get("dependencia"),
            "provincia": el.get("provincia"),
            "distrito": el.get("distrito"),
            "localidad": el.get("localidad"),
            "latitud": el.get("latitud"),
            "longitud": el.get("longitud")
        }

    elementos_list = [
        (
            data["id_elemento"], data["nombre"], data["tipo"],
            data["pendiente"], data["categoria"], data["dependencia"],
            data["provincia"], data["distrito"], data["localidad"],
            data["latitud"], data["longitud"]
        )
        for data in elementos_procesados.values()
    ]
    
    contador_elementos_insertados = 0
    with conn.cursor() as cur:
        try:
            execute_values(
                cur,
                """
                INSERT INTO elementos (id_elemento, nombre, tipo, pendiente, categoria, dependencia, provincia, distrito, localidad, latitud, longitud)
                VALUES %s
                ON CONFLICT (id_elemento) DO UPDATE 
                SET nombre = EXCLUDED.nombre, tipo = EXCLUDED.tipo, pendiente = EXCLUDED.pendiente,
                    categoria = EXCLUDED.categoria, dependencia = EXCLUDED.dependencia, provincia = EXCLUDED.provincia,
                    distrito = EXCLUDED.distrito, localidad = EXCLUDED.localidad, latitud = EXCLUDED.latitud,
                    longitud = EXCLUDED.longitud
                """,
                elementos_list
            )
            conn.commit()
            contador_elementos_insertados = len(elementos_list)
        except Exception as e:
            print(f"  [Error] No se pudo insertar elementos en lote: {e}")
            conn.rollback()
            # Alternativa segura uno a uno en caso de error masivo
            for data in elementos_procesados.values():
                try:
                    cur.execute(
                        """
                        INSERT INTO elementos (id_elemento, nombre, tipo, pendiente, categoria, dependencia, provincia, distrito, localidad, latitud, longitud) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            data["id_elemento"], data["nombre"], data["tipo"],
                            data["pendiente"], data["categoria"], data["dependencia"],
                            data["provincia"], data["distrito"], data["localidad"],
                            data["latitud"], data["longitud"]
                        )
                    )
                    contador_elementos_insertados += 1
                except Exception:
                    pass
            conn.commit()
            
    print(f"Total elementos cargados/actualizados: {contador_elementos_insertados}")

    # --- PROCESAR ORDENES DE TRABAJO (OTs) ---
    print("\nProcesando e insertando OTs en Supabase...")
    ots_procesadas = {}
    
    for row in raw_ots:
        if not any(row.values()):
            continue
            
        ot = map_row_to_ot(row)
        id_ot = ot["id_ot"]
        id_elemento = ot["id_elemento"]
        prioridad = ot["prioridad"]
        diagnostico = ot["diagnostico_inicial"]
        
        if not id_ot or not id_elemento:
            continue

        if id_elemento not in elementos_procesados:
            coincidencias = [k for k in elementos_procesados.keys() if k.startswith(id_elemento)]
            if coincidencias:
                id_elemento = coincidencias[0]
            else:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO elementos (id_elemento, nombre, tipo) VALUES (%s, %s, 'Nodo') ON CONFLICT DO NOTHING",
                            (id_elemento, f"Nodo {id_elemento}")
                        )
                    conn.commit()
                    elementos_procesados[id_elemento] = True
                except Exception:
                    conn.rollback()
                    continue

        if prioridad not in ('Alta', 'Media', 'Baja'):
            prioridad = 'Media'
            
        hora_recepcion = parse_iso_datetime(ot.get("hora_recepcion")) or datetime.now()
        hora_despacho = parse_iso_datetime(ot.get("hora_despacho"))
        hora_llegada = parse_iso_datetime(ot.get("hora_llegada"))
        hora_cierre = parse_iso_datetime(ot.get("hora_cierre"))
        
        estado = ot.get("estado", "Abierta")
        if estado not in ('Abierta', 'Despachada', 'En Sitio', 'Cerrada'):
            if hora_cierre:
                estado = 'Cerrada'
            elif hora_llegada:
                estado = 'En Sitio'
            elif hora_despacho:
                estado = 'Despachada'
            else:
                estado = 'Abierta'
                
        if hora_despacho and hora_despacho < hora_recepcion:
            hora_despacho = hora_recepcion
        if hora_llegada and hora_despacho and hora_llegada < hora_despacho:
            hora_llegada = hora_despacho
        if hora_cierre and hora_llegada and hora_cierre < hora_llegada:
            hora_cierre = hora_llegada

        original_ot = id_ot
        sufijo = 1
        while id_ot in ots_procesadas:
            sufijo += 1
            id_ot = f"{original_ot}-{sufijo}"
            
        ots_procesadas[id_ot] = {
            "id_ot": id_ot,
            "id_elemento": id_elemento,
            "prioridad": prioridad,
            "diagnostico_inicial": diagnostico,
            "hora_recepcion": hora_recepcion,
            "hora_despacho": hora_despacho,
            "hora_llegada": hora_llegada,
            "hora_cierre": hora_cierre,
            "estado": estado
        }

    ots_list = [
        (
            data["id_ot"], data["id_elemento"], data["prioridad"], data["diagnostico_inicial"],
            data["hora_recepcion"], data["hora_despacho"], data["hora_llegada"], data["hora_cierre"], data["estado"]
        )
        for data in ots_procesadas.values()
    ]
    
    contador_ots_insertadas = 0
    with conn.cursor() as cur:
        try:
            execute_values(
                cur,
                """
                INSERT INTO ordenes_trabajo 
                (id_ot, id_elemento, prioridad, diagnostico_inicial, hora_recepcion, hora_despacho, hora_llegada, hora_cierre, estado)
                VALUES %s
                ON CONFLICT (id_ot) DO UPDATE 
                SET id_elemento = EXCLUDED.id_elemento, prioridad = EXCLUDED.prioridad, 
                    diagnostico_inicial = EXCLUDED.diagnostico_inicial, hora_recepcion = EXCLUDED.hora_recepcion,
                    hora_despacho = EXCLUDED.hora_despacho, hora_llegada = EXCLUDED.hora_llegada,
                    hora_cierre = EXCLUDED.hora_cierre, estado = EXCLUDED.estado
                """,
                ots_list
            )
            conn.commit()
            contador_ots_insertadas = len(ots_list)
        except Exception as e:
            print(f"  [Error] No se pudo insertar OTs en lote: {e}")
            conn.rollback()
            # Alternativa segura uno a uno
            for data in ots_procesadas.values():
                try:
                    cur.execute(
                        """
                        INSERT INTO ordenes_trabajo 
                        (id_ot, id_elemento, prioridad, diagnostico_inicial, hora_recepcion, hora_despacho, hora_llegada, hora_cierre, estado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (data["id_ot"], data["id_elemento"], data["prioridad"], data["diagnostico_inicial"],
                         data["hora_recepcion"], data["hora_despacho"], data["hora_llegada"], data["hora_cierre"], data["estado"])
                    )
                    contador_ots_insertadas += 1
                except Exception:
                    pass
            conn.commit()
        
    conn.close()
    print(f"Total OTs cargadas/actualizadas: {contador_ots_insertadas}")
    print("\n[ÉXITO] Migración de elementos y OTs completada.")
    
    # Migrar personal
    migrar_personal()
    print("\n[ÉXITO] Migración completa desde Google Sheets a Supabase.")


def migrar_personal():
    """Migra el personal desde la hoja 'Personal' de Google Sheets a Supabase."""
    print("\n--- Migrando Personal ---")
    conn = test_and_get_db_connection()
    
    try:
        registros = sheets_service._obtener_datos_hoja("Personal")
    except Exception as e:
        print(f"  [ADVERTENCIA] No se pudo leer la hoja 'Personal': {e}")
        conn.close()
        return

    if not registros:
        print("  [INFO] No se encontraron registros en la hoja 'Personal'. Omitiendo.")
        conn.close()
        return

    # Normalizar claves de las columnas
    def norm(key): return key.strip().lower().replace(' ', '_')

    emails_vistos = {}  # Para detectar duplicados
    datos_personal = []
    
    for row in registros:
        row_norm = {norm(k): v for k, v in row.items()}
        
        nombre = str(row_norm.get('nombre', '') or '').strip()
        if not nombre:
            continue  # Omitir filas sin nombre
        
        cargo = str(row_norm.get('cargo', '') or '').strip() or None
        cm = str(row_norm.get('cm', '') or '').strip() or None
        estado_raw = str(row_norm.get('estado', '') or '').strip()
        estado = estado_raw if estado_raw in ('Activo', 'Inactivo') else 'Activo'
        
        # Generar email y contraseña inicial basados en nombre real
        email_base = generate_email_from_name(nombre)
        
        # Manejar emails duplicados añadiendo número
        if email_base in emails_vistos:
            emails_vistos[email_base] += 1
            local, domain = email_base.split('@')
            email = f"{local}{emails_vistos[email_base]}@{domain}"
        else:
            emails_vistos[email_base] = 1
            email = email_base
        
        password_plain = generate_password_from_name(nombre)
        password_hash = hash_password(password_plain)
        
        datos_personal.append((nombre, cargo, cm, estado, email, password_hash))
        print(f"  + {nombre} -> {email} | contraseña inicial: {password_plain}")
    
    if not datos_personal:
        print("  [INFO] No hay personal válido para migrar.")
        conn.close()
        return
    
    with conn.cursor() as cur:
        try:
            execute_values(
                cur,
                """
                INSERT INTO personal (nombre, cargo, cm, estado, email, password_hash)
                VALUES %s
                ON CONFLICT (email) DO UPDATE 
                SET nombre = EXCLUDED.nombre, cargo = EXCLUDED.cargo,
                    cm = EXCLUDED.cm, estado = EXCLUDED.estado,
                    updated_at = CURRENT_TIMESTAMP
                """,
                datos_personal
            )
            conn.commit()
            print(f"  [OK] {len(datos_personal)} miembros del personal migrados/actualizados.")
        except Exception as e:
            print(f"  [Error] No se pudo migrar personal: {e}")
            conn.rollback()
    
    conn.close()


if __name__ == "__main__":
    migrar_datos()
