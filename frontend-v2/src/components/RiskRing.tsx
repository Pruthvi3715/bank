import React from 'react';
import { motion } from 'framer-motion';

interface RiskRingProps {
  score: number;
  label: string;
}

export const RiskRing: React.FC<RiskRingProps> = ({ score, label }) => {
  const percentage = Math.min(score * 10, 100);
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (percentage / 100) * circumference;

  const getColor = () => {
    if (score >= 8) return '#ef4444';
    if (score >= 6) return '#f97316';
    return '#eab308';
  };

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: 0.3, duration: 0.4 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 p-6 flex flex-col items-center justify-center"
    >
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            strokeWidth="8"
            fill="none"
            className="text-gray-200 dark:text-gray-700"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke={getColor()}
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold" style={{ color: getColor() }}>
            {score}
          </span>
        </div>
      </div>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{label}</p>
    </motion.div>
  );
};