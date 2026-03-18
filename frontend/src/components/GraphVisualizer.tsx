"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Fullscreen, GitBranch } from "lucide-react";
import { GraphPayload } from "@/types/api";

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

  useEffect(() => {
    const currentContainer = containerRef.current;
    if (!currentContainer) return;

    const updateSize = () => {
      const w =
        currentContainer.offsetWidth ||
        currentContainer.clientWidth ||
        MIN_GRAPH_WIDTH;
      const h =
        currentContainer.offsetHeight ||
        currentContainer.clientHeight ||
        MIN_GRAPH_HEIGHT;
      setDimensions({
        width: Math.max(MIN_GRAPH_WIDTH, w),
        height: Math.max(MIN_GRAPH_HEIGHT, h),
      });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(currentContainer);

    return () => observer.disconnect();
  }, [graphData?.nodes?.length]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Topology Map</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="h-[400px] flex flex-col items-center justify-center text-muted-foreground gap-4">
          <div className="relative">
            <div className="w-20 h-20 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center">
              <div className="w-10 h-10 rounded-full border-2 border-muted-foreground/20 flex items-center justify-center">
                <GitBranch className="w-5 h-5 text-muted-foreground/40" />
              </div>
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-foreground/80">
              No graph data available
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Run a pipeline to visualize the knowledge graph
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const highlightSet = new Set(highlightedNodes || []);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-primary" />
            <CardTitle className="text-sm font-medium">Topology Map</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-3 text-[10px]">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
                <span className="text-muted-foreground">Suspicious</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-primary/70" />
                <span className="text-muted-foreground">Normal</span>
              </span>
            </div>
            {isolatedSubgraph && onShowFullGraph && (
              <Button
                size="sm"
                variant="outline"
                onClick={onShowFullGraph}
                className="gap-1.5 text-xs h-7"
              >
                <Fullscreen className="w-3 h-3" />
                Full Graph
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent
        className="flex-1 p-0 overflow-hidden rounded-b-xl"
        ref={containerRef}
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="w-full h-full"
        >
          {dimensions.width > 0 && dimensions.height > 0 && (
            <ForceGraph2D
              width={dimensions.width}
              height={dimensions.height}
              graphData={graphData}
              nodeLabel={(node: { id?: string | number }) => toNodeId(node)}
              nodeColor={(node: { id?: string | number }) =>
                highlightSet.has(toNodeId(node)) ? "#ef4444" : "#3b82f6"
              }
              nodeRelSize={6}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const n = node as {
                  id?: string | number;
                  x?: number;
                  y?: number;
                };
                const id = toNodeId(n);
                const isHighlighted = highlightSet.has(id);
                const label = id;
                const fontSize = 12 / globalScale;
                ctx.font = `${fontSize}px Inter, sans-serif`;

                if (isHighlighted) {
                  ctx.shadowColor = "#ef4444";
                  ctx.shadowBlur = 15;
                }

                const nx = n.x ?? 0;
                const ny = n.y ?? 0;
                ctx.beginPath();
                ctx.arc(nx, ny, isHighlighted ? 5 : 3, 0, 2 * Math.PI);
                ctx.fillStyle = isHighlighted ? "#ef4444" : "#3b82f6";
                ctx.fill();

                ctx.shadowBlur = 0;
                ctx.fillStyle = isHighlighted ? "#ef4444" : "#94a3b8";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(label, nx, ny + (isHighlighted ? 8 : 6));
              }}
              linkColor={(link: { source?: unknown; target?: unknown }) => {
                const sourceId = toNodeId(link.source);
                const targetId = toNodeId(link.target);
                if (
                  highlightSet.has(sourceId) &&
                  highlightSet.has(targetId)
                ) {
                  return "rgba(239, 68, 68, 0.6)";
                }
                return "rgba(59, 130, 246, 0.12)";
              }}
              linkWidth={(link: { source?: unknown; target?: unknown }) => {
                const sourceId = toNodeId(link.source);
                const targetId = toNodeId(link.target);
                return highlightSet.has(sourceId) && highlightSet.has(targetId)
                  ? 2
                  : 1;
              }}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              backgroundColor="transparent"
            />
          )}
        </motion.div>
      </CardContent>
    </Card>
  );
}
