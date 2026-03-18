"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, Clock } from "lucide-react";
import { AgentActivityStep } from "@/types/api";

interface AgentActivityPanelProps {
  steps: AgentActivityStep[];
}

const agentColors: Record<string, { text: string; dot: string; bg: string }> = {
  Graph: { text: "text-emerald-500", dot: "bg-emerald-500", bg: "bg-emerald-500/10" },
  Pathfinder: { text: "text-blue-500", dot: "bg-blue-500", bg: "bg-blue-500/10" },
  Profiler: { text: "text-cyan-500", dot: "bg-cyan-500", bg: "bg-cyan-500/10" },
  Scorer: { text: "text-purple-500", dot: "bg-purple-500", bg: "bg-purple-500/10" },
  Compiler: { text: "text-rose-500", dot: "bg-rose-500", bg: "bg-rose-500/10" },
};

function getAgentStyle(agent: string) {
  return agentColors[agent] || { text: "text-primary", dot: "bg-primary", bg: "bg-primary/10" };
}

export default function AgentActivityPanel({ steps }: AgentActivityPanelProps) {
  if (!steps || steps.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Agent Activity</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="w-10 h-10 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center mb-3">
              <Clock className="w-4 h-4 text-muted-foreground/50" />
            </div>
            <p className="text-sm text-muted-foreground">
              Waiting for pipeline execution
            </p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Run a pipeline to see agent activity
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            <CardTitle className="text-sm font-medium">Agent Activity</CardTitle>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            {steps.length} steps
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full px-4 pb-4">
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[7px] top-2 bottom-2 w-px bg-border" />

            <ul className="space-y-0">
              {steps.map((step, i) => {
                const style = getAgentStyle(step.agent);
                return (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03, duration: 0.2 }}
                    className="relative flex gap-3 py-2 group"
                  >
                    {/* Timeline dot */}
                    <div className="relative z-10 flex-shrink-0 mt-1">
                      <div
                        className={`w-[15px] h-[15px] rounded-full ${style.dot} ring-2 ring-background`}
                      />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${style.text} ${style.bg}`}
                        >
                          {step.agent}
                        </span>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          #{String(i + 1).padStart(2, "0")}
                        </span>
                      </div>
                      <p className="text-sm text-foreground/80 break-words">
                        {step.message}
                      </p>
                    </div>
                  </motion.li>
                );
              })}
            </ul>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
