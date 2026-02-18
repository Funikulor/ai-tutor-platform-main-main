import axios from 'axios';

// Для production используем VITE_API_URL из переменных окружения
// Для разработки - localhost
export const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? 'https://adapted-backend.onrender.com' : 'http://localhost:8000');
export const clearAuthStorage = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user_id');
  localStorage.removeItem('role');
  localStorage.removeItem('full_name');
};

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 120 секунд таймаут (для OpenAI может потребоваться больше времени)
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url as string | undefined;
    const isLoginOrRegister = !!requestUrl && /\/auth\/(login|register)\b/.test(requestUrl);

    if (status === 401 && !isLoginOrRegister) {
      clearAuthStorage();
      if (window.location.pathname !== '/') {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

