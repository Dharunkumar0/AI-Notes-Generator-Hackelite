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
  // Transcribe audio file
  transcribeAudioFile: async (file) => {
    try {
      // Validate file size
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        throw new Error('File size exceeds 10MB limit');
      }

      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/voice/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (!response.data || !response.data.transcription) {
        throw new Error(response.data?.error || 'Failed to transcribe audio file');
      }
      return response.data;
    } catch (error) {
      console.error('Transcribe audio file error:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Please check if the file format is supported and not corrupted');
      }
      throw error;
    }
  },

  // Transcribe from microphone
  transcribeMicrophone: async (duration = 10) => {
    try {
      const response = await api.post('/api/voice/microphone', { duration });
      if (!response.data || !response.data.transcription) {
      throw new Error('Transcription not received');
    }
    return response.data;

    } catch (error) {
      console.error('Transcribe microphone error:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      } else if (error.response?.status === 500) {
        throw new Error('Server error: Please check if your microphone is properly connected and accessible');
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
};
