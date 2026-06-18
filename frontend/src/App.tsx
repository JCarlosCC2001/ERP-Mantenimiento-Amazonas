import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { DashboardView } from './views/DashboardView';
import { OTManagerView } from './views/OTManagerView';
import { RedAmazonasView } from './views/RedAmazonasView';
import { DocumentacionView } from './views/DocumentacionView';

function App() {
  const [currentView, setCurrentView] = useState<string>('dashboard');

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
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  );
}

export default App;
