"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Download, FileText, AlertCircle, CheckCircle, HelpCircle, Send, MessageSquare, Brain, Shield } from "lucide-react";
import RiskRing from "@/components/RiskRing";
import { Alert, SARChatMessage } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const QUICK_QUESTIONS = [
  { label: "Why flagged?", prompt: "Explain in plain English why this alert was flagged and what makes it suspicious." },
  { label: "Key node?", prompt: "Which account is the most central to this fraud pattern and why?" },
  { label: "Money trail", prompt: "Describe the complete path the money took, with amounts and timestamps." },
  { label: "Draft FIU note", prompt: "Draft a formal one-paragraph FIU-IND submission note for this case." },
];

interface SARReportProps {
  alert: Alert | null;
  chatMessages?: SARChatMessage[];
  onSendChat?: (message: string) => void;
  isChatLoading?: boolean;
}

export default function SARReport({ alert, chatMessages = [], onSendChat, isChatLoading }: SARReportProps) {
  const printRef = useRef<HTMLDivElement>(null);
  const [feedbackConfidence, setFeedbackConfidence] = useState(3);
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);

  const submitFeedback = async (
    decision: "confirmed_fraud" | "false_positive" | "unclear"
  ) => {
    if (!alert) return;
    setFeedbackSent(null);
    try {
      const res = await fetch(`${API_BASE}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alert_id: alert.alert_id,
          decision,
          confidence: feedbackConfidence,
          pattern_type: alert.pattern_type,
          notes: feedbackNotes,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setFeedbackSent(decision);
    } catch {
      setFeedbackSent("error");
    }
  };

  const downloadPDF = async () => {
    if (!alert || typeof window === "undefined") return;
    const html2pdf = (await import("html2pdf.js")).default;
    const element = printRef.current;
    if (!element) return;
    html2pdf()
      .set({
        margin: 0.5,
        filename: `SAR_FIU_IND_${alert.alert_id.split("-")[0]}.pdf`,
        image: { type: "jpeg" as const, quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: "in", format: "letter", orientation: "portrait" as const },
      })
      .from(element)
      .save();
  };

  if (!alert) {
    return (
      <div className="border border-border bg-card p-8 flex flex-col items-center justify-center text-center h-full min-h-[300px]">
        <FileText className="w-10 h-10 text-muted-foreground/20 mb-3" />
        <p className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
          No alert selected
        </p>
        <p className="text-[10px] text-muted-foreground/60 mt-1">
          Select an alert to view its SAR
        </p>
      </div>
    );
  }

  return (
    <div className="border border-border bg-card flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
            SAR Report
          </span>
          <span className="text-[9px] font-mono px-1.5 py-0.5 bg-secondary text-muted-foreground">
            {alert.alert_id.slice(0, 8)}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <RiskRing score={alert.risk_score} size={36} strokeWidth={2.5} showValue />
          <Button
            onClick={downloadPDF}
            variant="outline"
            className="gap-1.5 text-[10px] font-mono uppercase tracking-wider h-7 px-2 cursor-pointer"
          >
            <Download className="w-3 h-3" />
            PDF
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-4 py-4 space-y-5" ref={printRef}>
          {/* Detection Summary */}
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.05 }}
          >
            <h3 className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
              <div className="w-1 h-3 bg-primary" />
              Detection Summary
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: "Pattern", value: alert.pattern_type },
                { label: "Discount", value: `${alert.innocence_discount}%` },
                { label: "Score", value: `${alert.risk_score.toFixed(1)}/100` },
              ].map((item) => (
                <div key={item.label} className="p-2.5 border border-border bg-secondary/30">
                  <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground block mb-0.5">
                    {item.label}
                  </span>
                  <span className="text-sm font-medium font-mono">{item.value}</span>
                </div>
              ))}
            </div>
          </motion.section>

          {/* Scoring Signals */}
          {alert.scoring_signals && Object.keys(alert.scoring_signals).length > 0 && (
            <motion.section
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <h3 className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
                <div className="w-1 h-3 bg-amber-500" />
                Scoring Signals
              </h3>
              <div className="border border-border">
                {Object.entries(alert.scoring_signals).map(([key, val]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between px-3 py-1.5 border-b border-border last:border-b-0 text-xs"
                  >
                    <span className="font-mono text-muted-foreground">{key}</span>
                    <span className="font-mono font-medium tabular-nums">{Number(val).toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </motion.section>
          )}

          {/* Narrative */}
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
          >
            <h3 className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
              <div className="w-1 h-3 bg-primary" />
              Investigative Narrative
            </h3>
            <div className="p-3 border border-border bg-secondary/20 text-sm leading-relaxed whitespace-pre-wrap font-mono text-foreground/80">
              {alert.llm_explanation || "No narrative available — run with LLM enabled."}
            </div>
          </motion.section>

          {/* Edge Flow */}
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <h3 className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
              <div className="w-1 h-3 bg-cyan-500" />
              Edge Flow ({alert.subgraph_edges.length})
            </h3>
            <div className="border border-border max-h-[120px] overflow-auto">
              {alert.subgraph_edges.map((edge, i) => (
                <div
                  key={i}
                  className="px-3 py-1 border-b border-border last:border-b-0 text-[11px] font-mono text-muted-foreground"
                >
                  {edge}
                </div>
              ))}
            </div>
          </motion.section>

          {/* Feedback */}
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
          >
            <h3 className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
              <div className="w-1 h-3 bg-emerald-500" />
              Investigator Feedback
            </h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-muted-foreground">Confidence:</span>
                <select
                  value={feedbackConfidence}
                  onChange={(e) => setFeedbackConfidence(Number(e.target.value))}
                  className="h-6 border border-border bg-secondary px-1.5 text-[10px] font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-wrap gap-1.5">
                <button
                  onClick={() => submitFeedback("false_positive")}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase tracking-wider border border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10 transition-colors cursor-pointer"
                >
                  <CheckCircle className="w-3 h-3" />
                  False Positive
                </button>
                <button
                  onClick={() => submitFeedback("confirmed_fraud")}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase tracking-wider border border-red-500/30 text-red-500 hover:bg-red-500/10 transition-colors cursor-pointer"
                >
                  <AlertCircle className="w-3 h-3" />
                  Confirmed
                </button>
                <button
                  onClick={() => submitFeedback("unclear")}
                  className="flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase tracking-wider border border-border text-muted-foreground hover:bg-secondary transition-colors cursor-pointer"
                >
                  <HelpCircle className="w-3 h-3" />
                  Unclear
                </button>
              </div>

              <textarea
                placeholder="Notes (optional)"
                value={feedbackNotes}
                onChange={(e) => setFeedbackNotes(e.target.value)}
                className="w-full border border-border bg-secondary/30 px-2 py-1.5 text-xs font-mono min-h-[48px] focus:outline-none focus:ring-1 focus:ring-primary resize-none"
              />

              {feedbackSent === "error" && (
                <p className="text-[10px] text-red-500 font-mono flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> Submission failed
                </p>
              )}
              {feedbackSent && feedbackSent !== "error" && (
                <p className="text-[10px] text-emerald-500 font-mono flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Recorded: {feedbackSent.replace("_", " ")}
                </p>
              )}
            </div>
          </motion.section>

          {/* ML Scores */}
          {(alert.if_score !== undefined && alert.if_score > 0) && (
            <motion.section
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <h3 className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-2">
                <div className="w-1 h-3 bg-violet-500" />
                ML Model Scores
              </h3>
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 border border-border bg-secondary/30">
                  <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground block mb-0.5">
                    <Brain className="w-3 h-3 inline mr-1" />Isolation Forest
                  </span>
                  <span className={`text-sm font-medium font-mono tabular-nums ${
                    alert.if_score > 0.7 ? "text-red-400" : alert.if_score > 0.4 ? "text-amber-400" : "text-emerald-400"
                  }`}>{alert.if_score.toFixed(3)}</span>
                </div>
                {alert.xgb_score !== undefined && (
                  <div className="p-2.5 border border-border bg-secondary/30">
                    <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground block mb-0.5">
                      <Shield className="w-3 h-3 inline mr-1" />Gradient Boost
                    </span>
                    <span className={`text-sm font-medium font-mono tabular-nums ${
                      alert.xgb_score > 0.7 ? "text-red-400" : alert.xgb_score > 0.4 ? "text-amber-400" : "text-emerald-400"
                    }`}>{alert.xgb_score.toFixed(3)}</span>
                  </div>
                )}
              </div>
            </motion.section>
          )}
        </div>
      </div>

      {/* SAR Chatbot Section */}
      {onSendChat && (
        <div className="border-t border-border">
          <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border">
            <MessageSquare className="w-3.5 h-3.5 text-primary" />
            <span className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground">
              Investigation Chat
            </span>
          </div>

          {/* Quick Questions */}
          <div className="flex flex-wrap gap-1 px-3 py-1.5 border-b border-border">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q.label}
                onClick={() => onSendChat(q.prompt)}
                disabled={isChatLoading}
                className="text-[9px] font-mono px-2 py-1 border border-border hover:bg-secondary transition-colors cursor-pointer disabled:opacity-50"
              >
                {q.label}
              </button>
            ))}
          </div>

          {/* Chat Messages */}
          {chatMessages.length > 0 && (
            <div className="max-h-[200px] overflow-y-auto px-3 py-2 space-y-2">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`text-[11px] font-mono p-2 ${
                    msg.role === "user"
                      ? "bg-primary/5 border-l-2 border-primary text-foreground/80"
                      : "bg-secondary/30 border-l-2 border-emerald-500 text-foreground/90"
                  }`}
                >
                  <span className="text-[8px] uppercase tracking-wider text-muted-foreground block mb-1">
                    {msg.role === "user" ? "You" : "GraphSentinel AI"}
                  </span>
                  <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                </div>
              ))}
            </div>
          )}

          {/* Chat Input */}
          <ChatInput onSend={onSendChat} isLoading={isChatLoading} />
        </div>
      )}
    </div>
  );
}

function ChatInput({ onSend, isLoading }: { onSend: (msg: string) => void; isLoading?: boolean }) {
  const [input, setInput] = useState("");
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput("");
  };
  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 px-3 py-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about this alert..."
        disabled={isLoading}
        className="flex-1 h-7 border border-border bg-secondary/30 px-2 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={!input.trim() || isLoading}
        className="p-1.5 bg-primary/10 hover:bg-primary/20 text-primary disabled:opacity-30 cursor-pointer"
      >
        <Send className="w-3.5 h-3.5" />
      </button>
    </form>
  );
}
