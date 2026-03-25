import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { runAdversarialTest } from "../lib/apiService";

interface TestResult {
  detected: boolean;
  details: string;
}

interface TestCard {
  id: string;
  name: string;
  description: string;
  expectedBehavior: string;
  icon: typeof Shield;
}

const testCards: TestCard[] = [
  {
    id: "cycle_plus_hop",
    name: "Cycle + 1 Hop",
    description:
      "Tests detection of circular transactions with an extra hop to break cycle detection. Funds are laundered through a circular path with an intermediary node inserted to evade simple cycle algorithms.",
    expectedBehavior:
      "System should identify the extended cycle and flag it as suspicious despite the additional hop.",
    icon: RefreshCw,
  },
  {
    id: "split_hub",
    name: "Split Hub",
    description:
      "Tests hub-based splitting where a central node distributes funds across multiple recipients to stay below reporting thresholds.",
    expectedBehavior:
      "System should correlate the hub pattern and detect the structured distribution as a coordinated scheme.",
    icon: AlertTriangle,
  },
  {
    id: "time_distributed_smurfing",
    name: "Time-Distributed Smurfing",
    description:
      "Tests detection of structuring spread over time to avoid velocity detection. Small deposits are made across extended time windows.",
    expectedBehavior:
      "System should recognize temporal aggregation patterns and flag repeated sub-threshold transactions.",
    icon: Clock,
  },
];

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: "easeOut" },
  },
};

export const TestsPage = () => {
  const [results, setResults] = useState<Record<string, TestResult>>({});
  const [running, setRunning] = useState<Record<string, boolean>>({});
  const [runningAll, setRunningAll] = useState(false);

  const runTest = async (testId: string) => {
    setRunning((prev) => ({ ...prev, [testId]: true }));
    try {
      const res = await runAdversarialTest(testId);
      const testResult = res?.tests?.[testId] ?? res?.results?.[testId];
      setResults((prev) => ({
        ...prev,
        [testId]: {
          detected: testResult?.detected ?? false,
          details: testResult?.details ?? JSON.stringify(testResult),
        },
      }));
    } catch (err: any) {
      setResults((prev) => ({
        ...prev,
        [testId]: {
          detected: false,
          details: err?.message ?? "Test execution failed",
        },
      }));
    } finally {
      setRunning((prev) => ({ ...prev, [testId]: false }));
    }
  };

  const runAllTests = async () => {
    setRunningAll(true);
    setRunning(Object.fromEntries(testCards.map((t) => [t.id, true])));
    try {
      const res = await runAdversarialTest();
      const tests = res?.tests ?? res?.results ?? {};
      const mapped: Record<string, TestResult> = {};
      for (const [key, val] of Object.entries(tests)) {
        const v = val as any;
        mapped[key] = {
          detected: v?.detected ?? false,
          details: v?.details ?? JSON.stringify(v),
        };
      }
      setResults(mapped);
    } catch (err: any) {
      const errObj: Record<string, TestResult> = {};
      for (const t of testCards) {
        errObj[t.id] = { detected: false, details: err?.message ?? "Run failed" };
      }
      setResults(errObj);
    } finally {
      setRunningAll(false);
      setRunning(Object.fromEntries(testCards.map((t) => [t.id, false])));
    }
  };

  const clearResults = () => {
    setResults({});
    setRunning({});
  };

  const totalRun = Object.keys(results).length;
  const detectedCount = Object.values(results).filter((r) => r.detected).length;
  const missedCount = totalRun - detectedCount;
  const detectionRate = totalRun > 0 ? Math.round((detectedCount / totalRun) * 100) : 0;

  const StatusIcon = ({ detected }: { detected: boolean }) =>
    detected ? (
      <CheckCircle className="w-5 h-5 text-emerald-400" />
    ) : (
      <XCircle className="w-5 h-5 text-red-400" />
    );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Adversarial Testing</h1>
        <p className="mt-1 text-sm text-gray-400">
          Validate detection robustness against evasion techniques
        </p>
      </div>

      {/* Info Banner */}
      <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
        <Shield className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-400" />
        <div className="text-sm text-amber-200">
          <p className="font-medium">About Adversarial Testing</p>
          <p className="mt-1 text-amber-200/70">
            These tests simulate known money-laundering evasion techniques to
            stress-test GraphSentinel's detection algorithms. Each test
            introduces synthetic graph patterns designed to bypass common
            AML rules. Use results to identify blind spots and tune detection
            thresholds.
          </p>
        </div>
      </div>

      {/* Test Cards */}
      <motion.div
        className="grid gap-6 md:grid-cols-3"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {testCards.map((card) => {
          const Icon = card.icon;
          const isRunning = running[card.id] ?? false;
          const result = results[card.id];

          return (
            <motion.div
              key={card.id}
              variants={cardVariants}
              className="flex flex-col rounded-xl border border-gray-700/60 bg-gray-800/50 p-5 backdrop-blur"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-indigo-500/15 p-2">
                  <Icon className="h-5 w-5 text-indigo-400" />
                </div>
                <h3 className="text-base font-semibold text-white">
                  {card.name}
                </h3>
              </div>

              <p className="mt-3 flex-1 text-sm leading-relaxed text-gray-400">
                {card.description}
              </p>

              <p className="mt-3 text-xs text-gray-500">
                <span className="font-medium text-gray-400">Expected:</span>{" "}
                {card.expectedBehavior}
              </p>

              {/* Run button */}
              <button
                onClick={() => runTest(card.id)}
                disabled={isRunning}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isRunning ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {isRunning ? "Running…" : "Run Test"}
              </button>

              {/* Result */}
              <AnimatePresence>
                {result && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <div
                      className={`mt-4 rounded-lg border p-3 ${
                        result.detected
                          ? "border-emerald-500/30 bg-emerald-500/10"
                          : "border-red-500/30 bg-red-500/10"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <StatusIcon detected={result.detected} />
                        <span
                          className={`text-sm font-medium ${
                            result.detected ? "text-emerald-300" : "text-red-300"
                          }`}
                        >
                          {result.detected ? "Detected" : "Missed"}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-relaxed text-gray-300">
                        {result.details}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Action Buttons */}
      <div className="flex items-center gap-4">
        <button
          onClick={runAllTests}
          disabled={runningAll}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {runningAll ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {runningAll ? "Running All…" : "Run All Tests"}
        </button>

        <button
          onClick={clearResults}
          disabled={totalRun === 0}
          className="rounded-lg border border-gray-600 px-5 py-2.5 text-sm font-medium text-gray-300 transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Clear Results
        </button>
      </div>

      {/* Results Summary */}
      <AnimatePresence>
        {totalRun > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            className="rounded-xl border border-gray-700/60 bg-gray-800/50 p-6 backdrop-blur"
          >
            <h2 className="text-lg font-semibold text-white">Results Summary</h2>

            <div className="mt-4 grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-white">{totalRun}</p>
                <p className="text-xs text-gray-400">Total Run</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-emerald-400">
                  {detectedCount}
                </p>
                <p className="text-xs text-gray-400">Detected</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-400">{missedCount}</p>
                <p className="text-xs text-gray-400">Missed</p>
              </div>
            </div>

            <div className="mt-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Detection Rate</span>
                <span className="font-semibold text-white">
                  {detectionRate}%
                </span>
              </div>
              <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-gray-700">
                <motion.div
                  className="h-full rounded-full bg-indigo-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${detectionRate}%` }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
