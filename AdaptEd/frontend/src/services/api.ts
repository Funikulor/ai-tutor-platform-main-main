import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 секунд таймаут (для Ollama может потребоваться больше времени)
});

// Добавляем interceptor для автоматической подстановки токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обработка ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user_id');
      localStorage.removeItem('role');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;

