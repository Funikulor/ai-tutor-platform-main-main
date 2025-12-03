import { useState } from 'react';
import { StudentDashboard } from './components/StudentDashboard';
import { TeacherDashboard } from './components/TeacherDashboard';
import { AdminPanel } from './components/AdminPanel';
import { BookOpen, Users, Settings } from 'lucide-react';

export default function App() {
  const [currentRole, setCurrentRole] = useState<'student' | 'teacher' | 'admin'>('student');
  const [currentUser] = useState({
    id: 1,
    name: 'Александр Иванов',
    role: 'student',
    avatar: '/avatar.png'
  });

  return (
    <div className="min-h-screen bg-gray-50">
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
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setCurrentRole('student')}
                  className={`px-4 py-2 rounded-md transition-colors ${
                    currentRole === 'student'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Users className="w-4 h-4 inline mr-2" />
                  Ученик
                </button>
                <button
                  onClick={() => setCurrentRole('teacher')}
                  className={`px-4 py-2 rounded-md transition-colors ${
                    currentRole === 'teacher'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <BookOpen className="w-4 h-4 inline mr-2" />
                  Учитель
                </button>
                <button
                  onClick={() => setCurrentRole('admin')}
                  className={`px-4 py-2 rounded-md transition-colors ${
                    currentRole === 'admin'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Settings className="w-4 h-4 inline mr-2" />
                  Админ
                </button>
              </div>
              
              <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
                <div className="text-right">
                  <p className="text-gray-900">{currentUser.name}</p>
                  <p className="text-sm text-gray-500 capitalize">{currentRole}</p>
                </div>
                <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white">
                  {currentUser.name.charAt(0)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentRole === 'student' && <StudentDashboard />}
        {currentRole === 'teacher' && <TeacherDashboard />}
        {currentRole === 'admin' && <AdminPanel />}
      </main>
    </div>
  );
}
