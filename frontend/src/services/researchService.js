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

// Research service implementation
export const researchService = {
  // Search for research papers
  searchPapers: async (params) => {
    try {
      const response = await api.post('/api/research/search', params);
      return response.data;
    } catch (error) {
      console.error('Research search error:', error);
      throw error;
    }
  },

  // Get research history
  getHistory: async () => {
    try {
      const response = await api.get('/api/research/history');
      return response.data;
    } catch (error) {
      console.error('Research history error:', error);
      throw error;
    }
  }
};
