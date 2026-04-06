import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, formatApiErrorDetail } from '../contexts/AuthContext';
import { MagnifyingGlass } from '@phosphor-icons/react';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(email, password, name);
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
            <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">Create Account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" data-testid="register-form">
            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full scoi-input"
                placeholder="John Doe"
                required
                data-testid="register-name-input"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full scoi-input"
                placeholder="investigator@example.com"
                required
                data-testid="register-email-input"
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
                data-testid="register-password-input"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="register-error-message">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full scoi-button-primary disabled:opacity-50"
              data-testid="register-submit-button"
            >
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-slate-600">
              Already have an account?{' '}
              <Link to="/login" className="font-bold text-slate-900 hover:underline" data-testid="login-link">
                Sign In
              </Link>
            </p>
          </div>
        </div>
      </div>

      <div
        className="hidden lg:block lg:w-1/2 bg-cover bg-center relative"
        style={{ backgroundImage: 'url(https://images.pexels.com/photos/3137068/pexels-photo-3137068.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
      >
        <div className="absolute inset-0 bg-slate-900 bg-opacity-60 flex items-center justify-center">
          <div className="text-center text-white p-8">
            <h2 className="text-3xl font-black tracking-tighter mb-4">Join the Investigation</h2>
            <p className="text-lg text-slate-200">Access powerful OSINT tools for corruption analysis</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;