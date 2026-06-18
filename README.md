# ERP Mantenimiento Amazonas

Un sistema ERP web de alta gama diseñado para la supervisión, gestión operativa de órdenes de trabajo (OTs), inventario de la **Red Amazonas** y control de paradas de reloj mediante **Constancias de Fuerza Mayor (CFMs)**. El sistema destaca por su doble motor de base de datos (SQLite/Supabase) y su completa integración con Google Sheets en tiempo real.

---

## 🚀 Arquitectura del Proyecto

El sistema está desarrollado con un diseño desacoplado y moderno en dos capas principales:

### 1. Backend (FastAPI)
* **API REST**: Construido sobre **FastAPI** (Python), proporcionando endpoints documentados e interactivos automáticamente (Swagger UI en `/docs`).
* **Arquitectura de Base de Datos Híbrida/Dual**:
  * **SQLite**: Base de datos local ligera (`mantenimiento_amazonas.db`) gestionada mediante el controlador personalizado `OTManager`. Ideal para desarrollo rápido sin dependencias de red.
  * **Supabase (PostgreSQL)**: Base de datos en la nube de nivel empresarial, administrada con `SupabaseOTManager` y conectada mediante `psycopg2`. Se habilita de manera dinámica con variables de entorno.
* **Integración con Google Sheets**: Conexión bidireccional en tiempo real mediante las APIs de Google Drive y Google Sheets (`gspread`).
* **Seguridad y Criptografía**: Módulo de seguridad (`security.py`) para el almacenamiento seguro de credenciales mediante hashes criptográficos **bcrypt** (factor de trabajo 12), así como utilidades para la generación automática de correos corporativos y contraseñas seguras a partir de nombres de personal.

### 2. Frontend (React + TypeScript)
* **Vite + React**: Entorno ágil de alto rendimiento estructurado con TypeScript para robustez en el tipado.
* **Diseño e Interfaz Premium**: Aspecto moderno adaptado a modo oscuro con paleta de colores HSL refinada, transiciones fluidas, micro-animaciones en botones y elementos de navegación.
* **Gestión de Sesiones**: Control de autenticación con almacenamiento y persistencia mediante `sessionStorage`.

---

## ✨ Características Principales

### 1. Módulo de Autenticación y Seguridad 🔒 [Nuevo]
* **Pantalla de Login Interactiva**: Interfaz premium de autenticación que valida las credenciales contra la base de datos (SQLite o Supabase) a través de hashes seguros de contraseña.
* **Persistencia de Sesión**: Guarda temporalmente el estado del usuario logueado en el navegador, previniendo pérdidas de sesión al recargar la página.

### 2. Gestión de Personal (Staff) 👥 [Nuevo]
* **Panel Administrativo de Personal**: Vista dedicada en formato de tabla interactiva para listar todos los colaboradores.
* **Edición de Datos de Staff**: Permite actualizar el cargo, centro de mantenimiento (CM), estado (Activo/Inactivo) y redefinir contraseñas de forma directa y segura.

### 3. Panel de Control (Dashboard) 📊
* Métricas analíticas en tiempo real sobre órdenes de trabajo abiertas, en sitio, despachadas y cerradas.

### 4. Gestión Operativa de OTs (`OTManagerView`) ⚙️
* **Flujo interactivo de estados**: Gestión secuencial guiada para transiciones de OTs (**Abierta** ➔ **Despachada** ➔ **En Sitio** ➔ **Cerrada**).
* **Línea de Tiempo de Estados**: Historial y bitácora de transiciones con marcas de tiempo, iconos dinámicos y conectores visuales.
* **Integración de CFMs**: Visualización de paradas de reloj directamente en el flujo temporal de la OT correspondiente.

### 5. Inventario de Red Amazonas (`RedAmazonasView`) 📡
* Infraestructura dividida por categorías: **Nodos**, **IAO** y **Hotspots** con capacidades de búsqueda en tiempo real y filtrado interactivo.
* Visualización rápida de coordenadas geográficas y georreferenciación directa con Google Maps.

