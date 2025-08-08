import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// History service implementation
export const historyService = {
  // Get user history with optional filtering
  getHistory: async (params = {}) => {
    try {
      const response = await api.get('/api/history/', { params });
      return response.data;
    } catch (error) {
      console.error('Get history error:', error);
      throw error;
    }
  },

  // Get history summary
  getSummary: async (days = 30) => {
    try {
      const response = await api.get('/api/history/summary', {
        params: { days }
      });
      return response.data;
    } catch (error) {
      console.error('Get history summary error:', error);
      throw error;
    }
  },

  // Get history for specific feature
  getFeatureHistory: async (featureType, limit = 20) => {
    try {
      const response = await api.get(`/api/history/feature/${featureType}`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Get feature history error:', error);
      throw error;
    }
  },

  // Delete specific history item
  deleteHistoryItem: async (historyId) => {
    try {
      await api.delete(`/api/history/${historyId}`);
    } catch (error) {
      console.error('Delete history item error:', error);
      throw error;
    }
  },

  // Clear history (all or by feature type)
  clearHistory: async (featureType) => {
    try {
      const response = await api.delete('/api/history/', {
        params: featureType ? { feature_type: featureType } : {}
      });
      return response.data;
    } catch (error) {
      console.error('Clear history error:', error);
      throw error;
    }
  },
}; 