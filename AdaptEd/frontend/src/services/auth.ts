import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Создаем экземпляр axios с таймаутом
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authService = {
  async login(email: string, password: string) {
    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password,
      });
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('role', response.data.role);
        if (response.data.full_name) {
          localStorage.setItem('full_name', response.data.full_name);
        }
      }
      return response.data;
    } catch (error: any) {
      throw error;
    }
  },

  async register(userData: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    class_id?: string;
    phone?: string;
  }) {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    } catch (error: any) {
      throw error;
    }
  },

  async getCurrentUser() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
      const response = await apiClient.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.data?.full_name) {
        localStorage.setItem('full_name', response.data.full_name);
      }
      return response.data;
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('user_id');
      localStorage.removeItem('role');
      localStorage.removeItem('full_name');
      return null;
    }
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('role');
    localStorage.removeItem('full_name');
  },

  isAuthenticated() {
    return !!localStorage.getItem('token');
  },
};

