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
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_personal_email ON personal(email);
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

    def listar_ots(self, estado: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM ordenes_trabajo"
        params = []
        if estado:
            query += " WHERE estado = %s"
            params.append(estado)

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
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
                    "SELECT id_personal, nombre, cargo, cm, estado, email, password_hash FROM personal WHERE email = %s",
                    (email.lower().strip(),)
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
