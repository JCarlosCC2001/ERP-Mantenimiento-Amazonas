-- ============================================================
-- ERP Mantenimiento Amazonas — Esquema SQL Server (T-SQL)
-- Adaptado desde SQLite. Compatible con SQL Server 2016+
-- ============================================================

USE [ErpMantenimientoAmazonas];  -- Cambia por el nombre de tu base de datos
GO

-- ============================================================
-- TABLA: elementos
-- Maestra de Nodos, IAOs y Hotspots de la red
-- ============================================================
CREATE TABLE elementos (
    id_elemento   NVARCHAR(50)   NOT NULL,
    nombre        NVARCHAR(255)  NOT NULL,
    tipo          NVARCHAR(10)   NOT NULL,
    pendiente     NVARCHAR(255)  NULL,
    categoria     NVARCHAR(100)  NULL,
    dependencia   NVARCHAR(255)  NULL,
    provincia     NVARCHAR(100)  NULL,
    distrito      NVARCHAR(100)  NULL,
    localidad     NVARCHAR(100)  NULL,
    latitud       NVARCHAR(30)   NULL,
    longitud      NVARCHAR(30)   NULL,

    CONSTRAINT PK_elementos       PRIMARY KEY (id_elemento),
    CONSTRAINT CK_elementos_tipo  CHECK (tipo IN ('Nodo', 'IAO', 'Hotspot'))
);
GO

-- ============================================================
-- TABLA: personal
-- Usuarios/técnicos del sistema
-- ============================================================
CREATE TABLE personal (
    id_personal    INT            NOT NULL IDENTITY(1,1),
    nombre         NVARCHAR(255)  NOT NULL,
    cargo          NVARCHAR(100)  NULL,
    cm             NVARCHAR(100)  NULL,
    estado         NVARCHAR(10)   NOT NULL DEFAULT 'Activo',
    email          NVARCHAR(255)  NOT NULL,
    password_hash  NVARCHAR(255)  NOT NULL,
    created_at     DATETIME2      NOT NULL DEFAULT GETDATE(),
    updated_at     DATETIME2      NOT NULL DEFAULT GETDATE(),

    CONSTRAINT PK_personal        PRIMARY KEY (id_personal),
    CONSTRAINT UQ_personal_email  UNIQUE (email),
    CONSTRAINT CK_personal_estado CHECK (estado IN ('Activo', 'Inactivo'))
);
GO

-- ============================================================
-- TABLA: cuadrillas
-- Equipos de trabajo de campo
-- ============================================================
CREATE TABLE cuadrillas (
    id_cuadrilla  INT            NOT NULL IDENTITY(1,1),
    nombre        NVARCHAR(255)  NOT NULL,
    id_lider      INT            NULL,
    estado        NVARCHAR(20)   NOT NULL DEFAULT 'Disponible',
    created_at    DATETIME2      NOT NULL DEFAULT GETDATE(),

    CONSTRAINT PK_cuadrillas        PRIMARY KEY (id_cuadrilla),
    CONSTRAINT UQ_cuadrillas_nombre UNIQUE (nombre),
    CONSTRAINT CK_cuadrillas_estado CHECK (estado IN ('Disponible', 'En Ruta', 'En Sitio', 'Fuera de Servicio')),
    CONSTRAINT FK_cuadrillas_lider  FOREIGN KEY (id_lider)
        REFERENCES personal(id_personal) ON DELETE SET NULL
);
GO

