import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, Search, Filter, ExternalLink, Eye, ChevronDown } from "lucide-react";
import { apiService } from "../lib/apiService";
import { formatCurrency, formatTimestamp, getRiskColor, getRiskBgColor } from "../lib/utils";

interface ScoringSignal {
  signal_name: string;
  signal_value: number;
  weight: number;
  contribution: number;
}

interface Alert {
  alert_id: string;
  timestamp: string;
  subgraph_nodes: number;
  subgraph_edges: number;
  risk_score: number;
  pattern_type: string;
  structural_score: number;
  innocence_discount: number;
  disposition: string;
  channels: string[];
  scoring_signals: ScoringSignal[];
  llm_explanation: string;
}

const PATTERN_TYPES = [
  "All",
  "Cycle",
  "Smurfing",
  "HubAndSpoke",
  "PassThrough",
  "DormantActivation",
  "TemporalLayering",
];

const RISK_RANGES = [
  { label: "All", min: 0, max: 100 },
  { label: "Critical 90+", min: 90, max: 100 },
  { label: "High 70-89", min: 70, max: 89 },
  { label: "Elevated 40-69", min: 40, max: 69 },
  { label: "Monitor 0-39", min: 0, max: 39 },
];

const SORT_OPTIONS = [
  { label: "Risk Score desc", key: "risk_desc" },
  { label: "Newest First", key: "newest" },
  { label: "Amount desc", key: "amount_desc" },
];

function getDispositionColor(disposition: string): string {
  switch (disposition?.toLowerCase()) {
    case "escalated":
    case "sar_filed":
      return "bg-red-500/20 text-red-400 border border-red-500/30";
    case "investigating":
    case "review":
      return "bg-amber-500/20 text-amber-400 border border-amber-500/30";
    case "cleared":
    case "dismissed":
      return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    case "pending":
    default:
      return "bg-slate-500/20 text-slate-400 border border-slate-500/30";
  }
}

function getPatternColor(pattern: string): string {
  switch (pattern) {
    case "Cycle":
      return "bg-violet-500/20 text-violet-400 border border-violet-500/30";
    case "Smurfing":
      return "bg-rose-500/20 text-rose-400 border border-rose-500/30";
    case "HubAndSpoke":
      return "bg-sky-500/20 text-sky-400 border border-sky-500/30";
    case "PassThrough":
      return "bg-lime-500/20 text-lime-400 border border-lime-500/30";
    case "DormantActivation":
      return "bg-orange-500/20 text-orange-400 border border-orange-500/30";
    case "TemporalLayering":
      return "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30";
    default:
      return "bg-slate-500/20 text-slate-400 border border-slate-500/30";
  }
}

function getRiskBadgeClasses(score: number): string {
  if (score >= 80) return "bg-red-500/20 text-red-400 border border-red-500/30";
  if (score >= 60) return "bg-orange-500/20 text-orange-400 border border-orange-500/30";
  if (score >= 40) return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
  return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
}

function SkeletonRow() {
  return (
    <tr className="border-b border-slate-800/50">
      {Array.from({ length: 8 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-slate-700/50 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
        </td>
      ))}
    </tr>
  );
}

