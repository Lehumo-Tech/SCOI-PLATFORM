import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Eye, Bell, Trash, Plus, ArrowsClockwise, Warning, ShieldCheck, CurrencyDollar, Handshake, X } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Watchlist = () => {
  const [watchlist, setWatchlist] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addEntityId, setAddEntityId] = useState('');
  const [addNotes, setAddNotes] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeView, setActiveView] = useState('alerts');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [watchlistRes, alertsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/watchlist/`, { withCredentials: true }),
        axios.get(`${BACKEND_URL}/api/watchlist/alerts?limit=100`, { withCredentials: true })
      ]);
      setWatchlist(watchlistRes.data.items || []);
      setAlerts(alertsRes.data.alerts || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load watchlist');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!addEntityId.trim()) return;
    setAddLoading(true);
    setError('');
    setSuccess('');
    try {
      const { data } = await axios.post(
        `${BACKEND_URL}/api/watchlist/add`,
        { entity_id: addEntityId.trim(), notes: addNotes },
        { withCredentials: true }
      );
      setSuccess(data.message);
      setAddEntityId('');
      setAddNotes('');
      setShowAddForm(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add to watchlist');
    } finally {
      setAddLoading(false);
    }
  };

  const handleRemove = async (itemId) => {
    try {
      await axios.delete(`${BACKEND_URL}/api/watchlist/${itemId}`, { withCredentials: true });
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove');
    }
  };

  const handleDismiss = async (alertId) => {
    try {
      await axios.post(
        `${BACKEND_URL}/api/watchlist/alerts/dismiss`,
        { alert_id: alertId },
        { withCredentials: true }
      );
      setAlerts(prev => prev.filter(a => a.id !== alertId));
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to dismiss');
    }
  };

  const handleScan = async () => {
    setScanLoading(true);
    setError('');
    try {
      const { data } = await axios.post(
        `${BACKEND_URL}/api/watchlist/scan`,
        {},
        { withCredentials: true }
      );
      setSuccess(data.message);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Scan failed');
    } finally {
      setScanLoading(false);
    }
  };

  const severityColor = {
    critical: 'bg-red-600 text-white',
    high: 'bg-red-100 text-red-800 border border-red-200',
    medium: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
    low: 'bg-slate-100 text-slate-700 border border-slate-200'
  };

  const alertIcon = (type) => {
    switch (type) {
      case 'red_flag': return <Warning size={18} weight="bold" className="text-red-600" />;
      case 'asset_transfer': return <CurrencyDollar size={18} weight="bold" className="text-amber-600" />;
      case 'new_tender': return <Handshake size={18} weight="bold" className="text-blue-600" />;
      default: return <Bell size={18} weight="bold" className="text-slate-600" />;
    }
  };

  const activeAlertCount = alerts.filter(a => !a.dismissed).length;

  return (
    <div data-testid="watchlist-container">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-slate-200 border border-slate-200 mb-6">
        <div className="bg-white p-6">
          <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Watched Entities</p>
          <p className="text-3xl font-black tracking-tight text-slate-900">{watchlist.length}</p>
        </div>
        <div className="bg-white p-6">
          <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Active Alerts</p>
          <p className={`text-3xl font-black tracking-tight ${activeAlertCount > 0 ? 'text-red-600' : 'text-slate-900'}`}>
            {activeAlertCount}
          </p>
        </div>
        <div className="bg-white p-6 flex items-center gap-3">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="scoi-button-primary flex items-center gap-2 flex-1"
            data-testid="add-to-watchlist-btn"
          >
            <Plus size={16} weight="bold" /> Add Entity
          </button>
          <button
            onClick={handleScan}
            disabled={scanLoading || watchlist.length === 0}
            className="scoi-button-primary flex items-center gap-2 flex-1 disabled:opacity-50"
            data-testid="scan-watchlist-btn"
          >
            <ArrowsClockwise size={16} weight="bold" className={scanLoading ? 'animate-spin' : ''} />
            {scanLoading ? 'Scanning...' : 'Scan All'}
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm flex items-center justify-between" data-testid="watchlist-error">
          <p className="text-sm text-red-700">{error}</p>
          <button onClick={() => setError('')}><X size={16} /></button>
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-sm flex items-center justify-between" data-testid="watchlist-success">
          <p className="text-sm text-green-700">{success}</p>
          <button onClick={() => setSuccess('')}><X size={16} /></button>
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <div className="scoi-card mb-6" data-testid="add-watchlist-form">
          <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900 mb-4">Add Entity to Watchlist</h3>
          <form onSubmit={handleAdd} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Entity ID</label>
                <input
                  type="text"
                  value={addEntityId}
                  onChange={(e) => setAddEntityId(e.target.value)}
                  placeholder="Paste entity ID from search results..."
                  className="w-full scoi-input"
                  required
                  data-testid="watchlist-entity-id-input"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Notes (optional)</label>
                <input
                  type="text"
                  value={addNotes}
                  onChange={(e) => setAddNotes(e.target.value)}
                  placeholder="Investigation context..."
                  className="w-full scoi-input"
                  data-testid="watchlist-notes-input"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={addLoading || !addEntityId.trim()}
              className="scoi-button-primary disabled:opacity-50"
              data-testid="watchlist-add-submit"
            >
              {addLoading ? 'Adding...' : 'Add to Watchlist'}
            </button>
          </form>
        </div>
      )}

      {/* View Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveView('alerts')}
          className={`px-4 py-2 text-xs uppercase tracking-widest font-bold border rounded-sm transition-all ${
            activeView === 'alerts' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-300'
          }`}
          data-testid="view-alerts-btn"
        >
          Alerts ({activeAlertCount})
        </button>
        <button
          onClick={() => setActiveView('watched')}
          className={`px-4 py-2 text-xs uppercase tracking-widest font-bold border rounded-sm transition-all ${
            activeView === 'watched' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-300'
          }`}
          data-testid="view-watched-btn"
        >
          Watched Entities ({watchlist.length})
        </button>
      </div>

      {loading ? (
        <div className="scoi-card text-center py-12">
          <p className="text-sm text-slate-600">Loading watchlist...</p>
        </div>
      ) : activeView === 'alerts' ? (
        /* Alerts View */
        alerts.length > 0 ? (
          <div className="space-y-3" data-testid="alerts-list">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="scoi-card flex items-start gap-4"
                data-testid={`alert-${alert.id}`}
              >
                <div className="flex-shrink-0 mt-1">
                  {alertIcon(alert.alert_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{alert.title}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {alert.entity_name} ({alert.entity_type}) | {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`text-xs font-bold uppercase tracking-widest px-2 py-1 rounded-sm ${severityColor[alert.severity] || severityColor.medium}`}>
                        {alert.severity}
                      </span>
                      <button
                        onClick={() => handleDismiss(alert.id)}
                        className="text-slate-400 hover:text-slate-700 transition-colors"
                        title="Dismiss alert"
                        data-testid={`dismiss-alert-${alert.id}`}
                      >
                        <X size={18} weight="bold" />
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-slate-700 mt-2">{alert.description}</p>
                  {alert.evidence.length > 0 && (
                    <p className="text-xs font-mono text-slate-400 mt-1">{alert.evidence.join(', ')}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="scoi-card text-center py-12" data-testid="no-alerts">
            <ShieldCheck size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
            <p className="text-sm text-slate-600">No active alerts. Add entities to your watchlist and scan for updates.</p>
          </div>
        )
      ) : (
        /* Watched Entities View */
        watchlist.length > 0 ? (
          <div className="space-y-3" data-testid="watched-list">
            {watchlist.map((item) => (
              <div
                key={item.id}
                className="scoi-card flex items-center justify-between"
                data-testid={`watched-${item.id}`}
              >
                <div className="flex items-center gap-4">
                  <Eye size={24} weight="bold" className="text-slate-400" />
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">
                      {item.entity?.name || 'Unknown Entity'}
                    </h4>
                    <p className="text-xs text-slate-500">
                      {item.entity?.type?.toUpperCase()} | {item.entity?.source} | Added: {new Date(item.created_at).toLocaleDateString()}
                    </p>
                    {item.notes && <p className="text-xs text-slate-400 mt-1">{item.notes}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {item.active_alerts > 0 && (
                    <span className="text-xs font-bold text-red-600 bg-red-50 border border-red-200 px-2 py-1 rounded-sm">
                      {item.active_alerts} ALERT{item.active_alerts > 1 ? 'S' : ''}
                    </span>
                  )}
                  <button
                    onClick={() => handleRemove(item.id)}
                    className="text-slate-400 hover:text-red-600 transition-colors"
                    title="Remove from watchlist"
                    data-testid={`remove-watched-${item.id}`}
                  >
                    <Trash size={18} weight="bold" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="scoi-card text-center py-12" data-testid="empty-watchlist">
            <Eye size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
            <p className="text-sm text-slate-600">No entities on your watchlist yet.</p>
          </div>
        )
      )}
    </div>
  );
};

export default Watchlist;
