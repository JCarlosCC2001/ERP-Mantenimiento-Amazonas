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
    FOREIGN KEY (id_elemento) REFERENCES elementos(id_elemento) ON DELETE RESTRICT ON UPDATE CASCADE
);
