import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create axios instance
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

// Auth service implementation
export const authService = {
  // Login with Firebase ID token
  login: async (idToken) => {
    try {
      const response = await api.post('/api/auth/login', {
        id_token: idToken,
      });
      
      const { access_token, ...data } = response.data;
      localStorage.setItem('authToken', access_token);
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  // Get current user info
  getCurrentUser: async () => {
    try {
      const response = await api.get('/api/auth/me');
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },

  // Update user profile
  updateProfile: async (userId, data) => {
    try {
      const response = await api.put(`/api/auth/profile`, data);
      return response.data;
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  },

  // Delete user account
  deleteAccount: async () => {
    try {
      await api.delete('/api/auth/account');
      localStorage.removeItem('authToken');
    } catch (error) {
      console.error('Delete account error:', error);
      throw error;
    }
  },
}; 