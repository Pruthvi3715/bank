import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, Download, Send, AlertTriangle, Clock, User, Building, ChevronRight } from "lucide-react";
import html2pdf from "html2pdf.js";
import { apiService } from "../lib/apiService";
import { formatTimestamp } from "../lib/utils";

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

interface FeedbackForm {
  decision: "confirmed_fraud" | "false_positive" | "unclear";
  confidence: number;
  notes: string;
}

function generateSarId(alertId: string): string {
  const datePart = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const alertSuffix = alertId.slice(-6).toUpperCase();
  return `SAR-${datePart}-${alertSuffix}`;
}

function getRiskLabel(score: number): string {
  if (score >= 80) return "Critical";
  if (score >= 60) return "High";
  if (score >= 40) return "Elevated";
  return "Low";
}

function getRiskBadgeClass(score: number): string {
  if (score >= 80) return "bg-red-500/20 text-red-400 border border-red-500/30";
  if (score >= 60) return "bg-orange-500/20 text-orange-400 border border-orange-500/30";
  if (score >= 40) return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
  return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
}

function getDispositionBadgeClass(disposition: string): string {
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

function AlertSelectorItem({
  alert,
  isSelected,
  onSelect,
  index,
}: {
  alert: Alert;
  isSelected: boolean;
  onSelect: () => void;
  index: number;
}) {
  return (
    <motion.button
      onClick={onSelect}
      className={`w-full text-left p-3 rounded-lg border transition-all ${
        isSelected
          ? "bg-sky-500/10 border-sky-500/30 shadow-lg shadow-sky-500/5"
          : "bg-slate-800/40 border-slate-700/30 hover:bg-slate-800/60 hover:border-slate-700/50"
      }`}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.04 }}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="font-mono text-xs text-slate-300 truncate">{alert.alert_id}</span>
        <ChevronRight className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 transition ${isSelected ? "text-sky-400" : "text-slate-600"}`} />
      </div>
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium ${getPatternColor(alert.pattern_type)}`}>
          {alert.pattern_type}
        </span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-slate-500">Risk Score</span>
        <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold ${getRiskBadgeClass(alert.risk_score)}`}>
          {alert.risk_score}
        </span>
      </div>
    </motion.button>
  );
}

function EmptyState() {
  return (
    <motion.div
      className="flex flex-col items-center justify-center h-full min-h-[400px] text-center px-8"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="p-4 rounded-2xl bg-slate-800/40 border border-slate-700/30 mb-6">
        <FileText className="w-12 h-12 text-slate-600" />
      </div>
      <h3 className="text-lg font-semibold text-slate-300 mb-2">No Alert Selected</h3>
      <p className="text-sm text-slate-500 max-w-sm">
        Select an alert from the left panel to generate a Suspicious Activity Report for review and filing.
      </p>
    </motion.div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 p-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="bg-slate-800/40 rounded-lg p-4 border border-slate-700/30 space-y-3">
          <div className="h-4 bg-slate-700/50 rounded animate-pulse w-2/3" />
          <div className="h-3 bg-slate-700/30 rounded animate-pulse w-full" />
          <div className="h-3 bg-slate-700/30 rounded animate-pulse w-4/5" />
        </div>
      ))}
    </div>
  );
}

function FeedbackModal({
  alertId,
  onClose,
  onSubmit,
}: {
  alertId: string;
  onClose: () => void;
  onSubmit: (form: FeedbackForm) => void;
}) {
  const [form, setForm] = useState<FeedbackForm>({
    decision: "unclear",
    confidence: 3,
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(form);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="bg-slate-900 border border-slate-700/50 rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-white mb-1">Submit Feedback</h3>
        <p className="text-xs text-slate-500 mb-5">Alert: <span className="font-mono text-slate-400">{alertId}</span></p>

        {/* Decision */}
        <div className="mb-4">
          <label className="text-xs font-medium text-slate-400 block mb-2">Decision</label>
          <div className="grid grid-cols-3 gap-2">
            {(["confirmed_fraud", "false_positive", "unclear"] as const).map((d) => (
              <button
                key={d}
                onClick={() => setForm((f) => ({ ...f, decision: d }))}
                className={`px-3 py-2 rounded-lg text-xs font-medium border transition ${
                  form.decision === d
                    ? d === "confirmed_fraud"
                      ? "bg-red-500/20 border-red-500/40 text-red-400"
                      : d === "false_positive"
                        ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-400"
                        : "bg-amber-500/20 border-amber-500/40 text-amber-400"
                    : "bg-slate-800/60 border-slate-700/40 text-slate-400 hover:bg-slate-800/80"
                }`}
              >
                {d === "confirmed_fraud" ? "Confirmed" : d === "false_positive" ? "False Positive" : "Unclear"}
              </button>
            ))}
          </div>
        </div>

        {/* Confidence */}
        <div className="mb-4">
          <label className="text-xs font-medium text-slate-400 block mb-2">
            Confidence: <span className="text-sky-400">{form.confidence}</span> / 5
          </label>
          <input
            type="range"
            min={1}
            max={5}
            step={1}
            value={form.confidence}
            onChange={(e) => setForm((f) => ({ ...f, confidence: Number(e.target.value) }))}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-sky-500"
          />
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-slate-600">Low</span>
            <span className="text-[10px] text-slate-600">High</span>
          </div>
        </div>

        {/* Notes */}
        <div className="mb-6">
          <label className="text-xs font-medium text-slate-400 block mb-2">Notes</label>
          <textarea
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            rows={3}
            placeholder="Additional context or reasoning..."
            className="w-full px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-sky-500/40 resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-slate-400 bg-slate-800/60 border border-slate-700/40 hover:bg-slate-800/80 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-sky-600 text-white hover:bg-sky-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-3.5 h-3.5" />
            {submitting ? "Submitting..." : "Submit Feedback"}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export const SARPage = () => {
  const [searchParams] = useSearchParams();
  const alertIdParam = searchParams.get("alert_id");

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [sarStatus, setSarStatus] = useState<"Draft" | "Submitted">("Draft");
  const [showFeedback, setShowFeedback] = useState(false);
  const sarContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchAlerts() {
      setLoading(true);
      try {
        const data = await apiService.getDemoTrackA();
        if (!cancelled && data?.alerts) {
          setAlerts(data.alerts);
          if (alertIdParam) {
            const match = data.alerts.find((a: Alert) => a.alert_id === alertIdParam);
            if (match) setSelectedAlert(match);
          }
        }
      } catch {
        // silently fail
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchAlerts();
    return () => {
      cancelled = true;
    };
  }, [alertIdParam]);

  const handleExportPdf = useCallback(() => {
    if (!sarContentRef.current || !selectedAlert) return;
    const sarId = generateSarId(selectedAlert.alert_id);
    const element = sarContentRef.current;
    const opt = {
      margin: 10,
      filename: `${sarId}.pdf`,
      image: { type: "jpeg" as const, quality: 0.98 },
      html2canvas: { scale: 2, backgroundColor: "#0f172a" },
      jsPDF: { unit: "mm" as const, format: "a4" as const, orientation: "portrait" as const },
    };
    html2pdf().set(opt).from(element).save();
  }, [selectedAlert]);

  const handleFeedbackSubmit = async (form: FeedbackForm) => {
    if (!selectedAlert) return;
    try {
      await apiService.submitFeedback({
        alert_id: selectedAlert.alert_id,
        decision: form.decision,
        confidence: form.confidence,
        notes: form.notes,
      });
      setSarStatus("Submitted");
    } catch {
      // feedback submission failure is non-critical
    }
  };

  const sarId = selectedAlert ? generateSarId(selectedAlert.alert_id) : "";
  const filingDate = new Date().toISOString().slice(0, 10);

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
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-sky-500/20 to-indigo-500/20 border border-sky-500/20">
            <FileText className="w-6 h-6 text-sky-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">SAR Reports</h1>
            <p className="text-sm text-slate-400">Suspicious Activity Report generation and review</p>
          </div>
        </motion.div>

        {/* Two-panel layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT PANEL: Alert Selector */}
          <motion.div
            className="lg:col-span-3 bg-slate-900/40 backdrop-blur border border-slate-800/50 rounded-xl overflow-hidden flex flex-col"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <div className="px-4 py-3 border-b border-slate-800/50">
              <h2 className="text-sm font-semibold text-slate-300">Alerts</h2>
              <p className="text-[10px] text-slate-500 mt-0.5">Select an alert to generate SAR</p>
            </div>
            <div className="p-3 space-y-2 overflow-y-auto flex-1 max-h-[calc(100vh-220px)]">
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="bg-slate-800/40 rounded-lg p-3 border border-slate-700/30 space-y-2 animate-pulse">
                    <div className="h-3 bg-slate-700/50 rounded w-3/4" />
                    <div className="h-2.5 bg-slate-700/30 rounded w-1/2" />
                    <div className="h-2.5 bg-slate-700/30 rounded w-2/3" />
                  </div>
                ))
              ) : alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-slate-500">
                  <AlertTriangle className="w-8 h-8 mb-2 opacity-40" />
                  <p className="text-xs">No alerts available</p>
                </div>
              ) : (
                alerts.map((alert, i) => (
                  <AlertSelectorItem
                    key={alert.alert_id}
                    alert={alert}
                    isSelected={selectedAlert?.alert_id === alert.alert_id}
                    onSelect={() => setSelectedAlert(alert)}
                    index={i}
                  />
                ))
              )}
            </div>
          </motion.div>

          {/* RIGHT PANEL: SAR Document */}
          <motion.div
            className="lg:col-span-9 bg-slate-900/40 backdrop-blur border border-slate-800/50 rounded-xl overflow-hidden"
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.15 }}
          >
            {loading ? (
              <LoadingSkeleton />
            ) : !selectedAlert ? (
              <EmptyState />
            ) : (
              <div className="flex flex-col">
                {/* Action Bar */}
                <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800/50">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500">SAR ID:</span>
                    <span className="font-mono text-xs text-slate-300">{sarId}</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      sarStatus === "Submitted"
                        ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                        : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    }`}>
                      {sarStatus}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleExportPdf}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/60 border border-slate-700/40 text-slate-300 hover:bg-slate-800/80 transition"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Export PDF
                    </button>
                    <button
                      onClick={() => setShowFeedback(true)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-sky-600 text-white hover:bg-sky-500 transition"
                    >
                      <Send className="w-3.5 h-3.5" />
                      Submit Feedback
                    </button>
                  </div>
                </div>

                {/* SAR Content */}
                <div ref={sarContentRef} className="p-8 space-y-8 overflow-y-auto max-h-[calc(100vh-260px)]">
                  {/* SAR Header */}
                  <div className="text-center pb-6 border-b border-slate-700/40">
                    <h2 className="text-xl font-bold text-white tracking-widest uppercase mb-2">
                      Suspicious Activity Report
                    </h2>
                    <p className="text-xs text-slate-500 tracking-wider">FIU-IND Reference Format</p>
                    <div className="mt-4 grid grid-cols-3 gap-4 max-w-lg mx-auto">
                      <div>
                        <span className="text-[10px] text-slate-500 block">SAR ID</span>
                        <span className="font-mono text-xs text-slate-300">{sarId}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Filing Date</span>
                        <span className="text-xs text-slate-300 flex items-center justify-center gap-1">
                          <Clock className="w-3 h-3" />
                          {filingDate}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Status</span>
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          sarStatus === "Submitted"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-amber-500/20 text-amber-400"
                        }`}>
                          {sarStatus}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Section 1: Detection Summary */}
                  <section>
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-4">
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                      Section 1: Detection Summary
                    </h3>
                    <div className="bg-slate-800/30 rounded-lg border border-slate-700/30 p-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Pattern Type</span>
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${getPatternColor(selectedAlert.pattern_type)}`}>
                            {selectedAlert.pattern_type}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Risk Score</span>
                          <div className="flex items-center gap-2">
                            <span className="text-lg font-bold text-white">{selectedAlert.risk_score}</span>
                            <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium ${getRiskBadgeClass(selectedAlert.risk_score)}`}>
                              {getRiskLabel(selectedAlert.risk_score)}
                            </span>
                          </div>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Structural Score</span>
                          <span className="text-sm font-mono text-slate-300">{selectedAlert.structural_score?.toFixed(2)}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Innocence Discount</span>
                          <span className="text-sm font-mono text-slate-300">{selectedAlert.innocence_discount?.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="mt-4 pt-3 border-t border-slate-700/30">
                        <span className="text-[10px] text-slate-500 block mb-1">Disposition</span>
                        <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${getDispositionBadgeClass(selectedAlert.disposition)}`}>
                          {selectedAlert.disposition || "pending"}
                        </span>
                      </div>
                    </div>
                  </section>

                  {/* Section 2: Scoring Signals */}
                  <section>
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-4">
                      <Building className="w-4 h-4 text-sky-400" />
                      Section 2: Scoring Signals
                    </h3>
                    {selectedAlert.scoring_signals && selectedAlert.scoring_signals.length > 0 ? (
                      <div className="bg-slate-800/30 rounded-lg border border-slate-700/30 overflow-hidden">
                        <table className="w-full text-left">
                          <thead>
                            <tr className="border-b border-slate-700/30">
                              <th className="px-4 py-2.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Signal</th>
                              <th className="px-4 py-2.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider text-center">Value</th>
                              <th className="px-4 py-2.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider text-center">Weight</th>
                              <th className="px-4 py-2.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider text-center">Contribution</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedAlert.scoring_signals.map((signal, i) => (
                              <tr key={i} className="border-b border-slate-700/20 last:border-0">
                                <td className="px-4 py-2.5 text-xs text-slate-300">{signal.signal_name}</td>
                                <td className="px-4 py-2.5 text-center">
                                  <div className="flex items-center justify-center gap-2">
                                    <div className="w-16 h-1.5 rounded-full bg-slate-700/50 overflow-hidden">
                                      <div
                                        className="h-full rounded-full bg-amber-500/60"
                                        style={{ width: `${Math.min(signal.signal_value * 100, 100)}%` }}
                                      />
                                    </div>
                                    <span className="text-xs font-mono text-slate-400">{signal.signal_value?.toFixed(2)}</span>
                                  </div>
                                </td>
                                <td className="px-4 py-2.5 text-center text-xs font-mono text-slate-400">{signal.weight?.toFixed(2)}</td>
                                <td className="px-4 py-2.5 text-center text-xs font-mono text-slate-400">{signal.contribution?.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="bg-slate-800/30 rounded-lg border border-slate-700/30 p-6 text-center">
                        <p className="text-xs text-slate-500">No scoring signals available</p>
                      </div>
                    )}
                  </section>

                  {/* Section 3: Investigative Narrative */}
                  <section>
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-4">
                      <User className="w-4 h-4 text-violet-400" />
                      Section 3: Investigative Narrative
                    </h3>
                    {selectedAlert.llm_explanation ? (
                      <div className="bg-slate-800/30 rounded-lg border border-slate-700/30 p-5">
                        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                          {selectedAlert.llm_explanation}
                        </p>
                      </div>
                    ) : (
                      <div className="bg-slate-800/30 rounded-lg border border-slate-700/30 p-6 text-center">
                        <p className="text-xs text-slate-500 italic">No narrative generated for this alert</p>
                      </div>
                    )}
                  </section>

                  {/* Section 4: Edge Flow Details */}
                  <section>
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200 mb-4">
                      <ChevronRight className="w-4 h-4 text-emerald-400" />
                      Section 4: Edge Flow Details
                    </h3>
                    <div className="bg-slate-800/30 rounded-lg border border-slate-700/30 p-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Nodes Involved</span>
                          <span className="text-sm font-mono text-slate-300">{selectedAlert.subgraph_nodes}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Transaction Edges</span>
                          <span className="text-sm font-mono text-slate-300">{selectedAlert.subgraph_edges}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Channels</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {(selectedAlert.channels || []).map((ch) => (
                              <span key={ch} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-700/50 text-slate-400 border border-slate-600/30">
                                {ch}
                              </span>
                            ))}
                            {(!selectedAlert.channels || selectedAlert.channels.length === 0) && (
                              <span className="text-[10px] text-slate-600">&mdash;</span>
                            )}
                          </div>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block mb-1">Alert Timestamp</span>
                          <span className="text-xs text-slate-400">{formatTimestamp(selectedAlert.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Feedback Modal */}
      <AnimatePresence>
        {showFeedback && selectedAlert && (
          <FeedbackModal
            alertId={selectedAlert.alert_id}
            onClose={() => setShowFeedback(false)}
            onSubmit={handleFeedbackSubmit}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
};