-- ============================================================
-- TABLA: ordenes_trabajo (OTs)
-- Ordenes de trabajo de mantenimiento
-- ============================================================
CREATE TABLE ordenes_trabajo (
    id_ot               NVARCHAR(50)   NOT NULL,
    id_elemento         NVARCHAR(50)   NOT NULL,
    prioridad           NVARCHAR(10)   NOT NULL,
    diagnostico_inicial NVARCHAR(MAX)  NULL,
    hora_recepcion      DATETIME2      NOT NULL,
    hora_despacho       DATETIME2      NULL,
    hora_llegada        DATETIME2      NULL,
    hora_cierre         DATETIME2      NULL,
    estado              NVARCHAR(15)   NOT NULL DEFAULT 'Abierta',
    informe             NVARCHAR(MAX)  NULL,
    noc_gilat           NVARCHAR(100)  NULL,
    requiere            NVARCHAR(255)  NULL,
    tiene               NVARCHAR(255)  NULL,
    inicio              NVARCHAR(50)   NULL,
    fin                 NVARCHAR(50)   NULL,
    inicio_1            NVARCHAR(50)   NULL,
    fin_1               NVARCHAR(50)   NULL,
    inicio_2            NVARCHAR(50)   NULL,
    fin_2               NVARCHAR(50)   NULL,
    id_cuadrilla        INT            NULL,
    fecha_planificacion NVARCHAR(50)   NULL,

    CONSTRAINT PK_ordenes_trabajo         PRIMARY KEY (id_ot),
    CONSTRAINT CK_ordenes_trabajo_prio    CHECK (prioridad IN ('Alta', 'Media', 'Baja')),
    CONSTRAINT CK_ordenes_trabajo_estado  CHECK (estado IN ('Abierta', 'Despachada', 'En Sitio', 'Cerrada')),
    CONSTRAINT FK_ot_elemento   FOREIGN KEY (id_elemento)
        REFERENCES elementos(id_elemento) ON DELETE NO ACTION ON UPDATE CASCADE,
    CONSTRAINT FK_ot_cuadrilla  FOREIGN KEY (id_cuadrilla)
        REFERENCES cuadrillas(id_cuadrilla) ON DELETE SET NULL
);
GO

-- ============================================================
-- TABLA: historial_gps
-- Posiciones GPS registradas por cuadrilla
-- ============================================================
CREATE TABLE historial_gps (
    id_posicion   INT           NOT NULL IDENTITY(1,1),
    id_cuadrilla  INT           NOT NULL,
    latitud       NVARCHAR(30)  NOT NULL,
    longitud      NVARCHAR(30)  NOT NULL,
    timestamp     DATETIME2     NOT NULL DEFAULT GETDATE(),

    CONSTRAINT PK_historial_gps  PRIMARY KEY (id_posicion),
    CONSTRAINT FK_gps_cuadrilla  FOREIGN KEY (id_cuadrilla)
        REFERENCES cuadrillas(id_cuadrilla) ON DELETE CASCADE
);
GO

-- ============================================================
-- TABLA: evidencias_ot
-- Fotos de evidencia subidas a Cloudinary
-- ============================================================
CREATE TABLE evidencias_ot (
    id_evidencia         INT            NOT NULL IDENTITY(1,1),
    id_ot                NVARCHAR(50)   NOT NULL,
    tipo_evidencia       NVARCHAR(20)   NOT NULL,
    url_foto             NVARCHAR(500)  NOT NULL,   -- URL HTTPS de Cloudinary
    latitud_foto         NVARCHAR(30)   NULL,
    longitud_foto        NVARCHAR(30)   NULL,
    timestamp_captura    DATETIME2      NOT NULL,
    estado_validacion    NVARCHAR(15)   NOT NULL DEFAULT 'Pendiente',
    motivo_rechazo       NVARCHAR(MAX)  NULL,
    usuario_validador_id INT            NULL,
    fecha_validacion     DATETIME2      NULL,

    CONSTRAINT PK_evidencias_ot          PRIMARY KEY (id_evidencia),
    CONSTRAINT CK_evidencias_tipo        CHECK (tipo_evidencia IN ('Desplazamiento', 'Antes', 'Despues')),
    CONSTRAINT CK_evidencias_validacion  CHECK (estado_validacion IN ('Pendiente', 'Aprobado', 'Rechazado')),
    CONSTRAINT FK_evidencias_ot          FOREIGN KEY (id_ot)
        REFERENCES ordenes_trabajo(id_ot) ON DELETE CASCADE,
    CONSTRAINT FK_evidencias_validador   FOREIGN KEY (usuario_validador_id)
        REFERENCES personal(id_personal) ON DELETE SET NULL
);
GO

