from fastapi import FastAPI, HTTPException, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any, Dict, Union
import os
from dotenv import load_dotenv
load_dotenv()

from ot_manager import OTManager
from supabase_ot_manager import SupabaseOTManager
from sheets_service import sheets_service
from security import verify_password
import cloudinary_service

app = FastAPI(
    title="ERP Mantenimiento Amazonas API",
    description="API para la gestión de Órdenes de Trabajo, Paradas de Reloj e Inventario de Amazonas",
    version="1.0.0"
)

# Verificar configuración de Cloudinary al iniciar
if not cloudinary_service.is_configured():
    print("[ADVERTENCIA] Las credenciales de Cloudinary no están configuradas en .env")
    print("  Configura CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY y CLOUDINARY_API_SECRET")
else:
    print("Cloudinary configurado correctamente para almacenamiento de evidencias.")

# Configuración de CORS para permitir la conexión desde el frontend (Vite por defecto corre en 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desarrollo permitimos todos, se puede restringir a http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar gestor de base de datos dinámicamente
use_supabase = os.environ.get("USE_SUPABASE", "false").lower() == "true"
if use_supabase:
    print("Iniciando con base de datos SUPABASE (PostgreSQL)...")
    ot_db = SupabaseOTManager()
else:
    print("Iniciando con base de datos SQLite local...")
    ot_db = OTManager()

# --- MODELOS PYDANTIC ---

class ElementoCreate(BaseModel):
    id_elemento: str = Field(..., description="ID único del elemento (ej. NOD-001, IAO-102)")
    nombre: str = Field(..., description="Nombre descriptivo del elemento")
    tipo: str = Field(..., description="Debe ser 'Nodo', 'IAO' o 'Hotspot'")
    pendiente: Optional[str] = None
    categoria: Optional[str] = None
    dependencia: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    localidad: Optional[str] = None
    latitud: Optional[str] = None
    longitud: Optional[str] = None

class ElementoResponse(BaseModel):
    id_elemento: str
    nombre: str
    tipo: str
    pendiente: Optional[str] = None
    categoria: Optional[str] = None
    dependencia: Optional[str] = None
    provincia: Optional[str] = None
    distrito: Optional[str] = None
    localidad: Optional[str] = None
    latitud: Optional[str] = None
    longitud: Optional[str] = None

class OTCreate(BaseModel):
    id_ot: str = Field(..., description="ID único de la OT (ej. OT-2026-0001)")
    id_elemento: str = Field(..., description="ID del elemento relacionado")
    prioridad: str = Field(..., description="Debe ser 'Alta', 'Media' o 'Baja'")
    diagnostico_inicial: str = Field(..., description="Descripción inicial del problema")
    hora_recepcion: Optional[datetime] = Field(None, description="Fecha/hora de recepción. Si no se pasa, toma la hora actual")

from typing import List, Optional, Any, Dict, Union

class OTResponse(BaseModel):
    id_ot: str
    id_elemento: str
    prioridad: str
    diagnostico_inicial: str
    hora_recepcion: Union[datetime, str]
    hora_despacho: Optional[Union[datetime, str]] = None
    hora_llegada: Optional[Union[datetime, str]] = None
    hora_cierre: Optional[Union[datetime, str]] = None
    estado: str
    informe: Optional[str] = None
    noc_gilat: Optional[str] = None
    requiere: Optional[str] = None
    tiene: Optional[str] = None
    inicio: Optional[str] = None
    fin: Optional[str] = None
    inicio_1: Optional[str] = None
    fin_1: Optional[str] = None
    inicio_2: Optional[str] = None
    fin_2: Optional[str] = None
    id_cuadrilla: Optional[int] = None
    fecha_planificacion: Optional[str] = None

class TransitionRequest(BaseModel):
    timestamp: Optional[datetime] = Field(None, description="Fecha/hora del cambio de estado. Por defecto es ahora")


