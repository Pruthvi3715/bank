import React from 'react';
import { motion } from 'framer-motion';

interface StatsCardProps {
  title: string;
  value: string;
  trend: string;
  icon: string;
  color: 'red' | 'orange' | 'blue' | 'green';
}

export const StatsCard: React.FC<StatsCardProps> = ({ title, value, trend, icon, color }) => {
  const getColorClasses = () => {
    switch (color) {
      case 'red': return 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200';
      case 'orange': return 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200';
      case 'blue': return 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200';
      case 'green': return 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200';
      default: return 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200';
    }
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.1, duration: 0.4 }}
      className={`${getColorClasses()} rounded-xl shadow-md border border-gray-200 dark:border-gray-700 p-6`}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-2xl">{icon}</span>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          trend.startsWith('↑') ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
          trend.startsWith('↓') ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
          'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
        }`}
        >
          {trend}
        </span>
      </div>
      <h3 className="text-lg font-semibold mb-1">{title}</h3>
      <p className="text-3xl font-bold">{value}</p>
    </motion.div>
  );
};