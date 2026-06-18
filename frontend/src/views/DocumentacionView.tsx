import React, { useState, useEffect } from 'react';
import { 
  FolderOpen, Upload, Search, Satellite, Radio, FileBadge2, 
  AlertTriangle, RefreshCw, X, Copy, Check, FileText, Settings, Layers, Calendar
} from 'lucide-react';
import { fetchCFMs } from '../services/api';
import type { CFM } from '../services/api';
import './DocumentacionView.css';

type DocSection = 'selnet' | 'gilat' | 'cfms';

interface DocSubOption {
  id: DocSection;
  label: string;
  icon: React.ElementType;
  description: string;
  color: string;
  colorBg: string;
  colorBorder: string;
}

const DOC_OPTIONS: DocSubOption[] = [
  {
    id: 'selnet',
    label: 'Informes SELNET',
    icon: Satellite,
    description: 'Repositorio de informes técnicos y reportes de operación de la red SELNET.',
    color: '#818cf8',
    colorBg: 'rgba(99, 102, 241, 0.08)',
    colorBorder: 'rgba(99, 102, 241, 0.2)',
  },
  {
    id: 'gilat',
    label: 'Informes GILAT',
    icon: Radio,
    description: 'Documentación y reportes técnicos generados por el sistema GILAT.',
    color: '#34d399',
    colorBg: 'rgba(16, 185, 129, 0.08)',
    colorBorder: 'rgba(16, 185, 129, 0.2)',
  },
  {
    id: 'cfms',
    label: 'CFMs',
    icon: FileBadge2,
    description: 'Constancia de Fuerza Mayor (CFM) para justificación y descuentos en OTs.',
    color: '#fbbf24',
    colorBg: 'rgba(245, 158, 11, 0.08)',
    colorBorder: 'rgba(245, 158, 11, 0.2)',
  },
];

const SECTION_TITLES: Record<DocSection, string> = {
  selnet: 'Informes SELNET',
  gilat: 'Informes GILAT',
  cfms: 'Constancias de Fuerza Mayor (CFMs)',
};

interface DocumentacionViewProps {
  activeSection?: DocSection;
  setActiveSection?: (section: DocSection) => void;
}

