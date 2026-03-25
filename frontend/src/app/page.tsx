"use client";

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  ShieldAlert,
  Play,
  Loader2,
  Upload,
  LayoutDashboard,
  Bell,
  GitBranch,
  FileText,
  Bug,
  Activity,
  Network,
  AlertTriangle,
  Zap,
} from "lucide-react";
import AdversarialTestPanel from "@/components/AdversarialTestPanel";
import AgentActivityPanel from "@/components/AgentActivityPanel";
import AlertFeed from "@/components/AlertFeed";
import GraphVisualizer from "@/components/GraphVisualizer";
import SARReport from "@/components/SARReport";
import StatsCard from "@/components/StatsCard";
import FilterBar from "@/components/FilterBar";
import ThemeToggle from "@/components/ThemeToggle";
import RiskRing from "@/components/RiskRing";
import {
  Alert,
  GraphLink,
  GraphNode,
  PatternType,
  PipelineResponse,
  SARChatMessage,
} from "@/types/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const tabItems = [
  { value: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { value: "alerts", label: "Alerts", icon: Bell },
  { value: "graph", label: "Graph", icon: GitBranch },
  { value: "sar", label: "SAR Report", icon: FileText },
  { value: "tests", label: "Tests", icon: Bug },
];

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PipelineResponse | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [isolatedAlert, setIsolatedAlert] = useState<Alert | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [demoTrack, setDemoTrack] = useState<"A" | "B">("B");
  const [patternFilter, setPatternFilter] = useState<PatternType | "All">(
    "All"
  );
  const [channelFilter, setChannelFilter] = useState<string>("All");
  const [minScore, setMinScore] = useState<number>(0);
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [chatMessages, setChatMessages] = useState<SARChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const handleSendChat = async (message: string) => {
    if (!selectedAlert) return;
    const userMsg: SARChatMessage = { role: "user", content: message };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/sar-chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alert_id: selectedAlert.alert_id,
          message,
          history: chatMessages,
        }),
      });
      const data = await res.json();
      const assistantMsg: SARChatMessage = {
        role: "assistant",
        content: data.response || "No response available.",
      };
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error connecting to the server." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleResponse = async (res: Response) => {
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`HTTP ${res.status}: ${body}`);
    }
    return (await res.json()) as PipelineResponse;
  };

  const runSyntheticPipeline = async () => {
    setLoading(true);
    setSelectedAlert(null);
    setChatMessages([]);
    try {
      const url =
        demoTrack === "A"
          ? `${API_BASE}/api/demo-track-a`
          : `${API_BASE}/api/run-pipeline`;
      const res = await fetch(url, {
        method: demoTrack === "A" ? "GET" : "POST",
      });
      const data = await handleResponse(res);
      setResults(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const runCsvPipeline = async () => {
    if (!csvFile) return;
    setLoading(true);
    setSelectedAlert(null);
    setIsolatedAlert(null);
    try {
      const formData = new FormData();
      formData.append("file", csvFile);
      const res = await fetch(`${API_BASE}/api/run-pipeline-csv`, {
        method: "POST",
        body: formData,
      });
      const data = await handleResponse(res);
      setResults(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const allChannels = useMemo(() => {
    const channels = new Set<string>();
    for (const alert of results?.alerts || []) {
      for (const ch of alert.channels || []) channels.add(ch);
    }
    return ["All", ...Array.from(channels).sort()];
  }, [results]);

  const filteredAlerts = useMemo(() => {
    const fromTs = fromDate ? new Date(fromDate).getTime() : null;
    const toTs = toDate ? new Date(toDate).getTime() : null;
    return (results?.alerts || []).filter((alert) => {
      if (alert.risk_score < minScore) return false;
      if (patternFilter !== "All" && alert.pattern_type !== patternFilter)
        return false;
      if (
        channelFilter !== "All" &&
        !(alert.channels || []).includes(channelFilter)
      )
        return false;
      const ts = new Date(alert.timestamp).getTime();
      if (fromTs !== null && ts < fromTs) return false;
      if (toTs !== null && ts > toTs) return false;
      return true;
    });
  }, [results, minScore, patternFilter, channelFilter, fromDate, toDate]);

  const activeAlert = useMemo(
    () =>
      selectedAlert
        ? filteredAlerts.find((a) => a.alert_id === selectedAlert.alert_id) ??
          null
        : null,
    [selectedAlert, filteredAlerts]
  );

  const graphPayloadForViz = useMemo(() => {
    const graph = results?.graph;
    if (!graph || !isolatedAlert?.subgraph_nodes?.length) {
      return graph ?? { nodes: [], links: [] };
    }
    const nodeSet = new Set(isolatedAlert.subgraph_nodes);
    const toId = (v: string | GraphNode) =>
      typeof v === "string" ? v : (v?.id ?? "");
    const nodes = (graph.nodes || []).filter((n) =>
      nodeSet.has(String(n.id))
    );
    const links = (graph.links || []).filter(
      (l: GraphLink) =>
        nodeSet.has(toId(l.source)) && nodeSet.has(toId(l.target))
    );
    return { nodes, links };
  }, [results?.graph, isolatedAlert]);

  const handleSelectAlert = (alert: Alert) => {
    setSelectedAlert(alert);
    setActiveTab("sar");
  };

  const handleInvestigate = (alert: Alert) => {
    setIsolatedAlert(alert);
    setSelectedAlert(alert);
    setActiveTab("graph");
  };

  const patternCounts = results?.stats?.pattern_counts || {};
  const criticalAlerts = filteredAlerts.filter(
    (a) => a.risk_score >= 80
  ).length;
  const highAlerts = filteredAlerts.filter(
    (a) => a.risk_score >= 60 && a.risk_score < 80
  ).length;
  const avgRisk =
    filteredAlerts.length > 0
      ? Math.round(
          filteredAlerts.reduce((s, a) => s + a.risk_score, 0) /
            filteredAlerts.length
        )
      : 0;

  return (
    <div className="min-h-screen w-full flex flex-col relative">
      {/* Ambient scanline */}
      <div className="scanline fixed inset-0 pointer-events-none z-50 opacity-30" />

      {/* Header — razor sharp, no rounded corners */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="flex items-center justify-between px-4 h-14">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 border border-primary/40 bg-primary/10">
              <ShieldAlert className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-widest uppercase text-foreground">
                GraphSentinel
              </h1>
              <p className="text-[10px] tracking-wider uppercase text-muted-foreground font-mono">
                AML Intelligence Platform
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-1.5">
            {/* Demo Track Toggle */}
            <div className="hidden sm:flex items-center border border-border bg-secondary">
              {(["A", "B"] as const).map((track) => (
                <button
                  key={track}
                  onClick={() => setDemoTrack(track)}
                  className={`px-3 py-1.5 text-[11px] font-mono font-medium tracking-wider uppercase transition-colors cursor-pointer ${
                    demoTrack === track
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {track}
                </button>
              ))}
            </div>

            <Button
              onClick={runSyntheticPipeline}
              disabled={loading}
              className="gap-1.5 text-[11px] font-mono uppercase tracking-wider h-8 px-3 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              <span className="hidden sm:inline">
                {loading ? "Analyzing" : "Run"}
              </span>
            </Button>

            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="hidden"
                aria-label="Upload CSV file"
              />
              <span className="inline-flex items-center gap-1 h-8 px-3 text-[11px] font-mono uppercase tracking-wider border border-border bg-secondary hover:bg-muted transition-colors cursor-pointer">
                <Upload className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">CSV</span>
              </span>
            </label>

            {csvFile && (
              <Button
                onClick={runCsvPipeline}
                disabled={loading}
                variant="secondary"
                className="h-8 px-3 text-[11px] font-mono uppercase tracking-wider cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5 mr-1" />
                Process
              </Button>
            )}

            <ThemeToggle />
          </div>
        </div>

        {/* Tab Navigation — underline style, sharp edges */}
        <div className="flex items-center px-4 gap-0 border-t border-border/50">
          {tabItems.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`relative flex items-center gap-1.5 px-4 py-2.5 text-[11px] font-mono uppercase tracking-wider transition-colors cursor-pointer ${
                activeTab === tab.value
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <tab.icon className="w-3.5 h-3.5" />
              {tab.label}
              {tab.value === "alerts" && filteredAlerts.length > 0 && (
                <span className="ml-1 flex h-4 min-w-4 items-center justify-center px-1 bg-destructive/20 text-destructive text-[9px] font-bold">
                  {filteredAlerts.length}
                </span>
              )}
              {activeTab === tab.value && (
                <motion.div
                  layoutId="tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
            </button>
          ))}
        </div>

        {/* Filter Bar */}
        {results && (
          <FilterBar
            patternFilter={patternFilter}
            setPatternFilter={setPatternFilter}
            channelFilter={channelFilter}
            setChannelFilter={setChannelFilter}
            minScore={minScore}
            setMinScore={setMinScore}
            fromDate={fromDate}
            setFromDate={setFromDate}
            toDate={toDate}
            setToDate={setToDate}
            allChannels={allChannels}
          />
        )}
      </header>

      {/* Content */}
      <div className="flex-1 p-4">
        <AnimatePresence mode="wait">
          {activeTab === "dashboard" && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="space-y-4"
            >
              {/* Top Row: Stats + Risk Ring */}
              <div className="grid grid-cols-1 lg:grid-cols-[1fr_200px] gap-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <StatsCard
                    title="Transactions"
                    value={results?.stats?.total_txns || 0}
                    subtitle="analyzed"
                    icon={Activity}
                    color="amber"
                    delay={0}
                  />
                  <StatsCard
                    title="Nodes"
                    value={results?.stats?.total_nodes || 0}
                    subtitle="entities"
                    icon={Network}
                    color="emerald"
                    delay={0.03}
                  />
                  <StatsCard
                    title="Alerts"
                    value={results?.alerts?.length || 0}
                    subtitle={`${criticalAlerts} crit / ${highAlerts} high`}
                    icon={AlertTriangle}
                    color={criticalAlerts > 0 ? "red" : "amber"}
                    delay={0.06}
                  />
                  <StatsCard
                    title="Patterns"
                    value={Object.keys(patternCounts).length}
                    subtitle={Object.entries(patternCounts)
                      .slice(0, 2)
                      .map(([k, v]) => `${v} ${k}`)
                      .join(", ")}
                    icon={GitBranch}
                    color="cyan"
                    delay={0.09}
                  />
                </div>

                {/* Risk Summary Ring */}
                <div className="flex items-center justify-center border border-border bg-card p-4">
                  <RiskRing
                    score={avgRisk}
                    label="AVG RISK"
                    size={120}
                  />
                </div>
              </div>

              {/* Bottom Row: Agent Activity + Alert Feed */}
              <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-4">
                <AgentActivityPanel
                  steps={results?.agent_activity ?? []}
                />
                <AlertFeed
                  alerts={filteredAlerts.slice(0, 6)}
                  selectedAlertId={activeAlert?.alert_id}
                  onSelectAlert={handleSelectAlert}
                  onInvestigate={handleInvestigate}
                  isolatedAlertId={isolatedAlert?.alert_id}
                  compact
                />
              </div>
            </motion.div>
          )}

          {activeTab === "alerts" && (
            <motion.div
              key="alerts"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="h-[calc(100vh-180px)]"
            >
              <AlertFeed
                alerts={filteredAlerts}
                selectedAlertId={activeAlert?.alert_id}
                onSelectAlert={handleSelectAlert}
                onInvestigate={handleInvestigate}
                isolatedAlertId={isolatedAlert?.alert_id}
              />
            </motion.div>
          )}

          {activeTab === "graph" && (
            <motion.div
              key="graph"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="h-[calc(100vh-180px)]"
            >
              <GraphVisualizer
                graphData={graphPayloadForViz}
                highlightedNodes={activeAlert?.subgraph_nodes || []}
                isolatedSubgraph={!!isolatedAlert}
                onShowFullGraph={() => setIsolatedAlert(null)}
              />
            </motion.div>
          )}

          {activeTab === "sar" && (
            <motion.div
              key="sar"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="h-[calc(100vh-180px)]"
            >
              <SARReport
                alert={activeAlert}
                chatMessages={chatMessages}
                onSendChat={handleSendChat}
                isChatLoading={chatLoading}
              />
            </motion.div>
          )}

          {activeTab === "tests" && (
            <motion.div
              key="tests"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <AdversarialTestPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
