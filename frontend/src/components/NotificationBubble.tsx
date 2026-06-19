import { useState, useEffect } from 'react';
import { fetchOTs } from '../services/api';
import './NotificationBubble.css';

interface NotificationBubbleProps {
  onClick: () => void;
}

export function NotificationBubble({ onClick }: NotificationBubbleProps) {
  const [pendingCount, setPendingCount] = useState<number>(0);

  useEffect(() => {
    const checkPending = async () => {
      try {
        // Por ahora, usamos las OTs en estado "En Sitio" como proxy 
        // para aquellas que están esperando validación por parte del técnico.
        const ots = await fetchOTs('En Sitio');
        setPendingCount(ots.length);
      } catch (error) {
        console.error("Error al obtener notificaciones:", error);
      }
    };

    checkPending();
    const interval = setInterval(checkPending, 30000); // Polling cada 30 segundos
    return () => clearInterval(interval);
  }, []);

  if (pendingCount === 0) return null;

  return (
    <div className="notification-bubble-container" onClick={onClick}>
      <div className="notification-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <span className="notification-badge">{pendingCount}</span>
      </div>
    </div>
  );
}
