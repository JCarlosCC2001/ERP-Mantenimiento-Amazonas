import React, { useEffect, useState } from 'react';
import { 
  fetchOTs, 
  fetchElementos, 
  fetchCFMs,
  createOT, 
  despacharOT, 
  registrarLlegadaOT, 
  cerrarOT 
} from '../services/api';
import type { CFM, Elemento, OT, Priority } from '../services/api';
import { 
  Plus, 
  Search, 
  FileText, 
  AlertCircle, 
  Clock, 
  Send, 
  MapPin, 
  CheckSquare, 
  X, 
  AlertTriangle,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
  Zap,
  Radio,
  CheckCircle2,
  Timer,
  ChevronRight,
  Calendar,
  PauseCircle,
  ShieldAlert
} from 'lucide-react';
import './OTManagerView.css';
import './RedAmazonasView.css';

const CLIENT_EMAIL = "erp-mantenimiento-amazonas@tensile-impact-499801-g7.iam.gserviceaccount.com";

type ErrorType = 
  | 'DRIVE_API_DISABLED' 
  | 'SHEETS_API_DISABLED' 
  | 'PERMISSION_DENIED' 
  | 'NOT_FOUND' 
  | 'WORKSHEET_NOT_FOUND' 
  | 'CREDENTIALS_NOT_FOUND'
  | 'GENERIC_ERROR';

interface ParsedError {
  type: ErrorType;
  message: string;
}

function parseError(rawMessage: string): ParsedError {
  const match = rawMessage.match(/^([A-Z_]+)\|(.+)$/s);
  if (match) {
    return {
      type: match[1] as ErrorType,
      message: match[2]
    };
  }
  return { type: 'GENERIC_ERROR', message: rawMessage };
}

// Icono según estado de OT
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'Abierta': return <Radio size={14} />;
    case 'Despachada': return <Send size={14} />;
    case 'En Sitio': return <MapPin size={14} />;
    case 'Cerrada': return <CheckCircle2 size={14} />;
    default: return <FileText size={14} />;
  }
};

