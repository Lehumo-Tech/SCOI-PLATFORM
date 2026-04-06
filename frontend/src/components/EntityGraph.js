import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Graph } from '@phosphor-icons/react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const EntityGraph = () => {
  const [entityId, setEntityId] = useState('');
  const [hops, setHops] = useState(2);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const nodeColors = {
    person: '#2563EB',
    company: '#16A34A',
    trust: '#D97706',
    tender: '#DC2626',
    judgment: '#7C3AED'
  };

  const handleFetchGraph = async (e) => {
    e.preventDefault();
    if (!entityId.trim()) return;

    setLoading(true);
    setError('');
    try {
      const { data } = await axios.get(
        `${BACKEND_URL}/api/entities/graph/${entityId.trim()}?hops=${hops}`,
        { withCredentials: true }
      );

      const graphNodes = data.nodes.map((node, idx) => ({
        id: node.id,
        data: { label: node.label },
        position: { x: Math.cos((idx / data.nodes.length) * 2 * Math.PI) * 300, y: Math.sin((idx / data.nodes.length) * 2 * Math.PI) * 300 },
        style: {
          background: nodeColors[node.type] || '#64748B',
          color: 'white',
          border: '2px solid #0F172A',
          borderRadius: '2px',
          padding: '12px',
          fontSize: '12px',
          fontWeight: 'bold',
          fontFamily: 'IBM Plex Sans'
        }
      }));

      const graphEdges = data.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        type: 'smoothstep',
        style: { stroke: '#94A3B8', strokeWidth: 2 },
        labelStyle: { fontSize: '10px', fontWeight: 'bold', fill: '#0F172A' },
        labelBgStyle: { fill: '#FFFFFF', fillOpacity: 0.9 }
      }));

      setNodes(graphNodes);
      setEdges(graphEdges);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch graph');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="entity-graph-container">
      <div className="scoi-card mb-6">
        <form onSubmit={handleFetchGraph} className="space-y-4" data-testid="graph-form">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Entity ID</label>
              <input
                type="text"
                value={entityId}
                onChange={(e) => setEntityId(e.target.value)}
                placeholder="Enter entity ID from search..."
                className="w-full scoi-input"
                data-testid="graph-entity-id-input"
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-[0.2em] font-bold text-slate-500 mb-2">Relationship Hops</label>
              <select
                value={hops}
                onChange={(e) => setHops(parseInt(e.target.value))}
                className="w-full scoi-input"
                data-testid="graph-hops-select"
              >
                <option value={1}>1 Hop</option>
                <option value={2}>2 Hops</option>
                <option value={3}>3 Hops</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !entityId.trim()}
            className="scoi-button-primary w-full disabled:opacity-50"
            data-testid="graph-submit-button"
          >
            {loading ? 'Loading Graph...' : 'Generate Network Graph'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-sm" data-testid="graph-error">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>

      {nodes.length > 0 ? (
        <div className="scoi-card p-0" data-testid="graph-visualization">
          <div className="p-4 border-b border-slate-200">
            <div className="flex items-center gap-2">
              <Graph size={20} weight="bold" className="text-slate-900" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900">
                Network Graph ({nodes.length} entities, {edges.length} relationships)
              </h3>
            </div>
          </div>
          <div style={{ height: '600px', background: '#F8FAFC' }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
            >
              <Background color="#CBD5E1" gap={16} />
              <Controls />
              <MiniMap nodeColor={(node) => node.style.background} />
            </ReactFlow>
          </div>
          <div className="p-4 border-t border-slate-200 bg-slate-50">
            <p className="text-xs text-slate-600">Use mouse wheel to zoom, drag to pan. Click and drag nodes to rearrange.</p>
          </div>
        </div>
      ) : (
        <div className="scoi-card text-center py-12" data-testid="graph-empty">
          <Graph size={48} weight="bold" className="mx-auto mb-4 text-slate-300" />
          <p className="text-sm text-slate-600">Enter an entity ID to visualize its network.</p>
        </div>
      )}
    </div>
  );
};

export default EntityGraph;