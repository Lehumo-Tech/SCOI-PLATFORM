import React, { useState } from 'react';
import axios from 'axios';
import { Warning, Target } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const RedFlagDashboard = () => {
  const [entityId, setEntityId] = useState('');
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleEvaluate = async (e) => {
    e.preventDefault();
    if (!entityId.trim()) return;

    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post(
        `${BACKEND_URL}/api/entities/rules/evaluate?entity_id=${entityId.trim()}`,
        {},
        { withCredentials: true }
      );
      setMatches(data.matches || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="red-flag-dashboard">
      <div className="scoi-card mb-6">
        <form onSubmit={handleEvaluate} className="space-y-4" data-testid="red-flag-form">
          <div>
            <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Entity ID</label>
            <input
              type="text"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
              placeholder="Enter entity ID from search results..."
              className="w-full scoi-input"
              data-testid="entity-id-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !entityId.trim()}
            className="scoi-button-primary w-full disabled:opacity-50"
            data-testid="evaluate-button"
          >
            {loading ? 'Evaluating...' : 'Run Red Flag Analysis'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="red-flag-error">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>

      {matches.length > 0 && (
        <div data-testid="red-flag-matches">
          <div className="mb-4 flex items-center gap-2">
            <Warning size={24} weight="bold" className="text-red-600" />
            <h3 className="text-lg font-bold text-slate-900">
              {matches.length} Red {matches.length === 1 ? 'Flag' : 'Flags'} Detected
            </h3>
          </div>

          <div className="space-y-4">
            {matches.map((match, idx) => (
              <div key={idx} className="border-l-4 border-red-600 bg-red-50 p-6" data-testid={`red-flag-${idx}`}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="text-base font-black tracking-tight text-slate-900 mb-1">{match.rule_name}</h4>
                    <p className="text-xs uppercase tracking-widest font-bold text-red-600">{match.rule_id}</p>
                  </div>
                  <span className="scoi-badge-red">CONFIDENCE: {(match.confidence * 100).toFixed(0)}%</span>
                </div>

                <div className="space-y-2 text-sm text-slate-700">
                  <p><strong>Entities Involved:</strong> {match.entities.length}</p>
                  {match.metadata && Object.keys(match.metadata).length > 0 && (
                    <div>
                      <strong>Details:</strong>
                      <ul className="mt-1 ml-4 list-disc text-xs">
                        {Object.entries(match.metadata).map(([key, value]) => (
                          <li key={key}>
                            {key}: {typeof value === 'object' ? JSON.stringify(value) : value}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <p className="text-xs text-slate-500">Detected: {new Date(match.detected_at).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && matches.length === 0 && entityId && (
        <div className="scoi-card text-center py-12" data-testid="no-red-flags">
          <Target size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
          <p className="text-sm text-slate-600">No red flags detected for this entity.</p>
        </div>
      )}
    </div>
  );
};

export default RedFlagDashboard;