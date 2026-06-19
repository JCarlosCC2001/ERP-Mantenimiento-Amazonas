import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Cargar dotenv para desarrollo local
from dotenv import load_dotenv
load_dotenv()

class SupabaseOTManager:
    def __init__(self, connection_uri: Optional[str] = None):
        self.uri = connection_uri or os.environ.get("DATABASE_URL")
        if not self.uri:
            raise ValueError("No se especificó un DATABASE_URL ni se encontró en las variables de entorno.")
        # Reemplazar opcionalmente postgres:// por postgresql:// que requiere psycopg2
        if self.uri.startswith("postgres://"):
            self.uri = self.uri.replace("postgres://", "postgresql://", 1)
        self._initialize_db()

    @contextmanager
    def _get_connection(self):
        conn = psycopg2.connect(self.uri, cursor_factory=RealDictCursor)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _initialize_db(self):
        """Inicializa la base de datos en Supabase (PostgreSQL) si las tablas no existen."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Crear tabla elementos
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS elementos (
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
                # Crear tabla personal con buenas prácticas de seguridad
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
                # Índice para búsqueda rápida por email (auth)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_personal_email ON personal(email);")
                
                # Crear tabla cuadrillas
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cuadrillas (
                        id_cuadrilla SERIAL PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL UNIQUE,
                        id_lider INTEGER REFERENCES personal(id_personal) ON DELETE SET NULL,
                        estado VARCHAR(50) CHECK(estado IN ('Disponible', 'En Ruta', 'En Sitio', 'Fuera de Servicio')) DEFAULT 'Disponible',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Crear tabla ordenes_trabajo
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ordenes_trabajo (
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
                
                # Migración incremental para agregar columnas si no existen
                try:
                    cur.execute("ALTER TABLE ordenes_trabajo ADD COLUMN id_cuadrilla INTEGER REFERENCES cuadrillas(id_cuadrilla) ON DELETE SET NULL;")
                    conn.commit()
                except psycopg2.DatabaseError:
                    conn.rollback()
                try:
                    cur.execute("ALTER TABLE ordenes_trabajo ADD COLUMN fecha_planificacion VARCHAR(100);")
                    conn.commit()
                except psycopg2.DatabaseError:
                    conn.rollback()

                # Crear tabla historial_gps
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS historial_gps (
                        id_posicion SERIAL PRIMARY KEY,
                        id_cuadrilla INTEGER NOT NULL REFERENCES cuadrillas(id_cuadrilla) ON DELETE CASCADE,
                        latitud VARCHAR(100) NOT NULL,
                        longitud VARCHAR(100) NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # Crear tabla evidencias_ot
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS evidencias_ot (
                        id_evidencia SERIAL PRIMARY KEY,
                        id_ot VARCHAR(100) NOT NULL REFERENCES ordenes_trabajo(id_ot) ON DELETE CASCADE,
                        tipo_evidencia VARCHAR(50) CHECK(tipo_evidencia IN ('Desplazamiento', 'Antes', 'Despues')) NOT NULL,
                        url_foto TEXT NOT NULL,
                        latitud_foto VARCHAR(100),
                        longitud_foto VARCHAR(100),
                        timestamp_captura TIMESTAMP NOT NULL,
                        estado_validacion VARCHAR(50) CHECK(estado_validacion IN ('Pendiente', 'Aprobado', 'Rechazado')) DEFAULT 'Pendiente',
                        motivo_rechazo TEXT,
                        usuario_validador_id INTEGER REFERENCES personal(id_personal) ON DELETE SET NULL,
                        fecha_validacion TIMESTAMP
                    );
                """)
                # Crear tabla cfms
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cfms (
                        id SERIAL PRIMARY KEY,
                        item VARCHAR(100),
                        ot VARCHAR(100),
                        tipo VARCHAR(100),
                        codigo VARCHAR(100),
                        selnet VARCHAR(100),
                        gilat VARCHAR(100),
                        factor VARCHAR(100),
                        inicio VARCHAR(100),
                        fin VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            conn.commit()

    # --- CRUD DE ELEMENTOS ---

    def registrar_elemento(self, id_elemento: str, nombre: str, tipo: str, 
                           pendiente: Optional[str] = None, categoria: Optional[str] = None,
                           dependencia: Optional[str] = None, provincia: Optional[str] = None,
                           distrito: Optional[str] = None, localidad: Optional[str] = None,
                           latitud: Optional[str] = None, longitud: Optional[str] = None) -> bool:
        if tipo not in ('Nodo', 'IAO', 'Hotspot'):
            raise ValueError("El tipo de elemento debe ser 'Nodo', 'IAO' o 'Hotspot'.")
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO elementos (id_elemento, nombre, tipo, pendiente, categoria, dependencia, provincia, distrito, localidad, latitud, longitud) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            id_elemento.strip(), nombre.strip(), tipo,
                            pendiente.strip() if pendiente else None,
                            categoria.strip() if categoria else None,
                            dependencia.strip() if dependencia else None,
                            provincia.strip() if provincia else None,
                            distrito.strip() if distrito else None,
                            localidad.strip() if localidad else None,
                            latitud.strip() if latitud else None,
                            longitud.strip() if longitud else None
                        )
                    )
                    conn.commit()
                    return True
                except psycopg2.IntegrityError as e:
                    raise ValueError(f"No se pudo registrar el elemento {id_elemento}: {e}")

    def obtener_elemento(self, id_elemento: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM elementos WHERE id_elemento = %s", (id_elemento.strip(),))
                row = cur.fetchone()
                return dict(row) if row else None

    def listar_elementos(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM elementos")
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def eliminar_elemento(self, id_elemento: str) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("DELETE FROM elementos WHERE id_elemento = %s", (id_elemento.strip(),))
                    conn.commit()
                    return cur.rowcount > 0
                except psycopg2.IntegrityError as e:
                    raise ValueError(f"No se puede eliminar el elemento {id_elemento} porque tiene registros relacionados: {e}")

    # --- GESTIÓN DE OTs ---

    def crear_ot(self, id_ot: str, id_elemento: str, prioridad: str, diagnostico_inicial: str, 
                  hora_recepcion: Optional[datetime] = None) -> bool:
        if prioridad not in ('Alta', 'Media', 'Baja'):
            raise ValueError("La prioridad debe ser 'Alta', 'Media' o 'Baja'.")
        
        if not hora_recepcion:
            hora_recepcion = datetime.now()

        elemento = self.obtener_elemento(id_elemento)
        if not elemento:
            raise ValueError(f"El elemento con ID '{id_elemento}' no existe en el catálogo.")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO ordenes_trabajo 
                        (id_ot, id_elemento, prioridad, diagnostico_inicial, hora_recepcion, estado) 
                        VALUES (%s, %s, %s, %s, %s, 'Abierta')
                        """,
                        (id_ot.strip(), id_elemento.strip(), prioridad, diagnostico_inicial.strip(), hora_recepcion)
                    )
                    conn.commit()
                    return True
                except psycopg2.IntegrityError as e:
                    raise ValueError(f"No se pudo crear la OT {id_ot}: {e}")

    def obtener_ot(self, id_ot: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM ordenes_trabajo WHERE id_ot = %s", (id_ot.strip(),))
                row = cur.fetchone()
                return dict(row) if row else None

    def listar_ots(self, estado: Optional[str] = None, id_cuadrilla: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM ordenes_trabajo WHERE 1=1"
        params = []
        if estado:
            query += " AND estado = %s"
            params.append(estado)
        if id_cuadrilla is not None:
            query += " AND id_cuadrilla = %s"
            params.append(id_cuadrilla)
            
        query += " ORDER BY hora_recepcion ASC"
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def despachar_cuadrilla(self, id_ot: str, hora_despacho: Optional[datetime] = None) -> bool:
        if not hora_despacho:
            hora_despacho = datetime.now()

        ot = self.obtener_ot(id_ot)
        if not ot:
            raise ValueError(f"La OT {id_ot} no existe.")
        
        if ot['estado'] != 'Abierta':
            raise ValueError(f"Transición inválida: La OT está en estado '{ot['estado']}' y debe estar en 'Abierta' para despachar.")

        # psycopg2/Postgres devuelven objetos datetime reales (con o sin zona horaria)
        # por lo que no es necesario parsear de string como en SQLite
        hora_recepcion = ot['hora_recepcion']
        if isinstance(hora_recepcion, str):
            hora_recepcion = datetime.fromisoformat(hora_recepcion)
        if hora_despacho.replace(tzinfo=None) < hora_recepcion.replace(tzinfo=None):
            raise ValueError("La hora de despacho no puede ser anterior a la hora de recepción.")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ordenes_trabajo SET estado = 'Despachada', hora_despacho = %s WHERE id_ot = %s",
                    (hora_despacho, id_ot.strip())
                )
                conn.commit()
                return True

    def registrar_llegada_sitio(self, id_ot: str, hora_llegada: Optional[datetime] = None) -> bool:
        if not hora_llegada:
            hora_llegada = datetime.now()

        ot = self.obtener_ot(id_ot)
        if not ot:
            raise ValueError(f"La OT {id_ot} no existe.")
        
        if ot['estado'] != 'Despachada':
            raise ValueError(f"Transición inválida: La OT está en estado '{ot['estado']}' y debe estar en 'Despachada' para registrar llegada.")

        hora_despacho = ot['hora_despacho']
        if isinstance(hora_despacho, str):
            hora_despacho = datetime.fromisoformat(hora_despacho)
        if hora_llegada.replace(tzinfo=None) < hora_despacho.replace(tzinfo=None):
            raise ValueError("La hora de llegada no puede ser anterior a la hora de despacho.")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ordenes_trabajo SET estado = 'En Sitio', hora_llegada = %s WHERE id_ot = %s",
                    (hora_llegada, id_ot.strip())
                )
                conn.commit()
                return True

    def cerrar_ot(self, id_ot: str, hora_cierre: Optional[datetime] = None) -> bool:
        if not hora_cierre:
            hora_cierre = datetime.now()

        ot = self.obtener_ot(id_ot)
        if not ot:
            raise ValueError(f"La OT {id_ot} no existe.")
        
        if ot['estado'] != 'En Sitio':
            raise ValueError(f"Transición inválida: La OT está en estado '{ot['estado']}' y debe estar en 'En Sitio' para cerrar.")

        hora_llegada = ot['hora_llegada']
        if isinstance(hora_llegada, str):
            hora_llegada = datetime.fromisoformat(hora_llegada)
        if hora_cierre.replace(tzinfo=None) < hora_llegada.replace(tzinfo=None):
            raise ValueError("La hora de cierre no puede ser anterior a la hora de llegada.")

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ordenes_trabajo SET estado = 'Cerrada', hora_cierre = %s WHERE id_ot = %s",
                    (hora_cierre, id_ot.strip())
                )
                conn.commit()
                return True

    # --- GESTIÓN DE PERSONAL ---

    def registrar_personal(self, nombre: str, cargo: Optional[str], cm: Optional[str],
                           estado: str, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """Registra un nuevo miembro del personal con la contraseña ya hasheada."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO personal (nombre, cargo, cm, estado, email, password_hash)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id_personal, nombre, cargo, cm, estado, email
                        """,
                        (nombre.strip(), cargo, cm, estado, email.lower().strip(), password_hash)
                    )
                    row = cur.fetchone()
                    conn.commit()
                    return dict(row) if row else None
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    raise ValueError(f"No se pudo registrar al personal '{nombre}': {e}")

    def listar_personal(self) -> List[Dict[str, Any]]:
        """Lista todo el personal. NO expone el password_hash."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_personal, nombre, cargo, cm, estado, email FROM personal ORDER BY nombre ASC"
                )
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def obtener_personal(self, id_personal: int) -> Optional[Dict[str, Any]]:
        """Obtiene datos públicos de un miembro del personal por ID. NO expone el password_hash."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_personal, nombre, cargo, cm, estado, email FROM personal WHERE id_personal = %s",
                    (id_personal,)
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def obtener_personal_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos COMPLETOS (incluyendo password_hash) de un miembro por email para autenticación."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_personal, nombre, cargo, cm, estado, email, password_hash FROM personal WHERE LOWER(email) = LOWER(%s)",
                    (email.strip(),)
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def actualizar_personal(self, id_personal: int, datos: Dict[str, Any]) -> bool:
        """Actualiza campos del personal. Si se incluye 'password', se hashea automáticamente."""
        from security import hash_password
        
        # Si se envió una nueva contraseña en texto plano, hashearla antes de guardar
        if "password" in datos:
            datos["password_hash"] = hash_password(datos.pop("password"))
        
        # No permitir actualizar campos de auditoría desde afuera
        datos.pop("id_personal", None)
        datos.pop("created_at", None)
        datos["updated_at"] = datetime.now()

        if not datos:
            return False

        set_clause = ", ".join(f"{k} = %s" for k in datos.keys())
        values = list(datos.values()) + [id_personal]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE personal SET {set_clause} WHERE id_personal = %s",
                    values
                )
                conn.commit()
                return cur.rowcount > 0

    # --- GESTIÓN DE CUADRILLAS ---

    def registrar_cuadrilla(self, nombre: str, id_lider: Optional[int]) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        "INSERT INTO cuadrillas (nombre, id_lider) VALUES (%s, %s) RETURNING id_cuadrilla",
                        (nombre.strip(), id_lider)
                    )
                    row = cur.fetchone()
                    conn.commit()
                    return self.obtener_cuadrilla(row["id_cuadrilla"]) if row else None
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    raise ValueError(f"No se pudo registrar la cuadrilla '{nombre}': {e}")

    def listar_cuadrillas(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.id_cuadrilla, c.nombre, c.id_lider, c.estado, c.created_at, p.nombre as nombre_lider 
                    FROM cuadrillas c 
                    LEFT JOIN personal p ON c.id_lider = p.id_personal 
                    ORDER BY c.nombre ASC
                    """
                )
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def obtener_cuadrilla(self, id_cuadrilla: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.id_cuadrilla, c.nombre, c.id_lider, c.estado, c.created_at, p.nombre as nombre_lider 
                    FROM cuadrillas c 
                    LEFT JOIN personal p ON c.id_lider = p.id_personal 
                    WHERE c.id_cuadrilla = %s
                    """,
                    (id_cuadrilla,)
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def asignar_ot(self, id_ot: str, id_cuadrilla: Optional[int], fecha_planificacion: Optional[str]) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ordenes_trabajo SET id_cuadrilla = %s, fecha_planificacion = %s WHERE id_ot = %s",
                    (id_cuadrilla, fecha_planificacion, id_ot.strip())
                )
                conn.commit()
                return cur.rowcount > 0

    # --- SEGUIMIENTO GPS ---

    def registrar_gps(self, id_cuadrilla: int, latitud: str, longitud: str) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        "INSERT INTO historial_gps (id_cuadrilla, latitud, longitud) VALUES (%s, %s, %s)",
                        (id_cuadrilla, latitud.strip(), longitud.strip())
                    )
                    cur.execute(
                        "UPDATE cuadrillas SET estado = 'En Ruta' WHERE id_cuadrilla = %s AND estado = 'Disponible'",
                        (id_cuadrilla,)
                    )
                    conn.commit()
                    return True
                except psycopg2.IntegrityError:
                    conn.rollback()
                    return False

    def obtener_ultimo_gps(self, id_cuadrilla: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM historial_gps WHERE id_cuadrilla = %s ORDER BY timestamp DESC LIMIT 1",
                    (id_cuadrilla,)
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def listar_historial_gps(self, id_cuadrilla: int, limite: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM historial_gps WHERE id_cuadrilla = %s ORDER BY timestamp DESC LIMIT %s",
                    (id_cuadrilla, limite)
                )
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    # --- GESTIÓN DE EVIDENCIAS FOTOGRÁFICAS ---

    def subir_evidencia(self, id_ot: str, tipo_evidencia: str, url_foto: str,
                        latitud_foto: Optional[str], longitud_foto: Optional[str],
                        timestamp_captura: datetime) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO evidencias_ot (id_ot, tipo_evidencia, url_foto, latitud_foto, longitud_foto, timestamp_captura)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_evidencia
                        """,
                        (id_ot.strip(), tipo_evidencia, url_foto, latitud_foto, longitud_foto, timestamp_captura)
                    )
                    row = cur.fetchone()
                    conn.commit()
                    return self.obtener_evidencia(row["id_evidencia"]) if row else None
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    raise ValueError(f"No se pudo registrar la evidencia para la OT {id_ot}: {e}")

    def obtener_evidencia(self, id_evidencia: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM evidencias_ot WHERE id_evidencia = %s",
                    (id_evidencia,)
                )
                row = cur.fetchone()
                return dict(row) if row else None

    def listar_evidencias_ot(self, id_ot: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM evidencias_ot WHERE id_ot = %s ORDER BY timestamp_captura ASC",
                    (id_ot.strip(),)
                )
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def validar_evidencia(self, id_evidencia: int, estado_validacion: str, motivo_rechazo: Optional[str],
                          usuario_validador_id: Optional[int]) -> bool:
        if estado_validacion not in ('Aprobado', 'Rechazado'):
            raise ValueError("El estado de validación debe ser 'Aprobado' o 'Rechazado'.")
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE evidencias_ot 
                    SET estado_validacion = %s, motivo_rechazo = %s, usuario_validador_id = %s, fecha_validacion = NOW()
                    WHERE id_evidencia = %s
                    """,
                    (estado_validacion, motivo_rechazo, usuario_validador_id, id_evidencia)
                )
                conn.commit()
                return cur.rowcount > 0

    # --- GESTIÓN DE CFMs ---
    
    def listar_cfms(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM cfms ORDER BY id ASC")
                rows = cur.fetchall()
                return [dict(row) for row in rows]

    def registrar_cfm(self, item: str, ot: str, tipo: str, codigo: str, selnet: str, gilat: str, factor: str, inicio: str, fin: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO cfms (item, ot, tipo, codigo, selnet, gilat, factor, inicio, fin)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                        """,
                        (item, ot, tipo, codigo, selnet, gilat, factor, inicio, fin)
                    )
                    row = cur.fetchone()
                    conn.commit()
                    return dict(row) if row else None
                except psycopg2.IntegrityError as e:
                    conn.rollback()
                    raise ValueError(f"No se pudo registrar la CFM: {e}")

    def vaciar_cfms(self) -> bool:
        """Elimina todas las CFMs de la base de datos para una recarga limpia."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE cfms RESTART IDENTITY;")
                conn.commit()
                return True
