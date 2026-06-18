# ERP Mantenimiento Amazonas

Un sistema ERP web premium diseñado para la supervisión y gestión operativa de órdenes de trabajo (OTs), inventario de la Red Amazonas y control de paradas de reloj mediante Constancias de Fuerza Mayor (CFMs). Este sistema está integrado en tiempo real con Google Sheets.

## 🚀 Arquitectura del Proyecto

El sistema está dividido en dos partes principales:
1. **Backend (FASTAPI)**:
   - Construido con **FastAPI** en Python.
   - Conexión e integración en tiempo real con Google Sheets mediante las APIs de Google Drive y Google Sheets (utilizando la librería `gspread`).
   - Base de datos local SQLite (`mantenimiento_amazonas.db`) gestionada a través de un controlador personalizado (`OTManager`).
2. **Frontend (React + TypeScript)**:
   - Desarrollado sobre **Vite** con **TypeScript**.
   - Interfaz con diseño premium moderno (modo oscuro, HSL tailored colors, animaciones sutiles, micro-interacciones).
   - Visualizaciones de líneas de tiempo para bitácora de estados de las OTs e integración con mapas geográficos de Google Maps.

---

## ✨ Características Principales

### 1. Panel de Control (Dashboard)
- Resumen analítico de órdenes de trabajo, rendimiento y estados.

### 2. Gestión Operativa de OTs (`OTManagerView`)
- Flujo interactivo de estados: **Abierta** ➔ **Despachada** ➔ **En Sitio** ➔ **Cerrada**.
- Visualización de la **Bitácora de Estados** en formato de línea de tiempo con iconos dinámicos y conectores visuales.
- **Paradas de Reloj (CFMs)** insertadas directamente en la línea de tiempo de la OT afectada, mostrando fechas/horas de inicio y fin, así como el factor/justificación del descuento.
- Control de reportes con badges informativos sobre la disponibilidad de **Informe SELNET** e **Informe GILAT**.

### 3. Inventario de Red Amazonas (`RedAmazonasView`)
- Visualización de la infraestructura de telecomunicaciones dividida en **Nodos**, **IAO** y **Hotspots**.
- Búsqueda en tiempo real y filtrado dinámico.
- Panel de detalles con coordenadas de latitud/longitud y un botón de redirección directa a Google Maps.

### 4. Módulo de Documentación (`DocumentacionView`)
- Repositorio y visualización en tiempo real de la hoja de **CFMs** de Google Sheets.
- Panel lateral premium con el desglose a detalle de la CFM seleccionada y copia rápida de número de OT al portapapeles.
- Soporte estructurado para la futura carga y descarga de informes SELNET y GILAT.

---

## 🛠️ Requisitos e Instalación

### Backend
1. Navega a la carpeta del backend:
   ```bash
   cd backend
   ```
2. Crea e inicia tu entorno virtual:
   ```bash
   python -m venv .venv
   # En Windows (Powershell)
   .\.venv\Scripts\Activate.ps1
   # En Linux/Mac
   source .venv/bin/activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ubica tu archivo de credenciales de Google Cloud Service Account en la raíz de la carpeta `backend/` y asígnale el nombre configurado en `backend/sheets_service.py` (por defecto, `tensile-impact-499801-g7-64b8caecbe2c.json`).
5. Corre el servidor FastAPI en el puerto 8000:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend
1. Navega a la carpeta del frontend:
   ```bash
   cd frontend
   ```
2. Instala las dependencias de Node.js:
   ```bash
   npm install
   ```
3. Ejecuta el servidor de desarrollo Vite:
   ```bash
   npm run dev
   ```
4. Abre [http://localhost:5173](http://localhost:5173) en tu navegador.

---

## 📊 Configuración de Google Sheets
Para que el sistema se integre correctamente con Google Sheets, asegúrate de compartir tu hoja de cálculo **"ERP-Mantenimiento-Amazonas"** con el correo de tu cuenta de servicio de Google Cloud:
`erp-mantenimiento-amazonas@tensile-impact-499801-g7.iam.gserviceaccount.com`

El documento de cálculo de Sheets debe contener tres pestañas con nombres exactos:
- **`RED A.`**: Contiene las columnas de inventario de red (`CÓDIGO`, `NODO`, `TIPO`, `UBICACIÓN`, `LATITUD`, `LONGITUD`, etc.).
- **`Master`**: Contiene las columnas de órdenes de trabajo (`NÚMERO OT`, `COD_NODO`, `ESTADO`, `INFORME`, `NOC_GILAT`, etc.).
- **`CFMs`**: Contiene las constancias de fuerza mayor (`ITEM`, `OT`, `TIPO`, `CODIGO`, `Selnet`, `Gilat`, `Factor`, `Inicio`, `Fin`).
