import React from 'react';
import { motion } from 'framer-motion';

interface FilterBarProps {
  onFilterChange: (filters: { searchTerm: string; riskLevel: string; status: string }) => void;
  placeholder?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({ onFilterChange, placeholder = 'Search...' }) => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [riskLevel, setRiskLevel] = React.useState('all');
  const [status, setStatus] = React.useState('all');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({ searchTerm, riskLevel, status });
  };

  const handleReset = () => {
    setSearchTerm('');
    setRiskLevel('all');
    setStatus('all');
    onFilterChange({ searchTerm: '', riskLevel: 'all', status: 'all' });
  };

  return (
    <motion.div 
      initial={{ y: 10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.8, duration: 0.3 }}
      className="space-y-4"
    >
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row sm:items-center sm:gap-4">
        <div className="flex-1 min-w-0">
          <label className="sr-only">Search alerts</label>
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={placeholder}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <label className="sr-only">Risk level filter</label>
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Risk Levels</option>
            <option value="high">High (8+)</option>
            <option value="medium">Medium (6-7.9)</option>
            <option value="low">Low (under 6)</option>
          </select>
        </div>
        
        <div className="flex-1 min-w-0">
          <label className="sr-only">Status filter</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">All Statuses</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="reviewed">Reviewed</option>
            <option value="false_positive">False Positive</option>
            <option value="confirmed_fraud">Confirmed Fraud</option>
          </select>
        </div>
        
        <button
          type="submit"
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors disabled:opacity-50"
        >
          Apply Filters
        </button>
      </form>
      
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center">
        <div className="text-sm text-gray-500 dark:text-gray-400">
          Showing filters: {searchTerm ? `Search: "${searchTerm}"` : 'No search'} | 
          Risk: {riskLevel === 'all' ? 'All' : riskLevel} | 
          Status: {status === 'all' ? 'All' : status}
        </div>
        <button
          type="button"
          onClick={handleReset}
          className="text-sm text-purple-600 hover:underline dark:text-purple-400"
        >
          Reset Filters
        </button>
      </div>
    </motion.div>
  );
};