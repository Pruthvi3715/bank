"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Fullscreen, GitBranch, X } from "lucide-react";
import { GraphPayload, GraphNode } from "@/types/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

interface GraphVisualizerProps {
  graphData?: GraphPayload;
  highlightedNodes: string[];
  isolatedSubgraph?: boolean;
  onShowFullGraph?: () => void;
}

function toNodeId(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (value && typeof value === "object" && "id" in value) {
    const obj = value as { id?: string | number };
    if (typeof obj.id === "string" || typeof obj.id === "number") {
      return String(obj.id);
    }
  }
  return "";
}

const MIN_GRAPH_WIDTH = 400;
const MIN_GRAPH_HEIGHT = 380;

const CHANNEL_COLORS: Record<string, string> = {
  UPI: "#378ADD",
  NEFT: "#EF9F27",
  RTGS: "#1D9E75",
  IMPS: "#7F77DD",
  SWIFT: "#D85A30",
  ATM: "#888780",
};

export default function GraphVisualizer({
  graphData,
  highlightedNodes,
  isolatedSubgraph,
  onShowFullGraph,
}: GraphVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({
    width: MIN_GRAPH_WIDTH,
    height: MIN_GRAPH_HEIGHT,
  });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateSize = () => {
      const w = el.offsetWidth || el.clientWidth || MIN_GRAPH_WIDTH;
      const h = el.offsetHeight || el.clientHeight || MIN_GRAPH_HEIGHT;
      setDimensions({
        width: Math.max(MIN_GRAPH_WIDTH, w),
        height: Math.max(MIN_GRAPH_HEIGHT, h),
      });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(el);
    return () => observer.disconnect();
  }, [graphData?.nodes?.length]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="border border-border bg-card p-8 flex flex-col items-center justify-center text-center h-full min-h-[400px]">
        <GitBranch className="w-10 h-10 text-muted-foreground/20 mb-3" />
        <p className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
          No graph data
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Run a pipeline to visualize the knowledge graph
        </p>
      </div>
    );
  }

  const highlightSet = new Set(highlightedNodes || []);

  return (
    <div className="border border-border bg-card flex flex-col h-full relative">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <GitBranch className="w-3.5 h-3.5 text-primary" />
          <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
            Topology Map
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 text-[9px] font-mono">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-red-500" />
              <span className="text-muted-foreground">Flagged</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-amber-500" />
              <span className="text-muted-foreground">Normal</span>
            </span>
          </div>
          {isolatedSubgraph && onShowFullGraph && (
            <Button
              onClick={onShowFullGraph}
              variant="outline"
              className="gap-1 text-[10px] font-mono uppercase h-6 px-2 cursor-pointer"
            >
              <Fullscreen className="w-3 h-3" />
              Full
            </Button>
          )}
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="flex-1 overflow-hidden" ref={containerRef}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
          className="w-full h-full"
        >
          {dimensions.width > 0 && dimensions.height > 0 && (
            <ForceGraph2D
              width={dimensions.width}
              height={dimensions.height}
              graphData={graphData}
              nodeLabel={(node: { id?: string | number }) => toNodeId(node)}
              nodeColor={(node: { id?: string | number }) =>
                highlightSet.has(toNodeId(node)) ? "#ef4444" : "#f59e0b"
              }
              nodeRelSize={5}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const n = node as { id?: string | number; x?: number; y?: number };
                const id = toNodeId(n);
                const isHighlighted = highlightSet.has(id);
                const fontSize = 11 / globalScale;
                ctx.font = `500 ${fontSize}px "IBM Plex Mono", monospace`;

                const nx = n.x ?? 0;
                const ny = n.y ?? 0;

                if (isHighlighted) {
                  ctx.shadowColor = "#ef4444";
                  ctx.shadowBlur = 12;
                }

                // Square nodes for industrial feel
                const s = isHighlighted ? 5 : 3;
                ctx.fillStyle = isHighlighted ? "#ef4444" : "#f59e0b";
                ctx.fillRect(nx - s, ny - s, s * 2, s * 2);

                ctx.shadowBlur = 0;
                ctx.fillStyle = isHighlighted ? "#ef4444" : "#71717a";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(id, nx, ny + (isHighlighted ? 9 : 7));
              }}
              linkColor={(link: { source?: unknown; target?: unknown; channel?: string; color?: string }) => {
                const sId = toNodeId(link.source);
                const tId = toNodeId(link.target);
                if (highlightSet.has(sId) && highlightSet.has(tId)) {
                  return link.color || CHANNEL_COLORS[link.channel || ""] || "rgba(239, 68, 68, 0.5)";
                }
                return link.color
                  ? `${link.color}33`
                  : "rgba(245, 158, 11, 0.1)";
              }}
              linkWidth={(link: { source?: unknown; target?: unknown }) => {
                const sId = toNodeId(link.source);
                const tId = toNodeId(link.target);
                return highlightSet.has(sId) && highlightSet.has(tId) ? 2 : 0.5;
              }}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              backgroundColor="transparent"
              onNodeClick={(node: { id?: string | number }) => {
                const id = toNodeId(node);
                const found = graphData.nodes.find((n) => n.id === id);
                setSelectedNode(found || { id, ...(node as object) } as GraphNode);
              }}
            />
          )}
        </motion.div>
      </div>

      {/* Channel Legend */}
      <div className="flex items-center gap-3 px-3 py-1.5 border-t border-border text-[9px] font-mono flex-wrap">
        {Object.entries(CHANNEL_COLORS).map(([ch, color]) => (
          <span key={ch} className="flex items-center gap-1">
            <span className="w-2.5 h-1" style={{ background: color }} />
            <span className="text-muted-foreground">{ch}</span>
          </span>
        ))}
      </div>

      {/* Node Detail Panel */}
      {selectedNode && (
        <div className="absolute right-0 top-0 w-[260px] h-full bg-card border-l border-border overflow-y-auto z-10">
          <div className="flex items-center justify-between px-3 py-2 border-b border-border">
            <span className="text-[10px] font-mono font-bold truncate">{selectedNode.id}</span>
            <button onClick={() => setSelectedNode(null)} className="p-1 hover:bg-secondary cursor-pointer">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="px-3 py-2 space-y-2 text-[10px] font-mono">
            {selectedNode.total_sent !== undefined && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Sent</span>
                <span className="tabular-nums">₹{selectedNode.total_sent.toLocaleString()}</span>
              </div>
            )}
            {selectedNode.total_received !== undefined && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Received</span>
                <span className="tabular-nums">₹{selectedNode.total_received.toLocaleString()}</span>
              </div>
            )}
            {selectedNode.channels && selectedNode.channels.length > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Channels</span>
                <span>{selectedNode.channels.join(", ")}</span>
              </div>
            )}
            {selectedNode.pagerank !== undefined && selectedNode.pagerank > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">PageRank</span>
                <span className="tabular-nums">{selectedNode.pagerank.toFixed(4)}</span>
              </div>
            )}
            {selectedNode.betweenness !== undefined && selectedNode.betweenness > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Betweenness</span>
                <span className="tabular-nums">{selectedNode.betweenness.toFixed(4)}</span>
              </div>
            )}
            {selectedNode.if_score !== undefined && selectedNode.if_score > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">IF Score</span>
                <span className={`tabular-nums ${selectedNode.if_score > 0.7 ? "text-red-400" : selectedNode.if_score > 0.4 ? "text-amber-400" : "text-emerald-400"}`}>
                  {selectedNode.if_score.toFixed(3)}
                </span>
              </div>
            )}
            {selectedNode.xgb_score !== undefined && selectedNode.xgb_score > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">XGB Score</span>
                <span className={`tabular-nums ${selectedNode.xgb_score > 0.7 ? "text-red-400" : selectedNode.xgb_score > 0.4 ? "text-amber-400" : "text-emerald-400"}`}>
                  {selectedNode.xgb_score.toFixed(3)}
                </span>
              </div>
            )}
            <div className="pt-2 border-t border-border">
              <span className={`text-[9px] uppercase tracking-wider ${highlightSet.has(selectedNode.id) ? "text-red-400" : "text-emerald-400"}`}>
                {highlightSet.has(selectedNode.id) ? "FLAGGED" : "NORMAL"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