-- ============================================================
-- TABLA: paradas_reloj
-- Interrupciones registradas durante una OT
-- ============================================================
CREATE TABLE paradas_reloj (
    id_parada      INT            NOT NULL IDENTITY(1,1),
    id_ot          NVARCHAR(50)   NOT NULL,
    motivo         NVARCHAR(255)  NOT NULL,
    hora_inicio    DATETIME2      NOT NULL,
    hora_fin       DATETIME2      NULL,
    observaciones  NVARCHAR(MAX)  NULL,

    CONSTRAINT PK_paradas_reloj  PRIMARY KEY (id_parada),
    CONSTRAINT FK_paradas_ot     FOREIGN KEY (id_ot)
        REFERENCES ordenes_trabajo(id_ot) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

-- ============================================================
-- TABLA: categorias
-- Categorias de elementos de red
-- ============================================================
CREATE TABLE categorias (
    id_categoria  INT            NOT NULL IDENTITY(1,1),
    nombre        NVARCHAR(100)  NOT NULL,
    descripcion   NVARCHAR(MAX)  NULL,

    CONSTRAINT PK_categorias        PRIMARY KEY (id_categoria),
    CONSTRAINT UQ_categorias_nombre UNIQUE (nombre)
);
GO

-- ============================================================
-- TABLA: alarmas
-- Alarmas activas o resueltas por elemento
-- ============================================================
CREATE TABLE alarmas (
    id_alarma     INT            NOT NULL IDENTITY(1,1),
    id_elemento   NVARCHAR(50)   NOT NULL,
    nombre_alarma NVARCHAR(255)  NOT NULL,
    gravedad      NVARCHAR(15)   NOT NULL DEFAULT 'Informativa',
    fecha_inicio  DATETIME2      NOT NULL,
    fecha_fin     DATETIME2      NULL,
    estado        NVARCHAR(10)   NOT NULL DEFAULT 'Activa',

    CONSTRAINT PK_alarmas          PRIMARY KEY (id_alarma),
    CONSTRAINT CK_alarmas_gravedad CHECK (gravedad IN ('Critica', 'Mayor', 'Menor', 'Informativa')),
    CONSTRAINT CK_alarmas_estado   CHECK (estado IN ('Activa', 'Resuelta')),
    CONSTRAINT FK_alarmas_elemento FOREIGN KEY (id_elemento)
        REFERENCES elementos(id_elemento) ON DELETE CASCADE ON UPDATE CASCADE
);
GO

-- ============================================================
-- TABLA: cfms
-- Constancias de Fuerza Mayor
-- ============================================================
CREATE TABLE cfms (
    id         INT            NOT NULL IDENTITY(1,1),
    item       NVARCHAR(50)   NULL,
    ot         NVARCHAR(50)   NULL,
    tipo       NVARCHAR(100)  NULL,
    codigo     NVARCHAR(50)   NULL,
    selnet     NVARCHAR(100)  NULL,
    gilat      NVARCHAR(100)  NULL,
    factor     NVARCHAR(100)  NULL,
    inicio     NVARCHAR(50)   NULL,
    fin        NVARCHAR(50)   NULL,
    created_at DATETIME2      NOT NULL DEFAULT GETDATE(),

    CONSTRAINT PK_cfms PRIMARY KEY (id)
);
GO

-- ============================================================
-- INDICES recomendados para rendimiento
-- ============================================================
CREATE INDEX IX_ot_estado       ON ordenes_trabajo (estado);
CREATE INDEX IX_ot_elemento     ON ordenes_trabajo (id_elemento);
CREATE INDEX IX_ot_cuadrilla    ON ordenes_trabajo (id_cuadrilla);
CREATE INDEX IX_evidencias_ot   ON evidencias_ot (id_ot);
CREATE INDEX IX_gps_cuadrilla   ON historial_gps (id_cuadrilla);
CREATE INDEX IX_alarmas_elem    ON alarmas (id_elemento);
GO
