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

export const textToSpeechService = {
  generateSpeech: async (text, language = 'en') => {
    try {
      const response = await api.post('/api/voice/text-to-speech', {
        text,
        language
      });
      return response.data;
    } catch (error) {
      console.error('Text to speech error:', error);
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Unable to generate speech');
      }
      throw error;
    }
  },
};
