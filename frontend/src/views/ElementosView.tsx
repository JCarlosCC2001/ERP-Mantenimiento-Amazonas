import React, { useEffect, useState } from 'react';
import { fetchElementos, createElemento, deleteElemento } from '../services/api';
import type { Elemento } from '../services/api';
import { Plus, Trash2, Search, Radio, Compass, Wifi, X, AlertCircle } from 'lucide-react';
import './ElementosView.css';

export const ElementosView: React.FC = () => {
  const [elementos, setElementos] = useState<Elemento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Búsqueda y filtrado
  const [searchTerm, setSearchTerm] = useState('');
  
  // Estado del modal de registro
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newElement, setNewElement] = useState<Omit<Elemento, ''>>({
    id_elemento: '',
    nombre: '',
    tipo: 'Nodo',
    ubicacion: '',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadElementos();
  }, []);

  async function loadElementos() {
    try {
      setLoading(true);
      const data = await fetchElementos();
      setElementos(data);
      setError(null);
    } catch (err: any) {
      setError('No se pudo cargar el catálogo de elementos.');
    } finally {
      setLoading(false);
    }
  }

  // Manejadores de entrada
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setNewElement(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Enviar formulario de registro
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Validaciones básicas
    if (!newElement.id_elemento.trim()) {
      setFormError('El ID del elemento es obligatorio.');
      return;
    }
    if (!newElement.nombre.trim()) {
      setFormError('El nombre del elemento es obligatorio.');
      return;
    }

    try {
      await createElemento(newElement as Elemento);
      setIsModalOpen(false);
      // Limpiar campos
      setNewElement({
        id_elemento: '',
        nombre: '',
        tipo: 'Nodo',
        ubicacion: '',
      });
      // Recargar listado
      loadElementos();
      showNotification('Elemento registrado con éxito en el catálogo.');
    } catch (err: any) {
      setFormError(err.message || 'Error al registrar el elemento. El ID podría estar duplicado.');
    }
  };

  // Eliminar elemento
  const handleDelete = async (id: string) => {
    if (!window.confirm(`¿Está seguro de que desea eliminar el elemento ${id}?`)) {
      return;
    }
    
    try {
      const res = await deleteElemento(id);
      loadElementos();
      showNotification(res.message || `Elemento ${id} eliminado con éxito.`);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const showNotification = (msg: string) => {
    setActionSuccess(msg);
    setTimeout(() => setActionSuccess(null), 4000);
  };

  // Obtener icono según tipo de elemento
  const getElementIcon = (tipo: string) => {
    switch (tipo) {
      case 'Nodo':
        return <Radio size={18} className="text-info" />;
      case 'IAO':
        return <Compass size={18} className="text-purple" />;
      default:
        return <Wifi size={18} className="text-warning" />;
    }
  };

  // Filtrado
  const filteredElementos = elementos.filter(el => 
    el.id_elemento.toLowerCase().includes(searchTerm.toLowerCase()) ||
    el.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (el.ubicacion && el.ubicacion.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="elementos-view">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Catálogo de Elementos</h1>
          <p>Registro y mantenimiento de Nodos principales, IAOs y Hotspots de Amazonas.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={18} />
          Registrar Elemento
        </button>
      </div>

      {/* Alerta de Éxito Temporal */}
      {actionSuccess && (
        <div className="alert-success-banner">
          <CheckCircleIcon size={18} />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Barra de Filtros */}
      <div className="card filter-bar-card">
        <div className="search-wrapper">
          <Search size={18} className="search-icon" />
          <input 
            type="text" 
            placeholder="Buscar por ID, nombre o ubicación..." 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      {/* Listado en Tabla */}
      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Cargando elementos de la red...</p>
        </div>
      ) : error ? (
        <div className="error-card card">
          <AlertCircle size={48} className="error-icon" />
          <h3>Error de Lectura</h3>
          <p>{error}</p>
        </div>
      ) : filteredElementos.length === 0 ? (
        <div className="card no-elements-card">
          <Radio size={48} className="no-elements-icon" />
          <h3>No se encontraron elementos</h3>
          <p>Prueba a cambiar el término de búsqueda o registra un nuevo elemento.</p>
        </div>
      ) : (
        <div className="card table-card">
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>ID Elemento</th>
                  <th>Nombre Descriptivo</th>
                  <th>Ubicación / Distrito</th>
                  <th style={{ textAlign: 'center' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredElementos.map((el) => (
                  <tr key={el.id_elemento}>
                    <td>
                      <div className="element-type-cell">
                        {getElementIcon(el.tipo)}
                        <span className={`tag-tipo tipo-${el.tipo.toLowerCase()}`}>{el.tipo}</span>
                      </div>
                    </td>
                    <td className="font-bold">{el.id_elemento}</td>
                    <td>{el.nombre}</td>
                    <td>{el.ubicacion || <span className="text-muted">No especificada</span>}</td>
                    <td style={{ textAlign: 'center' }}>
                      <button 
                        className="btn btn-danger btn-icon" 
                        onClick={() => handleDelete(el.id_elemento)}
                        title="Eliminar elemento"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal de Registro */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Registrar Nuevo Elemento</h3>
              <button className="modal-close" onClick={() => setIsModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              {formError && (
                <div className="form-error-msg">
                  <AlertCircle size={16} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">ID Elemento (Único)</label>
                <input 
                  type="text" 
                  name="id_elemento" 
                  value={newElement.id_elemento}
                  onChange={handleInputChange}
                  placeholder="Ej. NOD-402, IAO-900, HOT-010"
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Nombre del Elemento</label>
                <input 
                  type="text" 
                  name="nombre" 
                  value={newElement.nombre}
                  onChange={handleInputChange}
                  placeholder="Ej. Nodo Chachapoyas Centro"
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Tipo de Elemento</label>
                <select 
                  name="tipo" 
                  value={newElement.tipo}
                  onChange={handleInputChange}
                  className="form-select"
                >
                  <option value="Nodo">Nodo Principal</option>
                  <option value="IAO">Institución de Apoyo (IAO)</option>
                  <option value="Hotspot">Hotspot Público</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Ubicación / Distrito (Opcional)</label>
                <input 
                  type="text" 
                  name="ubicacion" 
                  value={newElement.ubicacion}
                  onChange={handleInputChange}
                  placeholder="Ej. Chachapoyas Centro, Pedro Ruiz Gallo"
                  className="form-input"
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
                  Guardar Registro
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Componente helper para el icono de check
const CheckCircleIcon: React.FC<{ size?: number }> = ({ size = 18 }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    style={{ color: 'var(--color-success)' }}
  >
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);
