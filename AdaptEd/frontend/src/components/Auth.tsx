import { useState, useEffect, useCallback } from 'react';
import { BookOpen, Mail, Lock, AlertCircle } from 'lucide-react';
import { authService } from '../services/auth';
import api from '../services/api';

interface AuthProps {
  onSuccess: () => void;
}

export function Auth({ onSuccess }: AuthProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('online');

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  const checkBackend = useCallback(async () => {
    try {
      // Логируем для отладки
      const baseURL = (api.defaults.baseURL || '') as string;
      console.log('Checking backend at:', baseURL || '/');
      
      // Проверяем доступность backend через корневой endpoint
      const response = await api.get('/', { timeout: 15000 });
      if (response.status === 200 && response.data) {
        console.log('✅ Backend is online:', response.data);
        setBackendStatus('online');
      } else {
        console.warn('⚠️ Backend responded but status is not 200:', response.status);
        setBackendStatus('offline');
      }
    } catch (error: any) {
      const baseURL = (api.defaults.baseURL || '') as string;
      const fullURL = baseURL + '/';
      
      console.error('❌ Backend check failed:', {
        error: error.message,
        code: error.code,
        status: error.response?.status,
        url: error.config?.url,
        baseURL: baseURL,
        fullURL: fullURL,
        env: {
          VITE_API_URL: import.meta.env.VITE_API_URL,
          PROD: import.meta.env.PROD
        }
      });
      
      // В production может быть холодный старт Railway или Neon
      if (import.meta.env.PROD && (error?.code === 'ETIMEDOUT' || error?.code === 'ECONNREFUSED' || error?.code === 'ERR_NETWORK')) {
        console.log('⏳ Retrying backend check in 3 seconds...');
        // Даем еще одну попытку через 3 секунды
        setTimeout(() => {
          api.get('/', { timeout: 15000 })
            .then(() => {
              console.log('✅ Backend is online (after retry)');
              setBackendStatus('online');
            })
            .catch(() => {
              console.error('❌ Backend is still offline after retry');
              setBackendStatus('offline');
            });
        }, 3000);
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

  const getAuthErrorMessage = (err: any) => {
    const fallback = 'Ошибка входа. Проверьте email и пароль.';

    if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error') || err?.code === 'ECONNREFUSED') {
      if (import.meta.env.PROD) {
        return '❌ Ошибка подключения к серверу!\n\nПроверьте:\n1. Backend запущен на Railway\n2. VITE_API_URL установлен правильно (с https://)\n3. Backend доступен по URL из VITE_API_URL\n4. Проверьте логи backend в Railway Dashboard';
      }
      return '❌ Ошибка подключения к серверу!\n\nУбедитесь, что бэкенд запущен:\n1. Откройте новое окно терминала\n2. Перейдите в папку AdaptEd/backend\n3. Запустите: uvicorn app:app --reload --port 8000\n\nИли используйте: start_backend.bat';
    }
    if (err?.code === 'ETIMEDOUT' || err?.message?.includes('timeout')) {
      return 'Превышено время ожидания ответа от сервера. Проверьте, что бэкенд запущен.';
    }
    if (err?.response?.status === 401) {
      return 'Неверный email или пароль. Проверьте данные и попробуйте снова.';
    }
    if (err?.response?.status === 405) {
      return 'Ошибка 405: Метод не разрешен. Проверьте, что backend правильно настроен и URL правильный.';
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
      setError(getAuthErrorMessage(err));
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
                    ? 'Backend API недоступен. Проверьте, что backend запущен на Railway и VITE_API_URL установлен правильно.'
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
        {/* Auth Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-red-700 text-sm whitespace-pre-line">{error}</p>
              </div>
            </div>
          )}

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
        </div>
      </div>
    </div>
  );
}
