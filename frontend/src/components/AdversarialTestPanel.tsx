"use client";

import { useState } from "react";
import { authHeaders } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Bug, Loader2, CheckCircle, XCircle, Zap, Clock, GitBranch } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type TestId = "cycle_plus_hop" | "split_hub" | "time_distributed_smurfing" | "all";

interface AdversarialResult {
  test: string;
  title: string;
  summary: string;
  details?: unknown[];
}

interface AllResult {
  cycle_plus_hop: AdversarialResult;
  split_hub: AdversarialResult;
  time_distributed_smurfing: AdversarialResult;
}

const testCards = [
  {
    id: "cycle_plus_hop" as TestId,
    title: "Cycle + 1 Hop",
    description: "Cycles with an additional hop to evade direct detection",
    icon: GitBranch,
    color: "amber",
  },
  {
    id: "split_hub" as TestId,
    title: "Split Hub",
    description: "Funds split across intermediaries to avoid thresholds",
    icon: Zap,
    color: "orange",
  },
  {
    id: "time_distributed_smurfing" as TestId,
    title: "Temporal Smurfing",
    description: "Time-distributed transactions below reporting limits",
    icon: Clock,
    color: "cyan",
  },
];

const colorMap: Record<string, { border: string; text: string; bg: string }> = {
  amber: { border: "border-amber-500/30", text: "text-amber-500", bg: "bg-amber-500/8" },
  orange: { border: "border-orange-500/30", text: "text-orange-500", bg: "bg-orange-500/8" },
  cyan: { border: "border-cyan-500/30", text: "text-cyan-500", bg: "bg-cyan-500/8" },
};

export default function AdversarialTestPanel() {
  const [loading, setLoading] = useState<string | null>(null);
  const [result, setResult] = useState<AdversarialResult | AllResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runTest = async (test: TestId) => {
    setLoading(test);
    setError(null);
    setResult(null);
    try {
      const url =
        test === "all"
          ? `${API_BASE}/api/adversarial-test`
          : `${API_BASE}/api/adversarial-test?test=${test}`;
      const res = await fetch(url, { headers: { ...authHeaders() } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(null);
    }
  };

  const isAllResult = (r: AdversarialResult | AllResult): r is AllResult =>
    "cycle_plus_hop" in r && "split_hub" in r;

  const renderSingle = (r: AdversarialResult) => (
    <motion.div
      key={r.test}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-3 border border-border bg-secondary/20 space-y-2"
    >
      <h4 className="text-xs font-mono font-medium">{r.title}</h4>
      <p className="text-[11px] text-muted-foreground">{r.summary}</p>
      {r.details && r.details.length > 0 && (
        <ul className="space-y-1 mt-1">
          {r.details.map((d: unknown, i: number) => {
            const row = d as Record<string, unknown>;
            if (row.message)
              return (
                <li key={i} className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
                  <span className="w-1 h-1 bg-muted-foreground" />
                  {String(row.message)}
                </li>
              );
            if (row.variant)
              return (
                <li key={i} className="flex items-center gap-2 text-[11px] font-mono">
                  {row.detected ? (
                    <CheckCircle className="w-3 h-3 text-emerald-500 shrink-0" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-500 shrink-0" />
                  )}
                  <span className="font-medium">{String(row.variant)}:</span>
                  {row.detected ? "Detected" : "Missed"}
                </li>
              );
            if (row.hops != null)
              return (
                <li key={i} className="flex items-center gap-2 text-[11px] font-mono">
                  {row.detected ? (
                    <CheckCircle className="w-3 h-3 text-emerald-500 shrink-0" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-500 shrink-0" />
                  )}
                  {Number(row.hops)}-hop: {row.detected ? "Detected" : "Missed"}
                </li>
              );
            if (row.note)
              return (
                <li key={i} className="text-[10px] text-muted-foreground font-mono">
                  {String(row.note)}
                </li>
              );
            return null;
          })}
        </ul>
      )}
    </motion.div>
  );

  return (
    <div className="border border-border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-primary" />
          <span className="text-[11px] font-mono uppercase tracking-wider font-medium">
            Adversarial Tests
          </span>
        </div>
        <Button
          onClick={() => runTest("all")}
          disabled={!!loading}
          className="gap-1.5 text-[10px] font-mono uppercase tracking-wider h-7 px-3 cursor-pointer"
        >
          {loading === "all" ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Zap className="w-3.5 h-3.5" />
          )}
          Run All
        </Button>
      </div>

      <div className="p-4 space-y-4">
        {/* Test Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {testCards.map((test) => {
            const c = colorMap[test.color];
            const isLoading = loading === test.id;
            return (
              <button
                key={test.id}
                className={`p-3 border ${c.border} ${c.bg} text-left transition-colors hover:bg-secondary/30 cursor-pointer`}
                onClick={() => runTest(test.id)}
                disabled={!!loading}
              >
                <div className="flex items-center gap-2 mb-2">
                  {isLoading ? (
                    <Loader2 className={`w-4 h-4 ${c.text} animate-spin`} />
                  ) : (
                    <test.icon className={`w-4 h-4 ${c.text}`} />
                  )}
                  <span className="text-xs font-mono font-medium">{test.title}</span>
                </div>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  {test.description}
                </p>
              </button>
            );
          })}
        </div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 p-2 bg-red-500/10 border border-red-500/20 text-red-500 text-[11px] font-mono"
            >
              <XCircle className="w-3.5 h-3.5 shrink-0" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
              <h4 className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <CheckCircle className="w-3 h-3 text-emerald-500" />
                Results
              </h4>
              <div className="space-y-2">
                {isAllResult(result)
                  ? [result.cycle_plus_hop, result.split_hub, result.time_distributed_smurfing].map(renderSingle)
                  : renderSingle(result as AdversarialResult)}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
