import React, { useState, useEffect } from 'react';
import { LayoutDashboard, FileText, Globe, Folder, ChevronDown, ChevronRight, Satellite, Radio, FileBadge2, Users, LogOut } from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  currentView: string;
  setCurrentView: (view: string) => void;
  currentUser: { id_personal: number; nombre: string; cargo?: string; email: string };
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView, currentUser, onLogout }) => {
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
    if (!currentView.startsWith('doc-')) {
      setCurrentView('doc-selnet');
    }
  };

  // Iniciales del usuario
  const getInitials = (nombre: string) => {
    const partes = nombre.trim().split(' ');
    if (partes.length >= 2) return `${partes[0][0]}${partes[1][0]}`.toUpperCase();
    return nombre.substring(0, 2).toUpperCase();
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

        {/* Personal */}
        <button
          className={`sidebar-nav-item ${currentView === 'personal' ? 'active' : ''}`}
          onClick={() => setCurrentView('personal')}
        >
          <Users size={20} className="nav-icon" />
          <span>Personal</span>
        </button>
      </nav>

      {/* Footer: usuario logueado + logout */}
      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">{getInitials(currentUser.nombre)}</div>
          <div className="user-info">
            <h4>{currentUser.nombre.split(' ')[0]}</h4>
            <span>{currentUser.cargo || 'Personal'}</span>
          </div>
        </div>
        <button
          className="sidebar-logout-btn"
          onClick={onLogout}
          title="Cerrar sesión"
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};
