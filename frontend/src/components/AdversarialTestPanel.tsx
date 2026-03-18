"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bug, Loader2, CheckCircle, XCircle, Zap, Clock, GitBranch } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type TestId =
  | "cycle_plus_hop"
  | "split_hub"
  | "time_distributed_smurfing"
  | "all";

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
    description: "Tests detection of cycles with an additional hop to evade direct cycle detection",
    icon: GitBranch,
    color: "blue",
  },
  {
    id: "split_hub" as TestId,
    title: "Split Hub",
    description: "Tests detection of funds split across multiple intermediaries to avoid threshold triggers",
    icon: Zap,
    color: "purple",
  },
  {
    id: "time_distributed_smurfing" as TestId,
    title: "Temporal Smurfing",
    description: "Tests detection of time-distributed transactions designed to stay below reporting thresholds",
    icon: Clock,
    color: "cyan",
  },
];

const colorMap: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  blue: { bg: "bg-blue-500/10", border: "border-blue-500/20", text: "text-blue-500", icon: "text-blue-500" },
  purple: { bg: "bg-purple-500/10", border: "border-purple-500/20", text: "text-purple-500", icon: "text-purple-500" },
  cyan: { bg: "bg-cyan-500/10", border: "border-cyan-500/20", text: "text-cyan-500", icon: "text-cyan-500" },
};

export default function AdversarialTestPanel() {
  const [loading, setLoading] = useState<string | null>(null);
  const [result, setResult] = useState<AdversarialResult | AllResult | null>(
    null
  );
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
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(null);
    }
  };

  const isAllResult = (
    r: AdversarialResult | AllResult
  ): r is AllResult =>
    r !== null &&
    "cycle_plus_hop" in r &&
    "split_hub" in r &&
    "time_distributed_smurfing" in r;

  const renderSingle = (r: AdversarialResult) => (
    <motion.div
      key={r.test}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 rounded-lg border border-border bg-muted/30 space-y-2"
    >
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-medium">{r.title}</h4>
      </div>
      <p className="text-xs text-muted-foreground">{r.summary}</p>
      {r.details && r.details.length > 0 && (
        <ul className="space-y-1 mt-2">
          {r.details.map((d: unknown, i: number) => {
            const row = d as Record<string, unknown>;
            if (row.message)
              return (
                <li key={i} className="flex items-center gap-2 text-xs">
                  <span className="w-1 h-1 rounded-full bg-muted-foreground" />
                  {String(row.message)}
                </li>
              );
            if (row.variant)
              return (
                <li key={i} className="flex items-center gap-2 text-xs">
                  {row.detected ? (
                    <CheckCircle className="w-3 h-3 text-emerald-500" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-500" />
                  )}
                  <span className="font-medium">{String(row.variant)}:</span>
                  {row.detected ? "Detected" : "Not detected"}
                </li>
              );
            if (row.note)
              return (
                <li key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="w-1 h-1 rounded-full bg-muted-foreground" />
                  {String(row.note)}
                </li>
              );
            if (row.hops != null)
              return (
                <li key={i} className="flex items-center gap-2 text-xs">
                  {row.detected ? (
                    <CheckCircle className="w-3 h-3 text-emerald-500" />
                  ) : (
                    <XCircle className="w-3 h-3 text-red-500" />
                  )}
                  <span className="font-medium">{Number(row.hops)}-hop cycle:</span>
                  {row.detected ? "Detected" : "Not detected"}
                </li>
              );
            return null;
          })}
        </ul>
      )}
    </motion.div>
  );

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bug className="w-5 h-5 text-primary" />
            <CardTitle className="text-base font-semibold">
              Adversarial Test Suite
            </CardTitle>
          </div>
          <Button
            onClick={() => runTest("all")}
            disabled={!!loading}
            className="gap-2"
          >
            {loading === "all" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            Run All Tests
          </Button>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Evaluate detection limits against known evasion techniques
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Test Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {testCards.map((test) => {
            const colors = colorMap[test.color];
            const isLoading = loading === test.id;
            return (
              <motion.div
                key={test.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${colors.border} ${colors.bg} hover:shadow-md`}
                onClick={() => runTest(test.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    runTest(test.id);
                  }
                }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={`p-2 rounded-lg ${colors.bg}`}>
                    {isLoading ? (
                      <Loader2 className={`w-5 h-5 ${colors.icon} animate-spin`} />
                    ) : (
                      <test.icon className={`w-5 h-5 ${colors.icon}`} />
                    )}
                  </div>
                  <h3 className="font-medium text-sm">{test.title}</h3>
                </div>
                <p className="text-xs text-muted-foreground">
                  {test.description}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm"
            >
              <XCircle className="w-4 h-4" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-3"
            >
              <h4 className="text-sm font-medium flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                Test Results
              </h4>
              <div className="space-y-3">
                {isAllResult(result)
                  ? [
                      result.cycle_plus_hop,
                      result.split_hub,
                      result.time_distributed_smurfing,
                    ].map(renderSingle)
                  : renderSingle(result as AdversarialResult)}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