# --- MODELOS PYDANTIC DE PERSONAL Y AUTENTICACIÓN ---

class PersonalCreate(BaseModel):
    nombre: str = Field(..., description="Nombre completo del personal")
    cargo: Optional[str] = Field(None, description="Cargo o puesto")
    cm: Optional[str] = Field(None, description="Centro de Mantenimiento asignado")
    estado: Optional[str] = Field('Activo', description="Estado: 'Activo' o 'Inactivo'")
    email: Optional[str] = Field(None, description="Correo electrónico (se auto-genera si no se envía)")

class PersonalResponse(BaseModel):
    id_personal: int
    nombre: str
    cargo: Optional[str] = None
    cm: Optional[str] = None
    estado: Optional[str] = None
    email: str

class PersonalUpdate(BaseModel):
    nombre: Optional[str] = None
    cargo: Optional[str] = None
    cm: Optional[str] = None
    estado: Optional[str] = None
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: str = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., description="Contraseña del usuario")

class LoginResponse(BaseModel):
    id_personal: int
    nombre: str
    cargo: Optional[str] = None
    email: str
    token: str = "session_ok"  # Placeholder para futura implementación de JWT


# --- FUNCIONES DE MAPEO INTELIGENTE PARA GOOGLE SHEETS ---

def map_row_to_elemento(row: Dict[str, Any]) -> Dict[str, Any]:
    def get_val(keys_to_search: List[str], default: Any = "") -> Any:
        for k in keys_to_search:
            for row_k in row.keys():
                if row_k.strip().lower() == k.lower():
                    return row[row_k]
        return default

    id_el = str(get_val(["código", "codigo", "código nodo", "codigo nodo", "id_elemento", "id"], "") or "").strip()
    nombre = str(get_val(["nombre", "nombre nodo", "nodo", "nombre_elemento", "descripcion", "descripción"], "") or "").strip()
    tipo = str(get_val(["tipo", "type", "clase"], "Nodo") or "Nodo").strip()
    
    pendiente = str(get_val(["pendiente"], "") or "").strip()
    categoria = str(get_val(["categoría", "categoria"], "") or "").strip()
    dependencia = str(get_val(["dependencia"], "") or "").strip()
    provincia = str(get_val(["provincia"], "") or "").strip()
    distrito = str(get_val(["distrito"], "") or "").strip()
    localidad = str(get_val(["localidad"], "") or "").strip()
    latitud = str(get_val(["latitud"], "") or "").strip()
    longitud = str(get_val(["longitud"], "") or "").strip()

    # Normalizar tipo: Considerar que las IAO son (Centro de salud, Comisaría y Institución Educativa)
    tipo_lower = tipo.lower()
    nombre_lower = nombre.lower()
    
    es_iao = (
        "iao" in tipo_lower or
        "salud" in tipo_lower or "salud" in nombre_lower or
        "comisar" in tipo_lower or "comisar" in nombre_lower or
        "educativ" in tipo_lower or "educativ" in nombre_lower or
        "colegio" in tipo_lower or "colegio" in nombre_lower or
        "escuela" in tipo_lower or "escuela" in nombre_lower or
        "i.e." in tipo_lower or "i.e." in nombre_lower or
        "ie" in tipo_lower or nombre_lower.startswith("ie ")
    )
    
    es_hs = (
        "hs" in tipo_lower or "hotspot" in tipo_lower or "wifi" in tipo_lower or
        "hs" in nombre_lower or "hotspot" in nombre_lower or "wifi" in nombre_lower
    )

    if es_iao:
        tipo = "IAO"
    elif es_hs:
        tipo = "Hotspot"
    else:
        tipo = "Nodo"

    if not id_el and nombre:
        id_el = f"EL-{nombre[:6].upper().replace(' ', '-')}"

    return {
        "id_elemento": id_el if id_el else "EL-GENERIC",
        "nombre": nombre if nombre else f"Elemento {id_el}",
        "tipo": tipo,
        "pendiente": pendiente,
        "categoria": categoria,
        "dependencia": dependencia,
        "provincia": provincia,
        "distrito": distrito,
        "localidad": localidad,
        "latitud": latitud,
        "longitud": longitud
    }

