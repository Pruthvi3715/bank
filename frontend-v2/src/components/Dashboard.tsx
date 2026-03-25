import { motion } from 'framer-motion';
import { AlertFeed } from './AlertFeed';
import { AgentActivityPanel } from './AgentActivityPanel';
import { GraphVisualizer } from './GraphVisualizer';
import { RiskRing } from './RiskRing';
import { StatsCard } from './StatsCard';
import { SARReport } from './SARReport';
import { ThemeToggle } from './ThemeToggle';
import { AdversarialTestPanel } from './AdversarialTestPanel';

export const Dashboard = () => {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="flex min-h-screen flex-col items-center justify-center p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800"
    >
      <header className="w-full mb-8">
        <h1 className="text-3xl font-bold text-center bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-indigo-600">
          GraphSentinel Dashboard
        </h1>
        <div className="flex justify-center mt-4 space-x-4">
          <ThemeToggle />
        </div>
      </header>

      <main className="w-full max-w-7xl space-y-8">
        {/* Top Row: Stats and Risk */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <StatsCard title="Active Alerts" value="24" trend="↑12%" icon="🚨" color="red" />
          <StatsCard title="Risk Score" value="7.2/10" trend="↓0.3" icon="⚖️" color="orange" />
          <StatsCard title="Entities Mapped" value="1,240" trend="↑8%" icon="🗺️" color="blue" />
          <RiskRing score={7.2} label="Overall Risk" />
        </div>

        {/* Middle Row: Main Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <GraphVisualizer 
              title="Transaction Flow Network"
              description="Force-directed graph showing entity relationships and money flow"
            />
          </div>
          <div className="lg:col-span-1">
            <AgentActivityPanel 
              title="Investigation Agents"
              description="Real-time agent activities and decision-making process"
            />
          </div>
        </div>

        {/* Bottom Row: Detailed Views */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AlertFeed 
            title="Active Alerts Feed"
            description="Prioritized list of suspicious transactions requiring investigation"
          />
          <div className="grid grid-cols-1 gap-4">
            <SARReport 
              title="Sample SAR Report"
              description="Generated Suspicious Activity Report template"
            />
            <AdversarialTestPanel 
              title="Adversarial Testing"
              description="Test system robustness against fraud evasion techniques"
            />
          </div>
        </div>
      </main>

      <footer className="w-full mt-12 pt-6 border-t border-gray-200 dark:border-gray-700">
        <p className="text-center text-sm text-gray-500 dark:text-gray-400">
          GraphSentinel v1.0 • AI-Powered AML Fraud Detection • 
          <a href="#" className="text-purple-600 hover:underline dark:text-purple-400">
            System Status: Operational
          </a>
        </p>
      </footer>
    </motion.div>
  );
};