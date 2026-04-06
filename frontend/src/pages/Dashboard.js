import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { MagnifyingGlass, SignOut, Database, Graph, Flag, FileText, ClockCounterClockwise, UserCircle, Detective, Eye, Robot, DownloadSimple } from '@phosphor-icons/react';
import SearchEntities from '../components/SearchEntities';
import EntityGraph from '../components/EntityGraph';
import RedFlagDashboard from '../components/RedFlagDashboard';
import AuditLogs from '../components/AuditLogs';
import DataIngestion from '../components/DataIngestion';
import AssetTracing from '../components/AssetTracing';
import Watchlist from '../components/Watchlist';
import Investigations from '../components/Investigations';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('search');

  const tabs = [
    { id: 'search', label: 'Entity Search', icon: MagnifyingGlass },
    { id: 'graph', label: 'Network Graph', icon: Graph },
    { id: 'assets', label: 'Asset Tracing', icon: Detective },
    { id: 'watchlist', label: 'Watchlist', icon: Eye },
    { id: 'investigate', label: 'Investigate', icon: Robot },
    { id: 'red-flags', label: 'Red Flags', icon: Flag },
    ...(user?.role === 'admin' ? [{ id: 'ingest', label: 'Data Ingestion', icon: Database }] : []),
    ...(user?.role === 'admin' ? [{ id: 'audit', label: 'Audit Logs', icon: ClockCounterClockwise }] : []),
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="scoi-header">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MagnifyingGlass size={28} weight="bold" className="text-slate-900" />
            <div>
              <h1 className="text-2xl font-black tracking-tighter text-slate-900">SCOI</h1>
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500">Corruption OSINT</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href={`${process.env.REACT_APP_BACKEND_URL}/api/download/project-zip`}
              className="flex items-center gap-1.5 px-3 py-2 text-xs uppercase tracking-widest font-bold text-slate-600 border border-slate-300 rounded-sm hover:bg-slate-100 transition-colors"
              data-testid="download-zip-button"
            >
              <DownloadSimple size={16} weight="bold" />
              Download ZIP
            </a>
            <div className="flex items-center gap-2" data-testid="user-profile">
              <UserCircle size={24} weight="bold" className="text-slate-600" />
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-900">{user?.name}</p>
                <p className="text-xs uppercase tracking-widest text-slate-500">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="scoi-button-primary flex items-center gap-2"
              data-testid="logout-button"
            >
              <SignOut size={16} weight="bold" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8 border-b border-slate-200" data-testid="dashboard-tabs">
          <div className="flex gap-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-xs uppercase tracking-widest font-bold transition-all duration-200 border-b-2 ${
                    activeTab === tab.id
                      ? 'border-slate-900 text-slate-900'
                      : 'border-transparent text-slate-500 hover:text-slate-900'
                  }`}
                  data-testid={`tab-${tab.id}`}
                >
                  <Icon size={18} weight="bold" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        <div data-testid="dashboard-content">
          {activeTab === 'search' && <SearchEntities />}
          {activeTab === 'graph' && <EntityGraph />}
          {activeTab === 'assets' && <AssetTracing />}
          {activeTab === 'watchlist' && <Watchlist />}
          {activeTab === 'investigate' && <Investigations />}
          {activeTab === 'red-flags' && <RedFlagDashboard />}
          {activeTab === 'ingest' && <DataIngestion />}
          {activeTab === 'audit' && <AuditLogs />}
        </div>
      </div>

      <footer className="mt-16 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-sm">
            <p className="text-xs font-semibold text-yellow-800 mb-1">COMPLIANCE WARNING</p>
            <p className="text-xs text-yellow-700">
              This tool provides OSINT analysis based on publicly available data only. All outputs are investigative patterns, not legal determinations.
              Human verification required. POPIA-compliant data handling in effect.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;