import React, { useState } from 'react';
import axios from 'axios';
import { MagnifyingGlass, User, Buildings, Vault, Gavel, Target, House } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SearchEntities = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedType, setSelectedType] = useState('');
  const [error, setError] = useState('');

  const entityTypes = [
    { value: '', label: 'All Types', icon: Target },
    { value: 'person', label: 'Person', icon: User },
    { value: 'company', label: 'Company', icon: Buildings },
    { value: 'trust', label: 'Trust', icon: Vault },
    { value: 'tender', label: 'Tender', icon: Target },
    { value: 'judgment', label: 'Judgment', icon: Gavel },
    { value: 'asset', label: 'Asset', icon: House },
  ];

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post(
        `${BACKEND_URL}/api/entities/search`,
        {
          query: query.trim(),
          type: selectedType || null,
          fuzzy: true,
          limit: 50
        },
        { withCredentials: true }
      );
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const getEntityIcon = (type) => {
    const iconMap = {
      person: User,
      company: Buildings,
      trust: Vault,
      tender: Target,
      judgment: Gavel
    };
    const Icon = iconMap[type] || Target;
    return <Icon size={20} weight="bold" />;
  };

  return (
    <div data-testid="search-entities-container">
      <div className="scoi-card mb-6">
        <form onSubmit={handleSearch} className="space-y-4" data-testid="entity-search-form">
          <div>
            <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-3">Search Query</label>
            <div className="relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter name, registration number, or address..."
                className="w-full scoi-input pl-12 text-base py-3"
                data-testid="search-input"
              />
              <MagnifyingGlass size={24} weight="bold" className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-3">Entity Type</label>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
              {entityTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setSelectedType(type.value)}
                    className={`p-3 border rounded-sm flex flex-col items-center justify-center gap-2 transition-all duration-200 ${
                      selectedType === type.value
                        ? 'bg-slate-900 text-white border-slate-900'
                        : 'bg-white text-slate-600 border-slate-300 hover:border-slate-900'
                    }`}
                    data-testid={`filter-${type.value || 'all'}`}
                  >
                    <Icon size={20} weight="bold" />
                    <span className="text-xs font-semibold">{type.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="scoi-button-primary w-full py-3 disabled:opacity-50"
            data-testid="search-submit-button"
          >
            {loading ? 'Searching...' : 'Search Entities'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="search-error">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="scoi-card" data-testid="search-results">
          <h3 className="text-lg font-bold mb-4 text-slate-900">
            Found {results.length} {results.length === 1 ? 'Entity' : 'Entities'}
          </h3>
          
          <div className="overflow-x-auto">
            <table className="scoi-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Confidence</th>
                  <th>First Seen</th>
                </tr>
              </thead>
              <tbody>
                {results.map((entity) => (
                  <tr key={entity.id} className="hover:bg-slate-50" data-testid={`entity-row-${entity.id}`}>
                    <td>
                      <div className="flex items-center gap-2">
                        {getEntityIcon(entity.type)}
                        <span className="text-xs uppercase tracking-widest font-bold text-slate-600">{entity.type}</span>
                      </div>
                    </td>
                    <td className="font-semibold text-slate-900">{entity.raw_name}</td>
                    <td className="text-sm text-slate-600">{entity.source}</td>
                    <td>
                      {entity.confidence_score && (
                        <span className="text-xs font-mono font-bold text-slate-700">
                          {(entity.confidence_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </td>
                    <td className="text-sm text-slate-600">
                      {new Date(entity.first_seen).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && results.length === 0 && query && (
        <div className="scoi-card text-center py-12" data-testid="no-results">
          <MagnifyingGlass size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
          <p className="text-sm text-slate-600">No entities found matching your query.</p>
        </div>
      )}
    </div>
  );
};

export default SearchEntities;