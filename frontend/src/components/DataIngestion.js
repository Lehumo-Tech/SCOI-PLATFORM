import React, { useState } from 'react';
import axios from 'axios';
import { Database, Plus, CheckCircle } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const DataIngestion = () => {
  const [entityData, setEntityData] = useState({
    type: 'person',
    raw_name: '',
    source: '',
    source_url: '',
    metadata: {}
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await axios.post(
        `${BACKEND_URL}/api/entities/`,
        entityData,
        { withCredentials: true }
      );
      setSuccess(`Entity "${entityData.raw_name}" created successfully!`);
      setEntityData({
        type: 'person',
        raw_name: '',
        source: '',
        source_url: '',
        metadata: {}
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create entity');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="data-ingestion-container">
      <div className="scoi-card">
        <div className="flex items-center gap-2 mb-6">
          <Database size={24} weight="bold" className="text-slate-900" />
          <h2 className="text-lg font-bold text-slate-900">Manual Data Ingestion</h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6" data-testid="ingestion-form">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Entity Type</label>
              <select
                value={entityData.type}
                onChange={(e) => setEntityData({ ...entityData, type: e.target.value })}
                className="w-full scoi-input"
                data-testid="entity-type-select"
              >
                <option value="person">Person</option>
                <option value="company">Company</option>
                <option value="trust">Trust</option>
                <option value="tender">Tender</option>
                <option value="judgment">Judgment</option>
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Name</label>
              <input
                type="text"
                value={entityData.raw_name}
                onChange={(e) => setEntityData({ ...entityData, raw_name: e.target.value })}
                className="w-full scoi-input"
                placeholder="Entity name..."
                required
                data-testid="entity-name-input"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Source</label>
              <input
                type="text"
                value={entityData.source}
                onChange={(e) => setEntityData({ ...entityData, source: e.target.value })}
                className="w-full scoi-input"
                placeholder="e.g., CIPC, Government Gazette"
                required
                data-testid="entity-source-input"
              />
            </div>

            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Source URL (Optional)</label>
              <input
                type="url"
                value={entityData.source_url}
                onChange={(e) => setEntityData({ ...entityData, source_url: e.target.value })}
                className="w-full scoi-input"
                placeholder="https://..."
                data-testid="entity-source-url-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Metadata (JSON)</label>
            <textarea
              value={JSON.stringify(entityData.metadata, null, 2)}
              onChange={(e) => {
                try {
                  setEntityData({ ...entityData, metadata: JSON.parse(e.target.value) });
                } catch {}
              }}
              className="w-full scoi-input font-mono text-xs"
              rows={6}
              placeholder='{"reg_no": "2023/123456/07", "status": "active"}'
              data-testid="entity-metadata-input"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="ingestion-error">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {success && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-sm flex items-center gap-2" data-testid="ingestion-success">
              <CheckCircle size={20} weight="bold" className="text-green-600" />
              <p className="text-sm text-green-700">{success}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="scoi-button-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-50"
            data-testid="ingestion-submit-button"
          >
            <Plus size={18} weight="bold" />
            {loading ? 'Creating Entity...' : 'Create Entity'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default DataIngestion;