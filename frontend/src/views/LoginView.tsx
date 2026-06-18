import { useState } from 'react';
import { Shield, Eye, EyeOff, Wifi, AlertCircle, Loader2 } from 'lucide-react';
import { loginUser } from '../services/api';
import './LoginView.css';

interface LoginViewProps {
  onLogin: (user: { id_personal: number; nombre: string; cargo?: string; email: string }) => void;
}

export function LoginView({ onLogin }: LoginViewProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Por favor completa todos los campos.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const user = await loginUser(email.trim(), password);
      onLogin(user);
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-bg">
      <div className="login-grid-overlay" />
      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">
            <Wifi size={28} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="login-title">Mantenimiento</h1>
            <p className="login-subtitle">Amazonas ERP · Sistema Interno</p>
          </div>
        </div>

        {/* Divider */}
        <div className="login-divider" />

        <p className="login-welcome">Ingresa tus credenciales corporativas para continuar</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="login-email">Correo institucional</label>
            <input
              id="login-email"
              type="email"
              placeholder="nombre.apellido@mantenimiento-amazonas.pe"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(''); }}
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="login-field">
            <label htmlFor="login-password">Contraseña</label>
            <div className="login-password-wrapper">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Tu contraseña"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                autoComplete="current-password"
                disabled={loading}
              />
              <button
                type="button"
                className="login-show-pass"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="login-error" role="alert">
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <>
                <Loader2 size={18} className="spin" />
                <span>Verificando...</span>
              </>
            ) : (
              <>
                <Shield size={18} />
                <span>Iniciar Sesión</span>
              </>
            )}
          </button>
        </form>

        <p className="login-footer">
          Acceso restringido al personal autorizado de Mantenimiento Amazonas.
        </p>
      </div>
    </div>
  );
}
