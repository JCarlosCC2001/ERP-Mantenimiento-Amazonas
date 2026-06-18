import React, { useState, useEffect } from 'react';
import { LayoutDashboard, FileText, Globe, Folder, ChevronDown, ChevronRight, Satellite, Radio, FileBadge2 } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  currentView: string;
  setCurrentView: (view: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView }) => {
  const [docExpanded, setDocExpanded] = useState(currentView.startsWith('doc-'));

  useEffect(() => {
    if (currentView.startsWith('doc-')) {
      setDocExpanded(true);
    }
  }, [currentView]);

  const toggleDoc = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDocExpanded(!docExpanded);
  };

  const handleDocClick = () => {
    setDocExpanded(true);
    // Por defecto, al hacer click en el padre, ir al primer sub-item si no estamos en uno
    if (!currentView.startsWith('doc-')) {
      setCurrentView('doc-selnet');
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">MA</div>
        <div className="logo-text">
          <h2>Mantenimiento</h2>
          <span>Amazonas ERP</span>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        {/* Dashboard */}
        <button
          className={`sidebar-nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
          onClick={() => setCurrentView('dashboard')}
        >
          <LayoutDashboard size={20} className="nav-icon" />
          <span>Dashboard</span>
        </button>

        {/* Órdenes de Trabajo */}
        <button
          className={`sidebar-nav-item ${currentView === 'ots' ? 'active' : ''}`}
          onClick={() => setCurrentView('ots')}
        >
          <FileText size={20} className="nav-icon" />
          <span>Órdenes de Trabajo</span>
        </button>

        {/* Red Amazonas */}
        <button
          className={`sidebar-nav-item ${currentView === 'red-amazonas' ? 'active' : ''}`}
          onClick={() => setCurrentView('red-amazonas')}
        >
          <Globe size={20} className="nav-icon" />
          <span>Red Amazonas</span>
        </button>

        {/* Documentación (Con Sub-opciones) */}
        <div className="sidebar-nav-group">
          <button
            className={`sidebar-nav-item ${currentView.startsWith('doc-') ? 'active' : ''}`}
            onClick={handleDocClick}
          >
            <Folder size={20} className="nav-icon" />
            <span style={{ flex: 1 }}>Documentación</span>
            <div className="chevron-toggle" onClick={toggleDoc}>
              {docExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </div>
          </button>

          {docExpanded && (
            <div className="sidebar-sub-nav">
              <button
                className={`sidebar-sub-nav-item ${currentView === 'doc-selnet' ? 'active' : ''}`}
                onClick={() => setCurrentView('doc-selnet')}
              >
                <Satellite size={16} className="sub-nav-icon" />
                <span>Informes SELNET</span>
              </button>
              <button
                className={`sidebar-sub-nav-item ${currentView === 'doc-gilat' ? 'active' : ''}`}
                onClick={() => setCurrentView('doc-gilat')}
              >
                <Radio size={16} className="sub-nav-icon" />
                <span>Informes GILAT</span>
              </button>
              <button
                className={`sidebar-sub-nav-item ${currentView === 'doc-cfms' ? 'active' : ''}`}
                onClick={() => setCurrentView('doc-cfms')}
              >
                <FileBadge2 size={16} className="sub-nav-icon" />
                <span>CFMs</span>
              </button>
            </div>
          )}
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">AD</div>
          <div className="user-info">
            <h4>Administrador</h4>
            <span>Conectado</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
