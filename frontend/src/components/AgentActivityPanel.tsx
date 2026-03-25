"use client";

import { motion } from "framer-motion";
import { Activity, Clock } from "lucide-react";
import { AgentActivityStep } from "@/types/api";

interface AgentActivityPanelProps {
  steps: AgentActivityStep[];
}

const agentColors: Record<string, { text: string; dot: string }> = {
  Graph: { text: "text-emerald-500", dot: "bg-emerald-500" },
  Pathfinder: { text: "text-amber-500", dot: "bg-amber-500" },
  Profiler: { text: "text-cyan-500", dot: "bg-cyan-500" },
  Scorer: { text: "text-orange-500", dot: "bg-orange-500" },
  Compiler: { text: "text-red-500", dot: "bg-red-500" },
};

function getAgentStyle(agent: string) {
  return agentColors[agent] || { text: "text-primary", dot: "bg-primary" };
}

export default function AgentActivityPanel({ steps }: AgentActivityPanelProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="border border-border bg-card p-8 flex flex-col items-center justify-center text-center h-full min-h-[200px]">
        <Clock className="w-8 h-8 text-muted-foreground/30 mb-3" />
        <p className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
          Awaiting pipeline
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Run to see agent activity
        </p>
      </div>
    );
  }

  return (
    <div className="border border-border bg-card flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
          <Activity className="w-3 h-3" />
          Agent Log
        </span>
        <span className="text-[10px] font-mono text-muted-foreground tabular-nums">
          {steps.length} ops
        </span>
      </div>

      <div className="flex-1 overflow-y-auto max-h-[360px]">
        <div className="relative px-3 py-2">
          {/* Timeline line */}
          <div className="absolute left-[18px] top-4 bottom-4 w-px bg-border" />

          {steps.map((step, i) => {
            const style = getAgentStyle(step.agent);
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.02, duration: 0.15 }}
                className="relative flex gap-3 py-1.5"
              >
                {/* Dot */}
                <div className="relative z-10 shrink-0 mt-1.5">
                  <div
                    className={`w-2 h-2 ${style.dot}`}
                  />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span
                      className={`text-[9px] font-mono font-bold uppercase tracking-wider ${style.text}`}
                    >
                      {step.agent}
                    </span>
                    <span className="text-[9px] font-mono text-muted-foreground/50">
                      #{String(i + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <p className="text-xs text-foreground/70 break-words leading-relaxed">
                    {step.message}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
