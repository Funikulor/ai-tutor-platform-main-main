import { useState, useEffect, useCallback } from 'react';
import { BookOpen, Mail, Lock, User, Phone, GraduationCap, AlertCircle } from 'lucide-react';
import { authService } from '../services/auth';
import api from '../services/api';

interface AuthProps {
  onSuccess: () => void;
}

export function Auth({ onSuccess }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Login form
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'student' as 'student' | 'teacher' | 'parent',
    class_id: '',
    phone: '',
  });

  const checkBackend = useCallback(async () => {
    setBackendStatus('checking');
    try {
      // Проверяем доступность backend через корневой endpoint
      const response = await api.get('/', { timeout: 10000 });
      if (response.status === 200 && response.data) {
        setBackendStatus('online');
      } else {
        setBackendStatus('offline');
      }
    } catch (error: any) {
      // В production не показываем ошибку сразу - может быть холодный старт Neon
      if (import.meta.env.PROD && error?.code === 'ETIMEDOUT') {
        // Даем еще одну попытку для холодного старта
        setTimeout(() => {
          api.get('/', { timeout: 10000 })
            .then(() => setBackendStatus('online'))
            .catch(() => setBackendStatus('offline'));
        }, 2000);
      } else {
        setBackendStatus('offline');
      }
    }
  }, []);

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 15000);
    return () => clearInterval(interval);
  }, [checkBackend]);

  const getAuthErrorMessage = (err: any, mode: 'login' | 'register') => {
    const fallback =
      mode === 'login'
        ? 'Ошибка входа. Проверьте email и пароль.'
        : 'Ошибка регистрации. Проверьте данные.';

    if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error') || err?.code === 'ECONNREFUSED') {
      if (import.meta.env.PROD) {
        return '❌ Ошибка подключения к серверу!\n\nПроверьте:\n1. Netlify Function "api" работает\n2. Переменная DATABASE_URL установлена в Netlify\n3. Проверьте логи функции в Netlify Dashboard';
      }
      return '❌ Ошибка подключения к серверу!\n\nУбедитесь, что бэкенд запущен:\n1. Откройте новое окно терминала\n2. Перейдите в папку AdaptEd/backend\n3. Запустите: uvicorn app:app --reload --port 8000\n\nИли используйте: start_backend.bat';
    }
    if (err?.code === 'ETIMEDOUT' || err?.message?.includes('timeout')) {
      return 'Превышено время ожидания ответа от сервера. Проверьте, что бэкенд запущен.';
    }
    if (mode === 'login' && err?.response?.status === 401) {
      return 'Неверный email или пароль. Проверьте данные и попробуйте снова.';
    }
    if (err?.response?.data?.detail) {
      return err.response.data.detail;
    }
    if (err?.message) {
      return err.message;
    }
    return fallback;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await authService.login(loginEmail, loginPassword);
      onSuccess();
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'login'));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await authService.register(registerData);
      await authService.login(registerData.email, registerData.password);
      onSuccess();
    } catch (err: any) {
      setError(getAuthErrorMessage(err, 'register'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AdaptEd</h1>
          <p className="text-gray-600">Интеллектуальная образовательная платформа</p>
        </div>

        {/* Backend Status */}
        {backendStatus === 'offline' && (
          <div className="mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 mb-1">
                  Бэкенд не доступен
                </p>
                <p className="text-xs text-red-700 mb-2">
                  {import.meta.env.PROD 
                    ? 'Backend API недоступен. Проверьте настройки Netlify Functions.'
                    : 'Запустите бэкенд на порту 8000 перед входом в систему.'}
                </p>
                <button
                  onClick={checkBackend}
                  className="text-xs text-red-700 hover:text-red-900 underline"
                >
                  Проверить снова
                </button>
              </div>
            </div>
          </div>
        )}
        {backendStatus === 'checking' && (
          <div className="mb-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm font-medium text-yellow-800">
                Проверка подключения к бэкенду...
              </p>
            </div>
          </div>
        )}
        {backendStatus === 'online' && (
          <div className="mb-4 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs">✓</span>
              </div>
              <p className="text-sm font-medium text-green-800">
                Бэкенд доступен и готов к работе
              </p>
            </div>
          </div>
        )}

        {/* Auth Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Tabs */}
          <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
            <button
              onClick={() => {
                setIsLogin(true);
                setError(null);
              }}
              className={`flex-1 py-2 px-4 rounded-md transition-all ${
                isLogin
                  ? 'bg-white text-blue-600 shadow-sm font-medium'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Вход
            </button>
            <button
              onClick={() => {
                setIsLogin(false);
                setError(null);
              }}
              className={`flex-1 py-2 px-4 rounded-md transition-all ${
                !isLogin
                  ? 'bg-white text-blue-600 shadow-sm font-medium'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Регистрация
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-red-700 text-sm whitespace-pre-line">{error}</p>
              </div>
            </div>
          )}

          {/* Login Form */}
          {isLogin ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="your@email.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Пароль
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || backendStatus === 'offline'}
                className="w-full bg-purple-600 text-white py-3 rounded-lg font-semibold hover:bg-purple-700 hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? 'Вход...' : 'Войти'}
              </button>
            </form>
          ) : (
            /* Register Form */
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ФИО
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={registerData.full_name}
                    onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })}
                    required
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Иванов Иван Иванович"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    value={registerData.email}
                    onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                    required
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="your@email.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Пароль
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="password"
                    value={registerData.password}
                    onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                    required
                    minLength={6}
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="Минимум 6 символов"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Роль
                </label>
                <div className="relative">
                  <GraduationCap className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <select
                    value={registerData.role}
                    onChange={(e) => setRegisterData({ ...registerData, role: e.target.value as any })}
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
                  >
                    <option value="student">Ученик</option>
                    <option value="teacher">Учитель</option>
                    <option value="parent">Родитель</option>
                  </select>
                </div>
              </div>

              {registerData.role === 'student' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Класс (опционально)
                  </label>
                  <input
                    type="text"
                    value={registerData.class_id}
                    onChange={(e) => setRegisterData({ ...registerData, class_id: e.target.value })}
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="7А"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Телефон (опционально)
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="tel"
                    value={registerData.phone}
                    onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
                    disabled={loading || backendStatus === 'offline'}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="+7 (999) 123-45-67"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || backendStatus === 'offline'}
                className="w-full bg-purple-600 text-white py-3 rounded-lg font-semibold hover:bg-purple-700 hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? 'Регистрация...' : 'Зарегистрироваться'}
              </button>
            </form>
          )}

          {/* Demo credentials hint */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-xs text-blue-700 text-center mb-2">
              💡 Для тестирования можно использовать любые данные. Система создаст нового пользователя при регистрации.
            </p>
            <p className="text-xs text-blue-600 text-center">
              🔑 Предустановленный админ: <strong>admin@adapted.ru</strong> / <strong>admin123</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