export const OTManagerView: React.FC = () => {
  const [ots, setOts] = useState<OT[]>([]);
  const [elementos, setElementos] = useState<Elemento[]>([]);
  const [selectedOtId, setSelectedOtId] = useState<string | null>(null);
  const [selectedOt, setSelectedOt] = useState<OT | null>(null);
  // Map: ot_id -> list of CFMs
  const [cfmsMap, setCfmsMap] = useState<Record<string, CFM[]>>({});
  
  const [loading, setLoading] = useState(true);
  
  // Filtros
  const [filterEstado, setFilterEstado] = useState<string>('Todos');
  const [filterPrioridad, setFilterPrioridad] = useState<string>('Todos');
  const [searchTerm, setSearchTerm] = useState('');

  // Registro de OT
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newOt, setNewOt] = useState({
    id_ot: '',
    id_elemento: '',
    prioridad: 'Media' as Priority,
    diagnostico_inicial: '',
    hora_recepcion: ''
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Carga inicial de datos
  useEffect(() => {
    loadData();
  }, []);

  // Cargar detalle de OT seleccionada
  useEffect(() => {
    if (selectedOtId) {
      const found = ots.find(o => o.id_ot === selectedOtId);
      if (found) {
        setSelectedOt(found);
      } else {
        setSelectedOt(null);
      }
    } else {
      setSelectedOt(null);
    }
  }, [selectedOtId, ots]);

  const [parsedError, setParsedError] = useState<ParsedError | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCopyEmail = () => {
    navigator.clipboard.writeText(CLIENT_EMAIL);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  async function loadData() {
    try {
      setLoading(true);
      setParsedError(null);
      const [otData, elData, cfmData] = await Promise.all([fetchOTs(), fetchElementos(), fetchCFMs()]);
      setOts(otData);
      setElementos(elData);
      // Build a map from OT id to list of CFMs for fast lookup
      const map: Record<string, CFM[]> = {};
      for (const cfm of cfmData) {
        const key = (cfm.ot || '').toString().trim().toUpperCase();
        if (!map[key]) map[key] = [];
        map[key].push(cfm);
      }
      setCfmsMap(map);
      
      if (otData.length > 0 && !selectedOtId) {
        setSelectedOtId(otData[0].id_ot);
      }
      
    } catch (err: any) {
      const errMsg = err.message || 'Error al cargar la información operativa de órdenes de trabajo.';
      setParsedError(parseError(errMsg));
    } finally {
      setLoading(false);
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewOt(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!newOt.id_ot.trim()) {
      setFormError('El código de la OT es requerido.');
      return;
    }
    if (!newOt.id_elemento) {
      setFormError('Debe seleccionar un elemento de red para relacionar con la OT.');
      return;
    }
    if (!newOt.diagnostico_inicial.trim()) {
      setFormError('El diagnóstico inicial es requerido.');
      return;
    }

    try {
      const formattedOt = {
        id_ot: newOt.id_ot.trim(),
        id_elemento: newOt.id_elemento,
        prioridad: newOt.prioridad,
        diagnostico_inicial: newOt.diagnostico_inicial.trim(),
        hora_recepcion: newOt.hora_recepcion ? new Date(newOt.hora_recepcion).toISOString() : new Date().toISOString()
      };

      const created = await createOT(formattedOt);
      setIsModalOpen(false);
      setNewOt({
        id_ot: '',
        id_elemento: elementos.length > 0 ? elementos[0].id_elemento : '',
        prioridad: 'Media',
        diagnostico_inicial: '',
        hora_recepcion: ''
      });
      await loadData();
      setSelectedOtId(created.id_ot);
      showNotification(`Orden de Trabajo ${created.id_ot} registrada.`);
    } catch (err: any) {
      setFormError(err.message || 'Error al guardar la Orden de Trabajo. El código podría estar repetido.');
    }
  };

  const handleDespachar = async (id: string) => {
    try {
      const updated = await despacharOT(id);
      updateOtInList(updated);
      showNotification(`Cuadrilla despachada para la OT ${id}.`);
    } catch (err: any) {
      alert(`Error al despachar: ${err.message}`);
    }
  };

  const handleLlegadaSitio = async (id: string) => {
    try {
      const updated = await registrarLlegadaOT(id);
      updateOtInList(updated);
      showNotification(`Arribo a sitio registrado para la OT ${id}.`);
    } catch (err: any) {
      alert(`Error al registrar llegada: ${err.message}`);
    }
  };

  const handleCerrarOT = async (id: string) => {
    try {
      const updated = await cerrarOT(id);
      updateOtInList(updated);
      showNotification(`Orden de Trabajo ${id} cerrada satisfactoriamente.`);
    } catch (err: any) {
      alert(`Error al cerrar OT: ${err.message}`);
    }
  };

  const updateOtInList = (updated: OT) => {
    setOts(prev => prev.map(o => o.id_ot === updated.id_ot ? updated : o));
  };

  const showNotification = (msg: string) => {
    setActionSuccess(msg);
    setTimeout(() => setActionSuccess(null), 3000);
  };

  // Helper de badges y clases
  const getPriorityBadgeClass = (prio: string) => {
    switch (prio) {
      case 'Alta': return 'badge badge-alta';
      case 'Media': return 'badge badge-media';
      default: return 'badge badge-baja';
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'Abierta': return 'badge badge-abierta';
      case 'Despachada': return 'badge badge-despachada';
      case 'En Sitio': return 'badge badge-en-sitio';
      default: return 'badge badge-cerrada';
    }
  };

  // Color del borde izquierdo por prioridad
  const getPriorityBorderColor = (prio: string) => {
    switch (prio) {
      case 'Alta': return 'var(--color-danger, #ef4444)';
      case 'Media': return 'var(--color-warning, #f59e0b)';
      default: return 'rgba(99, 102, 241, 0.6)';
    }
  };

  const formatTime = (isoString?: string) => {
    if (!isoString) return '—';
    try {
      return new Date(isoString).toLocaleString('es-PE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch { return '—'; }
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
    if (elementos.length > 0 && !newOt.id_elemento) {
      setNewOt(prev => ({
        ...prev,
        id_elemento: elementos[0].id_elemento
      }));
    }
  };

  // Filtrado
  const filteredOts = ots.filter(ot => {
    const matchEstado = filterEstado === 'Todos' || ot.estado === filterEstado;
    const matchPrioridad = filterPrioridad === 'Todos' || ot.prioridad === filterPrioridad;
    const matchSearch = ot.id_ot.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        ot.id_elemento.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        ot.diagnostico_inicial.toLowerCase().includes(searchTerm.toLowerCase());
    return matchEstado && matchPrioridad && matchSearch;
  });

  // Métricas rápidas
  const totalOts = ots.length;
  const otsAbiertas = ots.filter(o => o.estado === 'Abierta').length;
  const otsPendientes = ots.filter(o => ['Abierta', 'Despachada', 'En Sitio'].includes(o.estado)).length;
  const otsCerradas = ots.filter(o => o.estado === 'Cerrada').length;

  return (
    <div className="ot-view">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Órdenes de Trabajo (OT)</h1>
          <p>Supervisa el despacho, arribo a sitio y cierre de reportes de mantenimiento.</p>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={handleOpenModal}
          disabled={elementos.length === 0}
          title={elementos.length === 0 ? 'Debe registrar al menos un elemento de red primero' : 'Crear nueva OT'}
        >
          <Plus size={18} />
          Crear OT
        </button>
      </div>

      {actionSuccess && (
        <div className="alert-success-banner">
          <CheckCircle2 size={18} style={{ color: 'var(--color-success)' }} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Cargando flujo de trabajo desde Google Sheets...</p>
        </div>
      ) : parsedError ? (
        (() => {
          const isGoogleError = [
            'DRIVE_API_DISABLED', 
            'SHEETS_API_DISABLED', 
            'PERMISSION_DENIED', 
            'NOT_FOUND', 
            'WORKSHEET_NOT_FOUND', 
            'CREDENTIALS_NOT_FOUND'
          ].includes(parsedError.type);

          if (isGoogleError) {
            const isApiDisabled = parsedError.type === 'DRIVE_API_DISABLED' || parsedError.type === 'SHEETS_API_DISABLED';
            const isNotFound = parsedError.type === 'NOT_FOUND' || parsedError.type === 'PERMISSION_DENIED';
            const isWrongTab = parsedError.type === 'WORKSHEET_NOT_FOUND';

            return (
              <div className="card error-setup-card" style={{ maxWidth: '800px', margin: '2rem auto' }}>
                <div className="error-setup-header">
                  <AlertTriangle size={36} className="text-warning animate-pulse" />
                  <h3>
                    {isApiDisabled ? 'API de Google Cloud no habilitada' :
                     isNotFound ? 'Acceso no configurado a Google Sheets' :
                     isWrongTab ? 'Pestaña Master o RED A. no encontrada' :
                     'Error de Integración con Google Sheets'}
                  </h3>
                </div>

                <p className="error-setup-desc">{parsedError.message.split('Habilítala')[0]}</p>

                {parsedError.type === 'DRIVE_API_DISABLED' && (
                  <div className="setup-instructions">
                    <h4>Opciones para resolver este problema:</h4>
                    <div className="option-blocks">
                      <div className="option-block">
                        <div className="option-label">
                          <span className="option-badge">Opción A</span>
                          <strong>Habilitar la Google Drive API (Recomendado)</strong>
                        </div>
                        <ol>
                          <li>Abre la consola de Google Cloud de tu proyecto.</li>
                          <li>Habilita la <strong>Google Drive API</strong>.</li>
                          <li>Espera 2 minutos y reintenta.</li>
                        </ol>
                        <a 
                          href="https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=690005910043" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="btn btn-secondary btn-link-external"
                        >
                          <ExternalLink size={14} />
                          Ir a Google Cloud Console → Drive API
                        </a>
                      </div>
                      <div className="option-block">
                        <div className="option-label">
                          <span className="option-badge option-badge-alt">Opción B</span>
                          <strong>Usar URL directa (Evita la Drive API)</strong>
                        </div>
                        <ol>
                          <li>Copia la URL de tu documento en Google Sheets.</li>
                          <li>Pégala como valor de <code>SPREADSHEET_URL</code> en <code>backend/sheets_service.py</code>.</li>
                          <li>Reinicia el backend.</li>
                        </ol>
                      </div>
                    </div>
                  </div>
                )}

                {parsedError.type === 'SHEETS_API_DISABLED' && (
                  <div className="setup-instructions">
                    <h4>Habilitar la Google Sheets API:</h4>
                    <ol>
                      <li>Abre la consola de Google Cloud de tu proyecto.</li>
                      <li>Habilita la <strong>Google Sheets API</strong>.</li>
                      <li>Espera 2 minutos e inténtalo de nuevo.</li>
                    </ol>
                    <a 
                      href="https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=690005910043"
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-link-external"
                    >
                      <ExternalLink size={14} />
                      Ir a Google Cloud Console → Sheets API
                    </a>
                  </div>
                )}

                {(isNotFound) && (
                  <div className="setup-instructions">
                    <h4>Comparte el documento con la cuenta de servicio del ERP:</h4>
                    <ol>
                      <li>Abre tu hoja <strong>'ERP-Mantenimiento-Amazonas'</strong> en Google Sheets.</li>
                      <li>Haz clic en <strong>Compartir</strong>.</li>
                      <li>Agrega el siguiente correo como <strong>Lector</strong> o <strong>Editor</strong>:</li>
                    </ol>
                    <div className="email-copy-box">
                      <code>{CLIENT_EMAIL}</code>
                      <button className="btn btn-secondary btn-copy" onClick={handleCopyEmail}>
                        {copied ? <Check size={16} className="text-success" /> : <Copy size={16} />}
                        {copied ? 'Copiado' : 'Copiar'}
                      </button>
                    </div>
                  </div>
                )}

                {isWrongTab && (
                  <div className="setup-instructions">
                    <h4>Nombre de pestaña no encontrado:</h4>
                    <p style={{ color: '#9ca3af', margin: 0 }}>
                      Asegúrate de que la hoja de cálculo <strong>'ERP-Mantenimiento-Amazonas'</strong> contenga 
                      las pestañas llamadas exactamente <strong>RED A.</strong> y <strong>Master</strong>.
                    </p>
                  </div>
                )}

                <button className="btn btn-primary" onClick={loadData} style={{ marginTop: '1.5rem' }}>
                  <RefreshCw size={16} style={{ marginRight: '8px' }} />
                  Reintentar Conexión
                </button>
              </div>
            );
          }

          return (
            <div className="error-card card" style={{ maxWidth: '600px', margin: '2rem auto' }}>
              <AlertCircle size={48} className="error-icon" />
              <h3>Error de Carga</h3>
              <p>{parsedError.message}</p>
              <button className="btn btn-primary" onClick={loadData}>Reintentar</button>
            </div>
          );
        })()
      ) : (
        <>
          {/* Métricas rápidas */}
          <div className="ot-metrics-strip">
            <div className="ot-metric-pill">
              <FileText size={15} className="text-muted" />
              <span className="ot-metric-num">{totalOts}</span>
              <span className="ot-metric-lbl">Total OTs</span>
            </div>
            <div className="ot-metric-divider" />
            <div className="ot-metric-pill">
              <Radio size={15} style={{ color: '#60a5fa' }} />
              <span className="ot-metric-num" style={{ color: '#60a5fa' }}>{otsAbiertas}</span>
              <span className="ot-metric-lbl">Abiertas</span>
            </div>
            <div className="ot-metric-divider" />
            <div className="ot-metric-pill">
              <Timer size={15} style={{ color: '#f59e0b' }} />
              <span className="ot-metric-num" style={{ color: '#f59e0b' }}>{otsPendientes}</span>
              <span className="ot-metric-lbl">En Proceso</span>
            </div>
            <div className="ot-metric-divider" />
            <div className="ot-metric-pill">
              <CheckCircle2 size={15} style={{ color: '#34d399' }} />
              <span className="ot-metric-num" style={{ color: '#34d399' }}>{otsCerradas}</span>
              <span className="ot-metric-lbl">Cerradas</span>
            </div>
          </div>

          <div className={`ot-layout ${selectedOt ? 'has-selection' : ''}`}>
            
            {/* SECCIÓN DE LA IZQUIERDA: BUSCADOR Y LISTA DE OTS */}
            <div className="ot-list-section">
              <div className="card ot-filters-card">
                <div className="search-wrapper filter-search">
                  <Search size={18} className="search-icon" />
                  <input 
                    type="text" 
                    placeholder="Buscar OT o nodo..." 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                  />
                </div>

                {/* Filtros de Estado */}
                <div className="ot-filters">
                  <span className="filter-label-text">Estado:</span>
                  {['Todos', 'Abierta', 'Despachada', 'En Sitio', 'Cerrada'].map(est => (
                    <button
                      key={est}
                      className={`filter-btn ${filterEstado === est ? 'active' : ''}`}
                      onClick={() => setFilterEstado(est)}
                    >
                      {est}
                    </button>
                  ))}
                </div>

                {/* Filtros de Prioridad */}
                <div className="ot-filters">
                  <span className="filter-label-text">Prioridad:</span>
                  {['Todos', 'Alta', 'Media', 'Baja'].map(prio => (
                    <button
                      key={prio}
                      className={`filter-btn ${filterPrioridad === prio ? 'active' : ''}`}
                      onClick={() => setFilterPrioridad(prio)}
                    >
                      {prio}
                    </button>
                  ))}
                </div>
              </div>

              {/* Contador de resultados */}
              <div className="ot-list-count">
                Mostrando {filteredOts.length} de {ots.length} órdenes de trabajo
              </div>

              {/* Lista de OTs */}
              <div className="ot-items-container">
                {filteredOts.length === 0 ? (
                  <div className="card empty-list-card">
                    <FileText size={36} className="text-muted" />
                    <p>No se encontraron Órdenes de Trabajo con los filtros seleccionados.</p>
                  </div>
                ) : (
                  filteredOts.map(ot => (
                    <div
                      key={ot.id_ot}
                      className={`card ot-list-item ${selectedOtId === ot.id_ot ? 'selected' : ''}`}
                      onClick={() => setSelectedOtId(ot.id_ot)}
                      style={{ borderLeftColor: selectedOtId === ot.id_ot ? getPriorityBorderColor(ot.prioridad) : 'transparent' }}
                    >
                      <div className="ot-item-left">
                        <div className="ot-item-header">
                          <span className="ot-id-label">{ot.id_ot}</span>
                          <span className="tag-tipo-small">{ot.id_elemento}</span>
                        </div>
                        {/* Badges de informes y CFMs */}
                        <div className="ot-item-badges">
                          {ot.informe && ['si','sii','yes'].includes(ot.informe.toLowerCase()) && (
                            <span className="ot-badge-sm ot-badge-selnet">SELNET</span>
                          )}
                          {ot.noc_gilat && ot.noc_gilat.trim() !== '' && (
                            <span className="ot-badge-sm ot-badge-gilat">GILAT</span>
                          )}
                          {(() => {
                            const key = ot.id_ot.trim().toUpperCase();
                            const cnt = (cfmsMap[key] || []).length;
                            return cnt > 0 ? (
                              <span className="ot-badge-sm ot-badge-cfm">
                                <PauseCircle size={9} /> {cnt} CFM{cnt > 1 ? 's' : ''}
                              </span>
                            ) : null;
                          })()}
                        </div>
                        {/* Fecha de recepción en la tarjeta */}
                        <div className="ot-item-date">
                          <Calendar size={11} />
                          <span>{formatTime(ot.hora_recepcion)}</span>
                        </div>
                      </div>
                      <div className="ot-item-right">
                        <span className={getPriorityBadgeClass(ot.prioridad)}>{ot.prioridad}</span>
                        <span className={`${getStatusBadgeClass(ot.estado)} badge-with-icon`}>
                          {getStatusIcon(ot.estado)}
                          {ot.estado}
                        </span>
                        <ChevronRight size={14} className="ot-item-chevron" />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* SECCIÓN DE LA DERECHA: DETALLE Y LÍNEA DE TIEMPO INTERACTIVA */}
            <div className="ot-detail-section">
              {selectedOt ? (
                <div className="detail-card-premium ot-detail-premium animate-fade-in">

                  {/* Header premium con botón de cierre */}
                  <div className="detail-header-premium">
                    <div className="ot-detail-title-block">
                      <div className="ot-detail-icon-wrapper">
                        <FileText size={18} />
                      </div>
                      <div>
                        <span style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.07em', fontWeight: 600 }}>
                          Orden de Trabajo
                        </span>
                        <h2 style={{ margin: '2px 0 0 0', fontSize: '1.35rem', fontWeight: 800, color: '#ffffff' }}>
                          {selectedOt.id_ot}
                        </h2>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span className={`${getStatusBadgeClass(selectedOt.estado)} badge-with-icon`}>
                        {getStatusIcon(selectedOt.estado)}
                        {selectedOt.estado}
                      </span>
                      <button className="btn-close-detail" onClick={() => setSelectedOtId(null)} title="Cerrar detalle">
                        <X size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Cuerpo del detalle */}
                  <div className="detail-body-premium ot-detail-body">

                    {/* Metadatos rápidos */}
                    <div className="ot-meta-grid">
                      <div className="detail-field">
                        <span className="field-label">Elemento Asociado</span>
                        <span className="field-value">{selectedOt.id_elemento}</span>
                      </div>
                      <div className="detail-field">
                        <span className="field-label">Severidad / Prioridad</span>
                        <span className={getPriorityBadgeClass(selectedOt.prioridad)} style={{ marginTop: '4px' }}>
                          {selectedOt.prioridad}
                        </span>
                      </div>
                      <div className="detail-field">
                        <span className="field-label">Recepcionado</span>
                        <span className="field-value" style={{ fontSize: '0.85rem' }}>
                          {formatTime(selectedOt.hora_recepcion)}
                        </span>
                      </div>
                    </div>

                    {/* Diagnóstico y documentos */}
                    <div className="detail-field ot-docs-panel" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', gap: '10px' }}>
                      <span className="field-label">Documentos y Reportes</span>
                      <div className="ot-docs-badges">
                        {/* Informe SELNET */}
                        {selectedOt.informe && ['si','sii','yes'].includes(selectedOt.informe.toLowerCase()) ? (
                          <div className="ot-doc-badge ot-doc-badge--yes">
                            <CheckCircle2 size={15} />
                            <span>Informe SELNET</span>
                          </div>
                        ) : (
                          <div className="ot-doc-badge ot-doc-badge--no">
                            <Clock size={15} />
                            <span>Sin Informe SELNET</span>
                          </div>
                        )}
                        {/* Informe GILAT */}
                        {selectedOt.noc_gilat && selectedOt.noc_gilat.trim() !== '' ? (
                          <div className="ot-doc-badge ot-doc-badge--yes">
                            <CheckCircle2 size={15} />
                            <span>Informe GILAT</span>
                          </div>
                        ) : (
                          <div className="ot-doc-badge ot-doc-badge--no">
                            <Clock size={15} />
                            <span>Sin Informe GILAT</span>
                          </div>
                        )}
                        {/* CFMs */}
                        {(() => {
                          const key = selectedOt.id_ot.trim().toUpperCase();
                          const cfmsForOt = cfmsMap[key] || [];
                          return cfmsForOt.length > 0 ? (
                            <div className="ot-doc-badge ot-doc-badge--cfm">
                              <PauseCircle size={15} />
                              <span>{cfmsForOt.length} CFM{cfmsForOt.length > 1 ? 's' : ''} (Parada{cfmsForOt.length > 1 ? 's' : ''} de Reloj)</span>
                            </div>
                          ) : (
                            <div className="ot-doc-badge ot-doc-badge--none">
                              <ShieldAlert size={15} />
                              <span>Sin CFMs</span>
                            </div>
                          );
                        })()}
                      </div>
                      {selectedOt.diagnostico_inicial && (
                        <p style={{ margin: '6px 0 0 0', fontSize: '0.85rem', color: '#9ca3af', lineHeight: 1.55, whiteSpace: 'pre-wrap', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '8px' }}>
                          {selectedOt.diagnostico_inicial}
                        </p>
                      )}
                    </div>

                    {/* Línea de tiempo */}
                    <div>
                      <h4 className="detail-section-title">Bitácora de Estados</h4>
                      <div className="ot-timeline">

                        {/* Paso 1: Recibida */}
                        <div className="ot-timeline-step completed">
                          <div className="ot-tl-marker">
                            <CheckCircle2 size={14} />
                          </div>
                          <div className="ot-tl-connector" />
                          <div className="ot-tl-content">
                            <span className="ot-tl-title">Orden Recibida</span>
                            <span className="ot-tl-time">{formatTime(selectedOt.hora_recepcion)}</span>
                          </div>
                        </div>

                        {/* Paso 2: Despachada */}
                        <div className={`ot-timeline-step ${
                          ['Despachada', 'En Sitio', 'Cerrada'].includes(selectedOt.estado) ? 'completed' :
                          selectedOt.estado === 'Abierta' ? 'active' : ''
                        }`}>
                          <div className="ot-tl-marker">
                            <Send size={14} />
                          </div>
                          <div className="ot-tl-connector" />
                          <div className="ot-tl-content">
                            <span className="ot-tl-title">Cuadrilla Despachada</span>
                            <span className="ot-tl-time">{formatTime(selectedOt.hora_despacho)}</span>
                          </div>
                        </div>

                        {/* Paso 3: En Sitio */}
                        <div className={`ot-timeline-step ${
                          ['En Sitio', 'Cerrada'].includes(selectedOt.estado) ? 'completed' :
                          selectedOt.estado === 'Despachada' ? 'active' : ''
                        }`}>
                          <div className="ot-tl-marker">
                            <MapPin size={14} />
                          </div>
                          <div className="ot-tl-connector" />
                          <div className="ot-tl-content">
                            <span className="ot-tl-title">Personal en Sitio</span>
                            <span className="ot-tl-time">{formatTime(selectedOt.hora_llegada)}</span>
                          </div>
                        </div>

                        {/* Paradas de Reloj (CFMs) de la OT */}
                        {(() => {
                          const key = selectedOt.id_ot.trim().toUpperCase();
                          const cfmsForOt = cfmsMap[key] || [];
                          if (cfmsForOt.length === 0) return null;
                          return cfmsForOt.map((cfm, idx) => (
                            <div key={`cfm-stop-${idx}`} className="ot-timeline-step cfm-stop">
                              <div className="ot-tl-marker cfm-marker">
                                <PauseCircle size={14} />
                              </div>
                              <div className="ot-tl-connector" />
                              <div className="ot-tl-content">
                                <span className="ot-tl-title cfm-title">
                                  ⏸ Parada de Reloj — CFM {idx + 1}
                                </span>
                                <span className="ot-tl-time">
                                  {cfm.inicio ? cfm.inicio : '—'}
                                  {cfm.fin ? ` → ${cfm.fin}` : cfm.inicio ? ' (en curso)' : ''}
                                </span>
                                {cfm.factor && (
                                  <span className="ot-tl-subtitle">{cfm.factor}</span>
                                )}
                              </div>
                            </div>
                          ));
                        })()}


                        {/* Paso 4: Cerrada */}
                        <div className={`ot-timeline-step ${
                          selectedOt.estado === 'Cerrada' ? 'completed' :
                          selectedOt.estado === 'En Sitio' ? 'active' : ''
                        } last-step`}>
                          <div className="ot-tl-marker">
                            <CheckSquare size={14} />
                          </div>
                          <div className="ot-tl-content">
                            <span className="ot-tl-title">OT Cerrada</span>
                            <span className="ot-tl-time">{formatTime(selectedOt.hora_cierre)}</span>
                          </div>
                        </div>

                      </div>
                    </div>

                    {/* Panel de acciones */}
                    <div className="ot-action-panel">
                      <span className="detail-section-title" style={{ marginBottom: 0 }}>Controles Operativos</span>
                      
                      {selectedOt.estado === 'Abierta' && (
                        <button 
                          className="btn btn-primary ot-action-btn"
                          onClick={() => handleDespachar(selectedOt.id_ot)}
                        >
                          <Send size={16} />
                          Despachar Cuadrilla de Mantenimiento
                          <Zap size={14} style={{ marginLeft: 'auto', opacity: 0.7 }} />
                        </button>
                      )}

                      {selectedOt.estado === 'Despachada' && (
                        <button 
                          className="btn btn-primary ot-action-btn"
                          style={{ background: 'linear-gradient(135deg, #8b5cf6, #6366f1)' }}
                          onClick={() => handleLlegadaSitio(selectedOt.id_ot)}
                        >
                          <MapPin size={16} />
                          Registrar Llegada a Sitio (Arribo)
                          <Zap size={14} style={{ marginLeft: 'auto', opacity: 0.7 }} />
                        </button>
                      )}

                      {selectedOt.estado === 'En Sitio' && (
                        <button 
                          className="btn btn-primary btn-success-transition ot-action-btn"
                          onClick={() => handleCerrarOT(selectedOt.id_ot)}
                        >
                          <CheckSquare size={16} />
                          Finalizar y Cerrar Orden de Trabajo
                          <Zap size={14} style={{ marginLeft: 'auto', opacity: 0.7 }} />
                        </button>
                      )}

                      {selectedOt.estado === 'Cerrada' && (
                        <div className="closed-ot-success">
                          <CheckSquare size={20} className="text-success" />
                          <span>El servicio de mantenimiento de esta OT fue finalizado y cerrado con éxito.</span>
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              ) : (
                <div className="card no-selected-card">
                  <FileText size={48} className="text-muted" />
                  <h3>Detalle de la Orden</h3>
                  <p>Selecciona una orden de trabajo de la lista para gestionar su flujo e historial de estados.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Modal de Registro de OT */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Crear Orden de Trabajo (OT)</h3>
              <button className="modal-close" onClick={() => setIsModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              {formError && (
                <div className="form-error-msg">
                  <AlertTriangle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Código Único de OT</label>
                <input 
                  type="text" 
                  name="id_ot" 
                  value={newOt.id_ot}
                  onChange={handleInputChange}
                  placeholder="Ej. OT-2026-0005"
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Elemento de Red (Asociado)</label>
                <select 
                  name="id_elemento" 
                  value={newOt.id_elemento}
                  onChange={handleInputChange}
                  className="form-select"
                  required
                >
                  {elementos.map(el => (
                    <option key={el.id_elemento} value={el.id_elemento}>
                      [{el.tipo}] {el.id_elemento} - {el.nombre}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Severidad / Prioridad</label>
                <select 
                  name="prioridad" 
                  value={newOt.prioridad}
                  onChange={handleInputChange}
                  className="form-select"
                >
                  <option value="Alta">Alta (Corte de servicio / Crítico)</option>
                  <option value="Media">Media (Degradación / Falla parcial)</option>
                  <option value="Baja">Baja (Mantenimiento preventivo)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Fecha/Hora de Recepción (Opcional)</label>
                <input 
                  type="datetime-local" 
                  name="hora_recepcion" 
                  value={newOt.hora_recepcion}
                  onChange={handleInputChange}
                  className="form-input"
                />
                <span className="form-input-help">Dejar en blanco para registrar con la fecha/hora actual.</span>
              </div>

              <div className="form-group">
                <label className="form-label">Diagnóstico Operativo Inicial</label>
                <textarea 
                  name="diagnostico_inicial" 
                  value={newOt.diagnostico_inicial}
                  onChange={handleInputChange}
                  placeholder="Describa brevemente la anomalía reportada o el trabajo a realizar..."
                  className="form-textarea"
                  rows={3}
                  required
                />
              </div>

              <div className="modal-actions">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Registrar Orden
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
