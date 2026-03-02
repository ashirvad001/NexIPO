// components/AuthModal.tsx
import React, { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultView?: 'login' | 'signup';
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, defaultView = 'login' }) => {
  const { login, signup } = useAuth();
  const [view, setView] = useState<'login' | 'signup'>(defaultView);

  useEffect(() => {
    if (isOpen) {
      setView(defaultView);
      setError(null);
    }
  }, [isOpen, defaultView]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login form state
  const [loginIdentifier, setLoginIdentifier] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Signup form state
  const [signupData, setSignupData] = useState({
    email: '',
    username: '',
    password: '',
    confirm_password: '',
    full_name: '',
  });

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(loginIdentifier, loginPassword);
      onClose();
      setLoginIdentifier('');
      setLoginPassword('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await signup(signupData);
      onClose();
      setSignupData({ email: '', username: '', password: '', confirm_password: '', full_name: '' });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-navy-950/60 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-2xl shadow-modal max-w-md w-full p-6 sm:p-8 animate-slide-up">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1 rounded-lg text-navy-400 hover:text-navy-600 hover:bg-navy-100 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {/* Header */}
          <div className="mb-6">
            <h2 id="auth-modal-title" className="text-xl sm:text-2xl font-bold text-navy-900">
              {view === 'login' ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-sm text-navy-500 mt-1">
              {view === 'login'
                ? 'Sign in to access your IPO portfolio'
                : 'Join to start tracking IPOs'}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="alert-error mb-4" role="alert">
              <p>{error}</p>
            </div>
          )}

          {/* Login Form */}
          {view === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label htmlFor="login-id" className="label">Email or Username</label>
                <input
                  id="login-id"
                  type="text"
                  value={loginIdentifier}
                  onChange={(e) => setLoginIdentifier(e.target.value)}
                  className="input"
                  placeholder="you@example.com or username"
                  required
                  autoComplete="username"
                />
              </div>

              <div>
                <label htmlFor="login-pass" className="label">Password</label>
                <input
                  id="login-pass"
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="input"
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                />
              </div>

              <button type="submit" disabled={loading} className="w-full btn-primary py-3">
                {loading ? 'Signing in...' : 'Sign In'}
              </button>

              <p className="text-center text-sm text-navy-500">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setView('signup'); setError(null); }}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Sign up
                </button>
              </p>
            </form>
          )}

          {/* Signup Form */}
          {view === 'signup' && (
            <form onSubmit={handleSignup} className="space-y-4">
              <div>
                <label htmlFor="signup-email" className="label">Email *</label>
                <input
                  id="signup-email"
                  type="email"
                  value={signupData.email}
                  onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                  className="input"
                  placeholder="you@example.com"
                  required
                  autoComplete="email"
                />
              </div>

              <div className="grid grid-cols-1 xs:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="signup-user" className="label">Username *</label>
                  <input
                    id="signup-user"
                    type="text"
                    value={signupData.username}
                    onChange={(e) => setSignupData({ ...signupData, username: e.target.value })}
                    className="input"
                    placeholder="johndoe"
                    minLength={3}
                    maxLength={50}
                    required
                    autoComplete="username"
                  />
                </div>
                <div>
                  <label htmlFor="signup-name" className="label">Full Name</label>
                  <input
                    id="signup-name"
                    type="text"
                    value={signupData.full_name}
                    onChange={(e) => setSignupData({ ...signupData, full_name: e.target.value })}
                    className="input"
                    placeholder="John Doe"
                    autoComplete="name"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="signup-pass" className="label">Password *</label>
                <input
                  id="signup-pass"
                  type="password"
                  value={signupData.password}
                  onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                  className="input"
                  placeholder="••••••••"
                  minLength={8}
                  required
                  autoComplete="new-password"
                />
                <p className="text-xs text-navy-400 mt-1">Minimum 8 characters</p>
              </div>

              <div>
                <label htmlFor="signup-confirm" className="label">Confirm Password *</label>
                <input
                  id="signup-confirm"
                  type="password"
                  value={signupData.confirm_password}
                  onChange={(e) => setSignupData({ ...signupData, confirm_password: e.target.value })}
                  className="input"
                  placeholder="••••••••"
                  required
                  autoComplete="new-password"
                />
              </div>

              <button type="submit" disabled={loading} className="w-full btn-primary py-3">
                {loading ? 'Creating account...' : 'Create Account'}
              </button>

              <p className="text-center text-sm text-navy-500">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setView('login'); setError(null); }}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Sign in
                </button>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
