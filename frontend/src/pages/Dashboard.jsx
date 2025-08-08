import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  FileText, 
  Mic, 
  File, 
  Image as ImageIcon,
  HelpCircle, 
  Brain, 
  Lightbulb, 
  TrendingUp, 
  Clock,
  Activity,
  Sparkles,
  ArrowRight,
  Star,
  Users,
  Target,
  BarChart3
} from 'lucide-react';
import { historyService } from '../services/historyService';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const features = [
    {
      name: 'Notes Summarizer',
      description: 'Transform long text into concise summaries with AI',
      icon: FileText,
      href: '/notes',
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-200 dark:border-blue-800',
      iconColor: 'text-blue-600 dark:text-blue-400'
    },
    
    {
      name: 'Voice to Text',
      description: 'Convert speech to text with high accuracy',
      icon: Mic,
      href: '/voice',
      color: 'from-emerald-500 to-emerald-600',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-200 dark:border-emerald-800',
      iconColor: 'text-emerald-600 dark:text-emerald-400'
    },

    {
      name: 'PDF Processor',
      description: 'Extract and analyze content from PDF documents',
      icon: File,
      href: '/pdf',
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-200 dark:border-purple-800',
      iconColor: 'text-purple-600 dark:text-purple-400'
    },

    {
      name: 'Image OCR',
      description: 'Extract text from images and create summaries',
      icon: ImageIcon,
      href: '/image',
      color: 'from-indigo-500 to-indigo-600',
      bgColor: 'bg-indigo-500/10',
      borderColor: 'border-indigo-200 dark:border-indigo-800',
      iconColor: 'text-indigo-600 dark:text-indigo-400'
    },

    {
      name: 'Quiz Generator',
      description: 'Create interactive quizzes from study materials',
      icon: HelpCircle,
      href: '/quiz',
      color: 'from-orange-500 to-orange-600',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-200 dark:border-orange-800',
      iconColor: 'text-orange-600 dark:text-orange-400'
    },

    {
      name: 'Mind Map Creator',
      description: 'Visualize concepts with AI-powered mind maps',
      icon: Brain,
      href: '/mindmap',
      color: 'from-pink-500 to-pink-600',
      bgColor: 'bg-pink-500/10',
      borderColor: 'border-pink-200 dark:border-pink-800',
      iconColor: 'text-pink-600 dark:text-pink-400'
    },

    {
      name: 'ELI5 Simplifier',
      description: 'Simplify complex topics for easy understanding',
      icon: Lightbulb,
      href: '/eli5',
      color: 'from-amber-500 to-amber-600',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-200 dark:border-amber-800',
      iconColor: 'text-amber-600 dark:text-amber-400'
    }
  ];

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await historyService.getSummary(30);
        console.log('Dashboard stats:', data);
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
        setError(error.message);
        setStats({
          total_items: 0,
          processing_stats: {
            success_rate: 0,
            average_processing_time: 0,
            total_processing_time: 0
          },
          feature_breakdown: {}
        });
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchStats();
    } else {
      setLoading(false);
    }
  }, [user]);

  // Calculate statistics with fallbacks
  const totalActivities = stats?.total_items || 0;
  const successRate = stats?.processing_stats?.success_rate || 0;
  const avgProcessing = stats?.processing_stats?.average_processing_time || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-primary-600 via-primary-700 to-primary-800 p-8 md:p-12 mb-8">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="relative z-10">
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex items-center justify-center w-12 h-12 bg-white/20 rounded-xl backdrop-blur-sm">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl md:text-4xl font-bold text-white">
                  Welcome back, {user?.display_name || user?.email || 'User'}! 👋
                </h1>
                <p className="text-primary-100 text-lg mt-2">
                  Ready to supercharge your learning with AI-powered tools?
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-4 mt-6">
              <div className="flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                <Star className="h-4 w-4 text-yellow-300" />
                <span className="text-white font-medium">Premium AI Tools</span>
              </div>
              <div className="flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-lg px-4 py-2">
                <Target className="h-4 w-4 text-green-300" />
                <span className="text-white font-medium">Smart Learning</span>
              </div>
            </div>
          </div>
          <div className="absolute top-0 right-0 -mt-4 -mr-4 w-72 h-72 bg-white/10 rounded-full blur-3xl"></div>
        </div>

        {/* Stats Cards */}
        {error && (
          <div className="mb-8 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-4">
                <p className="text-sm text-red-800 dark:text-red-200">Error loading statistics: {error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:-translate-y-1">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-blue-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl">
                  <Activity className="h-6 w-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {loading ? (
                      <div className="animate-pulse bg-gray-300 dark:bg-gray-600 h-8 w-16 rounded"></div>
                    ) : totalActivities}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Activities</div>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Total Activities</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Your learning journey so far</p>
            </div>
          </div>

          <div className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:-translate-y-1">
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-emerald-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {loading ? (
                      <div className="animate-pulse bg-gray-300 dark:bg-gray-600 h-8 w-16 rounded"></div>
                    ) : `${successRate}%`}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Success</div>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Success Rate</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">AI processing accuracy</p>
            </div>
          </div>

          <div className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:-translate-y-1">
            <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-amber-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-gradient-to-r from-amber-500 to-amber-600 rounded-xl">
                  <Clock className="h-6 w-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {loading ? (
                      <div className="animate-pulse bg-gray-300 dark:bg-gray-600 h-8 w-16 rounded"></div>
                    ) : `${avgProcessing.toFixed(1)}s`}
                  </div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">Average</div>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Processing Time</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">AI response speed</p>
            </div>
          </div>


        </div>

        {/* Feature Grid */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">AI-Powered Tools</h2>
              <p className="text-gray-600 dark:text-gray-400">Choose your learning companion</p>
            </div>
            <div className="hidden md:flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <BarChart3 className="h-4 w-4" />
              <span>7 powerful tools</span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Link
                  key={feature.name}
                  to={feature.href}
                  className="group relative bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:-translate-y-2 hover:scale-105"
                >
                  <div className={`absolute inset-0 bg-gradient-to-r ${feature.color} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-300`}></div>
                  <div className="relative">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 rounded-xl ${feature.bgColor} border ${feature.borderColor}`}>
                        <Icon className={`h-6 w-6 ${feature.iconColor}`} />
                      </div>
                      <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors duration-300 group-hover:translate-x-1" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors duration-300">
                      {feature.name}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">{feature.description}</p>
                    <div className="flex items-center text-primary-600 dark:text-primary-400 font-semibold text-sm">
                      Get Started
                      <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform duration-300" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        { <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Recent Activity</h2>
              <p className="text-gray-600 dark:text-gray-400">Your learning journey</p>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <Users className="h-4 w-4" />
              <span>Learning Analytics</span>
            </div>
          </div>
          
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-600 dark:text-gray-400">Loading activity...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="h-8 w-8 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <p className="text-gray-600 dark:text-gray-400 mb-2">Unable to load activity data</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Try using some features to generate activity data</p>
            </div>
          ) : stats?.feature_breakdown && Object.keys(stats.feature_breakdown).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(stats.feature_breakdown).slice(0, 5).map(([feature, count], index) => (
                <div key={feature} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-4 ${
                      index === 0 ? 'bg-blue-500' :
                      index === 1 ? 'bg-emerald-500' :
                      index === 2 ? 'bg-amber-500' :
                      index === 3 ? 'bg-purple-500' :
                      'bg-pink-500'
                    }`}></div>
                    <span className="text-gray-700 dark:text-gray-300 font-medium capitalize">
                      {feature.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500 dark:text-gray-400">{count} activities</span>
                    <div className="w-2 h-2 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                  </div>
                </div>
              ))}
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <Link 
                  to="/history" 
                  className="inline-flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-semibold transition-colors duration-200"
                >
                  View all activity
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                <Lightbulb className="h-8 w-8 text-gray-400 dark:text-gray-500" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No activity recorded yet</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">Start your learning journey by trying our AI tools!</p>
              <Link 
                to="/eli5" 
                className="inline-flex items-center bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                <Lightbulb className="h-4 w-4 mr-2" />
                Try ELI5 First
              </Link>
            </div>
          )}
        </div> }
      </div>
    </div>
  );
};

export default Dashboard; 