def map_row_to_ot(row: Dict[str, Any]) -> Dict[str, Any]:
    def get_val(keys_to_search: List[str], default: Any = "") -> Any:
        for k in keys_to_search:
            for row_k in row.keys():
                if row_k.strip().lower() == k.lower():
                    return row[row_k]
        return default

    id_ot = str(get_val(["número ot", "numero ot", "nro_ot", "nro ot", "ot", "id_ot", "id"], "") or "").strip()
    id_elemento = str(get_val(["cod_nodo", "nodo", "código nodo", "codigo nodo", "cod nodo", "id_elemento", "elemento", "código", "codigo"], "") or "").strip()
    prioridad = str(get_val(["prioridad", "priority"], "Media") or "Media").strip()
    diagnostico_inicial = str(get_val(["diagnostico_inicial", "diagnostico", "diagnóstico", "detalle", "descripcion", "descripción"], "Mantenimiento Preventivo/Correctivo") or "Mantenimiento Preventivo/Correctivo").strip()
    
    hora_recepcion = str(get_val(["fecha de notificación", "fecha de notificacion", "fecha notificación", "fecha notificacion", "notificación", "notificacion", "fecha", "hora_recepcion", "recepcion"], "") or "").strip()
    if not hora_recepcion:
        hora_recepcion = datetime.now().isoformat()
        
    hora_despacho = get_val(["hora_despacho", "despacho", "fecha_despacho"])
    hora_despacho = str(hora_despacho).strip() if hora_despacho else None
    
    hora_llegada = get_val(["hora_llegada", "llegada", "fecha_llegada"])
    hora_llegada = str(hora_llegada).strip() if hora_llegada else None
    
    hora_cierre = get_val(["hora_cierre", "cierre", "fecha_cierre"])
    hora_cierre = str(hora_cierre).strip() if hora_cierre else None
    
    estado = str(get_val(["estado", "estado ot", "estado_ot", "status", "state"], "Abierta") or "Abierta").strip()

    estado_lower = estado.lower()
    if "abiert" in estado_lower:
        estado = "Abierta"
    elif "despach" in estado_lower or "camino" in estado_lower:
        estado = "Despachada"
    elif "sitio" in estado_lower or "proceso" in estado_lower:
        estado = "En Sitio"
    elif "cerrad" in estado_lower or "complet" in estado_lower or "resuelt" in estado_lower:
        estado = "Cerrada"

    prioridad_lower = prioridad.lower()
    if "alt" in prioridad_lower:
        prioridad = "Alta"
    elif "baj" in prioridad_lower:
        prioridad = "Baja"
    else:
        prioridad = "Media"

    informe = str(get_val(["informe"], "") or "").strip()
    noc_gilat = str(get_val(["noc_gilat", "noc gilat"], "") or "").strip()
    requiere = str(get_val(["requiere"], "") or "").strip()
    tiene = str(get_val(["tiene"], "") or "").strip()
    inicio = str(get_val(["inicio"], "") or "").strip()
    fin = str(get_val(["fin"], "") or "").strip()
    inicio_1 = str(get_val(["inicio_1", "inicio 1"], "") or "").strip()
    fin_1 = str(get_val(["fin_1", "fin 1"], "") or "").strip()
    inicio_2 = str(get_val(["inicio_2", "inicio 2"], "") or "").strip()
    fin_2 = str(get_val(["fin_2", "fin 2"], "") or "").strip()

    return {
        "id_ot": id_ot,
        "id_elemento": id_elemento if id_elemento else "NOD-GEN",
        "prioridad": prioridad,
        "diagnostico_inicial": diagnostico_inicial,
        "hora_recepcion": hora_recepcion,
        "hora_despacho": hora_despacho,
        "hora_llegada": hora_llegada,
        "hora_cierre": hora_cierre,
        "estado": estado,
        "informe": informe,
        "noc_gilat": noc_gilat,
        "requiere": requiere,
        "tiene": tiene,
        "inicio": inicio,
        "fin": fin,
        "inicio_1": inicio_1,
        "fin_1": fin_1,
        "inicio_2": inicio_2,
        "fin_2": fin_2
    }


