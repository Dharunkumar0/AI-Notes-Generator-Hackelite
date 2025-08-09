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

export const quizService = {
  // Generate quiz from text
  generateQuiz: async (text, numQuestions = 5, useBlooms = false, taxonomyLevels = []) => {
    try {
      const response = await api.post('/api/quiz/generate', {
        text,
        num_questions: numQuestions,
        use_blooms_taxonomy: useBlooms,
        taxonomy_levels: useBlooms ? taxonomyLevels : undefined
      });
      return response.data;
    } catch (error) {
      console.error('Generate quiz error:', error);
      throw error;
    }
  },

  // Get quiz statistics
  getQuizStats: async () => {
    try {
      const response = await api.get('/api/quiz/stats');
      return response.data;
    } catch (error) {
      console.error('Get quiz stats error:', error);
      throw error;
    }
  },
};
