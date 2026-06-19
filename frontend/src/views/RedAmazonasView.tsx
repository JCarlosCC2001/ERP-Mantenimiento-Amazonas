import React, { useEffect, useState } from 'react';
import { fetchRedAmazonas, fetchOTs } from '../services/api';
import type { OT } from '../services/api';
import { Globe, Search, RefreshCw, AlertTriangle, Copy, Check, Table, ExternalLink, School, Wifi, Server, X, Clock, FileText, MapPin } from 'lucide-react';
import './RedAmazonasView.css';

const CLIENT_EMAIL = "erp-mantenimiento-amazonas@tensile-impact-499801-g7.iam.gserviceaccount.com";

const renderElementIcon = (tipo: string) => {
  switch (tipo) {
    case 'IAO':
      return (
        <div className="element-icon-wrapper success-glow" style={{ padding: '6px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <School size={16} className="text-success" />
        </div>
      );
    case 'Hotspot':
      return (
        <div className="element-icon-wrapper warning-glow" style={{ padding: '6px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <Wifi size={16} className="text-warning" />
        </div>
      );
    default:
      return (
        <div className="element-icon-wrapper el-glow" style={{ padding: '6px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.1)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <Server size={16} className="text-primary" />
        </div>
      );
  }
};


// Tipos de error clasificados del backend
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

function ErrorCard({ error, onRetry, copied, onCopy }: {
  error: ParsedError;
  onRetry: () => void;
  copied: boolean;
  onCopy: () => void;
}) {
  const isApiDisabled = error.type === 'DRIVE_API_DISABLED' || error.type === 'SHEETS_API_DISABLED';
  const isNotFound = error.type === 'NOT_FOUND' || error.type === 'PERMISSION_DENIED';
  const isWrongTab = error.type === 'WORKSHEET_NOT_FOUND';

  return (
    <div className="card error-setup-card">
      <div className="error-setup-header">
        <AlertTriangle size={36} className="text-warning animate-pulse" />
        <h3>
          {isApiDisabled ? 'API de Google Cloud no habilitada' :
           isNotFound ? 'Acceso no configurado' :
           isWrongTab ? 'Pestaña no encontrada' :
           'Error de Integración con Google Sheets'}
        </h3>
      </div>

      <p className="error-setup-desc">{error.message.split('Habilítala')[0]}</p>

      {/* CASO 1: Google Drive API deshabilitada */}
      {error.type === 'DRIVE_API_DISABLED' && (
        <div className="setup-instructions">
          <h4>Opciones para resolver este problema:</h4>
          <div className="option-blocks">
            {/* Opción A: Habilitar Drive API */}
            <div className="option-block">
              <div className="option-label">
                <span className="option-badge">Opción A</span>
                <strong>Habilitar la Google Drive API (Recomendado si controlas GCP)</strong>
              </div>
              <ol>
                <li>Abre la consola de Google Cloud del proyecto.</li>
                <li>Habilita la <strong>Google Drive API</strong>.</li>
                <li>Espera ~2 minutos y vuelve a intentarlo.</li>
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

            {/* Opción B: Usar URL directa */}
            <div className="option-block">
              <div className="option-label">
                <span className="option-badge option-badge-alt">Opción B</span>
                <strong>Usar la URL directa del documento (Evita la Drive API)</strong>
              </div>
              <ol>
                <li>Abre tu hoja de cálculo en Google Sheets.</li>
                <li>Copia la URL completa de la barra del navegador.</li>
                <li>Pégala como valor de <code>SPREADSHEET_URL</code> en el archivo 
                  <code> backend/sheets_service.py</code>.
                </li>
                <li>Reinicia el servidor backend.</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* CASO 2: Sheets API deshabilitada */}
      {error.type === 'SHEETS_API_DISABLED' && (
        <div className="setup-instructions">
          <h4>Habilitar la Google Sheets API:</h4>
          <ol>
            <li>Abre la consola de Google Cloud del proyecto.</li>
            <li>Habilita la <strong>Google Sheets API</strong>.</li>
            <li>Espera ~2 minutos y vuelve a intentarlo.</li>
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

      {/* CASO 3: Documento no encontrado / sin permiso */}
      {(isNotFound) && (
        <div className="setup-instructions">
          <h4>Comparte el documento con la cuenta de servicio del ERP:</h4>
          <ol>
            <li>Abre tu hoja <strong>'ERP-Mantenimiento-Amazonas'</strong> en Google Sheets.</li>
            <li>Haz clic en <strong>Compartir</strong> (arriba a la derecha).</li>
            <li>Agrega el siguiente correo como <strong>Lector</strong> o <strong>Editor</strong>:</li>
          </ol>
          <div className="email-copy-box">
            <code>{CLIENT_EMAIL}</code>
            <button className="btn btn-secondary btn-copy" onClick={onCopy}>
              {copied ? <Check size={16} className="text-success" /> : <Copy size={16} />}
              {copied ? 'Copiado' : 'Copiar'}
            </button>
          </div>
        </div>
      )}

      {/* CASO 4: Pestaña incorrecta */}
      {isWrongTab && (
        <div className="setup-instructions">
          <h4>Nombre de pestaña no encontrado:</h4>
          <p style={{ color: '#9ca3af', margin: 0 }}>
            Verifica que la hoja de cálculo <strong>'ERP-Mantenimiento-Amazonas'</strong> contenga 
            una pestaña llamada exactamente <strong>RED A.</strong> (incluyendo el punto final).
          </p>
        </div>
      )}

      {/* CASO 5: Error genérico */}
      {error.type === 'GENERIC_ERROR' && (
        <div className="setup-instructions">
          <h4>Detalle técnico:</h4>
          <code style={{ color: '#9ca3af', fontSize: '0.85rem', wordBreak: 'break-all' }}>
            {error.message}
          </code>
        </div>
      )}

      <button className="btn btn-primary" onClick={onRetry} style={{ marginTop: '1.5rem' }}>
        <RefreshCw size={16} style={{ marginRight: '8px' }} />
        Reintentar Conexión
      </button>
    </div>
  );
}

export const RedAmazonasView: React.FC = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [parsedError, setParsedError] = useState<ParsedError | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [copied, setCopied] = useState(false);

  // Estados para selección e interactividad
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [nodeOts, setNodeOts] = useState<OT[]>([]);
  const [loadingOts, setLoadingOts] = useState(false);
  const [selectedType, setSelectedType] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setParsedError(null);
      setSelectedNode(null);
      setSelectedType(null);
      const res = await fetchRedAmazonas();
      setData(res);
    } catch (err: any) {
      setParsedError(parseError(err.message || 'Error desconocido'));
    } finally {
      setLoading(false);
    }
  }

  const handleToggleType = (type: string) => {
    const nextType = selectedType === type ? null : type;
    setSelectedType(nextType);
    if (selectedNode && nextType !== null && selectedNode.Tipo !== nextType) {
      setSelectedNode(null);
    }
  };

  const handleCopyEmail = () => {
    navigator.clipboard.writeText(CLIENT_EMAIL);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSelectNode = async (node: any) => {
    setSelectedNode(node);
    try {
      setLoadingOts(true);
      const allOts = await fetchOTs();
      const codeToMatch = String(node['Código'] || '').trim().toLowerCase();
      // Filtrar OTs relacionadas
      const filtered = allOts.filter((ot: OT) => 
        String(ot.id_elemento || '').trim().toLowerCase() === codeToMatch
      );
      setNodeOts(filtered);
    } catch (err) {
      console.error('Error al cargar OTs del elemento:', err);
    } finally {
      setLoadingOts(false);
    }
  };

  // Mapear y normalizar los datos de la red Amazonas a las columnas deseadas: Código, Nombre, Tipo
  const normalizedData = data.map(row => {
    const keys = Object.keys(row);
    
    // Buscar claves de forma insensible
    const tipoKey = keys.find(k => k.toLowerCase() === 'tipo' || k.toLowerCase().includes('tipo') || k.toLowerCase() === 'type');
    const idKey = keys.find(k => k.toLowerCase().includes('código') || k.toLowerCase().includes('codigo') || k.toLowerCase().includes('id') || k.toLowerCase().includes('nodo'));
    const nombreKey = keys.find(k => k.toLowerCase().includes('nombre') || k.toLowerCase().includes('nodo') || k.toLowerCase().includes('descripcion') || k.toLowerCase().includes('descripción'));

    const rawTipo = tipoKey ? String(row[tipoKey] || '') : '';
    const rawNombre = nombreKey ? String(row[nombreKey] || '') : '';
    const codigo = idKey ? String(row[idKey] || '') : '';

    const tipoVal = rawTipo.toLowerCase();
    const nombreVal = rawNombre.toLowerCase();

    // Regla de negocio: Considerar que las IAO son (Centro de salud, Comisaría y Institución Educativa)
    let tipo = 'Nodo';
    if (
      tipoVal.includes('iao') ||
      tipoVal.includes('salud') || nombreVal.includes('salud') ||
      tipoVal.includes('comisar') || nombreVal.includes('comisar') ||
      tipoVal.includes('educativ') || nombreVal.includes('educativ') ||
      tipoVal.includes('colegio') || nombreVal.includes('colegio') ||
      tipoVal.includes('escuela') || nombreVal.includes('escuela') ||
      tipoVal.includes('i.e.') || nombreVal.includes('i.e.') ||
      tipoVal.includes('ie') || nombreVal.startsWith('ie ')
    ) {
      tipo = 'IAO';
    } else if (
      tipoVal.includes('hs') || tipoVal.includes('hotspot') || tipoVal.includes('wifi') ||
      nombreVal.includes('hs') || nombreVal.includes('hotspot') || nombreVal.includes('wifi')
    ) {
      tipo = 'Hotspot';
    }

    return {
      'Código': codigo || `EL-GEN-${rawNombre.slice(0, 4).toUpperCase()}`,
      'Nombre': rawNombre || `Elemento sin nombre`,
      'Tipo': tipo,
      '_original': row
    };
  });

  // Filtrado de registros dinámico sobre los datos normalizados
  const filteredData = normalizedData.filter(row => {
    if (selectedType && row.Tipo !== selectedType) {
      return false;
    }
    if (!searchTerm.trim()) return true;
    return Object.values(row).some(value => 
      String(value).toLowerCase().includes(searchTerm.toLowerCase())
    );
  });


  // Calcular métricas
  const nodosCount = normalizedData.filter(r => r.Tipo === 'Nodo').length;
  const iaosCount = normalizedData.filter(r => r.Tipo === 'IAO').length;
  const hsCount = normalizedData.filter(r => r.Tipo === 'Hotspot').length;

  return (
    <div className="red-view">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Nodos Red Amazonas (RED A.)</h1>
        </div>
        <button className="btn btn-secondary btn-icon-only" onClick={loadData} disabled={loading} title="Actualizar datos">
          <RefreshCw size={18} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Estableciendo conexión y leyendo datos de Google Sheets...</p>
        </div>
      ) : parsedError ? (
        <ErrorCard
          error={parsedError}
          onRetry={loadData}
          copied={copied}
          onCopy={handleCopyEmail}
        />
      ) : data.length === 0 ? (
        <div className="card empty-data-card">
          <Table size={48} className="text-muted" />
          <h3>La hoja de cálculo está vacía</h3>
          <p>No se encontraron filas de datos en la pestaña 'RED A.'. Agrega información para visualizarla aquí.</p>
        </div>
      ) : (
        <>
          {/* Métricas rápidas */}
          <div className="sheets-metrics">
            <div 
              className={`card sheet-metric-card ${selectedType === 'Nodo' ? 'active active-nodo' : ''}`}
              onClick={() => handleToggleType('Nodo')}
            >
              <div className="metric-icon-wrapper el-glow">
                <Globe size={22} className="text-primary" />
              </div>
              <div className="metric-details">
                <span className="metric-value">{nodosCount}</span>
                <span className="metric-label">Nodos</span>
              </div>
            </div>
            <div 
              className={`card sheet-metric-card ${selectedType === 'IAO' ? 'active active-iao' : ''}`}
              onClick={() => handleToggleType('IAO')}
            >
              <div className="metric-icon-wrapper success-glow">
                <Search size={22} className="text-success" />
              </div>
              <div className="metric-details">
                <span className="metric-value">{iaosCount}</span>
                <span className="metric-label">IAOs</span>
              </div>
            </div>
            <div 
              className={`card sheet-metric-card ${selectedType === 'Hotspot' ? 'active active-hotspot' : ''}`}
              onClick={() => handleToggleType('Hotspot')}
            >
              <div className="metric-icon-wrapper warning-glow">
                <AlertTriangle size={22} className="text-warning" />
              </div>
              <div className="metric-details">
                <span className="metric-value">{hsCount}</span>
                <span className="metric-label">Hotspots (HS)</span>
              </div>
            </div>
          </div>

          {/* Buscador */}
          <div className="card filter-bar-card">
            <div className="search-wrapper">
              <Search size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Buscar por código, nombre o tipo..." 
                value={searchTerm} 
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          {/* Layout interactivo de Red Amazonas */}
          <div className={`red-amazonas-layout-wrapper ${selectedNode ? 'has-selection' : ''}`}>
            
            {/* Columna de la Tabla */}
            <div className="table-column">
              <div className="card table-card">
                <div className="table-container sheets-table-container">
                  <table className="custom-table sheets-table">
                    <thead>
                      <tr>
                        <th style={{ width: '30%' }}>Código</th>
                        <th style={{ width: '25%' }}>Tipo</th>
                        <th>Nombre</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredData.map((row: any, idx) => {
                        const tipo = row['Tipo'];
                        const codigo = row['Código'];
                        const nombre = row['Nombre'];
                        const isSelected = selectedNode?.Código === codigo;
                        
                        return (
                          <tr 
                            key={idx} 
                            className={`table-row-premium interactive-row ${isSelected ? 'row-selected' : ''}`}
                            onClick={() => handleSelectNode(row)}
                            style={{ cursor: 'pointer' }}
                          >
                            {/* 1. Código con icono descriptivo de tipo */}
                            <td className="font-bold cell-codigo">
                              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {renderElementIcon(tipo)}
                                <span style={{ fontSize: '0.95rem', letterSpacing: '0.02em', color: isSelected ? 'var(--color-primary-light)' : '#f3f4f6' }}>{codigo}</span>
                              </div>
                            </td>
                            
                            {/* 2. Tipo con badge estilizado */}
                            <td>
                              <span className={`badge-type badge-type-${tipo.toLowerCase()}`} style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                padding: '4px 10px',
                                borderRadius: '20px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                letterSpacing: '0.03em',
                                textTransform: 'uppercase',
                                background: tipo === 'IAO' ? 'rgba(16, 185, 129, 0.12)' : tipo === 'Hotspot' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(99, 102, 241, 0.12)',
                                color: tipo === 'IAO' ? '#34d399' : tipo === 'Hotspot' ? '#fbbf24' : '#818cf8',
                                border: `1px solid ${tipo === 'IAO' ? 'rgba(16, 185, 129, 0.25)' : tipo === 'Hotspot' ? 'rgba(245, 158, 11, 0.25)' : 'rgba(99, 102, 241, 0.25)'}`
                              }}>
                                {tipo}
                              </span>
                            </td>
                            
                            {/* 3. Nombre */}
                            <td className="cell-nombre" style={{ color: isSelected ? '#ffffff' : '#d1d5db', fontSize: '0.925rem' }}>
                              {nombre}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Columna de Detalle (Se abre a la derecha) */}
            {selectedNode && (
              <div className="detail-column animate-fade-in">
                <div className="card detail-card-premium">
                  
                  {/* Encabezado del detalle */}
                  <div className="detail-header-premium">
                    <div className="detail-title-wrapper" style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      {renderElementIcon(selectedNode.Tipo)}
                      <div>
                        <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>{selectedNode.Código}</h3>
                        <p style={{ margin: '2px 0 0 0', fontSize: '0.875rem', color: '#9ca3af' }}>{selectedNode.Nombre}</p>
                      </div>
                    </div>
                    <button className="btn-close-detail" onClick={() => setSelectedNode(null)} title="Cerrar detalles">
                      <X size={18} />
                    </button>
                  </div>

                  {/* Cuerpo del detalle */}
                  <div className="detail-body-premium">
                    
                    {/* Campos de datos del Excel */}
                    <div className="detail-section">
                      <h4 className="detail-section-title">Datos del Elemento</h4>
                      {/* Coordenadas destacadas si existen */}
                      {(() => {
                        const orig = selectedNode._original || {};
                        const latKey = Object.keys(orig).find(k => /^lat(itud)?$/i.test(k.trim()));
                        const lngKey = Object.keys(orig).find(k => /^lo?ng?(itud)?$/i.test(k.trim()) || /^lon$/i.test(k.trim()));
                        const lat = latKey ? String(orig[latKey] || '').trim() : '';
                        const lng = lngKey ? String(orig[lngKey] || '').trim() : '';
                        if (lat && lng) {
                          return (
                            <div className="coords-highlight" style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '10px',
                              background: 'rgba(99, 102, 241, 0.08)',
                              border: '1px solid rgba(99, 102, 241, 0.2)',
                              borderRadius: '10px',
                              padding: '10px 14px',
                              marginBottom: '1rem'
                            }}>
                              <MapPin size={16} style={{ color: '#818cf8', flexShrink: 0 }} />
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <span style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Coordenadas GPS</span>
                                <a
                                  href={`https://www.google.com/maps?q=${lat},${lng}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{ fontSize: '0.9rem', fontWeight: 600, color: '#a5b4fc', textDecoration: 'none', letterSpacing: '0.02em' }}
                                >
                                  {lat}, {lng}
                                </a>
                              </div>
                            </div>
                          );
                        }
                        return null;
                      })()}
                      <div className="detail-fields-grid">
                        {Object.entries(selectedNode._original || {}).map(([key, val]) => {
                          const strVal = String(val || '').trim();
                          // Omitir columnas vacías, claves del sistema y columnas vacías renombradas
                          if (key.startsWith('_') || !strVal || key.toLowerCase().includes('col_vacia')) {
                            return null;
                          }
                          return (
                            <div className="detail-field" key={key}>
                              <span className="field-label">{key}</span>
                              <span className="field-value">{strVal}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Historial de OTs */}
                    <div className="detail-section related-ots-section" style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
                      <h4 className="detail-section-title" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>Últimas OTs Relacionadas</span>
                        <span className="related-ots-badge">{nodeOts.length}</span>
                      </h4>

                      {loadingOts ? (
                        <div className="loading-ots-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem 0', gap: '10px' }}>
                          <div className="spinner-small" style={{ width: '20px', height: '20px', border: '2px solid rgba(255, 255, 255, 0.1)', borderTopColor: 'var(--color-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                          <span style={{ fontSize: '0.85rem', color: '#9ca3af' }}>Consultando hoja Master...</span>
                        </div>
                      ) : nodeOts.length === 0 ? (
                        <div className="no-related-ots" style={{ textAlign: 'center', padding: '2rem 0', color: '#9ca3af' }}>
                          <FileText size={32} style={{ opacity: 0.4, marginBottom: '8px' }} />
                          <p style={{ margin: 0, fontSize: '0.875rem' }}>No hay OTs registradas para este nodo.</p>
                        </div>
                      ) : (
                        <div className="ots-history-list" style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                          {nodeOts.slice(0, 5).map((ot: OT) => {
                            return (
                              <div key={ot.id_ot} className="ot-history-item" style={{
                                padding: '12px',
                                borderRadius: '8px',
                                background: 'rgba(255, 255, 255, 0.03)',
                                border: '1px solid rgba(255, 255, 255, 0.06)',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '6px'
                              }}>
                                <div className="ot-history-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-primary-light)' }}>{ot.id_ot}</span>
                                  <span className={`badge badge-${ot.estado.toLowerCase().replace(' ', '-')}`} style={{ fontSize: '0.7rem', padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 600 }}>
                                    {ot.estado}
                                  </span>
                                </div>
                                <p style={{ margin: 0, fontSize: '0.85rem', color: '#d1d5db', lineHeight: 1.4 }}>{ot.diagnostico_inicial}</p>
                                <div className="ot-history-meta" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#9ca3af' }}>
                                  <Clock size={12} />
                                  <span>Notificación: {new Date(ot.hora_recepcion).toLocaleString('es-PE')}</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