### 6. Módulo de Documentación (`DocumentacionView`) 📂
* Repositorio de CFMs leídas de Google Sheets, panel de inspección de detalles y soporte inicial para adjuntar informes técnicos SELNET y GILAT.

---

## 🛠️ Requisitos e Instalación

### Backend 🐍

1. Navega a la carpeta del backend:
   ```bash
   cd backend
   ```

2. Crea e inicia tu entorno virtual de Python:
   ```bash
   python -m venv .venv
   
   # En Windows (Powershell)
   .\.venv\Scripts\Activate.ps1
   # En Linux/Mac
   source .venv/bin/activate
   ```

3. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuración de Variables de Entorno (`.env`)**:
   Crea un archivo `.env` en la raíz de la carpeta `backend/` con la siguiente estructura:
   ```env
   # Control de Base de Datos (true para Supabase, false para SQLite local)
   USE_SUPABASE=true
   
   # URI de conexión de PostgreSQL en Supabase
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
   ```

5. **Credenciales de Google Sheets**:
   Ubica tu archivo de credenciales de Google Cloud Service Account en la raíz de `backend/` y asígnale el nombre `tensile-impact-499801-g7-64b8caecbe2c.json` (o el nombre configurado en `sheets_service.py`).

6. **Ejecución del Servidor**:
   Inicia la API con Uvicorn en el puerto 8000:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend ⚛️

1. Navega a la carpeta del frontend:
   ```bash
   cd frontend
   ```

2. Instala los paquetes de Node.js:
   ```bash
   npm install
   ```

3. Ejecuta el servidor de desarrollo de Vite:
   ```bash
   npm run dev
   ```

4. Abre [http://localhost:5173](http://localhost:5173) en tu navegador.

---

## 🔄 Migración de Datos a Supabase 🚀

Si decides utilizar la base de datos Supabase (PostgreSQL), puedes migrar e inicializar de forma automática toda la información histórica contenida en tu Google Sheets actual (Nodos, OTs y Personal).

Para hacerlo, ejecuta el script de migración en la terminal desde el directorio `backend`:

```bash
python migrate_sheets_to_supabase.py
```

### ¿Qué realiza este script?
1. **Recreación de Estructuras**: Genera las tablas `elementos`, `ordenes_trabajo` y `personal` de forma limpia y controlada en Supabase.
2. **Importación y Mapeo**: Lee las hojas `RED A.`, `Master` y `Personal`, normaliza los nombres de columnas y parsea fechas de múltiples formatos de manera inteligente.
3. **Provisionamiento de Personal**: Crea accesos para los colaboradores del Sheets, autogenerando correos (`nombre.apellido@mantenimiento-amazonas.pe`) y contraseñas seguras temporales (ej: `JPerez#Amazonas`), las cuales almacena encriptadas con hash **bcrypt**. Los accesos generados se imprimen en la consola para tu conveniencia.

---

## 📊 Configuración de Google Sheets

Para asegurar la correcta integración en tiempo real, comparte tu documento de Google Sheets **"ERP-Mantenimiento-Amazonas"** con el correo de la cuenta de servicio de Google Cloud:
`erp-mantenimiento-amazonas@tensile-impact-499801-g7.iam.gserviceaccount.com`

El documento de cálculo de Sheets debe contener cuatro pestañas con nombres exactos:
* **`RED A.`**: Tabla de elementos (`CÓDIGO`, `NODO`, `TIPO`, `UBICACIÓN`, `LATITUD`, `LONGITUD`, etc.).
* **`Master`**: Tabla de órdenes de trabajo (`NÚMERO OT`, `COD_NODO`, `ESTADO`, `INFORME`, `NOC_GILAT`, etc.).
* **`CFMs`**: Tabla de constancias de fuerza mayor (`ITEM`, `OT`, `TIPO`, `CODIGO`, `Factor`, `Inicio`, `Fin`, etc.).
* **`Personal`**: Tabla de miembros de personal autorizados (`Nombre`, `Cargo`, `CM`, `Estado`).