export const DocumentacionView: React.FC<DocumentacionViewProps> = ({
  activeSection: propActiveSection,
  setActiveSection: propSetActiveSection,
}) => {
  const [internalSection, setInternalSection] = useState<DocSection>('selnet');
  const [searchTerm, setSearchTerm] = useState('');

  // Estados para CFMs
  const [cfms, setCfms] = useState<CFM[]>([]);
  const [loadingCfms, setLoadingCfms] = useState(false);
  const [errorCfms, setErrorCfms] = useState<string | null>(null);
  const [selectedCfm, setSelectedCfm] = useState<CFM | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const activeSection = propActiveSection ?? internalSection;
  const setActiveSection = propSetActiveSection ?? setInternalSection;

  const current = DOC_OPTIONS.find(o => o.id === activeSection)!;
  const Icon = current.icon;

  // Cargar CFMs si está seleccionada la pestaña
  const loadCFMs = async () => {
    setLoadingCfms(true);
    setErrorCfms(null);
    setSelectedCfm(null);
    try {
      const data = await fetchCFMs();
      setCfms(data);
    } catch (err: any) {
      console.error(err);
      setErrorCfms(err.message || 'Error al conectar con Google Sheets para CFMs');
    } finally {
      setLoadingCfms(false);
    }
  };

  useEffect(() => {
    if (activeSection === 'cfms') {
      loadCFMs();
    }
  }, [activeSection]);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(label);
    setTimeout(() => setCopiedField(null), 2000);
  };

  // Filtrar CFMs
  const filteredCfms = cfms.filter(cfm => {
    const term = searchTerm.toLowerCase();
    return (
      (cfm.codigo || '').toLowerCase().includes(term) ||
      (cfm.ot || '').toLowerCase().includes(term) ||
      (cfm.tipo || '').toLowerCase().includes(term) ||
      (cfm.selnet || '').toLowerCase().includes(term) ||
      (cfm.gilat || '').toLowerCase().includes(term) ||
      (cfm.factor || '').toLowerCase().includes(term)
    );
  });

  // Helper para renderizar estado de CFM en badge
  const renderStatusBadge = (statusStr: string) => {
    const s = (statusStr || '').trim().toLowerCase();
    if (!s) return <span className="badge badge-baja">PENDIENTE</span>;
    if (s.includes('aprob') || s.includes('ok') || s.includes('complet') || s.includes('si')) {
      return <span className="badge badge-cerrada">{statusStr}</span>;
    }
    if (s.includes('rechaz') || s.includes('no') || s.includes('cancel')) {
      return <span className="badge badge-alta">{statusStr}</span>;
    }
    return <span className="badge badge-despachada">{statusStr}</span>;
  };

  return (
      <div className="doc-view">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Documentación</h1>
        </div>
      </div>

      {/* Contenido principal (sin sidebar interno – la navegación está en el Sidebar global) */}
      <div className="doc-content">
          {/* Header de sección */}
          <div className="card doc-section-header" style={{ borderColor: current.colorBorder }}>
            <div className="doc-section-header-inner">
              <div className="doc-section-icon" style={{ background: current.colorBg, color: current.color }}>
                <Icon size={28} />
              </div>
              <div style={{ flex: 1 }}>
                <h2 className="doc-section-title" style={{ color: current.color }}>
                  {SECTION_TITLES[activeSection]}
                </h2>
                <p className="doc-section-desc">{current.description}</p>
              </div>
              {activeSection === 'cfms' && (
                <button className="btn btn-secondary btn-icon-only" onClick={loadCFMs} disabled={loadingCfms} title="Recargar CFMs">
                  <RefreshCw size={16} className={loadingCfms ? 'spin' : ''} />
                </button>
              )}
            </div>
          </div>

          {/* Barra de búsqueda */}
          <div className="card doc-search-bar">
            <div className="search-wrapper">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder={`Buscar en ${current.label}...`}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          {/* Renderizado Condicional por Sección */}
          {activeSection === 'cfms' ? (
            /* Sección CFMs */
            loadingCfms ? (
              <div className="card doc-loading-card">
                <RefreshCw className="spin" size={32} style={{ color: '#fbbf24' }} />
                <p>Cargando información de Constancias de Fuerza Mayor desde Google Sheets...</p>
              </div>
            ) : errorCfms ? (
              <div className="card doc-error-card">
                <AlertTriangle size={40} style={{ color: 'var(--color-danger)' }} />
                <h3>Error al conectar con Google Sheets</h3>
                <p>{errorCfms}</p>
                <button className="btn btn-primary" onClick={loadCFMs} style={{ marginTop: '1rem' }}>
                  <RefreshCw size={16} /> Reintentar Conexión
                </button>
              </div>
            ) : (
              /* Grid Layout de CFMs (Dos Columnas si hay seleccionada) */
              <div className={`cfm-layout-grid ${selectedCfm ? 'has-selection' : ''}`}>
                
                {/* Listado / Tabla */}
                <div className="cfm-table-column">
                  <div className="card table-card">
                    <div className="table-container sheets-table-container">
                      <table className="custom-table sheets-table">
                        <thead>
                          <tr>
                            <th>Item</th>
                            <th>OT</th>
                            <th>Código</th>
                            <th>Tipo</th>
                            <th>Selnet</th>
                            <th>Gilat</th>
                            <th>Factor</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredCfms.length === 0 ? (
                            <tr>
                              <td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}>
                                No se encontraron registros de CFMs que coincidan con la búsqueda.
                              </td>
                            </tr>
                          ) : (
                            filteredCfms.map((cfm, idx) => {
                              const isSelected = selectedCfm?.item === cfm.item && selectedCfm?.ot === cfm.ot;
                              return (
                                <tr 
                                  key={idx} 
                                  className={`cfm-row ${isSelected ? 'selected' : ''}`}
                                  onClick={() => setSelectedCfm(cfm)}
                                  style={{ cursor: 'pointer' }}
                                >
                                  <td><span className="cfm-item-num">{cfm.item || '-'}</span></td>
                                  <td className="cfm-cell-ot">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                      <FileText size={14} style={{ color: '#fbbf24' }} />
                                      <strong>{cfm.ot || '-'}</strong>
                                    </div>
                                  </td>
                                  <td><code className="code-badge">{cfm.codigo || '-'}</code></td>
                                  <td><span className="cfm-cell-tipo">{cfm.tipo || '-'}</span></td>
                                  <td>{renderStatusBadge(cfm.selnet)}</td>
                                  <td>{renderStatusBadge(cfm.gilat)}</td>
                                  <td>
                                    <span className="factor-value" style={{ fontWeight: 600, color: '#fbbf24' }}>
                                      {cfm.factor || '-'}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>

                {/* Detalle Lateral */}
                {selectedCfm && (
                  <div className="cfm-detail-column">
                    <div className="card detail-panel-premium">
                      {/* Header de Detalle */}
                      <div className="detail-header-premium">
                        <div className="detail-header-info">
                          <div className="detail-logo-wrapper" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' }}>
                            <FileBadge2 size={22} />
                          </div>
                          <div>
                            <h3>Detalle de CFM</h3>
                            <span className="detail-subtitle">Constancia de Fuerza Mayor</span>
                          </div>
                        </div>
                        <button className="detail-close-btn" onClick={() => setSelectedCfm(null)}>
                          <X size={18} />
                        </button>
                      </div>

                      {/* Cuerpo de Detalle */}
                      <div className="detail-body-premium">
                        
                        {/* Indicadores Clave */}
                        <div className="coords-highlight" style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px',
                          background: 'rgba(245, 158, 11, 0.08)',
                          border: '1px solid rgba(245, 158, 11, 0.2)',
                          borderRadius: '10px',
                          padding: '10px 14px',
                          marginBottom: '1rem'
                        }}>
                          <FileText size={16} style={{ color: '#fbbf24', flexShrink: 0 }} />
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: 1 }}>
                            <span style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Orden de Trabajo Relacionada</span>
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fde047' }}>{selectedCfm.ot}</span>
                          </div>
                          <button 
                            className="btn btn-secondary btn-icon-only"
                            style={{ padding: '4px 8px', height: 'auto' }}
                            onClick={() => handleCopy(selectedCfm.ot, 'ot')}
                          >
                            {copiedField === 'ot' ? <Check size={14} style={{ color: '#34d399' }} /> : <Copy size={14} />}
                          </button>
                        </div>

                        {/* Estado General */}
                        <div className="detail-section">
                          <h4 className="detail-section-title">Información CFM</h4>
                          <div className="detail-fields-grid">
                            <div className="detail-field">
                              <span className="field-label">ITEM</span>
                              <span className="field-value">{selectedCfm.item}</span>
                            </div>
                            <div className="detail-field">
                              <span className="field-label">Código Elemento</span>
                              <span className="field-value"><code>{selectedCfm.codigo}</code></span>
                            </div>
                            <div className="detail-field">
                              <span className="field-label">Tipo</span>
                              <span className="field-value">{selectedCfm.tipo}</span>
                            </div>
                            <div className="detail-field">
                              <span className="field-label">Factor</span>
                              <span className="field-value" style={{ color: '#fbbf24', fontWeight: 600 }}>{selectedCfm.factor}</span>
                            </div>
                            <div className="detail-field">
                              <span className="field-label">CFM SELNET</span>
                              <span className="field-value">{renderStatusBadge(selectedCfm.selnet)}</span>
                            </div>
                            <div className="detail-field">
                              <span className="field-label">CFM GILAT</span>
                              <span className="field-value">{renderStatusBadge(selectedCfm.gilat)}</span>
                            </div>
                          </div>
                        </div>

                        {/* Todos los datos originales */}
                        <div className="detail-section" style={{ marginTop: '1.25rem' }}>
                          <h4 className="detail-section-title">Columnas Adicionales del Excel</h4>
                          <div className="detail-fields-grid">
                            {Object.entries(selectedCfm._original || {}).map(([key, val]) => {
                              const strVal = String(val || '').trim();
                              // Omitir campos que ya mostramos o vacíos
                              const alreadyShown = ['item', 'ot', 'tipo', 'codigo', 'selnet', 'gilat', 'factor'].includes(key.toLowerCase());
                              if (alreadyShown || key.startsWith('_') || !strVal || key.toLowerCase().includes('col_vacia')) {
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

                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          ) : (
            /* Informes SELNET & GILAT Placeholders */
            <div className="card doc-empty-state">
              <div className="doc-empty-icon" style={{ background: current.colorBg, color: current.color }}>
                <FolderOpen size={40} />
              </div>
              <h3>Sin documentos cargados</h3>
              <p>
                La sección <strong style={{ color: current.color }}>{current.label}</strong> aún no tiene archivos registrados.
                Próximamente podrás cargar, visualizar y descargar documentos desde aquí.
              </p>
              <button className="btn btn-primary doc-upload-btn" disabled>
                <Upload size={16} />
                Cargar Documento
              </button>
              <span className="doc-coming-soon">Funcionalidad en desarrollo</span>
            </div>
          )}
        </div>
      </div>
  );
};