export const AlertsPage = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [patternFilter, setPatternFilter] = useState("All");
  const [riskRange, setRiskRange] = useState("All");
  const [sortBy, setSortBy] = useState("risk_desc");
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchAlerts() {
      setLoading(true);
      try {
        const data = await apiService.getDemoTrackA();
        if (!cancelled && data?.alerts) {
          setAlerts(data.alerts);
        }
      } catch {
        // apiService should handle errors; silently fail with empty state
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchAlerts();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredAlerts = useMemo(() => {
    let result = [...alerts];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.alert_id.toLowerCase().includes(q) ||
          a.pattern_type.toLowerCase().includes(q) ||
          (a.channels || []).some((c) => c.toLowerCase().includes(q))
      );
    }

    if (patternFilter !== "All") {
      result = result.filter((a) => a.pattern_type === patternFilter);
    }

    if (riskRange !== "All") {
      const range = RISK_RANGES.find((r) => r.label === riskRange);
      if (range) {
        result = result.filter((a) => a.risk_score >= range.min && a.risk_score <= range.max);
      }
    }

    switch (sortBy) {
      case "risk_desc":
        result.sort((a, b) => b.risk_score - a.risk_score);
        break;
      case "newest":
        result.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        break;
      case "amount_desc":
        result.sort((a, b) => b.subgraph_edges - a.subgraph_edges);
        break;
    }

    return result;
  }, [alerts, searchQuery, patternFilter, riskRange, sortBy]);

  const toggleExpand = (alertId: string) => {
    setExpandedAlertId((prev) => (prev === alertId ? null : alertId));
  };

  return (
    <motion.div
      className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          className="flex items-center gap-3"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-amber-500/20 to-red-500/20 border border-amber-500/20">
            <Bell className="w-6 h-6 text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Alert Triage</h1>
            <p className="text-sm text-slate-400">Prioritized suspicious activity alerts</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-slate-500">
              {filteredAlerts.length} alert{filteredAlerts.length !== 1 ? "s" : ""}
            </span>
          </div>
        </motion.div>

        {/* Filter Bar */}
        <motion.div
          className="flex flex-wrap gap-3 items-center bg-slate-900/60 backdrop-blur border border-slate-800/50 rounded-xl p-4"
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          {/* Search */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search by Alert ID, pattern type, entity name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500/40 focus:border-amber-500/40 transition"
            />
          </div>

          {/* Pattern Type */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
            <select
              value={patternFilter}
              onChange={(e) => setPatternFilter(e.target.value)}
              className="pl-9 pr-8 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-200 appearance-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 focus:border-amber-500/40 transition cursor-pointer"
            >
              {PATTERN_TYPES.map((p) => (
                <option key={p} value={p}>
                  {p === "All" ? "All Patterns" : p}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>

          {/* Risk Range */}
          <div className="relative">
            <select
              value={riskRange}
              onChange={(e) => setRiskRange(e.target.value)}
              className="pl-3 pr-8 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-200 appearance-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 focus:border-amber-500/40 transition cursor-pointer"
            >
              {RISK_RANGES.map((r) => (
                <option key={r.label} value={r.label}>
                  {r.label === "All" ? "All Risk Levels" : r.label}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>

          {/* Sort */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="pl-3 pr-8 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-200 appearance-none focus:outline-none focus:ring-1 focus:ring-amber-500/40 focus:border-amber-500/40 transition cursor-pointer"
            >
              {SORT_OPTIONS.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          </div>
        </motion.div>

        {/* Alert Table */}
        <motion.div
          className="bg-slate-900/40 backdrop-blur border border-slate-800/50 rounded-xl overflow-hidden"
          initial={{ y: 10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          {loading ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-800/50">
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Alert ID</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Pattern</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Risk</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Nodes / Edges</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Channels</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Timestamp</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                    <th className="px-4 py-3 w-10" />
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: 6 }).map((_, i) => (
                    <SkeletonRow key={i} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
              <Bell className="w-10 h-10 mb-3 opacity-40" />
              <p className="text-sm font-medium">No alerts match your filters</p>
              <p className="text-xs text-slate-600 mt-1">Try adjusting the search or filter criteria</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-800/50">
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Alert ID</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Pattern</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Risk</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Nodes / Edges</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Channels</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Timestamp</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
                    <th className="px-4 py-3 w-10" />
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.map((alert, index) => (
                    <AlertRow
                      key={alert.alert_id}
                      alert={alert}
                      index={index}
                      isExpanded={expandedAlertId === alert.alert_id}
                      onToggle={() => toggleExpand(alert.alert_id)}
                      onInvestigate={() => navigate("/graph", { state: { alertId: alert.alert_id } })}
                      onViewSar={() => navigate("/sar", { state: { alertId: alert.alert_id } })}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
};

function AlertRow({
  alert,
  index,
  isExpanded,
  onToggle,
  onInvestigate,
  onViewSar,
}: {
  alert: Alert;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  onInvestigate: () => void;
  onViewSar: () => void;
}) {
  return (
    <AnimatePresence>
      <motion.tr
        className={`border-b border-slate-800/30 cursor-pointer transition-colors ${getRiskBgColor(alert.risk_score)} hover:bg-slate-800/40`}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.03 }}
        onClick={onToggle}
      >
        <td className="px-4 py-3">
          <span className="font-mono text-sm text-slate-200">{alert.alert_id}</span>
        </td>
        <td className="px-4 py-3">
          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${getPatternColor(alert.pattern_type)}`}>
            {alert.pattern_type}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold ${getRiskBadgeClasses(alert.risk_score)}`}>
            {alert.risk_score}
          </span>
        </td>
        <td className="px-4 py-3">
          <span className="text-sm text-slate-300">
            {alert.subgraph_nodes} / {alert.subgraph_edges}
          </span>
        </td>
        <td className="px-4 py-3">
          <div className="flex flex-wrap gap-1">
            {(alert.channels || []).map((ch) => (
              <span key={ch} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-700/50 text-slate-400 border border-slate-600/30">
                {ch}
              </span>
            ))}
            {(!alert.channels || alert.channels.length === 0) && (
              <span className="text-xs text-slate-600">&mdash;</span>
            )}
          </div>
        </td>
        <td className="px-4 py-3">
          <span className="text-xs text-slate-400">{formatTimestamp(alert.timestamp)}</span>
        </td>
        <td className="px-4 py-3">
          <div className="flex gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onInvestigate();
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition"
            >
              <Eye className="w-3 h-3" />
              Investigate
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onViewSar();
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20 hover:bg-sky-500/20 transition"
            >
              <ExternalLink className="w-3 h-3" />
              View SAR
            </button>
          </div>
        </td>
        <td className="px-4 py-3">
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown className="w-4 h-4 text-slate-500" />
          </motion.div>
        </td>
      </motion.tr>

      {isExpanded && (
        <motion.tr
          className="border-b border-slate-800/30"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.25 }}
        >
          <td colSpan={8} className="px-6 py-4 bg-slate-900/60">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Disposition + Scores */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Alert Details</h3>
                <div className="flex flex-wrap gap-3">
                  <div>
                    <span className="text-[10px] text-slate-500 block mb-1">Disposition</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${getDispositionColor(alert.disposition)}`}>
                      {alert.disposition || "pending"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block mb-1">Structural Score</span>
                    <span className="text-sm font-mono text-slate-300">{alert.structural_score?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block mb-1">Innocence Discount</span>
                    <span className="text-sm font-mono text-slate-300">{alert.innocence_discount?.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 block mb-1">Risk Score</span>
                    <span className={`text-sm font-mono font-semibold ${getRiskColor(alert.risk_score)}`}>{alert.risk_score}</span>
                  </div>
                </div>

                {/* Scoring Signals */}
                {alert.scoring_signals && alert.scoring_signals.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Scoring Signals</h4>
                    <div className="space-y-1.5">
                      {alert.scoring_signals.map((signal, i) => (
                        <div key={i} className="flex items-center gap-3 text-xs">
                          <span className="text-slate-400 flex-1 truncate">{signal.signal_name}</span>
                          <div className="w-24 h-1.5 rounded-full bg-slate-700/50 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-amber-500/60"
                              style={{ width: `${Math.min(signal.signal_value * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-slate-500 font-mono w-10 text-right">{signal.signal_value?.toFixed(2)}</span>
                          <span className="text-slate-600 font-mono w-10 text-right">w:{signal.weight?.toFixed(1)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* LLM Explanation */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Explanation</h3>
                {alert.llm_explanation ? (
                  <div className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/30">
                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{alert.llm_explanation}</p>
                  </div>
                ) : (
                  <p className="text-xs text-slate-600 italic">No explanation available</p>
                )}
              </div>
            </div>
          </td>
        </motion.tr>
      )}
    </AnimatePresence>
  );
}
