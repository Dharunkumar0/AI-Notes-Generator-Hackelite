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

// Notes service implementation
export const notesService = {
  // Generate comprehensive notes
  generateNotes: async (text) => {
    try {
      const response = await api.post('/api/notes/generate', {
        text
      });
      return response.data;
    } catch (error) {
      console.error('Generate notes error:', error);
      throw error;
    }
  },

  // Summarize text
  summarize: async (text, maxLength = 500) => {
    try {
      const response = await api.post('/api/notes/summarize', {
        text,
        max_length: maxLength
      });
      return response.data;
    } catch (error) {
      console.error('Summarize error:', error);
      throw error;
    }
  },

  // Extract key points
  extractKeyPoints: async (text) => {
    try {
      const response = await api.post('/api/notes/extract', {
        text
      });
      return response.data;
    } catch (error) {
      console.error('Extract key points error:', error);
      throw error;
    }
  },

  // Get notes statistics
  getStats: async () => {
    try {
      const response = await api.get('/api/notes/stats');
      return response.data;
    } catch (error) {
      console.error('Get notes stats error:', error);
      throw error;
    }
  },
}; 