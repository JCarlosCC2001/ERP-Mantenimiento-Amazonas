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
        """Inicializa la base de datos usando el esquema SQL provisto."""
        if not os.path.exists(self.db_path):
            if os.path.exists(self.schema_path):
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                with self._get_connection() as conn:
                    conn.executescript(schema_sql)
            else:
                # Esquema embebido de respaldo si no se encuentra el archivo SQL
                with self._get_connection() as conn:
                    conn.execute("PRAGMA foreign_keys = ON;")
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS elementos (
                            id_elemento TEXT PRIMARY KEY,
                            nombre TEXT NOT NULL,
                            tipo TEXT CHECK(tipo IN ('Nodo', 'IAO', 'Hotspot')) NOT NULL,
                            pendiente TEXT,
                            categoria TEXT,
                            dependencia TEXT,
                            provincia TEXT,
                            distrito TEXT,
                            localidad TEXT,
                            latitud TEXT,
                            longitud TEXT
                        );
                    """)
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                            id_ot TEXT PRIMARY KEY,
                            id_elemento TEXT NOT NULL,
                            prioridad TEXT CHECK(prioridad IN ('Alta', 'Media', 'Baja')) NOT NULL,
                            diagnostico_inicial TEXT,
                            hora_recepcion DATETIME NOT NULL,
                            hora_despacho DATETIME,
                            hora_llegada DATETIME,
                            hora_cierre DATETIME,
                            estado TEXT CHECK(estado IN ('Abierta', 'Despachada', 'En Sitio', 'Cerrada')) DEFAULT 'Abierta',
                            FOREIGN KEY (id_elemento) REFERENCES elementos(id_elemento) ON DELETE RESTRICT ON UPDATE CASCADE
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
