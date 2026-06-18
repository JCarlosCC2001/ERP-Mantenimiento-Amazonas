import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { LoginView } from './views/LoginView';
import { DashboardView } from './views/DashboardView';
import { OTManagerView } from './views/OTManagerView';
import { RedAmazonasView } from './views/RedAmazonasView';
import { DocumentacionView } from './views/DocumentacionView';
import { PersonalView } from './views/PersonalView';
import type { AuthUser } from './services/api';

function App() {
  // Estado de autenticación: null = no autenticado
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => {
    // Persistir sesión en sessionStorage para que no se pierda al recargar
    try {
      const stored = sessionStorage.getItem('erp_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [currentView, setCurrentView] = useState<string>('dashboard');

  const handleLogin = (user: AuthUser) => {
    setCurrentUser(user);
    sessionStorage.setItem('erp_user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setCurrentUser(null);
    sessionStorage.removeItem('erp_user');
    setCurrentView('dashboard');
  };

  // Si no está autenticado, mostrar pantalla de login
  if (!currentUser) {
    return <LoginView onLogin={handleLogin} />;
  }

  const renderView = () => {
    if (currentView.startsWith('doc-')) {
      const section = currentView.substring(4) as 'selnet' | 'gilat' | 'cfms';
      return (
        <DocumentacionView 
          activeSection={section} 
          setActiveSection={(sec) => setCurrentView(`doc-${sec}`)} 
        />
      );
    }

    switch (currentView) {
      case 'dashboard':
        return <DashboardView />;
      case 'ots':
        return <OTManagerView />;
      case 'red-amazonas':
        return <RedAmazonasView />;
      case 'personal':
        return <PersonalView currentUser={currentUser} />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        currentUser={currentUser}
        onLogout={handleLogout}
      />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
}

export default App;
