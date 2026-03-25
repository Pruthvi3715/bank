import React from 'react';
import { motion } from 'framer-motion';

interface AgentActivityPanelProps {
  title: string;
  description: string;
}

export const AgentActivityPanel: React.FC<AgentActivityPanelProps> = ({ title, description }) => {
  const mockActivities = [
    {
      id: 'ACT-001',
      agent: 'ContextAgent',
      action: 'Analyzed transaction patterns',
      timestamp: '2026-03-18 14:20:00',
      status: 'completed',
      details: 'Found 3 suspicious patterns in layering detection'
    },
    {
      id: 'ACT-002',
      agent: 'PathfinderAgent',
      action: 'Traced money flow',
      timestamp: '2026-03-18 14:18:30',
      status: 'running',
      details: 'Following 5 hops through 2 jurisdictions'
    },
    {
      id: 'ACT-003',
      agent: 'ScorerAgent',
      action: 'Calculated risk scores',
      timestamp: '2026-03-18 14:15:00',
      status: 'completed',
      details: 'Updated scores for 12 entities'
    },
    {
      id: 'ACT-004',
      agent: 'ReportAgent',
      action: 'Generated SAR draft',
      timestamp: '2026-03-18 14:10:00',
      status: 'completed',
      details: 'SAR-2026-00187 ready for review'
    }
  ];

  return (
    <motion.div 
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.4, duration: 0.4 }}
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
      
      <div className="p-4 space-y-4">
        {mockActivities.map(activity => (
          <motion.div
            key={activity.id}
            initial={{ x: -10, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: mockActivities.indexOf(activity) * 0.05, duration: 0.3 }}
            className="p-3 rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h3 className="font-medium text-gray-900 dark:text-gray-100">
                  {activity.agent}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {activity.timestamp}
                </p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                activity.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                activity.status === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
              }`}
              >
                {activity.status}
              </span>
            </div>
            
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {activity.action}
            </p>
            
            <p className="text-xs text-gray-600 dark:text-gray-400">
              {activity.details}
            </p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};