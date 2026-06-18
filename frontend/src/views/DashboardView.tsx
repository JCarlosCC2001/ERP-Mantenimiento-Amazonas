import React, { useEffect, useState } from 'react';
import { fetchElementos, fetchOTs } from '../services/api';
import type { Elemento, OT } from '../services/api';
import { Radio, AlertTriangle, FileText, CheckCircle2, Clock, RefreshCw, Copy, Check, ExternalLink } from 'lucide-react';
import './DashboardView.css';
import './RedAmazonasView.css'; // Reutilizar estilos de la vista de Red para el ErrorCard

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

export const DashboardView: React.FC = () => {
  const [elementos, setElementos] = useState<Elemento[]>([]);
  const [ots, setOts] = useState<OT[]>([]);
  const [loading, setLoading] = useState(true);
  const [parsedError, setParsedError] = useState<ParsedError | null>(null);
  const [copied, setCopied] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setParsedError(null);
      const [elData, otData] = await Promise.all([fetchElementos(), fetchOTs()]);
      setElementos(elData);
      setOts(otData);
    } catch (err: any) {
      const errMsg = err.message || 'Error al conectar con la base de datos de Amazonas.';
      setParsedError(parseError(errMsg));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCopyEmail = () => {
    navigator.clipboard.writeText(CLIENT_EMAIL);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Cargando información del ERP Amazonas desde Google Sheets...</p>
      </div>
    );
  }

  if (parsedError) {
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
        <div className="dashboard-view" style={{ padding: '2rem' }}>
          <div className="card error-setup-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
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
        </div>
      );
    }

    // Error de backend general
    return (
      <div className="error-card card">
        <AlertTriangle size={48} className="error-icon" />
        <h3>Error de Conexión</h3>
        <p>{parsedError.message}</p>
        <button className="btn btn-primary" onClick={loadData}>Reintentar</button>
      </div>
    );
  }

  // Cálculos estadísticos
  const totalElementos = elementos.length;
  const totalOts = ots.length;
  
  const nodosCount = elementos.filter(e => e.tipo === 'Nodo').length;
  const iaoCount = elementos.filter(e => e.tipo === 'IAO').length;
  const hotspotCount = elementos.filter(e => e.tipo === 'Hotspot').length;

  const otsAbiertas = ots.filter(o => o.estado === 'Abierta').length;
  const otsDespachadas = ots.filter(o => o.estado === 'Despachada').length;
  const otsEnSitio = ots.filter(o => o.estado === 'En Sitio').length;
  const otsCerradas = ots.filter(o => o.estado === 'Cerrada').length;
  const otsPendientes = totalOts - otsCerradas;

  const otsAlta = ots.filter(o => o.prioridad === 'Alta').length;
  const otsMedia = ots.filter(o => o.prioridad === 'Media').length;
  const otsBaja = ots.filter(o => o.prioridad === 'Baja').length;

  // Últimas 5 OTs
  const recentOts = [...ots]
    .sort((a, b) => new Date(b.hora_recepcion).getTime() - new Date(a.hora_recepcion).getTime())
    .slice(0, 5);

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

  return (
    <div className="dashboard-view">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Panel de Monitoreo</h1>
          <p>Métricas generales y control operativo en tiempo real.</p>
        </div>
      </div>

      {/* Grid de Métricas Principales */}
      <div className="metrics-grid">
        <div className="card metric-card">
          <div className="metric-icon-wrapper el-glow">
            <Radio size={24} className="metric-icon icon-primary" />
          </div>
          <div className="metric-details">
            <span className="metric-value">{totalElementos}</span>
            <span className="metric-label">Elementos en Catálogo</span>
          </div>
        </div>

        <div className="card metric-card">
          <div className="metric-icon-wrapper ot-glow">
            <FileText size={24} className="metric-icon icon-warning" />
          </div>
          <div className="metric-details">
            <span className="metric-value">{totalOts}</span>
            <span className="metric-label">Órdenes Creadas</span>
          </div>
        </div>

        <div className="card metric-card">
          <div className="metric-icon-wrapper pending-glow">
            <Clock size={24} className="metric-icon icon-info" />
          </div>
          <div className="metric-details">
            <span className="metric-value">{otsPendientes}</span>
            <span className="metric-label">OTs en Curso</span>
          </div>
        </div>

        <div className="card metric-card">
          <div className="metric-icon-wrapper success-glow">
            <CheckCircle2 size={24} className="metric-icon icon-success" />
          </div>
          <div className="metric-details">
            <span className="metric-value">{otsCerradas}</span>
            <span className="metric-label">OTs Completadas</span>
          </div>
        </div>
      </div>

      {/* Grid de Secciones Analíticas */}
      <div className="analytics-grid">
        
        {/* Desglose de Elementos */}
        <div className="card analytics-card">
          <h3 className="card-title">Distribución de Red</h3>
          <div className="breakdown-list">
            <div className="breakdown-item">
              <div className="breakdown-info">
                <span>Nodos Principales</span>
                <span className="breakdown-value">{nodosCount}</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill fill-primary" 
                  style={{ width: `${totalElementos ? (nodosCount / totalElementos) * 100 : 0}%` }}
                ></div>
              </div>
            </div>

            <div className="breakdown-item">
              <div className="breakdown-info">
                <span>Instituciones de Apoyo (IAO)</span>
                <span className="breakdown-value">{iaoCount}</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill fill-secondary" 
                  style={{ width: `${totalElementos ? (iaoCount / totalElementos) * 100 : 0}%` }}
                ></div>
              </div>
            </div>

            <div className="breakdown-item">
              <div className="breakdown-info">
                <span>Hotspots de Internet Público</span>
                <span className="breakdown-value">{hotspotCount}</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill fill-info" 
                  style={{ width: `${totalElementos ? (hotspotCount / totalElementos) * 100 : 0}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Desglose del Flujo de Trabajo */}
        <div className="card analytics-card">
          <h3 className="card-title">Estados Operativos de OTs</h3>
          <div className="ot-status-breakdown">
            <div className="status-grid-item">
              <span className="status-number text-info">{otsAbiertas}</span>
              <span className="status-label">Abiertas</span>
            </div>
            <div className="status-grid-item">
              <span className="status-number text-warning">{otsDespachadas}</span>
              <span className="status-label">Despachadas</span>
            </div>
            <div className="status-grid-item">
              <span className="status-number text-purple">{otsEnSitio}</span>
              <span className="status-label">En Sitio</span>
            </div>
            <div className="status-grid-item">
              <span className="status-number text-success">{otsCerradas}</span>
              <span className="status-label">Cerradas</span>
            </div>
          </div>
          
          <div className="priority-distribution">
            <h4>Severidad de Incidentes</h4>
            <div className="priority-pills">
              <div className="prio-pill pill-alta">
                <span>Alta</span>
                <strong>{otsAlta}</strong>
              </div>
              <div className="prio-pill pill-media">
                <span>Media</span>
                <strong>{otsMedia}</strong>
              </div>
              <div className="prio-pill pill-baja">
                <span>Baja</span>
                <strong>{otsBaja}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabla de Actividad Reciente */}
      <div className="card recent-activity-card">
        <h3 className="card-title">Últimas Órdenes Registradas</h3>
        {recentOts.length === 0 ? (
          <div className="no-data-msg">
            <p>No se registran órdenes de trabajo activas en la base de datos.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Código OT</th>
                  <th>ID Elemento</th>
                  <th>Prioridad</th>
                  <th>Fecha de Recepción</th>
                  <th>Estado</th>
                  <th>Diagnóstico</th>
                </tr>
              </thead>
              <tbody>
                {recentOts.map((ot) => (
                  <tr key={ot.id_ot}>
                    <td className="font-bold">{ot.id_ot}</td>
                    <td>{ot.id_elemento}</td>
                    <td>
                      <span className={getPriorityBadgeClass(ot.prioridad)}>{ot.prioridad}</span>
                    </td>
                    <td>{new Date(ot.hora_recepcion).toLocaleString('es-PE')}</td>
                    <td>
                      <span className={getStatusBadgeClass(ot.estado)}>{ot.estado}</span>
                    </td>
                    <td className="text-truncate">{ot.diagnostico_inicial}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
