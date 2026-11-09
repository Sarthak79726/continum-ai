import React, { useEffect, useState } from 'react';
import {
  Network,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Filter,
  ShieldAlert,
  CheckCircle,
  FileText,
  User,
  GitFork,
  X,
  Layers
} from 'lucide-react';
import { projectApi, graphApi } from '../services/api';
import { Project, KnowledgeGraphData, GraphNode } from '../types';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

export const KnowledgeGraphPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters & Interactivity
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadGraph(selectedProjectId);
    }
  }, [selectedProjectId]);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const projs = await projectApi.list();
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadGraph = async (projId: number) => {
    try {
      const data = await graphApi.getGraph(projId);
      setGraphData(data);
      setSelectedNode(null);
    } catch (err) {
      console.error(err);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Filter nodes based on category filter
  const visibleNodes = (graphData?.nodes || []).filter((n) => {
    if (categoryFilter === 'all') return true;
    return n.type === categoryFilter;
  });

  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));

  const visibleEdges = (graphData?.edges || []).filter(
    (e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target)
  );

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Interactive Knowledge Graph</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Signature Feature: Multi-entity topological graph showing people, tasks, decisions, dependencies and blockers.
          </p>
        </div>

        {projects.length > 0 && (
          <div className="flex items-center gap-3">
            <select
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(Number(e.target.value))}
              className="px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-teal-500 font-semibold text-slate-800"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.is_demo ? '(DEMO)' : ''}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Canvas Area */}
      <div className="relative bg-slate-950 rounded-2xl border border-slate-800 h-[640px] overflow-hidden shadow-xl select-none">
        {/* Top Control Bar */}
        <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
          {/* Category Filter Pill Group */}
          <div className="flex items-center gap-1 bg-slate-900/90 backdrop-blur-md p-1 rounded-lg border border-slate-800 text-[11px]">
            {['all', 'project', 'person', 'component', 'task', 'decision', 'risk'].map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded-md capitalize font-medium transition-colors ${
                  categoryFilter === cat
                    ? 'bg-teal-500 text-slate-950'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Zoom & Pan Controls */}
        <div className="absolute top-4 right-4 z-20 flex items-center gap-1 bg-slate-900/90 backdrop-blur-md p-1 rounded-lg border border-slate-800 text-slate-400">
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.15, 2.0))}
            className="p-1.5 hover:text-white hover:bg-slate-800 rounded"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.15, 0.5))}
            className="p-1.5 hover:text-white hover:bg-slate-800 rounded"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={resetView}
            className="p-1.5 hover:text-white hover:bg-slate-800 rounded"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Interactive SVG Canvas */}
        <div
          className="w-full h-full cursor-grab active:cursor-grabbing"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <svg
            className="w-full h-full"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '500px 300px',
              transition: isDragging ? 'none' : 'transform 0.1s ease-out',
            }}
            viewBox="0 0 1000 600"
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="16"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="#06b6d4" />
              </marker>
            </defs>

            {/* Edge Lines */}
            {visibleEdges.map((e, idx) => {
              const sNode = visibleNodes.find((n) => n.id === e.source);
              const tNode = visibleNodes.find((n) => n.id === e.target);
              if (!sNode || !tNode) return null;

              const isDependency = e.label === 'Depends on';
              const isRiskEdge = e.label?.includes('Risk');

              return (
                <g key={idx}>
                  <line
                    x1={sNode.position.x}
                    y1={sNode.position.y}
                    x2={tNode.position.x}
                    y2={tNode.position.y}
                    stroke={isRiskEdge ? '#f43f5e' : isDependency ? '#06b6d4' : '#334155'}
                    strokeWidth={isDependency ? 2 : 1.2}
                    strokeDasharray={isDependency || isRiskEdge ? '4 4' : undefined}
                    markerEnd={isDependency ? 'url(#arrowhead)' : undefined}
                  />
                  {e.label && (
                    <text
                      x={(sNode.position.x + tNode.position.x) / 2}
                      y={(sNode.position.y + tNode.position.y) / 2 - 4}
                      textAnchor="middle"
                      fill="#94a3b8"
                      fontSize={9}
                      fontFamily="monospace"
                    >
                      {e.label}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Nodes */}
            {visibleNodes.map((n) => {
              const isSelected = selectedNode?.id === n.id;
              const isRoot = n.type === 'project';
              const isPerson = n.type === 'person';
              const isRisk = n.type === 'risk';
              const isComp = n.type === 'component';
              const isDecision = n.type === 'decision';

              let fill = '#1e293b';
              let stroke = '#475569';
              let radius = 20;

              if (isRoot) {
                fill = '#0d9488';
                stroke = '#2dd4bf';
                radius = 32;
              } else if (isPerson) {
                fill = '#0284c7';
                stroke = '#38bdf8';
                radius = 24;
              } else if (isRisk) {
                fill = '#e11d48';
                stroke = '#fb7185';
                radius = 20;
              } else if (isComp) {
                fill = '#4f46e5';
                stroke = '#818cf8';
                radius = 22;
              } else if (isDecision) {
                fill = '#d97706';
                stroke = '#fbbf24';
                radius = 20;
              }

              return (
                <g
                  key={n.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNode(n);
                  }}
                  className="cursor-pointer group"
                >
                  <circle
                    cx={n.position.x}
                    cy={n.position.y}
                    r={radius}
                    fill={fill}
                    stroke={isSelected ? '#ffffff' : stroke}
                    strokeWidth={isSelected ? 3 : 2}
                    className="transition-all hover:opacity-90"
                  />
                  <text
                    x={n.position.x}
                    y={n.position.y + radius + 14}
                    textAnchor="middle"
                    fill={isSelected ? '#ffffff' : '#cbd5e1'}
                    fontSize={10}
                    fontWeight={isSelected ? 'bold' : '500'}
                  >
                    {n.data.label.length > 24 ? n.data.label.slice(0, 22) + '...' : n.data.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <div className="absolute bottom-4 right-4 z-30 w-80 bg-slate-900/95 backdrop-blur-md rounded-xl border border-slate-700 p-4 shadow-2xl text-xs text-slate-300 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center justify-between mb-2">
              <span className="uppercase text-[10px] font-bold text-teal-400 font-mono tracking-wider">
                {selectedNode.type} Entity
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 text-slate-400 hover:text-white rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <h4 className="text-sm font-bold text-white mb-1.5">{selectedNode.data.label}</h4>
            <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
              {selectedNode.data.details || 'Reconstructed entity in project state.'}
            </p>

            {selectedNode.data.evidence && (
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px]">
                <div className="font-semibold text-teal-300 mb-0.5">Source Evidence:</div>
                <div className="text-slate-400 font-mono italic">"{selectedNode.data.evidence}"</div>
              </div>
            )}

            {selectedNode.data.status && (
              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                <span>Status:</span>
                <span className="font-semibold text-slate-200 capitalize">{selectedNode.data.status}</span>
              </div>
            )}
          </div>
        )}

        {/* Footer Legend */}
        <div className="absolute bottom-3 left-4 z-20 flex items-center gap-4 text-[10px] text-slate-400 bg-slate-900/80 backdrop-blur-xs px-3 py-1.5 rounded-lg border border-slate-800">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-teal-500" /> Project</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-sky-500" /> Team Member</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-indigo-500" /> Component</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500" /> Decision</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500" /> Blocker / Risk</span>
        </div>
      </div>
    </div>
  );
};

