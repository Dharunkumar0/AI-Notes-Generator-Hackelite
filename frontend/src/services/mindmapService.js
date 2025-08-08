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

export const mindmapService = {
  // Create mind map
  createMindMap: async (topic, subtopics = null) => {
    try {
      const response = await api.post('/api/mindmap/create', {
        topic,
        subtopics
      });
      return response.data;
    } catch (error) {
      console.error('Create mind map error:', error);
      throw error;
    }
  },

  // Get mind map statistics
  getMindMapStats: async () => {
    try {
      const response = await api.get('/api/mindmap/stats');
      return response.data;
    } catch (error) {
      console.error('Get mind map stats error:', error);
      throw error;
    }
  },
};
