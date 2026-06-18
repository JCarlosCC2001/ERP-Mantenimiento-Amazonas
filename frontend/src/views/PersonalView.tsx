import { useState, useEffect } from 'react';
import { Users, Search, Edit3, X, Save, Loader2, CheckCircle, XCircle, Mail, Briefcase, MapPin } from 'lucide-react';
import { fetchPersonal, updatePersonal } from '../services/api';
import type { Personal } from '../services/api';
import './PersonalView.css';

interface PersonalViewProps {
  currentUser: { id_personal: number; nombre: string; cargo?: string; email: string };
}

export function PersonalView({ currentUser }: PersonalViewProps) {
  const [personal, setPersonal] = useState<Personal[]>([]);
  const [filtro, setFiltro] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Personal | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState<Partial<Personal>>({});
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');

  useEffect(() => {
    cargarPersonal();
  }, []);

  async function cargarPersonal() {
    setLoading(true);
    setError('');
    try {
      const data = await fetchPersonal();
      setPersonal(data);
      if (data.length > 0 && !selected) {
        setSelected(data[0]);
      }
    } catch (e: any) {
      setError(e.message || 'Error al cargar el personal.');
    } finally {
      setLoading(false);
    }
  }

  const filtrado = personal.filter(p =>
    p.nombre.toLowerCase().includes(filtro.toLowerCase()) ||
    (p.cargo || '').toLowerCase().includes(filtro.toLowerCase()) ||
    (p.cm || '').toLowerCase().includes(filtro.toLowerCase())
  );

  const handleSelect = (p: Personal) => {
    setSelected(p);
    setEditMode(false);
    setEditData({});
    setSaveMsg('');
  };

  const handleEdit = () => {
    if (!selected) return;
    setEditData({ nombre: selected.nombre, cargo: selected.cargo, cm: selected.cm, estado: selected.estado });
    setEditMode(true);
    setSaveMsg('');
  };

  const handleCancel = () => {
    setEditMode(false);
    setEditData({});
    setSaveMsg('');
  };

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    setSaveMsg('');
    try {
      await updatePersonal(selected.id_personal, editData);
      setSaveMsg('ok');
      setEditMode(false);
      // Refrescar y actualizar seleccionado
      const data = await fetchPersonal();
      setPersonal(data);
      const updated = data.find(p => p.id_personal === selected.id_personal);
      if (updated) setSelected(updated);
    } catch (e: any) {
      setSaveMsg('error: ' + (e.message || 'Error al guardar.'));
    } finally {
      setSaving(false);
    }
  };

  const getInitials = (nombre: string) => {
    const partes = nombre.trim().split(' ');
    if (partes.length >= 2) return `${partes[0][0]}${partes[1][0]}`.toUpperCase();
    return nombre.substring(0, 2).toUpperCase();
  };

  const estadoClass = (estado?: string) => estado === 'Activo' ? 'badge-activo' : 'badge-inactivo';

  return (
    <div className="personal-layout">
      {/* ---- LEFT PANEL: Lista de personal ---- */}
      <div className="personal-list-panel">
        <div className="personal-list-header">
          <div className="personal-list-title">
            <Users size={18} />
            <h2>Personal</h2>
            <span className="personal-count">{personal.length}</span>
          </div>
          <div className="personal-search-wrap">
            <Search size={14} className="personal-search-icon" />
            <input
              type="text"
              placeholder="Buscar..."
              value={filtro}
              onChange={e => setFiltro(e.target.value)}
              className="personal-search"
            />
            {filtro && (
              <button className="personal-search-clear" onClick={() => setFiltro('')}>
                <X size={13} />
              </button>
            )}
          </div>
        </div>

        <div className="personal-list-body">
          {loading ? (
            <div className="personal-loading">
              <Loader2 size={22} className="spin" />
              <span>Cargando...</span>
            </div>
          ) : error ? (
            <div className="personal-empty-msg">{error}</div>
          ) : filtrado.length === 0 ? (
            <div className="personal-empty-msg">Sin resultados</div>
          ) : filtrado.map(p => (
            <button
              key={p.id_personal}
              className={`personal-list-item ${selected?.id_personal === p.id_personal ? 'active' : ''}`}
              onClick={() => handleSelect(p)}
            >
              <div className={`personal-avatar-sm ${estadoClass(p.estado)}`}>
                {getInitials(p.nombre)}
              </div>
              <div className="personal-item-info">
                <span className="personal-item-nombre">{p.nombre}</span>
                <span className="personal-item-cargo">{p.cargo || '—'}</span>
              </div>
              <span className={`personal-badge ${estadoClass(p.estado)}`}>
                {p.estado || 'Activo'}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* ---- RIGHT PANEL: Detalle ---- */}
      <div className="personal-detail-panel">
        {!selected ? (
          <div className="personal-detail-empty">
            <Users size={40} opacity={0.15} />
            <p>Selecciona un miembro del personal</p>
          </div>
        ) : (
          <>
            {/* Header del detalle */}
            <div className="personal-detail-header">
              <div className={`personal-avatar-lg ${estadoClass(selected.estado)}`}>
                {getInitials(selected.nombre)}
              </div>
              <div className="personal-detail-names">
                <h2>{selected.nombre}</h2>
                <p>{selected.cargo || 'Sin cargo asignado'}</p>
              </div>
              <div className="personal-detail-actions">
                {!editMode ? (
                  <button className="btn-icon-edit" onClick={handleEdit} title="Editar">
                    <Edit3 size={16} />
                    <span>Editar</span>
                  </button>
                ) : (
                  <>
                    <button className="btn-icon-cancel" onClick={handleCancel}>
                      <X size={16} />
                      <span>Cancelar</span>
                    </button>
                    <button className="btn-icon-save" onClick={handleSave} disabled={saving}>
                      {saving ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
                      <span>Guardar</span>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Mensaje de guardado */}
            {saveMsg === 'ok' && (
              <div className="save-feedback ok">
                <CheckCircle size={15} />
                <span>Datos guardados correctamente.</span>
              </div>
            )}
            {saveMsg.startsWith('error') && (
              <div className="save-feedback err">
                <XCircle size={15} />
                <span>{saveMsg.replace('error: ', '')}</span>
              </div>
            )}

            {/* Campos */}
            <div className="personal-fields-grid">
              <div className="personal-field-card">
                <div className="personal-field-label">
                  <Users size={13} />
                  <span>Nombre completo</span>
                </div>
                {editMode ? (
                  <input
                    className="personal-field-input"
                    value={editData.nombre ?? ''}
                    onChange={e => setEditData(d => ({ ...d, nombre: e.target.value }))}
                  />
                ) : (
                  <span className="personal-field-value">{selected.nombre}</span>
                )}
              </div>

              <div className="personal-field-card">
                <div className="personal-field-label">
                  <Briefcase size={13} />
                  <span>Cargo</span>
                </div>
                {editMode ? (
                  <input
                    className="personal-field-input"
                    value={editData.cargo ?? ''}
                    onChange={e => setEditData(d => ({ ...d, cargo: e.target.value }))}
                    placeholder="Sin cargo"
                  />
                ) : (
                  <span className="personal-field-value">{selected.cargo || '—'}</span>
                )}
              </div>

              <div className="personal-field-card">
                <div className="personal-field-label">
                  <MapPin size={13} />
                  <span>Centro de Mantenimiento (CM)</span>
                </div>
                {editMode ? (
                  <input
                    className="personal-field-input"
                    value={editData.cm ?? ''}
                    onChange={e => setEditData(d => ({ ...d, cm: e.target.value }))}
                    placeholder="Sin CM asignado"
                  />
                ) : (
                  <span className="personal-field-value">{selected.cm || '—'}</span>
                )}
              </div>

              <div className="personal-field-card">
                <div className="personal-field-label">
                  <Mail size={13} />
                  <span>Correo institucional</span>
                </div>
                <span className="personal-field-value personal-field-email">{selected.email}</span>
              </div>

              <div className="personal-field-card">
                <div className="personal-field-label">
                  <CheckCircle size={13} />
                  <span>Estado</span>
                </div>
                {editMode ? (
                  <select
                    className="personal-field-input"
                    value={editData.estado ?? 'Activo'}
                    onChange={e => setEditData(d => ({ ...d, estado: e.target.value }))}
                  >
                    <option value="Activo">Activo</option>
                    <option value="Inactivo">Inactivo</option>
                  </select>
                ) : (
                  <span className={`personal-estado-pill ${estadoClass(selected.estado)}`}>
                    {selected.estado === 'Activo' ? <CheckCircle size={13} /> : <XCircle size={13} />}
                    {selected.estado || 'Activo'}
                  </span>
                )}
              </div>
            </div>

            {/* Nota de acceso */}
            <div className="personal-access-note">
              <Mail size={14} />
              <div>
                <strong>Acceso al sistema:</strong>
                <p>Credencial de inicio de sesión: <code>{selected.email}</code></p>
                <p>La contraseña inicial se genera automáticamente basada en el nombre (ej: <code>JPérez#Amazonas</code>). El usuario puede solicitar cambio de contraseña al administrador.</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
