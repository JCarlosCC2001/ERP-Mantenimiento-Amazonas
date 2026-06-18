from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any, Dict
from ot_manager import OTManager
from sheets_service import sheets_service

app = FastAPI(
    title="ERP Mantenimiento Amazonas API",
    description="API para la gestión de Órdenes de Trabajo, Paradas de Reloj e Inventario de Amazonas",
    version="1.0.0"
)

# Configuración de CORS para permitir la conexión desde el frontend (Vite por defecto corre en 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desarrollo permitimos todos, se puede restringir a http://localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar gestor de base de datos
ot_db = OTManager()

# --- MODELOS PYDANTIC ---

class ElementoCreate(BaseModel):
    id_elemento: str = Field(..., description="ID único del elemento (ej. NOD-001, IAO-102)")
    nombre: str = Field(..., description="Nombre descriptivo del elemento")
    tipo: str = Field(..., description="Debe ser 'Nodo', 'IAO' o 'Hotspot'")
    ubicacion: Optional[str] = Field(None, description="Distrito o coordenadas de ubicación")

class ElementoResponse(BaseModel):
    id_elemento: str
    nombre: str
    tipo: str
    ubicacion: Optional[str]

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

class TransitionRequest(BaseModel):
    timestamp: Optional[datetime] = Field(None, description="Fecha/hora del cambio de estado. Por defecto es ahora")


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
    ubicacion = str(get_val(["ubicacion", "ubicación", "distrito", "provincia", "direccion", "dirección"], "") or "").strip()

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
        "ubicacion": ubicacion
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
    """Obtiene la lista de elementos mapeados directamente desde la hoja de Google Sheets (RED A.)."""
    try:
        raw_rows = sheets_service.obtener_datos_red()
        # Filtrar filas vacías
        filtered_rows = [row for row in raw_rows if any(str(v).strip() for v in row.values())]
        return [map_row_to_elemento(row) for row in filtered_rows]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener catálogo de elementos desde Sheets: {str(e)}")

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
    """Obtiene la lista de OTs mapeada directamente desde la hoja de Google Sheets (Master)."""
    try:
        raw_rows = sheets_service.obtener_datos_master()
        # Filtrar filas vacías
        filtered_rows = [row for row in raw_rows if any(str(v).strip() for v in row.values())]
        mapped_ots = [map_row_to_ot(row) for row in filtered_rows]
        # Filtrar aquellas que no tengan número de OT (id_ot vacío)
        mapped_ots = [ot for ot in mapped_ots if ot["id_ot"] and str(ot["id_ot"]).strip()]
        # Invertir el orden para mostrar las más recientes primero
        mapped_ots.reverse()
        if estado:
            mapped_ots = [ot for ot in mapped_ots if ot["estado"].lower() == estado.lower()]
        return mapped_ots
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener OTs desde Google Sheets: {str(e)}")

@app.get("/api/ots/{id_ot}", response_model=OTResponse, tags=["Órdenes de Trabajo"])
def get_ot(id_ot: str):
    """Obtiene la información detallada de una OT específica desde Sheets."""
    try:
        raw_rows = sheets_service.obtener_datos_master()
        filtered_rows = [row for row in raw_rows if any(str(v).strip() for v in row.values())]
        mapped_ots = [map_row_to_ot(row) for row in filtered_rows]
        # Filtrar las que tienen número
        mapped_ots = [ot for ot in mapped_ots if ot["id_ot"] and str(ot["id_ot"]).strip()]
        
        ot = next((ot for ot in mapped_ots if ot["id_ot"] == id_ot), None)
        if not ot:
            raise HTTPException(status_code=404, detail=f"La OT '{id_ot}' no fue encontrada en la hoja Master.")
        return ot
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    """Obtiene los datos de los nodos de la red desde Google Sheets (RED. AMEX)."""
    try:
        return sheets_service.obtener_datos_red()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINTS CFMs (GOOGLE SHEETS) ---

def map_row_to_cfm(row: Dict[str, Any]) -> Dict[str, Any]:
    def get_val(keys_to_search: List[str], default: Any = "") -> Any:
        for k in keys_to_search:
            for row_k in row.keys():
                if row_k.strip().lower() == k.lower():
                    return row[row_k]
        return default

    item = str(get_val(["item", "nro", "no", "id"], "") or "").strip()
    ot = str(get_val(["ot", "orden de trabajo", "nro_ot", "número ot", "nro ot"], "") or "").strip()
    tipo = str(get_val(["tipo", "type"], "") or "").strip()
    codigo = str(get_val(["codigo", "código", "cod", "cod_nodo", "código nodo", "codigo nodo"], "") or "").strip()
    
    selnet = str(get_val([
        "selnet", 
        "estado de cfm en selnet", 
        "estado selnet", 
        "cfm selnet", 
        "estado de cfm selnet",
        "cfm en selnet"
    ], "") or "").strip()
    
    gilat = str(get_val([
        "gilat", 
        "estado de cfm en gilat", 
        "estado gilat", 
        "cfm gilat", 
        "estado de cfm gilat",
        "cfm en gilat"
    ], "") or "").strip()
    
    factor = str(get_val(["factor", "factor de descuento", "factor_descuento", "descuento"], "") or "").strip()
    inicio = str(get_val(["inicio", "fecha inicio", "fecha_inicio", "f. inicio"], "") or "").strip()
    fin = str(get_val(["fin", "fecha fin", "fecha_fin", "f. fin", "fecha termino"], "") or "").strip()

    return {
        "item": item,
        "ot": ot,
        "tipo": tipo,
        "codigo": codigo,
        "selnet": selnet,
        "gilat": gilat,
        "factor": factor,
        "inicio": inicio,
        "fin": fin,
        "_original": row
    }

@app.get("/api/cfms", response_model=List[Dict[str, Any]], tags=["CFMs"])
def get_cfms():
    """Obtiene los datos de las CFMs desde Google Sheets (CFMs)."""
    try:
        raw_rows = sheets_service.obtener_datos_cfms()
        # Filtrar filas vacías
        filtered_rows = [row for row in raw_rows if any(str(v).strip() for v in row.values())]
        return [map_row_to_cfm(row) for row in filtered_rows]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de CFMs: {str(e)}")

