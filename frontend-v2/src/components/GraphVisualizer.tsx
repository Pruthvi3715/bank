import React from 'react';
import { motion } from 'framer-motion';

interface GraphVisualizerProps {
  title: string;
  description: string;
}

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({ title, description }) => {
  return (
    <motion.div 
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.6, duration: 0.4 }}
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
      
      <div className="p-6">
        {/* Mock SVG visualization - in real implementation this would use react-force-graph-2d */}
        <div className="h-96 w-full relative bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-700">
          {/* This is a placeholder for the actual graph visualization */}
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 dark:text-gray-500">
            <div className="text-center">
              <svg className="w-16 h-16 mb-3 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 12c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-8c0 1.1-.9 2-2 2s-2 .9-2-2 .9-2 2-2 2-.9 2 2z"></path>
              </svg>
              <p className="font-medium">Network Graph Visualization</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Interactive force-directed graph showing entity relationships
              </p>
            </div>
          </div>
        </div>
        
        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-2">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>High Risk Entities</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Low Risk Entities</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Medium Risk Entities</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};