import React, { useState } from 'react';
import axios from 'axios';
import { Detective, House, Car, CurrencyDollar, ShieldWarning } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AssetTracing = () => {
  const [personId, setPersonId] = useState('');
  const [traceResult, setTraceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTrace = async (e) => {
    e.preventDefault();
    if (!personId.trim()) return;

    setLoading(true);
    setError('');
    setTraceResult(null);
    try {
      const { data } = await axios.get(
        `${BACKEND_URL}/api/assets/trace/${personId.trim()}`,
        { withCredentials: true }
      );
      setTraceResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Asset trace failed');
    } finally {
      setLoading(false);
    }
  };

  const getAssetIcon = (type) => {
    if (type === 'property') return <House size={20} weight="bold" />;
    if (type === 'vehicle') return <Car size={20} weight="bold" />;
    return <CurrencyDollar size={20} weight="bold" />;
  };

  const getOwnershipBadge = (type) => {
    const styles = {
      direct: 'bg-green-50 text-green-700 border-green-200',
      'VIA_TRUST': 'bg-yellow-50 text-yellow-800 border-yellow-200',
      'VIA_NOMINEE': 'bg-red-50 text-red-700 border-red-200',
      'BENEFICIAL_OWNER_OF': 'bg-blue-50 text-blue-700 border-blue-200',
      'OWNS': 'bg-green-50 text-green-700 border-green-200',
    };
    return styles[type] || 'bg-slate-50 text-slate-700 border-slate-200';
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR', maximumFractionDigits: 0 }).format(value);
  };

  return (
    <div data-testid="asset-tracing-container">
      <div className="scoi-card mb-6">
        <div className="flex items-center gap-2 mb-6">
          <Detective size={24} weight="bold" className="text-slate-900" />
          <h2 className="text-lg font-bold text-slate-900">Asset Tracing</h2>
        </div>
        <p className="text-sm text-slate-600 mb-6">
          Trace assets linked to individuals, including those disguised under trusts or nominee structures.
        </p>

        <form onSubmit={handleTrace} className="space-y-4" data-testid="asset-trace-form">
          <div>
            <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Person Entity ID</label>
            <input
              type="text"
              value={personId}
              onChange={(e) => setPersonId(e.target.value)}
              placeholder="Enter person entity ID from search..."
              className="w-full scoi-input"
              data-testid="asset-trace-person-id"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !personId.trim()}
            className="scoi-button-primary w-full py-3 disabled:opacity-50"
            data-testid="asset-trace-submit"
          >
            {loading ? 'Tracing Assets...' : 'Trace Assets'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="asset-trace-error">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>

      {traceResult && (
        <div data-testid="asset-trace-results">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-slate-200 border border-slate-200 mb-6">
            <div className="bg-white p-6">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Subject</p>
              <p className="text-lg font-black tracking-tight text-slate-900">{traceResult.person.name}</p>
              <p className="text-xs uppercase tracking-widest text-slate-500 mt-1">{traceResult.person.type}</p>
            </div>
            <div className="bg-white p-6">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Assets Found</p>
              <p className="text-3xl font-black tracking-tight text-slate-900">{traceResult.total_assets}</p>
            </div>
            <div className="bg-white p-6">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Est. Total Value</p>
              <p className="text-2xl font-black tracking-tight text-slate-900">{formatCurrency(traceResult.total_estimated_value)}</p>
            </div>
          </div>

          <div className="space-y-3">
            {traceResult.assets.map((asset, idx) => (
              <div
                key={idx}
                className="scoi-card flex items-start gap-4"
                data-testid={`traced-asset-${idx}`}
              >
                <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center bg-slate-100 rounded-sm">
                  {getAssetIcon(asset.asset_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{asset.asset_name}</h4>
                      <p className="text-xs text-slate-500 mt-1">
                        {asset.asset_type} {asset.transfer_date && `| Transferred: ${asset.transfer_date}`}
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-bold font-mono text-slate-900">{formatCurrency(asset.value)}</p>
                      <p className="text-xs font-mono text-slate-500">Conf: {(asset.confidence * 100).toFixed(0)}%</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-xs font-bold uppercase tracking-widest px-2 py-1 border rounded-sm ${getOwnershipBadge(asset.ownership_type)}`}>
                      {asset.via_type === 'direct' ? 'Direct' : asset.ownership_type.replace(/_/g, ' ')}
                    </span>
                    {asset.via_entity && (
                      <span className="text-xs text-slate-500">
                        via {asset.via_entity.name} ({asset.via_entity.type})
                      </span>
                    )}
                  </div>
                  {asset.evidence.length > 0 && (
                    <p className="text-xs text-slate-400 mt-1 font-mono">{asset.evidence.join(', ')}</p>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-sm flex items-start gap-3">
            <ShieldWarning size={20} weight="bold" className="text-yellow-700 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-yellow-800">{traceResult.disclaimer}</p>
          </div>
        </div>
      )}

      {!loading && !traceResult && !error && (
        <div className="scoi-card text-center py-12" data-testid="asset-trace-empty">
          <Detective size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
          <p className="text-sm text-slate-600">Enter a person's entity ID to trace their assets through trusts and nominees.</p>
        </div>
      )}
    </div>
  );
};

export default AssetTracing;
