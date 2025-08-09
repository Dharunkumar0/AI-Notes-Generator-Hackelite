import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

const handleError = error => {
  console.error('API Error:', error);
  throw new Error(error.response?.data?.detail || 'An error occurred');
};

const voiceService = {
  async getSupportedFormats() {
    try {
      const response = await api.get('/api/voice/formats');
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  async uploadAudio(formData, onProgress) {
    try {
      const config = {
        headers: { 'Content-Type': 'multipart/form-data' }
      };
      
      if (onProgress) {
        config.onUploadProgress = e => onProgress((e.loaded / e.total) * 100);
      }

      const response = await api.post('/api/voice/upload', formData, config);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  async processRecording(data) {
    try {
      const response = await api.post('/api/voice/record', data);
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  async processVoiceToNotes(speechText) {
    try {
      const response = await api.post('/api/voice/process-to-notes', { speech_text: speechText });
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  async transcribeAudioFile(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/api/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  },

  async analyzeEmotion(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/api/voice/emotion', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      return handleError(error);
    }
  }
};

export { voiceService };
