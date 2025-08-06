import React from 'react';
import { History as HistoryIcon, Clock, Activity, Trash2 } from 'lucide-react';

const HistoryPage = () => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Activity History</h1>
          <p className="text-gray-600 dark:text-gray-400">View and manage your AI processing history</p>
        </div>
        <div className="flex items-center space-x-2">
          <HistoryIcon className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="card">
        <div className="text-center py-12">
          <HistoryIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Your Activity History</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Track all your AI-powered activities and processing history
          </p>
          <div className="flex justify-center space-x-4">
            <button className="btn-primary flex items-center">
              <Activity className="h-4 w-4 mr-2" />
              View History
            </button>
            <button className="btn-secondary flex items-center">
              <Clock className="h-4 w-4 mr-2" />
              Filter by Date
            </button>
            <button className="btn-error flex items-center">
              <Trash2 className="h-4 w-4 mr-2" />
              Clear History
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;