import React from 'react';
import { motion } from 'framer-motion';
import { FilterBar } from './FilterBar';

interface AlertFeedProps {
  title: string;
  description: string;
}

export const AlertFeed: React.FC<AlertFeedProps> = ({ title, description }) => {
  const mockAlerts = [
    {
      id: 'ALT-001',
      timestamp: '2026-03-18 14:23:18',
      amount: 45000,
      currency: 'USD',
      fromEntity: 'Shell Corp LLC',
      toEntity: 'Offshore Holdings Ltd',
      riskScore: 9.2,
      status: 'Investigating',
      type: 'Structuring',
      jurisdiction: 'High Risk'
    },
    {
      id: 'ALT-002',
      timestamp: '2026-03-18 13:45:02',
      amount: 120000,
      currency: 'EUR',
      fromEntity: 'Import/Export Co',
      toEntity: 'Private Individual',
      riskScore: 8.7,
      status: 'New',
      type: 'Unusual Pattern',
      jurisdiction: 'Medium Risk'
    },
    {
      id: 'ALT-003',
      timestamp: '2026-03-18 12:30:45',
      amount: 75000,
      currency: 'GBP',
      fromEntity: 'Trading Company',
      toEntity: 'Crypto Exchange',
      riskScore: 7.9,
      status: 'Reviewed',
      type: 'Rapid Movement',
      jurisdiction: 'Low Risk'
    }
  ];

  return (
    <motion.div 
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.2, duration: 0.4 }}
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
      
      <div className="p-4">
        <FilterBar 
          onFilterChange={(filters) => console.log('Filters changed:', filters)}
          placeholder="Filter alerts..."
        />
        
        <div className="mt-4 space-y-3">
          {mockAlerts.map(alert => (
            <motion.div
              key={alert.id}
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: mockAlerts.indexOf(alert) * 0.1, duration: 0.3 }}
              className="p-4 rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Alert #{alert.id}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {alert.timestamp}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  alert.riskScore >= 8 ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                  alert.riskScore >= 6 ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                  'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                }`}
                >
                  {alert.riskScore}/10
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300">Amount:</p>
                  <p className="text-gray-900 dark:text-gray-100">{alert.currency} {alert.amount.toLocaleString()}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300">From:</p>
                  <p className="text-gray-900 dark:text-gray-100">{alert.fromEntity}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300">To:</p>
                  <p className="text-gray-900 dark:text-gray-100">{alert.toEntity}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300">Type:</p>
                  <p className="text-gray-900 dark:text-gray-100 capitalize">{alert.type}</p>
                </div>
              </div>
              
              <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  alert.status === 'New' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                  alert.status === 'Investigating' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                  alert.status === 'Reviewed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                }`}
                >
                  {alert.status}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};