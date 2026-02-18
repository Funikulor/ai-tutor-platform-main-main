import axios from 'axios';

// Для production используем VITE_API_URL из переменных окружения
// Для разработки - localhost
// ВАЖНО: VITE_API_URL должен быть установлен в Railway Variables для frontend!
export const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:8000'); // В production без VITE_API_URL будет ошибка

// Логируем для отладки
if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
  console.error('⚠️ VITE_API_URL не установлен! Установите его в Railway Variables для frontend.');
}
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
  
  // Логируем запросы для отладки (особенно для auth)
  if (config.url?.includes('/auth/')) {
    console.log('API Request:', {
      method: config.method?.toUpperCase(),
      url: `${API_BASE_URL}${config.url}`,
      baseURL: API_BASE_URL,
      path: config.url,
      fullUrl: `${API_BASE_URL}${config.url}`,
      env: {
        VITE_API_URL: import.meta.env.VITE_API_URL,
        PROD: import.meta.env.PROD,
        MODE: import.meta.env.MODE
      }
    });
  }
  
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url as string | undefined;
    const isLoginOrRegister = !!requestUrl && /\/auth\/(login|register)\b/.test(requestUrl);
    const method = error.config?.method?.toUpperCase();
    const fullUrl = error.config?.url ? `${API_BASE_URL}${error.config.url}` : 'unknown';

    // Логируем ошибки для отладки
    if (status === 405) {
      console.error('405 Method Not Allowed:', {
        method,
        url: fullUrl,
        requestUrl,
        baseURL: API_BASE_URL,
        error: error.message
      });
    }

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

