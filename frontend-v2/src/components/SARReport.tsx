import React from 'react';
import { motion } from 'framer-motion';

interface SARReportProps {
  title: string;
  description: string;
}

export const SARReport: React.FC<SARReportProps> = ({ title, description }) => {
  const mockSAR = {
    id: 'SAR-2026-00187',
    timestamp: '2026-03-18 14:10:00',
    status: 'Draft',
    subject: 'Suspicious Transaction Pattern - Layering via Shell Companies',
    filingDeadline: '2026-03-25',
    summary: 'Multiple transactions totaling $450,000 over 72 hours involving 3 jurisdictions and 5 intermediary entities consistent with classic layering technique.',
    entities: [
      { name: 'Shell Corp LLC', role: 'Subject', jurisdiction: 'BVI' },
      { name: 'Offshore Holdings Ltd', role: 'Intermediary', jurisdiction: 'Cayman Islands' },
      { name: 'Import/Export Co', role: 'Counterparty', jurisdiction: 'USA' }
    ],
    transactions: [
      { id: 'TXN-001', amount: 150000, timestamp: '2026-03-16 09:30:00' },
      { id: 'TXN-002', amount: 120000, timestamp: '2026-03-16 14:15:00' },
      { id: 'TXN-003', amount: 90000, timestamp: '2026-03-17 11:45:00' },
      { id: 'TXN-004', amount: 90000, timestamp: '2026-03-17 16:20:00' }
    ]
  };

  return (
    <motion.div 
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 1.0, duration: 0.4 }}
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
      
      <div className="p-6 space-y-5">
        {/* Header Info */}
        <div className="grid grid-cols-2 gap-4 mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">SAR ID:</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{mockSAR.id}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Timestamp:</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{mockSAR.timestamp}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Status:</p>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              mockSAR.status === 'Draft' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
              mockSAR.status === 'Filed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
            }`}
            >
              {mockSAR.status}
            </span>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Filing Deadline:</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{mockSAR.filingDeadline}</p>
          </div>
        </div>
        
        {/* Subject and Summary */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Subject:
          </h3>
          <p className="text-gray-700 dark:text-gray-300">
            {mockSAR.subject}
          </p>
          
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-4">
            Summary:
          </h3>
          <p className="text-gray-700 dark:text-gray-300">
            {mockSAR.summary}
          </p>
        </div>
        
        {/* Entities Section */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Involved Entities:
          </h3>
          <div className="space-y-2">
            {mockSAR.entities.map((entity, index) => (
              <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {entity.name}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Role: {entity.role} • Jurisdiction: {entity.jurisdiction}
                </p>
              </div>
            ))}
          </div>
        </div>
        
        {/* Transactions Section */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Suspicious Transactions:
          </h3>
          <div className="space-y-2">
            {mockSAR.transactions.map((txn, index) => (
              <div key={index} className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Transaction {txn.id}
                  </p>
                </div>
                <div className="text-right space-x-3">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    ${txn.amount.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {txn.timestamp}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
          <button
            onClick={() => alert('Exporting SAR as PDF...')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors"
          >
            Export PDF
          </button>
          <button
            onClick={() => alert('Submitting SAR to FinCEN...')}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors"
          >
            Submit SAR
          </button>
        </div>
      </div>
    </motion.div>
  );
};