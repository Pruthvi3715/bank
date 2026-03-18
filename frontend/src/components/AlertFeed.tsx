"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bell, Search, Network, ArrowRight } from "lucide-react";
import RiskRing from "@/components/RiskRing";
import { Alert } from "@/types/api";

interface AlertFeedProps {
  alerts: Alert[];
  onSelectAlert: (alert: Alert) => void;
  onInvestigate?: (alert: Alert) => void;
  selectedAlertId?: string;
  isolatedAlertId?: string;
  compact?: boolean;
}

const patternColors: Record<string, string> = {
  Cycle: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  Smurfing: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
  HubAndSpoke: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  PassThrough: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  DormantActivation: "bg-rose-500/10 text-rose-500 border-rose-500/20",
  TemporalLayering: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
};

function getPatternColor(pattern: string) {
  return patternColors[pattern] || "bg-muted text-muted-foreground";
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
      <Card className="h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">Alert Queue</CardTitle>
          </div>
          <CardDescription>No alerts generated yet</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="w-10 h-10 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center mb-3">
              <Bell className="w-4 h-4 text-muted-foreground/50" />
            </div>
            <p className="text-sm text-muted-foreground">
              Run a pipeline to detect suspicious patterns
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const displayAlerts = compact ? alerts.slice(0, 5) : alerts;

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-primary" />
            <CardTitle className="text-sm font-medium">Alert Queue</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground font-mono">
              {alerts.length} alerts
            </span>
            {alerts.filter((a) => a.risk_score >= 80).length > 0 && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 text-[10px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                {alerts.filter((a) => a.risk_score >= 80).length} critical
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-hidden">
        <ScrollArea className="h-full px-4 pb-4">
          <div className="flex flex-col gap-3">
            {displayAlerts.map((alert: Alert, index: number) => (
              <motion.div
                key={alert.alert_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.2 }}
                role="button"
                tabIndex={0}
                className={`group relative p-4 rounded-xl border cursor-pointer transition-all duration-200 hover:shadow-md ${
                  selectedAlertId === alert.alert_id
                    ? "border-primary/50 bg-primary/5 shadow-sm"
                    : isolatedAlertId === alert.alert_id
                    ? "border-accent/50 bg-accent/5"
                    : "border-border hover:border-primary/30 hover:bg-muted/50"
                }`}
                onClick={() => onSelectAlert(alert)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelectAlert(alert);
                  }
                }}
              >
                <div className="flex items-start gap-4">
                  {/* Risk Ring */}
                  <div className="flex-shrink-0">
                    <RiskRing score={alert.risk_score} size={48} strokeWidth={3} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge
                        variant="outline"
                        className={`text-[10px] font-medium ${getPatternColor(
                          alert.pattern_type
                        )}`}
                      >
                        {alert.pattern_type}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground font-mono">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Network className="w-3 h-3" />
                        {alert.subgraph_nodes.length} nodes
                      </span>
                      <span className="flex items-center gap-1">
                        <ArrowRight className="w-3 h-3" />
                        {alert.subgraph_edges.length} edges
                      </span>
                    </div>

                    <p className="text-[10px] text-muted-foreground mt-1.5 truncate">
                      {alert.disposition}
                    </p>
                  </div>

                  {/* Action Button */}
                  {onInvestigate && (
                    <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          onInvestigate(alert);
                        }}
                        className="gap-1 text-xs h-7"
                      >
                        <Search className="w-3 h-3" />
                        Investigate
                      </Button>
                    </div>
                  )}
                </div>

                {/* Risk Score Bar */}
                <div className="mt-3 h-1 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
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
              </motion.div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