# --- ENDPOINTS ELEMENTOS ---

@app.get("/api/elementos", response_model=List[ElementoResponse], tags=["Elementos"])
def get_elementos():
    """Obtiene la lista de elementos directamente desde la base de datos."""
    try:
        elementos = ot_db.listar_elementos()
        return elementos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener catálogo de elementos desde la BD: {str(e)}")

@app.post("/api/elementos", response_model=ElementoResponse, status_code=status.HTTP_201_CREATED, tags=["Elementos"])
def create_elemento(elemento: ElementoCreate):
    """Registra un nuevo elemento."""
    try:
        ot_db.registrar_elemento(
            id_elemento=elemento.id_elemento,
            nombre=elemento.nombre,
            tipo=elemento.tipo,
            ubicacion=elemento.ubicacion
        )
        return {
            "id_elemento": elemento.id_elemento,
            "nombre": elemento.nombre,
            "tipo": elemento.tipo,
            "ubicacion": elemento.ubicacion
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/elementos/{id_elemento}", status_code=status.HTTP_200_OK, tags=["Elementos"])
def delete_elemento(id_elemento: str):
    """Elimina un elemento."""
    try:
        deleted = ot_db.eliminar_elemento(id_elemento)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"El elemento '{id_elemento}' no existe.")
        return {"message": f"Elemento '{id_elemento}' eliminado con éxito."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS ÓRDENES DE TRABAJO (OTs) ---

@app.get("/api/ots", response_model=List[OTResponse], tags=["Órdenes de Trabajo"])
def get_ots(estado: Optional[str] = None):
    """Obtiene la lista de OTs directamente desde la base de datos."""
    try:
        ots = ot_db.listar_ots(estado=estado)
        # Invertir el orden para mostrar las más recientes primero
        ots.reverse()
        return ots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener OTs desde la BD: {str(e)}")

@app.get("/api/ots/{id_ot}", response_model=OTResponse, tags=["Órdenes de Trabajo"])
def get_ot(id_ot: str):
    """Obtiene la información detallada de una OT específica desde la BD."""
    try:
        ot = ot_db.obtener_ot(id_ot)
        if not ot:
            raise HTTPException(status_code=404, detail=f"La OT '{id_ot}' no fue encontrada en la BD.")
        return ot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ots", response_model=OTResponse, status_code=status.HTTP_201_CREATED, tags=["Órdenes de Trabajo"])
def create_ot(ot: OTCreate):
    """Crea una nueva orden de trabajo en estado 'Abierta'."""
    try:
        ot_db.crear_ot(
            id_ot=ot.id_ot,
            id_elemento=ot.id_elemento,
            prioridad=ot.prioridad,
            diagnostico_inicial=ot.diagnostico_inicial,
            hora_recepcion=ot.hora_recepcion
        )
        return ot_db.obtener_ot(ot.id_ot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ots/{id_ot}/despachar", response_model=OTResponse, tags=["Órdenes de Trabajo"])
def despachar_ot(id_ot: str, payload: Optional[TransitionRequest] = None):
    """Despacha la cuadrilla para la OT, registrando la hora del despacho."""
    try:
        ts = payload.timestamp if payload else None
        ot_db.despachar_cuadrilla(id_ot, hora_despacho=ts)
        return ot_db.obtener_ot(id_ot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ots/{id_ot}/llegada", response_model=OTResponse, tags=["Órdenes de Trabajo"])
def registrar_llegada_ot(id_ot: str, payload: Optional[TransitionRequest] = None):
    """Registra el arribo a sitio de la cuadrilla para la OT."""
    try:
        ts = payload.timestamp if payload else None
        ot_db.registrar_llegada_sitio(id_ot, hora_llegada=ts)
        return ot_db.obtener_ot(id_ot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ots/{id_ot}/cerrar", response_model=OTResponse, tags=["Órdenes de Trabajo"])
def cerrar_ot(id_ot: str, payload: Optional[TransitionRequest] = None):
    """Cierra la orden de trabajo."""
    try:
        ts = payload.timestamp if payload else None
        ot_db.cerrar_ot(id_ot, hora_cierre=ts)
        return ot_db.obtener_ot(id_ot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINTS RED AMAZONAS (GOOGLE SHEETS) ---

@app.get("/api/red-amazonas", response_model=List[Dict[str, Any]], tags=["Red Amazonas"])
def get_red_amazonas():
    """Obtiene los datos de los nodos de la red desde la BD."""
    try:
        return ot_db.listar_elementos()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS CFMs (GOOGLE SHEETS) ---

@app.get("/api/cfms", response_model=List[Dict[str, Any]], tags=["CFMs"])
def get_cfms():
    """Obtiene los datos de las CFMs desde la base de datos."""
    try:
        return ot_db.listar_cfms()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de CFMs: {str(e)}")


# --- ENDPOINTS DE PERSONAL ---

@app.get("/api/personal", response_model=List[PersonalResponse], tags=["Personal"])
def get_personal():
    """Lista todo el personal registrado en el sistema."""
    try:
        return ot_db.listar_personal()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/personal/{id_personal}", response_model=PersonalResponse, tags=["Personal"])
def get_personal_by_id(id_personal: int):
    """Obtiene los datos de un miembro del personal por su ID."""
    try:
        persona = ot_db.obtener_personal(id_personal)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Personal con ID {id_personal} no encontrado.")
        return persona
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/personal/{id_personal}", response_model=PersonalResponse, tags=["Personal"])
def update_personal(id_personal: int, datos: PersonalUpdate):
    """Actualiza los datos de un miembro del personal."""
    try:
        persona = ot_db.obtener_personal(id_personal)
        if not persona:
            raise HTTPException(status_code=404, detail=f"Personal con ID {id_personal} no encontrado.")
        ot_db.actualizar_personal(id_personal, datos.model_dump(exclude_none=True))
        return ot_db.obtener_personal(id_personal)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS DE AUTENTICACIÓN ---

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Autenticación"])
def login(credentials: LoginRequest):
    """
    Autentica a un usuario con su correo y contraseña.
    La contraseña se verifica contra el hash bcrypt almacenado en la base de datos.
    """
    try:
        usuario = ot_db.obtener_personal_por_email(credentials.email.lower().strip())
        if not usuario:
            raise HTTPException(
                status_code=401,
                detail="Correo electrónico o contraseña incorrectos."
            )
        
        # Verificar la contraseña contra el hash almacenado
        if not verify_password(credentials.password, usuario.get("password_hash", "")):
            raise HTTPException(
                status_code=401,
                detail="Correo electrónico o contraseña incorrectos."
            )
        
        # Verificar que el usuario esté activo
        if usuario.get("estado", "Activo") == "Inactivo":
            raise HTTPException(
                status_code=403,
                detail="La cuenta está desactivada. Contacta al administrador."
            )
        
        return {
            "id_personal": usuario["id_personal"],
            "nombre": usuario["nombre"],
            "cargo": usuario.get("cargo"),
            "email": usuario["email"],
            "token": "session_ok"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- MODELOS DE CUADRILLAS Y EVIDENCIAS ---

class CuadrillaCreate(BaseModel):
    nombre: str = Field(..., description="Nombre de la cuadrilla")
    id_lider: Optional[int] = Field(None, description="ID de personal asignado como líder")

class CuadrillaResponse(BaseModel):
    id_cuadrilla: int
    nombre: str
    id_lider: Optional[int] = None
    estado: str
    nombre_lider: Optional[str] = None
    created_at: Optional[Any] = None

class GPSReportRequest(BaseModel):
    latitud: str
    longitud: str

class GPSReportResponse(BaseModel):
    id_posicion: int
    id_cuadrilla: int
    latitud: str
    longitud: str
    timestamp: Any

class OTAssignRequest(BaseModel):
    id_cuadrilla: Optional[int] = None
    fecha_planificacion: Optional[str] = None

class EvidenciaValidationRequest(BaseModel):
    estado_validacion: str = Field(..., description="Aprobado o Rechazado")
    motivo_rechazo: Optional[str] = None
    usuario_validador_id: Optional[int] = None

class EvidenciaResponse(BaseModel):
    id_evidencia: int
    id_ot: str
    tipo_evidencia: str
    url_foto: str
    latitud_foto: Optional[str] = None
    longitud_foto: Optional[str] = None
    timestamp_captura: Any
    estado_validacion: str
    motivo_rechazo: Optional[str] = None
    usuario_validador_id: Optional[int] = None
    fecha_validacion: Optional[Any] = None


# --- ENDPOINTS DE CUADRILLAS ---

@app.post("/api/cuadrillas", response_model=CuadrillaResponse, status_code=status.HTTP_201_CREATED, tags=["Cuadrillas"])
def create_cuadrilla(cuadrilla: CuadrillaCreate):
    """Crea una nueva cuadrilla."""
    try:
        res = ot_db.registrar_cuadrilla(cuadrilla.nombre, cuadrilla.id_lider)
        if not res:
            raise HTTPException(status_code=400, detail="No se pudo crear la cuadrilla.")
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cuadrillas", response_model=List[CuadrillaResponse], tags=["Cuadrillas"])
def get_cuadrillas():
    """Lista todas las cuadrillas."""
    try:
        return ot_db.listar_cuadrillas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cuadrillas/{id_cuadrilla}", response_model=CuadrillaResponse, tags=["Cuadrillas"])
def get_cuadrilla_by_id(id_cuadrilla: int):
    """Obtiene datos de una cuadrilla por su ID."""
    try:
        cuadrilla = ot_db.obtener_cuadrilla(id_cuadrilla)
        if not cuadrilla:
            raise HTTPException(status_code=404, detail=f"Cuadrilla {id_cuadrilla} no encontrada.")
        return cuadrilla
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS DE GEOLOCALIZACIÓN (GPS) ---

@app.post("/api/cuadrillas/{id_cuadrilla}/gps", tags=["Cuadrillas"])
def report_gps(id_cuadrilla: int, payload: GPSReportRequest):
    """Registra la ubicación GPS actual de una cuadrilla."""
    try:
        ok = ot_db.registrar_gps(id_cuadrilla, payload.latitud, payload.longitud)
        if not ok:
            raise HTTPException(status_code=400, detail="Error al registrar la ubicación GPS.")
        return {"message": "Ubicación GPS registrada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cuadrillas/{id_cuadrilla}/gps/ultimo", response_model=Optional[GPSReportResponse], tags=["Cuadrillas"])
def get_ultimo_gps(id_cuadrilla: int):
    """Obtiene la última ubicación GPS de una cuadrilla."""
    try:
        return ot_db.obtener_ultimo_gps(id_cuadrilla)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cuadrillas/{id_cuadrilla}/gps/historial", response_model=List[GPSReportResponse], tags=["Cuadrillas"])
def get_historial_gps(id_cuadrilla: int, limite: int = 50):
    """Obtiene el historial de ubicación GPS de una cuadrilla."""
    try:
        return ot_db.listar_historial_gps(id_cuadrilla, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS DE ASIGNACIÓN / PLANIFICACIÓN ---

@app.post("/api/ots/{id_ot}/asignar", tags=["Órdenes de Trabajo"])
def assign_ot(id_ot: str, payload: OTAssignRequest):
    """Asigna una OT a una cuadrilla y le asocia una fecha de planificación."""
    try:
        ok = ot_db.asignar_ot(id_ot, payload.id_cuadrilla, payload.fecha_planificacion)
        if not ok:
            raise HTTPException(status_code=400, detail=f"No se pudo asignar la OT '{id_ot}'.")
        return {"message": f"OT '{id_ot}' asignada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS DE EVIDENCIAS FOTOGRÁFICAS ---

@app.post("/api/ots/{id_ot}/evidencias", response_model=EvidenciaResponse, status_code=status.HTTP_201_CREATED, tags=["Evidencias"])
def upload_evidencia(
    id_ot: str,
    file: UploadFile = File(...),
    tipo_evidencia: str = Form(..., description="Debe ser 'Desplazamiento', 'Antes' o 'Despues'"),
    latitud_foto: Optional[str] = Form(None),
    longitud_foto: Optional[str] = Form(None),
    timestamp_captura: Optional[str] = Form(None)
):
    """Sube una foto de evidencia a Cloudinary y guarda la URL permanente en la base de datos."""
    try:
        # Validar tipo de evidencia
        if tipo_evidencia not in ('Desplazamiento', 'Antes', 'Despues'):
            raise HTTPException(status_code=400, detail="El tipo de evidencia debe ser 'Desplazamiento', 'Antes' o 'Despues'.")

        # Verificar que Cloudinary está configurado
        if not cloudinary_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="El servicio de almacenamiento de imágenes (Cloudinary) no está configurado. "
                       "Contacta al administrador del sistema."
            )

        # Validar existencia de la OT
        ot = ot_db.obtener_ot(id_ot)
        if not ot:
            raise HTTPException(status_code=404, detail=f"La OT '{id_ot}' no existe.")

        # Parsear fecha de captura
        t_captura = datetime.now()
        if timestamp_captura:
            try:
                t_captura = datetime.fromisoformat(timestamp_captura)
            except ValueError:
                pass

        # Leer el archivo en memoria y subir a Cloudinary
        import time
        epoch = int(time.time())
        file_bytes = file.file.read()

        upload_result = cloudinary_service.upload_evidencia(
            file_bytes=file_bytes,
            id_ot=id_ot,
            tipo_evidencia=tipo_evidencia,
            epoch=epoch
        )

        # URL pública permanente de Cloudinary (HTTPS)
        url_foto = upload_result["secure_url"]

        # Guardar en BD
        res = ot_db.subir_evidencia(id_ot, tipo_evidencia, url_foto, latitud_foto, longitud_foto, t_captura)
        if not res:
            raise HTTPException(status_code=400, detail="No se pudo registrar la evidencia en la base de datos.")

        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir la evidencia: {str(e)}")

@app.get("/api/ots/{id_ot}/evidencias", response_model=List[EvidenciaResponse], tags=["Evidencias"])
def get_evidencias_ot(id_ot: str):
    """Lista todas las evidencias registradas para una OT."""
    try:
        return ot_db.listar_evidencias_ot(id_ot)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evidencias/{id_evidencia}/validar", tags=["Evidencias"])
def validate_evidencia(id_evidencia: int, payload: EvidenciaValidationRequest):
    """Aprueba o rechaza una foto de evidencia."""
    try:
        ok = ot_db.validar_evidencia(id_evidencia, payload.estado_validacion, payload.motivo_rechazo, payload.usuario_validador_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Evidencia {id_evidencia} no encontrada o error al validar.")
        return {"message": "Evidencia validada correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
