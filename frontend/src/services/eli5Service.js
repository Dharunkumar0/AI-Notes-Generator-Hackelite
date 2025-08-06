import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with auth token interceptor
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

export const eli5Service = {
  // Simplify topic using ELI5 approach
  simplifyTopic: async (topic, complexityLevel = 'basic') => {
    try {
      const response = await api.post('/api/eli5/simplify', {
        topic,
        complexity_level: complexityLevel
      });
      return response.data;
    } catch (error) {
      console.error('Simplify topic error:', error);
      throw error;
    }
  },

  // Get available complexity levels
  getComplexityLevels: async () => {
    try {
      const response = await api.get('/api/eli5/complexity-levels');
      return response.data;
    } catch (error) {
      console.error('Get complexity levels error:', error);
      throw error;
    }
  },

  // Get ELI5 statistics
  getELI5Stats: async () => {
    try {
      const response = await api.get('/api/eli5/stats');
      return response.data;
    } catch (error) {
      console.error('Get ELI5 stats error:', error);
      throw error;
    }
  },
};
