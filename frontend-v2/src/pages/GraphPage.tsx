import React, { useState, useRef, useCallback, Suspense, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Network, ZoomIn, ZoomOut, Maximize2, Download, ChevronRight, ChevronLeft, Loader2, AlertCircle, Activity } from 'lucide-react';
import { apiService } from '../lib/apiService';

const ForceGraph2D = React.lazy(() => import('react-force-graph-2d'));

interface GraphNode {
  id: string;
  name?: string;
  riskScore?: number;
  flagged?: boolean;
  [key: string]: unknown;
}

interface GraphLink {
  source: string;
  target: string;
  amount: number;
  channel: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface TooltipData {
  node: GraphNode;
  x: number;
  y: number;
}

const NODE_COLORS = {
  flagged: '#ef4444',   // red-500
  normal: '#f59e0b',    // amber-500
  low: '#22c55e',       // green-500
};

function getNodeColor(node: GraphNode): string {
  if (node.flagged) return NODE_COLORS.flagged;
  if (node.riskScore !== undefined && node.riskScore >= 6) return NODE_COLORS.normal;
  return NODE_COLORS.low;
}

function Legend() {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Legend</h3>
      <div className="space-y-1.5">
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
          <span className="w-3 h-3 rounded-full bg-red-500 shrink-0" />
          High Risk (Flagged)
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
          <span className="w-3 h-3 rounded-full bg-amber-500 shrink-0" />
          Normal Risk
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
          <span className="w-3 h-3 rounded-full bg-green-500 shrink-0" />
          Low Risk
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <span className="w-6 h-0.5 bg-gray-400 shrink-0" />
          Transaction Link
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
          <span className="w-6 h-px bg-gray-400 shrink-0" style={{ borderBottom: '1px dashed' }} />
          Link width = Amount
        </div>
      </div>
    </div>
  );
}

function SelectedNodePanel({ node }: { node: GraphNode | null }) {
  if (!node) {
    return (
      <div className="text-xs text-gray-500 dark:text-gray-400 italic">
        Click a node to view details
      </div>
    );
  }

  const entries = Object.entries(node).filter(([key]) => key !== '__indexColor');

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Selected Node</h3>
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 space-y-1.5">
        {entries.map(([key, value]) => (
          <div key={key} className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400 font-medium">{key}</span>
            <span className="text-gray-900 dark:text-gray-100 font-mono truncate ml-2">
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </span>
          </div>
        ))}
      </div>
      <div
        className="w-2 h-2 rounded-full mt-1"
        style={{ backgroundColor: getNodeColor(node) }}
      />
    </div>
  );
}

