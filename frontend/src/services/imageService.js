import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle response errors
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

export const imageService = {
  // Process uploaded image
  async processImage(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/image/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error) {
      console.error('Error processing image:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to process image. Please try again later.';
      throw new Error(errorMessage);
    }
  },

  // Get image processing history
  async getImageHistory(limit = 20, offset = 0) {
    try {
      const response = await api.get(`/api/image/history?limit=${limit}&offset=${offset}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching image history:', error);
      throw error;
    }
  },

  // Get specific image processing detail
  async getImageDetail(imageId) {
    try {
      const response = await api.get(`/api/image/history/${imageId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching image detail:', error);
      throw error;
    }
  },

  // Delete specific image processing record
  async deleteImageRecord(imageId) {
    try {
      const response = await api.delete(`/api/image/history/${imageId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting image record:', error);
      throw error;
    }
  },

  // Clear all image processing history
  async clearImageHistory() {
    try {
      const response = await api.delete('/api/image/history');
      return response.data;
    } catch (error) {
      console.error('Error clearing image history:', error);
      throw error;
    }
  },
};
