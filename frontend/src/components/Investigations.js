import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Robot, Play, CheckCircle, XCircle, FileText, FileCsv, Download, ShieldCheck, Warning, CaretDown, CaretRight } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Investigations = () => {
  const [investigations, setInvestigations] = useState([]);
  const [selectedInv, setSelectedInv] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [query, setQuery] = useState('');
  const [entityIds, setEntityIds] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [runLoading, setRunLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedSections, setExpandedSections] = useState({});

  const fetchInvestigations = useCallback(async () => {
    try {
      const { data } = await axios.get(`${BACKEND_URL}/api/investigations/`, { withCredentials: true });
      setInvestigations(data);
    } catch (err) {
      // Silently handle - user might not have any investigations yet
    }
  }, []);

  useEffect(() => { fetchInvestigations(); }, [fetchInvestigations]);

  const handleRunInvestigation = async (e) => {
    e.preventDefault();
    if (!entityIds.trim()) return;
    setRunLoading(true);
    setError('');

    try {
      const ids = entityIds.split(',').map(s => s.trim()).filter(Boolean);
      const { data } = await axios.post(
        `${BACKEND_URL}/api/investigations/run`,
        { query: query || 'Investigation', entity_ids: ids, title: title || null },
        { withCredentials: true }
      );
      setSelectedInv(data);
      setShowNewForm(false);
      fetchInvestigations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Investigation failed');
    } finally {
      setRunLoading(false);
    }
  };

  const handleViewInvestigation = async (id) => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${BACKEND_URL}/api/investigations/${id}`, { withCredentials: true });
      setSelectedInv(data.result || data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load investigation');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id, approved) => {
    try {
      await axios.post(
        `${BACKEND_URL}/api/investigations/${id}/approve`,
        { approved, notes: approved ? 'Approved after review' : 'Rejected' },
        { withCredentials: true }
      );
      fetchInvestigations();
    } catch (err) {
      setError(err.response?.data?.detail || 'Approval failed');
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const SectionToggle = ({ id, title, count, children }) => (
    <div className="border border-slate-200 rounded-sm mb-3">
      <button
        onClick={() => toggleSection(id)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
        data-testid={`section-toggle-${id}`}
      >
        <div className="flex items-center gap-2">
          {expandedSections[id] ? <CaretDown size={16} weight="bold" /> : <CaretRight size={16} weight="bold" />}
          <span className="text-sm font-bold uppercase tracking-widest text-slate-900">{title}</span>
          {count !== undefined && (
            <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded-sm">{count}</span>
          )}
        </div>
      </button>
      {expandedSections[id] && <div className="p-4 pt-0 border-t border-slate-200">{children}</div>}
    </div>
  );

  return (
    <div data-testid="investigations-container">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Robot size={24} weight="bold" className="text-slate-900" />
          <h2 className="text-lg font-bold text-slate-900">Multi-Agent Investigations</h2>
        </div>
        <button
          onClick={() => { setShowNewForm(!showNewForm); setSelectedInv(null); }}
          className="scoi-button-primary flex items-center gap-2"
          data-testid="new-investigation-btn"
        >
          <Play size={16} weight="bold" /> New Investigation
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="investigation-error">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {showNewForm && (
        <div className="scoi-card mb-6" data-testid="new-investigation-form">
          <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900 mb-4">Launch Investigation Pipeline</h3>
          <p className="text-xs text-slate-500 mb-4">
            Runs 5 agents: Lead Investigator &rarr; Deep Researcher &rarr; Entity Resolver &rarr; Compliance Auditor &rarr; Report Synthesizer
          </p>
          <form onSubmit={handleRunInvestigation} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Investigation Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Ekurhuleni Tender Network Analysis"
                  className="w-full scoi-input"
                  data-testid="investigation-title-input"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Query / Focus</label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g., Director rotation in Ekurhuleni"
                  className="w-full scoi-input"
                  data-testid="investigation-query-input"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Entity IDs (comma-separated)</label>
              <input
                type="text"
                value={entityIds}
                onChange={(e) => setEntityIds(e.target.value)}
                placeholder="Paste entity IDs from search results, separated by commas..."
                className="w-full scoi-input"
                required
                data-testid="investigation-entity-ids-input"
              />
            </div>
            <button
              type="submit"
              disabled={runLoading || !entityIds.trim()}
              className="scoi-button-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-50"
              data-testid="run-investigation-btn"
            >
              <Robot size={18} weight="bold" className={runLoading ? 'animate-spin' : ''} />
              {runLoading ? 'Running 5-Agent Pipeline...' : 'Run Investigation'}
            </button>
          </form>
        </div>
      )}

      {/* Investigation Result */}
      {selectedInv && (
        <div className="space-y-4 mb-8" data-testid="investigation-result">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 border border-slate-200">
            <div className="bg-white p-4">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-1">Status</p>
              <p className="text-sm font-black uppercase tracking-widest text-slate-900">{selectedInv.status}</p>
            </div>
            <div className="bg-white p-4">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-1">Confidence</p>
              <p className="text-2xl font-black text-slate-900">{((selectedInv.confidence || 0) * 100).toFixed(0)}%</p>
            </div>
            <div className="bg-white p-4">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-1">Compliance</p>
              <p className={`text-2xl font-black ${(selectedInv.compliance_score || 0) >= 80 ? 'text-green-600' : 'text-red-600'}`}>
                {(selectedInv.compliance_score || 0).toFixed(0)}/100
              </p>
            </div>
            <div className="bg-white p-4">
              <p className="text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-1">Red Flags</p>
              <p className={`text-2xl font-black ${(selectedInv.red_flags_count || 0) > 0 ? 'text-red-600' : 'text-slate-900'}`}>
                {selectedInv.red_flags_count || 0}
              </p>
            </div>
          </div>

          {/* Red Flags */}
          {selectedInv.red_flags && selectedInv.red_flags.length > 0 && (
            <SectionToggle id="red_flags" title="Red Flags Detected" count={selectedInv.red_flags.length}>
              <div className="space-y-2">
                {selectedInv.red_flags.map((rf, idx) => (
                  <div key={idx} className="border-l-4 border-red-600 bg-red-50 p-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-bold text-slate-900">{rf.rule_name || rf.rule_id}</h4>
                      <span className="scoi-badge-red">CONF: {((rf.confidence || 0) * 100).toFixed(0)}%</span>
                    </div>
                    {rf.metadata && Object.entries(rf.metadata).map(([k, v]) => (
                      <p key={k} className="text-xs text-slate-600 mt-1">{k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}</p>
                    ))}
                  </div>
                ))}
              </div>
            </SectionToggle>
          )}

          {/* Audit Trail */}
          {selectedInv.audit_trail && selectedInv.audit_trail.length > 0 && (
            <SectionToggle id="audit_trail" title="Agent Audit Trail" count={selectedInv.audit_trail.length}>
              <div className="space-y-1">
                {selectedInv.audit_trail.map((entry, idx) => (
                  <div key={idx} className="flex items-start gap-3 py-2 border-b border-slate-100 last:border-0">
                    <span className="text-xs font-mono text-slate-400 flex-shrink-0 w-36">{entry.timestamp?.slice(11, 19) || ''}</span>
                    <span className="text-xs font-bold uppercase tracking-widest text-blue-700 flex-shrink-0 w-40">{entry.agent}</span>
                    <span className="text-xs text-slate-700">{entry.action}: {entry.detail}</span>
                  </div>
                ))}
              </div>
            </SectionToggle>
          )}

          {/* Report */}
          {selectedInv.report && (
            <SectionToggle id="report" title="Investigation Report">
              <div className="prose prose-sm max-w-none text-slate-800 font-mono text-xs whitespace-pre-wrap bg-slate-50 p-4 border border-slate-200 rounded-sm max-h-96 overflow-y-auto">
                {selectedInv.report}
              </div>
            </SectionToggle>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            {selectedInv.id && (
              <>
                <a
                  href={`${BACKEND_URL}/api/investigations/${selectedInv.id}/export/markdown`}
                  className="scoi-button-primary flex items-center gap-2"
                  data-testid="export-markdown-btn"
                >
                  <FileText size={16} weight="bold" /> Export Markdown
                </a>
                <a
                  href={`${BACKEND_URL}/api/investigations/${selectedInv.id}/export/csv`}
                  className="scoi-button-primary flex items-center gap-2"
                  data-testid="export-csv-btn"
                >
                  <FileCsv size={16} weight="bold" /> Export CSV
                </a>
              </>
            )}
          </div>
        </div>
      )}

      {/* Past Investigations List */}
      {investigations.length > 0 && (
        <div data-testid="investigations-list">
          <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900 mb-4">Past Investigations</h3>
          <div className="space-y-2">
            {investigations.map((inv) => (
              <div
                key={inv.id}
                className="scoi-card flex items-center justify-between cursor-pointer hover:bg-slate-50"
                onClick={() => handleViewInvestigation(inv.id)}
                data-testid={`investigation-item-${inv.id}`}
              >
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{inv.title}</h4>
                  <p className="text-xs text-slate-500">
                    {new Date(inv.created_at).toLocaleString()} | Confidence: {((inv.confidence || 0) * 100).toFixed(0)}% | Red Flags: {inv.red_flags_count || 0}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold uppercase tracking-widest px-2 py-1 rounded-sm border ${
                    inv.approved ? 'bg-green-50 text-green-700 border-green-200' :
                    inv.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200' :
                    'bg-yellow-50 text-yellow-700 border-yellow-200'
                  }`}>
                    {inv.approved ? 'APPROVED' : inv.status === 'rejected' ? 'REJECTED' : 'PENDING'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!showNewForm && !selectedInv && investigations.length === 0 && (
        <div className="scoi-card text-center py-12" data-testid="no-investigations">
          <Robot size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
          <p className="text-sm text-slate-600">No investigations yet. Click "New Investigation" to launch the multi-agent pipeline.</p>
        </div>
      )}
    </div>
  );
};

export default Investigations;
