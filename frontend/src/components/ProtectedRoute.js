import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-sm uppercase tracking-widest font-bold text-slate-500">Loading...</div>
      </div>
    );
  }

  if (user === false) {
    return <Navigate to="/login" replace />;
  }

  return children;
};