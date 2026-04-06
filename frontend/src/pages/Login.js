import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, formatApiErrorDetail } from '../contexts/AuthContext';
import { MagnifyingGlass } from '@phosphor-icons/react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-2">
              <MagnifyingGlass size={32} weight="bold" className="text-slate-900" />
              <h1 className="text-4xl font-black tracking-tighter text-slate-900">SCOI</h1>
            </div>
            <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">SA Corruption OSINT Investigator</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" data-testid="login-form">
            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full scoi-input"
                placeholder="admin@scoi.gov.za"
                required
                data-testid="login-email-input"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full scoi-input"
                placeholder="••••••••"
                required
                data-testid="login-password-input"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="login-error-message">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full scoi-button-primary disabled:opacity-50"
              data-testid="login-submit-button"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-slate-600">
              Don't have an account?{' '}
              <Link to="/register" className="font-bold text-slate-900 hover:underline" data-testid="register-link">
                Register
              </Link>
            </p>
          </div>

          <div className="mt-12 p-4 bg-slate-50 border border-slate-200 rounded-sm">
            <p className="text-xs text-slate-600 mb-2 font-semibold">Demo Credentials:</p>
            <p className="text-xs font-mono text-slate-700">admin@scoi.gov.za / SCOI2026!Admin</p>
          </div>
        </div>
      </div>

      <div
        className="hidden lg:block lg:w-1/2 bg-cover bg-center relative"
        style={{ backgroundImage: 'url(https://images.pexels.com/photos/3137068/pexels-photo-3137068.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
      >
        <div className="absolute inset-0 bg-slate-900 bg-opacity-60 flex items-center justify-center">
          <div className="text-center text-white p-8">
            <h2 className="text-3xl font-black tracking-tighter mb-4">Mapping Corruption Networks</h2>
            <p className="text-lg text-slate-200">Legally compliant OSINT platform for South Africa</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;