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

export const pdfService = {
  // Extract text from PDF
  extractText: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/pdf/extract', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Extract PDF text error:', error);
      throw error;
    }
  },

  // Get PDF information
  getPDFInfo: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/pdf/info', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Get PDF info error:', error);
      throw error;
    }
  },

  // Get supported formats
  getSupportedFormats: async () => {
    try {
      const response = await api.get('/api/pdf/formats');
      return response.data;
    } catch (error) {
      console.error('Get supported formats error:', error);
      throw error;
    }
  },

  // Get PDF processing stats
  getPDFStats: async () => {
    try {
      const response = await api.get('/api/pdf/stats');
      return response.data;
    } catch (error) {
      console.error('Get PDF stats error:', error);
      throw error;
    }
  },

  // Summarize text
  summarizeText: async (text, maxLength = 500) => {
    try {
      const response = await api.post('/api/notes/summarize', {
        text,
        max_length: maxLength
      });
      return response.data;
    } catch (error) {
      console.error('Summarize text error:', error);
      throw error;
    }
  },
};
