import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ClockCounterClockwise } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.get(
        `${BACKEND_URL}/api/audit/logs?limit=100`,
        { withCredentials: true }
      );
      setLogs(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="audit-logs-container">
      <div className="scoi-card">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <ClockCounterClockwise size={24} weight="bold" className="text-slate-900" />
            <h2 className="text-lg font-bold text-slate-900">Audit Logs</h2>
          </div>
          <button
            onClick={fetchLogs}
            className="scoi-button-primary"
            data-testid="refresh-logs-button"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="audit-logs-error">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12" data-testid="audit-logs-loading">
            <p className="text-sm text-slate-600">Loading audit logs...</p>
          </div>
        ) : logs.length > 0 ? (
          <div className="overflow-x-auto" data-testid="audit-logs-table">
            <table className="scoi-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Entities</th>
                  <th>IP Hash</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} data-testid={`audit-log-${log.id}`}>
                    <td className="text-xs font-mono">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="text-sm">{log.user_email}</td>
                    <td>
                      <span className="text-xs uppercase tracking-widest font-bold text-slate-600">{log.action}</span>
                    </td>
                    <td className="text-xs font-mono">{log.entity_ids.length}</td>
                    <td className="text-xs font-mono text-slate-500">{log.ip_hash.slice(0, 12)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12" data-testid="audit-logs-empty">
            <ClockCounterClockwise size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
            <p className="text-sm text-slate-600">No audit logs found.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditLogs;