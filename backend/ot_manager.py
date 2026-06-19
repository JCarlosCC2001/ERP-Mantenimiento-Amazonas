import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Rutas dinámicas relativas a este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "mantenimiento_amazonas.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "db_schema.sql")

class OTManager:
    def __init__(self, db_path: Optional[str] = None, schema_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("AMAZONAS_DB_PATH") or DB_FILE
        self.schema_path = schema_path or SCHEMA_FILE
        self._initialize_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Rutas dinámicas relativas a este archivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "mantenimiento_amazonas.db")
SCHEMA_FILE = os.path.join(BASE_DIR, "db_schema.sql")

class OTManager:
    def __init__(self, db_path: Optional[str] = None, schema_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("AMAZONAS_DB_PATH") or DB_FILE
        self.schema_path = schema_path or SCHEMA_FILE
        self._initialize_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Habilitar soporte para llaves foráneas explicitamente por conexión
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _initialize_db(self):
        """Inicializa la base de datos usando el esquema SQL provisto y aplica migraciones incrementales."""
        if os.path.exists(self.schema_path):
            with open(self.schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            with self._get_connection() as conn:
                conn.executescript(schema_sql)
        
        # Migraciones incrementales para base de datos SQLite existente
        with self._get_connection() as conn:
            # 1. Crear tabla personal si no existe (por si db_schema no la creó)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS personal (
                    id_personal INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    cargo TEXT,
                    cm TEXT,
                    estado TEXT CHECK(estado IN ('Activo', 'Inactivo')) DEFAULT 'Activo',
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # 2. Crear tabla cuadrillas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cuadrillas (
                    id_cuadrilla INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    id_lider INTEGER REFERENCES personal(id_personal) ON DELETE SET NULL,
                    estado TEXT CHECK(estado IN ('Disponible', 'En Ruta', 'En Sitio', 'Fuera de Servicio')) DEFAULT 'Disponible',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # 3. Agregar id_cuadrilla a ordenes_trabajo
            try:
                conn.execute("ALTER TABLE ordenes_trabajo ADD COLUMN id_cuadrilla INTEGER REFERENCES cuadrillas(id_cuadrilla) ON DELETE SET NULL;")
            except sqlite3.OperationalError:
                pass  # Columna ya existe
            # 4. Agregar fecha_planificacion a ordenes_trabajo
            try:
                conn.execute("ALTER TABLE ordenes_trabajo ADD COLUMN fecha_planificacion TEXT;")
            except sqlite3.OperationalError:
                pass  # Columna ya existe
            # 5. Crear tabla historial_gps
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historial_gps (
                    id_posicion INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cuadrilla INTEGER NOT NULL REFERENCES cuadrillas(id_cuadrilla) ON DELETE CASCADE,
                    latitud TEXT NOT NULL,
                    longitud TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # 6. Crear tabla evidencias_ot
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidencias_ot (
                    id_evidencia INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_ot TEXT NOT NULL REFERENCES ordenes_trabajo(id_ot) ON DELETE CASCADE,
                    tipo_evidencia TEXT CHECK(tipo_evidencia IN ('Desplazamiento', 'Antes', 'Despues')) NOT NULL,
                    url_foto TEXT NOT NULL,
                    latitud_foto TEXT,
                    longitud_foto TEXT,
                    timestamp_captura DATETIME NOT NULL,
                    estado_validacion TEXT CHECK(estado_validacion IN ('Pendiente', 'Aprobado', 'Rechazado')) DEFAULT 'Pendiente',
                    motivo_rechazo TEXT,
                    usuario_validador_id INTEGER REFERENCES personal(id_personal) ON DELETE SET NULL,
                    fecha_validacion DATETIME
                );
            """)
            # 7. Crear tabla cfms
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cfms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT,
                    ot TEXT,
                    tipo TEXT,
                    codigo TEXT,
                    selnet TEXT,
                    gilat TEXT,
                    factor TEXT,
                    inicio TEXT,
                    fin TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    # --- CRUD DE ELEMENTOS ---

    def registrar_elemento(self, id_elemento: str, nombre: str, tipo: str, 
                           pendiente: Optional[str] = None, categoria: Optional[str] = None,
                           dependencia: Optional[str] = None, provincia: Optional[str] = None,
                           distrito: Optional[str] = None, localidad: Optional[str] = None,
                           latitud: Optional[str] = None, longitud: Optional[str] = None) -> bool:
        """Registra un nuevo elemento en el sistema SQLite."""
        if tipo not in ('Nodo', 'IAO', 'Hotspot'):
            raise ValueError("El tipo de elemento debe ser 'Nodo', 'IAO' o 'Hotspot'.")
        
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO elementos (id_elemento, nombre, tipo, pendiente, categoria, dependencia, provincia, distrito, localidad, latitud, longitud) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se pudo registrar el elemento {id_elemento}: {e}")

    def obtener_elemento(self, id_elemento: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información de un elemento por su ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM elementos WHERE id_elemento = ?", (id_elemento.strip(),)).fetchone()
            return dict(row) if row else None

    def listar_elementos(self) -> List[Dict[str, Any]]:
        """Lista todos los elementos registrados."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM elementos").fetchall()
            return [dict(row) for row in rows]

    def eliminar_elemento(self, id_elemento: str) -> bool:
        """Elimina un elemento si no tiene OTs asociadas."""
        with self._get_connection() as conn:
            try:
                cursor = conn.execute("DELETE FROM elementos WHERE id_elemento = ?", (id_elemento.strip(),))
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se puede eliminar el elemento {id_elemento} porque tiene registros relacionados: {e}")

    # --- GESTIÓN DE ÓRDENES DE TRABAJO (OTs) ---

    def _parse_datetime(self, val: Any) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
                try:
                    return datetime.strptime(val, fmt)
                except ValueError:
                    continue
        return None

    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None

    def crear_ot(self, id_ot: str, id_elemento: str, prioridad: str, diagnostico_inicial: str, 
                 hora_recepcion: Optional[datetime] = None) -> bool:
        """Crea una nueva orden de trabajo en estado 'Abierta'."""
        if prioridad not in ('Alta', 'Media', 'Baja'):
            raise ValueError("La prioridad debe ser 'Alta', 'Media' o 'Baja'.")
        
        if not hora_recepcion:
            hora_recepcion = datetime.now()

        # Validar existencia del elemento
        elemento = self.obtener_elemento(id_elemento)
        if not elemento:
            raise ValueError(f"El elemento con ID '{id_elemento}' no existe en el catálogo.")

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO ordenes_trabajo 
                    (id_ot, id_elemento, prioridad, diagnostico_inicial, hora_recepcion, estado) 
                    VALUES (?, ?, ?, ?, ?, 'Abierta')
                    """,
                    (id_ot.strip(), id_elemento.strip(), prioridad, diagnostico_inicial.strip(), self._format_datetime(hora_recepcion))
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se pudo crear la OT {id_ot}: {e}")

    def obtener_ot(self, id_ot: str) -> Optional[Dict[str, Any]]:
        """Obtiene la información de una OT por su ID, convirtiendo marcas de tiempo a datetime."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM ordenes_trabajo WHERE id_ot = ?", (id_ot.strip(),)).fetchone()
            if not row:
                return None
            ot = dict(row)
            ot['hora_recepcion'] = self._parse_datetime(ot['hora_recepcion'])
            ot['hora_despacho'] = self._parse_datetime(ot['hora_despacho'])
            ot['hora_llegada'] = self._parse_datetime(ot['hora_llegada'])
            ot['hora_cierre'] = self._parse_datetime(ot['hora_cierre'])
            return ot

    def listar_ots(self, estado: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todas las OTs, opcionalmente filtrando por estado."""
        query = "SELECT * FROM ordenes_trabajo"
        params = []
        if estado:
            query += " WHERE estado = ?"
            params.append(estado)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            ots = []
            for row in rows:
                ot = dict(row)
                ot['hora_recepcion'] = self._parse_datetime(ot['hora_recepcion'])
                ot['hora_despacho'] = self._parse_datetime(ot['hora_despacho'])
                ot['hora_llegada'] = self._parse_datetime(ot['hora_llegada'])
                ot['hora_cierre'] = self._parse_datetime(ot['hora_cierre'])
                ots.append(ot)
            return ots

    def despachar_cuadrilla(self, id_ot: str, hora_despacho: Optional[datetime] = None) -> bool:
        """Pasa la OT a estado 'Despachada' y registra la hora de despacho."""
        if not hora_despacho:
            hora_despacho = datetime.now()

        ot = self.obtener_ot(id_ot)
        if not ot:
            raise ValueError(f"La OT {id_ot} no existe.")
        
        if ot['estado'] != 'Abierta':
            raise ValueError(f"Transición inválida: La OT está en estado '{ot['estado']}' y debe estar en 'Abierta' para despachar.")

        if hora_despacho < ot['hora_recepcion']:
            raise ValueError("La hora de despacho no puede ser anterior a la hora de recepción.")

        with self._get_connection() as conn:
            conn.execute(
                "UPDATE ordenes_trabajo SET estado = 'Despachada', hora_despacho = ? WHERE id_ot = ?",
                (self._format_datetime(hora_despacho), id_ot.strip())
            )
            conn.commit()
            return True

    def registrar_llegada_sitio(self, id_ot: str, hora_llegada: Optional[datetime] = None) -> bool:
        """Pasa la OT a estado 'En Sitio' y registra la hora de llegada."""
        if not hora_llegada:
            hora_llegada = datetime.now()

        ot = self.obtener_ot(id_ot)
        if not ot:
            raise ValueError(f"La OT {id_ot} no existe.")
        
        if ot['estado'] != 'Despachada':
            raise ValueError(f"Transición inválida: La OT está en estado '{ot['estado']}' y debe estar en 'Despachada' para registrar llegada.")

        if hora_llegada < ot['hora_despacho']:
            raise ValueError("La hora de llegada no puede ser anterior a la hora de despacho.")

        with self._get_connection() as conn:
            conn.execute(
                "UPDATE ordenes_trabajo SET estado = 'En Sitio', hora_llegada = ? WHERE id_ot = ?",
                (self._format_datetime(hora_llegada), id_ot.strip())
            )
            conn.commit()
            return True

    def cerrar_ot(self, id_ot: str, hora_cierre: Optional[datetime] = None) -> bool:
        """Pasa la OT a estado 'Cerrada' y registra la hora de cierre."""
        if not hora_cierre:
            hora_cierre = datetime.now()

        ot = self.obtener_ot(id_ot)
        if not ot:
            raise ValueError(f"La OT {id_ot} no existe.")
        
        if ot['estado'] != 'En Sitio':
            raise ValueError(f"Transición inválida: La OT está en estado '{ot['estado']}' y debe estar en 'En Sitio' para cerrar.")

        if hora_cierre < ot['hora_llegada']:
            raise ValueError("La hora de cierre no puede ser anterior a la hora de llegada.")

        with self._get_connection() as conn:
            conn.execute(
                "UPDATE ordenes_trabajo SET estado = 'Cerrada', hora_cierre = ? WHERE id_ot = ?",
                (self._format_datetime(hora_cierre), id_ot.strip())
            )
            conn.commit()
            return True

    # --- GESTIÓN DE PERSONAL ---

    def registrar_personal(self, nombre: str, cargo: Optional[str], cm: Optional[str],
                           estado: str, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """Registra un nuevo miembro del personal."""
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO personal (nombre, cargo, cm, estado, email, password_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (nombre.strip(), cargo, cm, estado, email.lower().strip(), password_hash)
                )
                conn.commit()
                id_pers = cursor.lastrowid
                return self.obtener_personal(id_pers)
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se pudo registrar al personal '{nombre}': {e}")

    def listar_personal(self) -> List[Dict[str, Any]]:
        """Lista todo el personal."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id_personal, nombre, cargo, cm, estado, email FROM personal ORDER BY nombre ASC"
            ).fetchall()
            return [dict(row) for row in rows]

    def obtener_personal(self, id_personal: int) -> Optional[Dict[str, Any]]:
        """Obtiene datos de un miembro del personal por ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id_personal, nombre, cargo, cm, estado, email FROM personal WHERE id_personal = ?",
                (id_personal,)
            ).fetchone()
            return dict(row) if row else None

    def obtener_personal_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos completos de un miembro por email."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id_personal, nombre, cargo, cm, estado, email, password_hash FROM personal WHERE LOWER(email) = LOWER(?)",
                (email.strip(),)
            ).fetchone()
            return dict(row) if row else None

    def actualizar_personal(self, id_personal: int, datos: Dict[str, Any]) -> bool:
        """Actualiza campos del personal."""
        from security import hash_password
        if "password" in datos:
            datos["password_hash"] = hash_password(datos.pop("password"))
        
        datos.pop("id_personal", None)
        datos["updated_at"] = self._format_datetime(datetime.now())

        if not datos:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in datos.keys())
        values = list(datos.values()) + [id_personal]

        with self._get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE personal SET {set_clause} WHERE id_personal = ?",
                values
            )
            conn.commit()
            return cursor.rowcount > 0

    # --- GESTIÓN DE CUADRILLAS ---

    def registrar_cuadrilla(self, nombre: str, id_lider: Optional[int]) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO cuadrillas (nombre, id_lider) VALUES (?, ?)",
                    (nombre.strip(), id_lider)
                )
                conn.commit()
                return self.obtener_cuadrilla(cursor.lastrowid)
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se pudo registrar la cuadrilla '{nombre}': {e}")

    def listar_cuadrillas(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT c.id_cuadrilla, c.nombre, c.id_lider, c.estado, c.created_at, p.nombre as nombre_lider 
                FROM cuadrillas c 
                LEFT JOIN personal p ON c.id_lider = p.id_personal 
                ORDER BY c.nombre ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def obtener_cuadrilla(self, id_cuadrilla: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT c.id_cuadrilla, c.nombre, c.id_lider, c.estado, c.created_at, p.nombre as nombre_lider 
                FROM cuadrillas c 
                LEFT JOIN personal p ON c.id_lider = p.id_personal 
                WHERE c.id_cuadrilla = ?
                """,
                (id_cuadrilla,)
            ).fetchone()
            return dict(row) if row else None

    def asignar_ot(self, id_ot: str, id_cuadrilla: Optional[int], fecha_planificacion: Optional[str]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE ordenes_trabajo SET id_cuadrilla = ?, fecha_planificacion = ? WHERE id_ot = ?",
                (id_cuadrilla, fecha_planificacion, id_ot.strip())
            )
            conn.commit()
            return cursor.rowcount > 0

    # --- SEGUIMIENTO GPS ---

    def registrar_gps(self, id_cuadrilla: int, latitud: str, longitud: str) -> bool:
        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO historial_gps (id_cuadrilla, latitud, longitud) VALUES (?, ?, ?)",
                    (id_cuadrilla, latitud.strip(), longitud.strip())
                )
                conn.execute(
                    "UPDATE cuadrillas SET estado = 'En Ruta' WHERE id_cuadrilla = ? AND estado = 'Disponible'",
                    (id_cuadrilla,)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def obtener_ultimo_gps(self, id_cuadrilla: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM historial_gps WHERE id_cuadrilla = ? ORDER BY timestamp DESC LIMIT 1",
                (id_cuadrilla,)
            ).fetchone()
            return dict(row) if row else None

    def listar_historial_gps(self, id_cuadrilla: int, limite: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM historial_gps WHERE id_cuadrilla = ? ORDER BY timestamp DESC LIMIT ?",
                (id_cuadrilla, limite)
            ).fetchall()
            return [dict(row) for row in rows]

    # --- GESTIÓN DE EVIDENCIAS FOTOGRÁFICAS ---

    def subir_evidencia(self, id_ot: str, tipo_evidencia: str, url_foto: str,
                        latitud_foto: Optional[str], longitud_foto: Optional[str],
                        timestamp_captura: datetime) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO evidencias_ot (id_ot, tipo_evidencia, url_foto, latitud_foto, longitud_foto, timestamp_captura)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (id_ot.strip(), tipo_evidencia, url_foto, latitud_foto, longitud_foto, self._format_datetime(timestamp_captura))
                )
                conn.commit()
                return self.obtener_evidencia(cursor.lastrowid)
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se pudo registrar la evidencia para la OT {id_ot}: {e}")

    def obtener_evidencia(self, id_evidencia: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM evidencias_ot WHERE id_evidencia = ?",
                (id_evidencia,)
            ).fetchone()
            return dict(row) if row else None

    def listar_evidencias_ot(self, id_ot: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM evidencias_ot WHERE id_ot = ? ORDER BY timestamp_captura ASC",
                (id_ot.strip(),)
            ).fetchall()
            return [dict(row) for row in rows]

    def validar_evidencia(self, id_evidencia: int, estado_validacion: str, motivo_rechazo: Optional[str],
                          usuario_validador_id: Optional[int]) -> bool:
        if estado_validacion not in ('Aprobado', 'Rechazado'):
            raise ValueError("El estado de validación debe ser 'Aprobado' o 'Rechazado'.")
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE evidencias_ot 
                SET estado_validacion = ?, motivo_rechazo = ?, usuario_validador_id = ?, fecha_validacion = ?
                WHERE id_evidencia = ?
                """,
                (estado_validacion, motivo_rechazo, usuario_validador_id, self._format_datetime(datetime.now()), id_evidencia)
            )
            conn.commit()
            return cursor.rowcount > 0

    # --- GESTIÓN DE CFMs ---
    
    def listar_cfms(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM cfms ORDER BY id ASC").fetchall()
            return [dict(row) for row in rows]

    def registrar_cfm(self, item: str, ot: str, tipo: str, codigo: str, selnet: str, gilat: str, factor: str, inicio: str, fin: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO cfms (item, ot, tipo, codigo, selnet, gilat, factor, inicio, fin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item, ot, tipo, codigo, selnet, gilat, factor, inicio, fin)
                )
                conn.commit()
                row = conn.execute("SELECT * FROM cfms WHERE id = ?", (cursor.lastrowid,)).fetchone()
                return dict(row) if row else None
            except sqlite3.IntegrityError as e:
                raise ValueError(f"No se pudo registrar la CFM: {e}")

    def vaciar_cfms(self) -> bool:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cfms;")
            conn.commit()
            return True
