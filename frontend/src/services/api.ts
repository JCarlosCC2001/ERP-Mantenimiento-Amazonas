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
  id_cuadrilla?: number;
  fecha_planificacion?: string;
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

// --- SERVICIOS DE PERSONAL Y AUTENTICACIÓN ---

export interface Personal {
  id_personal: number;
  nombre: string;
  cargo?: string;
  cm?: string;
  estado?: string;
  email: string;
}

export interface AuthUser {
  id_personal: number;
  nombre: string;
  cargo?: string;
  email: string;
  token: string;
}

export async function loginUser(email: string, password: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Correo electrónico o contraseña incorrectos.');
  }
  return response.json();
}

export async function fetchPersonal(): Promise<Personal[]> {
  const response = await fetch(`${API_BASE_URL}/personal`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener el personal');
  }
  return response.json();
}

export async function updatePersonal(
  id: number,
  datos: Partial<Omit<Personal, 'id_personal' | 'email'>>
): Promise<Personal> {
  const response = await fetch(`${API_BASE_URL}/personal/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al actualizar el personal');
  }
  return response.json();
}

// --- SERVICIOS DE CUADRILLAS Y PLANIFICACIÓN ---

export interface Cuadrilla {
  id_cuadrilla: number;
  nombre: string;
  id_lider?: number;
  estado: string;
  nombre_lider?: string;
  created_at?: string;
}

export interface EvidenciaOT {
  id_evidencia: number;
  id_ot: string;
  tipo_evidencia: 'Desplazamiento' | 'Antes' | 'Despues';
  url_foto: string;
  latitud_foto?: string;
  longitud_foto?: string;
  timestamp_captura: string;
  estado_validacion: 'Pendiente' | 'Aprobado' | 'Rechazado';
  motivo_rechazo?: string;
  usuario_validador_id?: number;
  fecha_validacion?: string;
}

export async function fetchCuadrillas(): Promise<Cuadrilla[]> {
  const response = await fetch(`${API_BASE_URL}/cuadrillas`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener las cuadrillas');
  }
  return response.json();
}

export async function createCuadrilla(nombre: string, idLider?: number): Promise<Cuadrilla> {
  const response = await fetch(`${API_BASE_URL}/cuadrillas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nombre, id_lider: idLider }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al crear la cuadrilla');
  }
  return response.json();
}

export async function assignOT(idOt: string, idCuadrilla: number | null, fechaPlanificacion: string | null): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/ots/${idOt}/assign` || `${API_BASE_URL}/ots/${idOt}/asignar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_cuadrilla: idCuadrilla, fecha_planificacion: fechaPlanificacion }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al asignar la orden');
  }
  return response.json();
}

// --- SERVICIOS DE EVIDENCIAS FOTOGRÁFICAS ---

export async function fetchEvidenciasOT(idOt: string): Promise<EvidenciaOT[]> {
  const response = await fetch(`${API_BASE_URL}/ots/${idOt}/evidencias`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al obtener las evidencias');
  }
  return response.json();
}

export async function uploadEvidenciaOT(
  idOt: string,
  file: File,
  tipoEvidencia: 'Desplazamiento' | 'Antes' | 'Despues',
  latitud?: string,
  longitud?: string,
  timestampCaptura?: string
): Promise<EvidenciaOT> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tipo_evidencia', tipoEvidencia);
  if (latitud) formData.append('latitud_foto', latitud);
  if (longitud) formData.append('longitud_foto', longitud);
  if (timestampCaptura) formData.append('timestamp_captura', timestampCaptura);

  const response = await fetch(`${API_BASE_URL}/ots/${idOt}/evidencias`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al subir la evidencia');
  }
  return response.json();
}

export async function validateEvidenciaOT(
  idEvidencia: number,
  estadoValidacion: 'Aprobado' | 'Rechazado',
  motivoRechazo?: string,
  usuarioValidadorId?: number
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/evidencias/${idEvidencia}/validar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      estado_validacion: estadoValidacion,
      motivo_rechazo: motivoRechazo,
      usuario_validador_id: usuarioValidadorId,
    }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Error al validar la evidencia');
  }
  return response.json();
}
