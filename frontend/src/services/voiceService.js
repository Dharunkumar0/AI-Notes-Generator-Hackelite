import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
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

// Handle API errors consistently
const handleError = (error) => {
  console.error('API Error:', error);

  let errorMessage = 'An unexpected error occurred';

  if (error.response) {
    const data = error.response.data;
    errorMessage = data?.detail || data?.error || data?.message || error.response.statusText;
  } else if (error.request) {
    errorMessage = 'No response from server. Please check your connection.';
  } else {
    errorMessage = error.message;
  }

  throw new Error(errorMessage);
};

const voiceService = {
  // Get available microphones
  async getAvailableMicrophones() {
    try {
      const response = await api.get('/api/voice/microphones');
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // Start recording from selected microphone
  async startRecording(deviceIndex = null) {
    try {
      const formData = new FormData();
      if (deviceIndex !== null) {
        formData.append('device_index', deviceIndex);
      }
      const response = await api.post('/api/voice/record', formData);
      return response.data;
    } catch (error) {
      handleError(error);
    }
  },

  // Get supported audio formats
  async getSupportedFormats() {
    try {
      const response = await api.get('/api/voice/formats');
      return response.data;
    } catch (error) {
      console.warn('Could not fetch supported formats, using defaults');
      return {
        success: true,
        data: {
          supported_formats: ['wav', 'mp3', 'm4a', 'ogg', 'flac', 'webm'],
          max_file_size: 10 * 1024 * 1024,
          max_file_size_mb: '10MB',
          max_duration: 600
        }
      };
    }
  },

  // Transcribe uploaded audio file
  async transcribeAudioFile(file) {
    try {
      if (!file) throw new Error('No file provided');
      if (file.size > 10 * 1024 * 1024) throw new Error('File size exceeds 10MB limit. Please select a smaller file.');

      const fileName = file.name.toLowerCase();
      const fileExtension = fileName.split('.').pop();
      const supportedFormats = ['wav', 'mp3', 'm4a', 'ogg', 'flac', 'webm'];
      if (!supportedFormats.includes(fileExtension)) {
        throw new Error(`Unsupported file format: ${fileExtension}. Supported formats: ${supportedFormats.join(', ')}`);
      }

      const token = localStorage.getItem('authToken');
      if (!token) throw new Error('You must be logged in to use this feature');

      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/voice/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        timeout: 120000
      });

      if (response.data && response.data.success) {
        return response.data;
      } else if (response.data && response.data.success === false) {
        throw new Error(response.data.error || 'Transcription failed');
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      return handleError(error);
    }
  },

  // Generate summary of transcription
  async summarizeTranscription(transcription, maxLength = 200) {
    try {
      if (!transcription || !transcription.trim()) throw new Error('No transcription text provided');
      const token = localStorage.getItem('authToken');
      if (!token) throw new Error('You must be logged in to use this feature');

      const response = await api.post('/api/voice/summarize', {
        transcription: transcription.trim(),
        max_length: maxLength
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        timeout: 30000
      });

      if (response.data && response.data.success) {
        return response.data.data;
      } else if (response.data && response.data.success === false) {
        throw new Error(response.data.error || 'Summary generation failed');
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      return handleError(error);
    }
  },

  // Get user's voice processing statistics
  async getStats() {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) throw new Error('You must be logged in to view statistics');

      const response = await api.get('/api/voice/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        timeout: 10000
      });

      if (response.data && response.data.success) {
        return response.data.data;
      } else {
        throw new Error('Failed to fetch statistics');
      }
    } catch (error) {
      return {
        total_processed: 0,
        total_words: 0,
        average_processing_time: 0,
        format_breakdown: {},
        last_processed: null
      };
    }
  },

  // Record from microphone and transcribe
  async recordAndTranscribe(duration = 10) {
    try {
      const token = localStorage.getItem('authToken');
      if (!token) throw new Error('You must be logged in to use this feature');
      if (duration < 1 || duration > 60) throw new Error('Duration must be between 1 and 60 seconds');

      const formData = new FormData();
      formData.append('duration', duration.toString());

      const response = await api.post('/api/voice/microphone', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        timeout: (duration + 30) * 1000
      });

      if (response.data && response.data.success) {
        return response.data;
      } else if (response.data && response.data.success === false) {
        throw new Error(response.data.error || 'Microphone transcription failed');
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      return handleError(error);
    }
  }
};

export { voiceService };