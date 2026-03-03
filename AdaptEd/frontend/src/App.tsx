import { useState, useEffect } from 'react';
import { StudentDashboard } from './components/StudentDashboard';
import { TeacherDashboard } from './components/TeacherDashboard';
import { AdminPanel } from './components/AdminPanel';
import { Auth } from './components/Auth';
import { UserProfile } from './components/UserProfile';
import { BookOpen, Users, Settings, LogOut, User as UserIcon } from 'lucide-react';
import { authService } from './services/auth';
import { getAvatarUrl } from './utils/avatar';
import { Toaster } from 'sonner';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [currentRole, setCurrentRole] = useState<'student' | 'teacher' | 'admin'>('student');
  const [showProfile, setShowProfile] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    setLoading(true);
    try {
      const user = await authService.getCurrentUser();
      if (user) {
        setCurrentUser(user);
        setIsAuthenticated(true);
        // Устанавливаем роль из данных пользователя
        const userRole = user.role || localStorage.getItem('role') || 'student';
        setCurrentRole(userRole as 'student' | 'teacher' | 'admin');
      } else {
        setIsAuthenticated(false);
      }
    } catch (error) {
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = () => {
    checkAuth();
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setCurrentRole('student');
    setShowProfile(false);
  };

  const handleRoleSwitch = (role: 'student' | 'teacher' | 'admin') => {
    // Только админ может переключаться между ролями
    if (currentUser?.role === 'admin') {
      setCurrentRole(role);
      // Сохраняем выбранную роль в localStorage для удобства
      localStorage.setItem('viewing_as_role', role);
    }
  };

  // Показываем загрузку
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Показываем авторизацию, если не авторизован
  if (!isAuthenticated) {
    return <Auth onSuccess={handleLoginSuccess} />;
  }

  // Определяем реальную роль пользователя
  const actualRole = currentUser?.role || 'student';
  const isAdmin = actualRole === 'admin';
  const viewingRole = isAdmin ? currentRole : actualRole;

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" richColors />
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-gray-900">EduAI Platform</h1>
                <p className="text-sm text-gray-500">Интеллектуальная образовательная платформа</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Переключение ролей - только для админа */}
              {isAdmin && (
                <div className="flex bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => handleRoleSwitch('student')}
                    className={`px-4 py-2 rounded-md transition-colors ${
                      currentRole === 'student'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="Переключиться на вид ученика"
                  >
                    <Users className="w-4 h-4 inline mr-2" />
                    Ученик
                  </button>
                  <button
                    onClick={() => handleRoleSwitch('teacher')}
                    className={`px-4 py-2 rounded-md transition-colors ${
                      currentRole === 'teacher'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="Переключиться на вид учителя"
                  >
                    <BookOpen className="w-4 h-4 inline mr-2" />
                    Учитель
                  </button>
                  <button
                    onClick={() => handleRoleSwitch('admin')}
                    className={`px-4 py-2 rounded-md transition-colors ${
                      currentRole === 'admin'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                    title="Переключиться на вид админа"
                  >
                    <Settings className="w-4 h-4 inline mr-2" />
                    Админ
                  </button>
                </div>
              )}
              
              <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
                <div className="text-right">
                  <p className="text-gray-900">{currentUser?.full_name || 'Пользователь'}</p>
                  <p className="text-sm text-gray-500">
                    {isAdmin && currentRole !== actualRole ? (
                      <span>Смотрю как: <span className="capitalize">{viewingRole}</span></span>
                    ) : (
                      <span className="capitalize">{actualRole}</span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowProfile(!showProfile)}
                    className="w-10 h-10 rounded-full flex items-center justify-center overflow-hidden bg-gradient-to-br from-blue-400 to-purple-500 text-white hover:scale-105 transition-transform border-2 border-white shadow"
                    title="Профиль"
                  >
                    {getAvatarUrl(currentUser?.avatar_seed) ? (
                      <img src={getAvatarUrl(currentUser?.avatar_seed)!} alt="" className="w-full h-full object-cover" />
                    ) : (
                      currentUser?.full_name?.charAt(0) || <UserIcon className="w-5 h-5" />
                    )}
                  </button>
                  <button
                    onClick={handleLogout}
                    className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Выйти"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {showProfile ? (
          <UserProfile onClose={() => setShowProfile(false)} onProfileUpdated={checkAuth} />
        ) : (
          <>
            {viewingRole === 'student' && <StudentDashboard />}
            {viewingRole === 'teacher' && <TeacherDashboard />}
            {viewingRole === 'admin' && <AdminPanel />}
          </>
        )}
      </main>
    </div>
  );
}
