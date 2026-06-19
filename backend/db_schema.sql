-- Habilitar el soporte para llaves foráneas en SQLite
PRAGMA foreign_keys = ON;

-- Tabla Maestra de Elementos (Nodos, IAOs, Hotspots)
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

-- Tabla de Personal
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

-- Tabla de Cuadrillas
CREATE TABLE IF NOT EXISTS cuadrillas (
    id_cuadrilla INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    id_lider INTEGER REFERENCES personal(id_personal) ON DELETE SET NULL,
    estado TEXT CHECK(estado IN ('Disponible', 'En Ruta', 'En Sitio', 'Fuera de Servicio')) DEFAULT 'Disponible',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Órdenes de Trabajo (OTs)
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
    id_cuadrilla INTEGER REFERENCES cuadrillas(id_cuadrilla) ON DELETE SET NULL,
    fecha_planificacion TEXT,
    FOREIGN KEY (id_elemento) REFERENCES elementos(id_elemento) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla de Historial GPS de Cuadrillas
CREATE TABLE IF NOT EXISTS historial_gps (
    id_posicion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cuadrilla INTEGER NOT NULL REFERENCES cuadrillas(id_cuadrilla) ON DELETE CASCADE,
    latitud TEXT NOT NULL,
    longitud TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Evidencias de OTs (Fotos)
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

-- Tabla de Paradas de Reloj
CREATE TABLE IF NOT EXISTS paradas_reloj (
    id_parada INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ot TEXT NOT NULL,
    motivo TEXT NOT NULL,
    hora_inicio DATETIME NOT NULL,
    hora_fin DATETIME,
    observaciones TEXT,
    FOREIGN KEY (id_ot) REFERENCES ordenes_trabajo(id_ot) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla de Categorías
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT
);

-- Tabla de Alarmas
CREATE TABLE IF NOT EXISTS alarmas (
    id_alarma INTEGER PRIMARY KEY AUTOINCREMENT,
    id_elemento TEXT NOT NULL,
    nombre_alarma TEXT NOT NULL,
    gravedad TEXT CHECK(gravedad IN ('Crítica', 'Mayor', 'Menor', 'Informativa')) DEFAULT 'Informativa',
    fecha_inicio DATETIME NOT NULL,
    fecha_fin DATETIME,
    estado TEXT CHECK(estado IN ('Activa', 'Resuelta')) DEFAULT 'Activa',
    FOREIGN KEY (id_elemento) REFERENCES elementos(id_elemento) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla de CFMs (Constancias de Fuerza Mayor)
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