function AgentActivityFeed() {
  const activities = [
    { id: 1, agent: 'ContextAgent', msg: 'Scanning transaction clusters', status: 'active' },
    { id: 2, agent: 'PathfinderAgent', msg: 'Tracing 5 fund flows', status: 'completed' },
    { id: 3, agent: 'ScorerAgent', msg: 'Recalculating risk scores', status: 'completed' },
  ];

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-1.5">
        <Activity className="w-3.5 h-3.5" />
        Agent Activity
      </h3>
      <div className="space-y-1.5">
        {activities.map((a) => (
          <div key={a.id} className="flex items-start gap-2 text-xs">
            <span
              className={`mt-0.5 w-1.5 h-1.5 rounded-full shrink-0 ${
                a.status === 'active'
                  ? 'bg-blue-500 animate-pulse'
                  : 'bg-green-500'
              }`}
            />
            <div>
              <span className="font-medium text-gray-700 dark:text-gray-300">{a.agent}</span>
              <span className="text-gray-500 dark:text-gray-400"> - {a.msg}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      <p className="text-sm text-gray-500 dark:text-gray-400">Loading graph data...</p>
    </div>
  );
}

function EmptyState({ onLoad }: { onLoad: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-6">
      <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
        <Network className="w-8 h-8 text-gray-400 dark:text-gray-500" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">No Graph Data</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Load transaction data to visualize the network graph.
        </p>
      </div>
      <button
        onClick={onLoad}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        Load Demo Data
      </button>
    </div>
  );
}

function GraphError({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-6">
      <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
        <AlertCircle className="w-6 h-6 text-red-500" />
      </div>
      <p className="text-sm text-red-600 dark:text-red-400 max-w-xs">{error}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-sm font-medium rounded-lg transition-colors text-gray-900 dark:text-gray-100"
      >
        Retry
      </button>
    </div>
  );
}

export const GraphPage: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoom, setZoom] = useState(1);

  const graphRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);

  const handleLoadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getDemoTrackA();
      const data = response.data;
      const graphPayload: GraphData = data.graph ?? data;
      if (graphPayload.nodes && graphPayload.links) {
        setGraphData(graphPayload);
        setSelectedNode(null);
        setTooltip(null);
      } else {
        setError('Unexpected data format received from API.');
      }
    } catch (err: any) {
      setError(err?.message ?? 'Failed to load graph data.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRunPipeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.runPipeline();
      const data = response.data;
      const graphPayload: GraphData = data.graph ?? data;
      if (graphPayload.nodes && graphPayload.links) {
        setGraphData(graphPayload);
        setSelectedNode(null);
        setTooltip(null);
      }
    } catch (err: any) {
      setError(err?.message ?? 'Pipeline execution failed.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleZoomIn = useCallback(() => {
    setZoom((z) => {
      const next = Math.min(z + 0.5, 4);
      fgRef.current?.zoom(next);
      return next;
    });
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((z) => {
      const next = Math.max(z - 0.5, 0.2);
      fgRef.current?.zoom(next);
      return next;
    });
  }, []);

  const handleToggleFullscreen = useCallback(() => {
    if (!graphRef.current) return;
    if (!document.fullscreenElement) {
      graphRef.current.requestFullscreen().then(() => setIsFullscreen(true));
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false));
    }
  }, []);

  const handleExportPNG = useCallback(() => {
    if (!fgRef.current) return;
    const canvas = graphRef.current?.querySelector('canvas');
    if (!canvas) return;
    const url = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.download = 'graph-analysis.png';
    a.href = url;
    a.click();
  }, []);

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node as GraphNode);
    setTooltip(null);
    setSidePanelOpen(true);
  }, []);

  const handleNodeHover = useCallback(
    (node: any) => {
      if (node) {
        setTooltip({
          node: node as GraphNode,
          x: (node as any).x ?? 0,
          y: (node as any).y ?? 0,
        });
      } else {
        setTooltip(null);
      }
    },
    [],
  );

  const nodeCanvasObject = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const n = node as GraphNode & { x: number; y: number };
      const label = n.id;
      const fontSize = 12 / globalScale;
      const radius = 6 / globalScale;

      ctx.beginPath();
      ctx.arc(n.x, n.y, radius, 0, 2 * Math.PI, false);
      ctx.fillStyle = getNodeColor(n);
      ctx.fill();

      if (n.flagged) {
        ctx.strokeStyle = '#dc2626';
        ctx.lineWidth = 2 / globalScale;
        ctx.stroke();
      }

      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#1f2937';
      ctx.fillText(label, n.x, n.y + radius + fontSize);
    },
    [],
  );

  const linkWidth = useCallback((link: any) => {
    const l = link as GraphLink;
    return Math.max(1, Math.min(6, l.amount / 1000));
  }, []);

  const linkColor = useCallback(() => '#9ca3af', []);

  const hasData = graphData && graphData.nodes.length > 0;

  return (
    <div className="flex flex-col h-full min-h-[calc(100vh-4rem)]">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
            <Network className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Graph Analysis</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Interactive transaction flow network visualization
            </p>
          </div>
        </div>
      </motion.div>

      {/* Controls Bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.3 }}
        className="flex flex-wrap items-center gap-2 px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
      >
        <button
          onClick={handleLoadData}
          disabled={loading}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
          Load Data
        </button>
        <button
          onClick={handleRunPipeline}
          disabled={loading}
          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-1.5"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
          Run Pipeline
        </button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        <button
          onClick={handleZoomIn}
          disabled={!hasData}
          className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 text-gray-700 dark:text-gray-300 transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          disabled={!hasData}
          className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 text-gray-700 dark:text-gray-300 transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>

        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />

        <button
          onClick={handleToggleFullscreen}
          disabled={!hasData}
          className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 text-gray-700 dark:text-gray-300 transition-colors"
          title="Full Screen"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={handleExportPNG}
          disabled={!hasData}
          className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 text-gray-700 dark:text-gray-300 transition-colors"
          title="Export PNG"
        >
          <Download className="w-4 h-4" />
        </button>

        <div className="flex-1" />

        <button
          onClick={() => setSidePanelOpen((v) => !v)}
          className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
          title={sidePanelOpen ? 'Close Panel' : 'Open Panel'}
        >
          {sidePanelOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </motion.div>

      {/* Main Content */}
      <div className="flex flex-1 min-h-0">
        {/* Graph Area */}
        <motion.div
          ref={graphRef}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="flex-1 relative bg-white dark:bg-gray-900 min-h-[400px]"
        >
          {loading && <LoadingSpinner />}

          {!loading && error && (
            <GraphError error={error} onRetry={handleLoadData} />
          )}

          {!loading && !error && !hasData && (
            <EmptyState onLoad={handleLoadData} />
          )}

          {!loading && !error && hasData && (
            <Suspense fallback={<LoadingSpinner />}>
              <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeCanvasObject={nodeCanvasObject}
                nodeLabel={(node: any) => `${node.id}${node.riskScore != null ? ` (Risk: ${node.riskScore})` : ''}`}
                linkWidth={linkWidth}
                linkColor={linkColor}
                linkDirectionalArrowLength={4}
                linkDirectionalArrowRelPos={1}
                onNodeClick={handleNodeClick}
                onNodeHover={handleNodeHover}
                backgroundColor="transparent"
                width={undefined}
                height={undefined}
                cooldownTicks={100}
                onEngineStop={() => fgRef.current?.zoomToFit(400)}
              />
            </Suspense>
          )}

          {/* Tooltip overlay */}
          <AnimatePresence>
            {tooltip && (
              <motion.div
                key={tooltip.node.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="absolute top-4 left-4 bg-gray-900/90 dark:bg-gray-100/90 text-white dark:text-gray-900 text-xs rounded-lg px-3 py-2 pointer-events-none shadow-lg max-w-xs z-10"
              >
                <div className="font-semibold">{tooltip.node.id}</div>
                {tooltip.node.riskScore != null && (
                  <div>Risk Score: {tooltip.node.riskScore}</div>
                )}
                {tooltip.node.flagged && (
                  <div className="text-red-400 dark:text-red-600 font-medium">Flagged</div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Side Panel */}
        <AnimatePresence>
          {sidePanelOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-y-auto overflow-x-hidden"
            >
              <div className="p-4 space-y-5 min-w-[280px]">
                <SelectedNodePanel node={selectedNode} />
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <Legend />
                </div>
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <AgentActivityFeed />
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
