import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface AdversarialTestPanelProps {
  title: string;
  description: string;
}

export const AdversarialTestPanel: React.FC<AdversarialTestPanelProps> = ({ title, description }) => {
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const tests = [
    { id: 'cycle_plus_hop', name: 'Cycle + 1 Hop', description: 'Tests detection of circular transactions with an extra hop' },
    { id: 'split_hub', name: 'Split Hub', description: 'Tests hub-based splitting detection' },
    { id: 'time_distributed_smurfing', name: 'Time-Distributed Smurfing', description: 'Tests detection of time-based structuring' },
  ];

  const runTest = async (testId: string) => {
    setSelectedTest(testId);
    setIsRunning(true);
    // Simulate API call
    setTimeout(() => {
      setIsRunning(false);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 1.2, duration: 0.4 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden"
    >
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
          {title}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {description}
        </p>
      </div>
      
      <div className="p-4 space-y-3">
        {tests.map(test => (
          <div 
            key={test.id}
            className={`p-4 rounded-lg border transition-colors ${
              selectedTest === test.id 
                ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20' 
                : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">
                  {test.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {test.description}
                </p>
              </div>
              <button
                onClick={() => runTest(test.id)}
                disabled={isRunning && selectedTest === test.id}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isRunning && selectedTest === test.id
                    ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                    : 'bg-purple-600 text-white hover:bg-purple-700'
                }`}
              >
                {isRunning && selectedTest === test.id ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Running...
                  </span>
                ) : 'Run Test'}
              </button>
            </div>
          </div>
        ))}
        
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => runTest('all')}
            disabled={isRunning}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors disabled:opacity-50"
          >
            Run All Tests
          </button>
        </div>
      </div>
    </motion.div>
  );
};