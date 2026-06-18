const API_BASE_URL = 'http://localhost:8000/api';

export interface Elemento {
  id_elemento: string;
  nombre: string;
  tipo: 'Nodo' | 'IAO' | 'Hotspot';
  ubicacion?: string;
}

export type Priority = 'Alta' | 'Media' | 'Baja';
export type OTState = 'Abierta' | 'Despachada' | 'En Sitio' | 'Cerrada';

export interface OT {
  id_ot: string;
  id_elemento: string;
  prioridad: Priority;
  diagnostico_inicial: string;
  hora_recepcion: string;
  hora_despacho?: string;
  hora_llegada?: string;
  hora_cierre?: string;
  estado: OTState;
  // Campos adicionales del Master
  informe?: string;
  noc_gilat?: string;
  requiere?: string;
  tiene?: string;
  inicio?: string;
  fin?: string;
  inicio_1?: string;
  fin_1?: string;
  inicio_2?: string;
  fin_2?: string;
}

export interface TransitionRequest {
  timestamp?: string;
}

// --- SERVICIOS DE ELEMENTOS ---

export async function fetchElementos(): Promise<Elemento[]> {
  const response = await fetch(`${API_BASE_URL}/elementos`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener elementos');
  }
  return response.json();
}

export async function createElemento(elemento: Elemento): Promise<Elemento> {
  const response = await fetch(`${API_BASE_URL}/elementos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(elemento),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al crear elemento');
  }
  return response.json();
}

export async function deleteElemento(idElemento: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/elementos/${idElemento}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al eliminar elemento');
  }
  return response.json();
}

// --- SERVICIOS DE ÓRDENES DE TRABAJO (OTs) ---

export async function fetchOTs(estado?: string): Promise<OT[]> {
  const url = estado 
    ? `${API_BASE_URL}/ots?estado=${encodeURIComponent(estado)}` 
    : `${API_BASE_URL}/ots`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener órdenes de trabajo');
  }
  return response.json();
}

export async function fetchOTById(idOt: string): Promise<OT> {
  const response = await fetch(`${API_BASE_URL}/ots/${idOt}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener detalle de la orden');
  }
  return response.json();
}

export async function createOT(ot: Omit<OT, 'estado' | 'hora_despacho' | 'hora_llegada' | 'hora_cierre'>): Promise<OT> {
  const response = await fetch(`${API_BASE_URL}/ots`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(ot),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al crear orden de trabajo');
  }
  return response.json();
}

export async function despacharOT(idOt: string, payload?: TransitionRequest): Promise<OT> {
  const response = await fetch(`${API_BASE_URL}/ots/${idOt}/despachar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload || {}),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al despachar orden');
  }
  return response.json();
}

export async function registrarLlegadaOT(idOt: string, payload?: TransitionRequest): Promise<OT> {
  const response = await fetch(`${API_BASE_URL}/ots/${idOt}/llegada`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload || {}),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al registrar llegada');
  }
  return response.json();
}

export async function cerrarOT(idOt: string, payload?: TransitionRequest): Promise<OT> {
  const response = await fetch(`${API_BASE_URL}/ots/${idOt}/cerrar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload || {}),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al cerrar orden de trabajo');
  }
  return response.json();
}

export async function fetchRedAmazonas(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/red-amazonas`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener datos de la red Amazonas');
  }
  return response.json();
}

export interface CFM {
  item: string;
  ot: string;
  tipo: string;
  codigo: string;
  selnet: string;
  gilat: string;
  factor: string;
  inicio?: string;
  fin?: string;
  _original?: Record<string, any>;
}

export async function fetchCFMs(): Promise<CFM[]> {
  const response = await fetch(`${API_BASE_URL}/cfms`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener datos de las CFMs');
  }
  return response.json();
}
