"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Crosshair } from "lucide-react";
import type { Alert } from "@/types/api";

interface AlertFeedProps {
  alerts: Alert[];
  onSelectAlert: (alert: Alert) => void;
  onInvestigate?: (alert: Alert) => void;
  selectedAlertId?: string;
  isolatedAlertId?: string;
  compact?: boolean;
}

const patternLabels: Record<string, string> = {
  Cycle: "CYCLE",
  Smurfing: "SMURF",
  HubAndSpoke: "HUB",
  PassThrough: "PASS",
  DormantActivation: "DORMANT",
  TemporalLayering: "TEMPORAL",
};

function riskBorder(score: number): string {
  if (score >= 80) return "border-l-red-500";
  if (score >= 60) return "border-l-orange-500";
  if (score >= 40) return "border-l-yellow-500";
  return "border-l-emerald-500";
}

function riskText(score: number): string {
  if (score >= 80) return "text-red-500";
  if (score >= 60) return "text-orange-500";
  if (score >= 40) return "text-yellow-500";
  return "text-emerald-500";
}

export default function AlertFeed({
  alerts,
  onSelectAlert,
  onInvestigate,
  selectedAlertId,
  isolatedAlertId,
  compact = false,
}: AlertFeedProps) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="border border-border bg-card p-8 flex flex-col items-center justify-center text-center h-full min-h-[200px]">
        <AlertTriangle className="w-8 h-8 text-muted-foreground/30 mb-3" />
        <p className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
          No alerts detected
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Run the pipeline to generate alerts
        </p>
      </div>
    );
  }

  const displayAlerts = compact ? alerts.slice(0, 6) : alerts;

  return (
    <div className="border border-border bg-card flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
          Alert Feed
        </span>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-primary tabular-nums">
            {alerts.length}
          </span>
          {alerts.filter((a) => a.risk_score >= 80).length > 0 && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 bg-red-500/10 text-red-500 text-[9px] font-mono">
              <span className="w-1.5 h-1.5 bg-red-500 pulse-critical" />
              {alerts.filter((a) => a.risk_score >= 80).length} CRIT
            </span>
          )}
        </div>
      </div>

      <div className={`flex-1 overflow-y-auto ${compact ? "max-h-[360px]" : ""}`}>
        {displayAlerts.map((alert, i) => {
          const isSelected = selectedAlertId === alert.alert_id;
          const isIsolated = isolatedAlertId === alert.alert_id;

          return (
            <motion.div
              key={alert.alert_id}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.12, delay: i * 0.02 }}
              className={`border-l-2 ${riskBorder(alert.risk_score)} border-b border-border px-3 py-2.5 transition-colors cursor-pointer group ${
                isSelected ? "bg-primary/5" : "hover:bg-secondary/50"
              } ${isIsolated ? "ring-1 ring-inset ring-primary/30" : ""}`}
              onClick={() => onSelectAlert(alert)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectAlert(alert);
                }
              }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 bg-secondary text-foreground uppercase tracking-wider">
                      {patternLabels[alert.pattern_type] || alert.pattern_type}
                    </span>
                    <span className="text-[9px] font-mono text-muted-foreground tabular-nums">
                      {alert.alert_id.slice(0, 8)}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground">
                    <span>{alert.subgraph_nodes?.length || 0} nodes</span>
                    <span>{alert.subgraph_edges?.length || 0} edges</span>
                    <span>{(alert.channels || []).join("/") || "—"}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={`text-sm font-mono font-bold tabular-nums ${riskText(alert.risk_score)}`}
                  >
                    {Math.round(alert.risk_score)}
                  </span>

                  {onInvestigate && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInvestigate(alert);
                      }}
                      className="p-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-primary/10 hover:bg-primary/20 text-primary cursor-pointer"
                      title="Investigate in graph"
                      aria-label={`Investigate alert ${alert.alert_id}`}
                    >
                      <Crosshair className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Risk bar */}
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-[2px] bg-border overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      alert.risk_score >= 80
                        ? "bg-red-500"
                        : alert.risk_score >= 60
                          ? "bg-orange-500"
                          : alert.risk_score >= 40
                            ? "bg-yellow-500"
                            : "bg-emerald-500"
                    }`}
                    style={{ width: `${alert.risk_score}%` }}
                  />
                </div>
                {/* ML Scores */}
                {alert.if_score !== undefined && alert.if_score > 0 && (
                  <div className="flex gap-1 shrink-0">
                    <span className={`text-[9px] font-mono px-1 py-0.5 border border-border/50 ${
                      alert.if_score > 0.7 ? "text-red-400" : alert.if_score > 0.4 ? "text-amber-400" : "text-emerald-400"
                    }`}>
                      IF:{alert.if_score.toFixed(2)}
                    </span>
                    {alert.xgb_score !== undefined && alert.xgb_score > 0 && (
                      <span className={`text-[9px] font-mono px-1 py-0.5 border border-border/50 ${
                        alert.xgb_score > 0.7 ? "text-red-400" : alert.xgb_score > 0.4 ? "text-amber-400" : "text-emerald-400"
                      }`}>
                        XGB:{alert.xgb_score.toFixed(2)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
