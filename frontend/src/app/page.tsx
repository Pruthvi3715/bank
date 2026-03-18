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
} from "lucide-react";
import AdversarialTestPanel from "@/components/AdversarialTestPanel";
import AgentActivityPanel from "@/components/AgentActivityPanel";
import AlertFeed from "@/components/AlertFeed";
import GraphVisualizer from "@/components/GraphVisualizer";
import SARReport from "@/components/SARReport";
import StatsCard from "@/components/StatsCard";
import FilterBar from "@/components/FilterBar";
import ThemeToggle from "@/components/ThemeToggle";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Alert,
  GraphLink,
  GraphNode,
  PatternType,
  PipelineResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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
  const [patternFilter, setPatternFilter] = useState<PatternType | "All">("All");
  const [channelFilter, setChannelFilter] = useState<string>("All");
  const [minScore, setMinScore] = useState<number>(0);
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

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
    try {
      if (demoTrack === "A") {
        const res = await fetch(`${API_BASE}/api/demo-track-a`);
        const data = await handleResponse(res);
        setResults(data);
      } else {
        const res = await fetch(`${API_BASE}/api/run-pipeline`, {
          method: "POST",
        });
        const data = await handleResponse(res);
        setResults(data);
      }
    } catch (e) {
      console.error(e);
      alert("Failed to run pipeline. Ensure backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  const runCsvPipeline = async () => {
    if (!csvFile) {
      alert("Select a CSV file first.");
      return;
    }

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
      alert(
        "Failed to process uploaded CSV. Check the file format and backend logs."
      );
    } finally {
      setLoading(false);
    }
  };

  const allChannels = useMemo(() => {
    const channels = new Set<string>();
    for (const alert of results?.alerts || []) {
      for (const ch of alert.channels || []) {
        channels.add(ch);
      }
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

  const activeAlert = useMemo(() => {
    if (!selectedAlert) return null;
    return (
      filteredAlerts.find((a) => a.alert_id === selectedAlert.alert_id) || null
    );
  }, [selectedAlert, filteredAlerts]);

  const graphPayloadForViz = useMemo(() => {
    const graph = results?.graph;
    if (!graph || !isolatedAlert?.subgraph_nodes?.length) {
      return graph ?? { nodes: [], links: [] };
    }
    const nodeSet = new Set(isolatedAlert.subgraph_nodes);
    const toId = (v: string | GraphNode) =>
      typeof v === "string" ? v : (v?.id ?? "");
    const nodes = (graph.nodes || []).filter((n: GraphNode) =>
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
  const criticalAlerts = filteredAlerts.filter((a) => a.risk_score >= 80).length;
  const highAlerts = filteredAlerts.filter(
    (a) => a.risk_score >= 60 && a.risk_score < 80
  ).length;

  return (
    <div className="min-h-screen w-full flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10 border border-primary/20">
              <ShieldAlert className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">
                GraphSentinel
              </h1>
              <p className="text-[11px] text-muted-foreground">
                AI-Powered Fraud Detection
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Demo Track Selector */}
            <div className="hidden sm:flex items-center rounded-lg border border-input bg-muted/50 p-0.5">
              <button
                onClick={() => setDemoTrack("A")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  demoTrack === "A"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Track A
              </button>
              <button
                onClick={() => setDemoTrack("B")}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  demoTrack === "B"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Track B
              </button>
            </div>

            <Button
              onClick={runSyntheticPipeline}
              disabled={loading}
              className="gap-2 text-sm"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">
                {loading ? "Running..." : "Run Pipeline"}
              </span>
            </Button>

            <label className="cursor-pointer">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <span className="inline-flex items-center gap-1.5 h-8 px-3 text-xs font-medium rounded-lg border border-input bg-background hover:bg-muted transition-colors cursor-pointer">
                <Upload className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Upload</span>
              </span>
            </label>

            {csvFile && (
              <Button
                onClick={runCsvPipeline}
                disabled={loading}
                variant="secondary"
                size="sm"
              >
                Run CSV
              </Button>
            )}

            <ThemeToggle />
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-transparent h-auto p-0 gap-0">
              {tabItems.map((tab) => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  className="relative rounded-none border-b-2 border-transparent px-4 py-2.5 data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
                >
                  <tab.icon className="w-4 h-4 mr-1.5" />
                  {tab.label}
                  {tab.value === "alerts" && filteredAlerts.length > 0 && (
                    <span className="ml-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] font-medium text-primary">
                      {filteredAlerts.length}
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
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

      {/* Main Content */}
      <div className="flex-1 p-4">
        <AnimatePresence mode="wait">
          {activeTab === "dashboard" && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* Stats Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard
                  title="Total Transactions"
                  value={results?.stats?.total_txns || 0}
                  subtitle="Analyzed in last run"
                  icon={Activity}
                  color="blue"
                  delay={0}
                />
                <StatsCard
                  title="Network Nodes"
                  value={results?.stats?.total_nodes || 0}
                  subtitle="Entities mapped"
                  icon={Network}
                  color="cyan"
                  delay={0.05}
                />
                <StatsCard
                  title="Alerts Generated"
                  value={results?.alerts?.length || 0}
                  subtitle={`${criticalAlerts} critical, ${highAlerts} high`}
                  icon={AlertTriangle}
                  color={criticalAlerts > 0 ? "red" : "amber"}
                  delay={0.1}
                />
                <StatsCard
                  title="Pattern Types"
                  value={Object.keys(patternCounts).length}
                  subtitle={Object.entries(patternCounts)
                    .slice(0, 2)
                    .map(([k, v]) => `${v} ${k}`)
                    .join(", ")}
                  icon={GitBranch}
                  color="purple"
                  delay={0.15}
                />
              </div>

              {/* Agent Activity + Recent Alerts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="lg:col-span-1">
                  <AgentActivityPanel
                    steps={results?.agent_activity ?? []}
                  />
                </div>
                <div className="lg:col-span-1">
                  <AlertFeed
                    alerts={filteredAlerts.slice(0, 5)}
                    selectedAlertId={activeAlert?.alert_id}
                    onSelectAlert={handleSelectAlert}
                    onInvestigate={handleInvestigate}
                    isolatedAlertId={isolatedAlert?.alert_id}
                    compact
                  />
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "alerts" && (
            <motion.div
              key="alerts"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
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
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
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
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-[calc(100vh-180px)]"
            >
              <SARReport alert={activeAlert} />
            </motion.div>
          )}

          {activeTab === "tests" && (
            <motion.div
              key="tests"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <AdversarialTestPanel />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
