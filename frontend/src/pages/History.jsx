import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, Clock, Activity, Trash2, Filter, ChevronDown } from 'lucide-react';
import { historyService } from '../services/historyService';
import { format } from 'date-fns';
import { useAuth } from '../contexts/AuthContext';

const HistoryPage = () => {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null); // <-- Add error state
  const [filterType, setFilterType] = useState('');
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (user) {
      loadHistory();
      loadSummary();
    }
  }, [filterType, days, user]);

  const loadHistory = async () => {
    try {
      setIsLoading(true);
      setError(null); // Reset error
      const data = await historyService.getHistory({ feature_type: filterType });
      setHistory(data);
    } catch (error) {
      setError(error?.response?.data?.detail || error.message || 'Unknown error');
      setHistory([]);
      console.error('Error loading history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await historyService.getSummary(days);
      setSummary(data);
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear your history?')) {
      try {
        await historyService.clearHistory(filterType);
        await loadHistory();
        await loadSummary();
      } catch (error) {
        console.error('Error clearing history:', error);
      }
    }
  };

  const handleDeleteItem = async (id) => {
    try {
      await historyService.deleteHistoryItem(id);
      await loadHistory();
      await loadSummary();
    } catch (error) {
      console.error('Error deleting history item:', error);
    }
  };

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

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card p-4">
            <h3 className="text-lg font-semibold mb-2">Total Activities</h3>
            <p className="text-3xl font-bold text-primary-600">{summary.total_items}</p>
          </div>
          <div className="card p-4">
            <h3 className="text-lg font-semibold mb-2">Success Rate</h3>
            <p className="text-3xl font-bold text-primary-600">
              {summary.processing_stats.success_rate}%
            </p>
          </div>
          <div className="card p-4">
            <h3 className="text-lg font-semibold mb-2">Average Time</h3>
            <p className="text-3xl font-bold text-primary-600">
              {summary.processing_stats.average_processing_time.toFixed(2)}s
            </p>
          </div>
        </div>
      )}

      <div className="card">
        <div className="p-4 border-b dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <select
                className="form-select"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="">All Activities</option>
                <option value="voice">Voice</option>
                <option value="notes">Notes</option>
                <option value="quiz">Quiz</option>
                <option value="mindmap">Mind Map</option>
                <option value="pdf">PDF</option>
                <option value="eli5">ELI5</option>
              </select>
              <select
                className="form-select"
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value))}
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
            </div>
            <button
              onClick={handleClearHistory}
              className="btn-error flex items-center"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear History
            </button>
          </div>
        </div>

        <div className="p-4">
          {!user ? (
            <div className="text-center py-12 text-yellow-600">
              <h2 className="text-xl font-semibold mb-2">You are not logged in</h2>
              <p>Please log in to view your history.</p>
            </div>
          ) : isLoading ? (
            <div className="text-center py-8">
              <div className="spinner"></div>
              <p className="mt-2 text-gray-600">Loading history...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">
              <h2 className="text-xl font-semibold mb-2">Error loading history</h2>
              <p>{error}</p>
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12">
              <HistoryIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                No History Found
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Start using the app's features (ELI5, PDF, Quiz, etc.) to see your activity history.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg shadow"
                >
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      {item.feature_type}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {format(new Date(item.created_at), 'PPpp')}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {item.processing_time ? `${item.processing_time.toFixed(2)}s` : 'N/A'}
                    </span>
                    <button
                      onClick={() => handleDeleteItem(item.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;