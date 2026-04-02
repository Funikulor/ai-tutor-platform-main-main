import api, { clearAuthStorage } from './api';

export const authService = {
  async login(email: string, password: string) {
    const { data } = await api.post(
      '/auth/login',
      { email, password },
      { timeout: 30000 }
    );
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('role', data.role);
      try {
        const userInfo = await this.getCurrentUser();
        if (userInfo) {
          localStorage.setItem('full_name', userInfo.full_name || '');
          localStorage.setItem('email', userInfo.email || email);
        }
      } catch {
        // Если профиль не загрузился, авторизация все равно успешна
      }
    }
    return data;
  },

  async register(userData: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    class_id?: string;
    phone?: string;
  }) {
    const { data } = await api.post('/auth/register', userData, { timeout: 30000 });
    return data;
  },

  async getCurrentUser() {
    if (!localStorage.getItem('token')) return null;

    try {
      const { data } = await api.get('/auth/me', { timeout: 20000 });
      if (data?.full_name) {
        localStorage.setItem('full_name', data.full_name);
      }
      return data;
    } catch {
      clearAuthStorage();
      return null;
    }
  },

  logout() {
    clearAuthStorage();
  },

  isAuthenticated() {
    return !!localStorage.getItem('token');
  },
};

