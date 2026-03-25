import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { StatsCard } from '../components/StatsCard';
import { RiskRing } from '../components/RiskRing';
import { AgentActivityPanel } from '../components/AgentActivityPanel';
import { AlertFeed } from '../components/AlertFeed';
import { apiService } from '../lib/apiService';

interface DashboardStats {
  total_txns: number;
  total_nodes: number;
  total_edges: number;
  alerts_generated: number;
  pattern_counts: Record<string, number>;
}

interface DashboardData {
  alerts: unknown[];
  graph: { nodes: unknown[]; links: unknown[] };
  stats: DashboardStats;
  agent_activity: unknown[];
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { duration: 0.4 } },
};

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiService.getDemoTrackA();
        setData(response.data);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Failed to load dashboard data. Showing default values.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleRunDetection = async () => {
    try {
      setPipelineRunning(true);
      setPipelineError(null);
      const response = await apiService.runPipeline();
      if (response.data) {
        setData(response.data);
      }
    } catch (err) {
      console.error('Pipeline execution failed:', err);
      setPipelineError('Pipeline execution failed. Please try again.');
    } finally {
      setPipelineRunning(false);
    }
  };

  const alertsGenerated = data?.stats?.alerts_generated ?? 24;
  const totalNodes = data?.stats?.total_nodes ?? 1240;
  const totalTxns = data?.stats?.total_txns ?? 10240;

  const riskScore = (() => {
    if (!data?.alerts?.length) return 7.2;
    const scores = data.alerts
      .map((a: any) => a.risk_score ?? a.riskScore)
      .filter((s: any) => typeof s === 'number');
    if (scores.length === 0) return 7.2;
    return parseFloat((scores.reduce((a: number, b: number) => a + b, 0) / scores.length).toFixed(1));
  })();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col items-center gap-4">
          <svg
            className="animate-spin h-10 w-10 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Loading dashboard data...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-7xl mx-auto space-y-6"
      >
        {/* Page Header */}
        <motion.div
          variants={itemVariants}
          className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        >
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Dashboard
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Real-time fraud detection overview
            </p>
          </div>
          <div className="flex items-center gap-3">
            {pipelineError && (
              <span className="text-xs text-red-500 dark:text-red-400">
                {pipelineError}
              </span>
            )}
            <button
              onClick={handleRunDetection}
              disabled={pipelineRunning}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
            >
              {pipelineRunning ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Running...
                </>
              ) : (
                <>
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Run Detection
                </>
              )}
            </button>
          </div>
        </motion.div>

        {error && (
          <motion.div
            variants={itemVariants}
            className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg px-4 py-3 text-sm text-yellow-800 dark:text-yellow-200"
          >
            {error}
          </motion.div>
        )}

        {/* Stats Row */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <StatsCard
            title="Active Alerts"
            value={String(alertsGenerated)}
            trend="↑ 12%"
            icon="🚨"
            color="red"
          />
          <StatsCard
            title="Risk Score"
            value={`${riskScore}/10`}
            trend="↑ 0.3"
            icon="⚖️"
            color="orange"
          />
          <StatsCard
            title="Entities Mapped"
            value={totalNodes.toLocaleString()}
            trend="↑ 8%"
            icon="🗄️"
            color="blue"
          />
          <StatsCard
            title="Transactions Processed"
            value={totalTxns.toLocaleString()}
            trend="↑ 15%"
            icon="📈"
            color="green"
          />
        </motion.div>

        {/* Second Row: Agent Activity + Risk Ring */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1 lg:grid-cols-3 gap-4"
        >
          <div className="lg:col-span-2">
            <AgentActivityPanel
              title="Agent Activity"
              description="Live agent execution pipeline"
            />
          </div>
          <div className="lg:col-span-1">
            <RiskRing score={riskScore} label="Overall Risk Score" />
          </div>
        </motion.div>

        {/* Third Row: Alert Feed */}
        <motion.div variants={itemVariants}>
          <AlertFeed
            title="Recent Alerts"
            description="Latest flagged transactions and entities"
          />
        </motion.div>
      </motion.div>
    </div>
  );
};
