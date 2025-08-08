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

export const voiceService = {
  // Process voice text to notes
  processVoiceToNotes: async (speechText) => {
    try {
      const response = await api.post('/api/voice/process-to-notes', {
        speech_text: speechText
      });
      return response.data;
    } catch (error) {
      console.error('Process voice to notes error:', error);
      throw error;
    }
  },

  // Transcribe audio file
  transcribeAudioFile: async (file) => {
    try {
      // Validate file size
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        throw new Error('File size exceeds 10MB limit');
      }

      // Create form data
      const formData = new FormData();
      formData.append('file', file); // Using 'file' to match backend expectation

      const response = await api.post('/api/voice/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // The response is already the data object since FastAPI returns just the response_model
      return response.data;
    } catch (error) {
      console.error('Transcribe audio file error:', error);
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.response?.status === 422) {
        throw new Error('Invalid request format. Please ensure you are sending a valid audio file.');
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Please check if the file format is supported and not corrupted');
      }
      throw error;
    }
  },

  // Get supported formats
  getSupportedFormats: async () => {
    try {
      const response = await api.get('/api/voice/formats');
      return response.data;
    } catch (error) {
      console.error('Get supported formats error:', error);
      throw error;
    }
  },

  // Get voice stats
  getVoiceStats: async () => {
    try {
      const response = await api.get('/api/voice/stats');
      return response.data;
    } catch (error) {
      console.error('Get voice stats error:', error);
      throw error;
    }
  },

  // Analyze voice emotion
  analyzeEmotion: async (file) => {
    try {
      const response = await api.post('/api/voice/analyze-emotion', file, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Voice emotion analysis error:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Unable to analyze voice emotion');
      }
      throw error;
    }
  },
};
