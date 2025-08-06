import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  FileText, 
  Mic, 
  File, 
  HelpCircle, 
  Brain, 
  Lightbulb, 
  TrendingUp, 
  Clock,
  Activity,
  Zap
} from 'lucide-react';
import { historyService } from '../services/historyService';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const features = [
    {
      name: 'Notes Summarizer',
      description: 'Summarize long text notes with AI',
      icon: FileText,
      href: '/notes',
      color: 'bg-blue-500',
      gradient: 'from-blue-500 to-blue-600'
    },
    {
      name: 'Voice to Text',
      description: 'Convert voice recordings to text',
      icon: Mic,
      href: '/voice',
      color: 'bg-green-500',
      gradient: 'from-green-500 to-green-600'
    },
    {
      name: 'PDF Processor',
      description: 'Extract and process text from PDFs',
      icon: File,
      href: '/pdf',
      color: 'bg-purple-500',
      gradient: 'from-purple-500 to-purple-600'
    },
    {
      name: 'Quiz Generator',
      description: 'Generate quizzes from study materials',
      icon: HelpCircle,
      href: '/quiz',
      color: 'bg-orange-500',
      gradient: 'from-orange-500 to-orange-600'
    },
    {
      name: 'Mind Map Creator',
      description: 'Create visual mind maps for topics',
      icon: Brain,
      href: '/mindmap',
      color: 'bg-pink-500',
      gradient: 'from-pink-500 to-pink-600'
    },
    {
      name: 'ELI5 Simplifier',
      description: 'Simplify complex topics',
      icon: Lightbulb,
      href: '/eli5',
      color: 'bg-yellow-500',
      gradient: 'from-yellow-500 to-yellow-600'
    }
  ];

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await historyService.getSummary(30);
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold">
          Welcome back, {user?.displayName || user?.email}!
        </h1>
        <p className="mt-2 text-primary-100">
          Ready to transform your study materials with AI? Choose a tool below to get started.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Activities</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.totalItems || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.processingStats?.success_rate || 0}%
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Clock className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg. Processing</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.processingStats?.average_processing_time || 0}s
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Zap className="h-8 w-8 text-error-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Time Saved</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.processingStats?.total_processing_time ? Math.round(stats.processingStats.total_processing_time / 60) : 0}m
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Grid */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">AI-Powered Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link
                key={feature.name}
                to={feature.href}
                className="card hover:shadow-lg transition-all duration-200 hover:-translate-y-1 group"
              >
                <div className="flex items-center mb-4">
                  <div className={`p-3 rounded-lg ${feature.color} text-white`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="ml-3 text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400">
                    {feature.name}
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-4">{feature.description}</p>
                <div className="flex items-center text-primary-600 dark:text-primary-400 font-medium">
                  Get Started
                  <svg className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Recent Activity</h2>
        {loading ? (
          <p className="text-gray-500 dark:text-gray-400">Loading activity...</p>
        ) : stats?.featureBreakdown && Object.keys(stats.featureBreakdown).length > 0 ? (
          <div className="space-y-4">
            {Object.entries(stats.featureBreakdown).slice(0, 5).map(([feature, count]) => (
              <div key={feature} className="flex items-center justify-between py-2">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mr-3"></div>
                  <span className="text-gray-700 dark:text-gray-300 capitalize">{feature.replace('_', ' ')}</span>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">{count} activities</span>
              </div>
            ))}
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <Link to="/history" className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium">
                View all activity →
              </Link>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No activity recorded yet. Try using some features to get started!</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 