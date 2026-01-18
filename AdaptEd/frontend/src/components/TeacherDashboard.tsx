import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Users, TrendingDown, AlertCircle, Download, Filter, BarChart3, FileText, X, BookOpen, Target, TrendingUp } from 'lucide-react';
import { TestCreator } from './TestCreator';
import api from '../services/api';

interface StudentData {
  student: string;
  score: number;
  topics: number;
  errors: number;
  status: string;
  user_id?: string;
}

export function TeacherDashboard() {
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'analytics' | 'tests'>('analytics');
  const [classData, setClassData] = useState<StudentData[]>([]);
  const [commonErrors, setCommonErrors] = useState<Array<{
    topic: string;
    students: number;
    errorType: string;
    frequency: number;
  }>>([]);
  const [topicPerformance, setTopicPerformance] = useState<Array<{
    topic: string;
    avgScore: number;
    completion: number;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalStudents, setTotalStudents] = useState(0);
  const [averageScore, setAverageScore] = useState(0);
  const [needsHelpCount, setNeedsHelpCount] = useState(0);
  
  // Модальное окно для детальной информации об ученике
  const [selectedStudent, setSelectedStudent] = useState<StudentData | null>(null);
  const [studentDetails, setStudentDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    loadClassAnalytics();
  }, [selectedClass]);

  const loadClassAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get('/teacher/class-analytics', {
        params: selectedClass ? { class_id: selectedClass } : {}
      });
      
      const data = response.data;
      setClassData(data.classData || []);
      setCommonErrors(data.commonErrors || []);
      setTopicPerformance(data.topicPerformance || []);
      setTotalStudents(data.totalStudents || 0);
      setAverageScore(data.averageScore || 0);
      setNeedsHelpCount(data.needsHelpCount || 0);
    } catch (err: any) {
      console.error('Error loading class analytics:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить аналитику класса');
      setClassData([]);
      setCommonErrors([]);
      setTopicPerformance([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      excellent: 'bg-green-100 text-green-700',
      good: 'bg-blue-100 text-blue-700',
      average: 'bg-yellow-100 text-yellow-700',
      'needs-help': 'bg-red-100 text-red-700'
    };
    const labels = {
      excellent: 'Отлично',
      good: 'Хорошо',
      average: 'Средне',
      'needs-help': 'Нужна помощь'
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  // Загрузка детальной информации об ученике
  const loadStudentDetails = async (student: StudentData) => {
    if (!student.user_id) {
      alert('ID ученика не найден');
      return;
    }
    
    setSelectedStudent(student);
    setLoadingDetails(true);
    try {
      const response = await api.get(`/agents/profile/${student.user_id}`);
      setStudentDetails(response.data);
    } catch (err: any) {
      console.error('Error loading student details:', err);
      alert('Не удалось загрузить детальную информацию об ученике');
    } finally {
      setLoadingDetails(false);
    }
  };

  // Экспорт данных
  const handleExport = () => {
    const dataToExport = {
      class: selectedClass || 'Все классы',
      date: new Date().toLocaleString('ru-RU'),
      totalStudents,
      averageScore,
      needsHelpCount,
      students: classData.map(s => ({
        name: s.student,
        score: s.score,
        topics: s.topics,
        errors: s.errors,
        status: s.status
      })),
      commonErrors,
      topicPerformance
    };

    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `class-analytics-${selectedClass || 'all'}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Назначение дополнительных занятий
  const handleAssignExtraLessons = async (student: StudentData) => {
    if (!student.user_id) {
      alert('ID ученика не найден');
      return;
    }
    
    const confirmed = window.confirm(
      `Назначить дополнительные занятия для ${student.student}?\n\n` +
      `Это создаст персональные задания по проблемным темам.`
    );
    
    if (confirmed) {
      try {
        // Здесь можно добавить API вызов для назначения заданий
        alert(`Дополнительные занятия назначены для ${student.student}`);
      } catch (err) {
        alert('Ошибка при назначении занятий');
      }
    }
  };

  // Связь с родителями
  const handleContactParents = async (student: StudentData) => {
    if (!student.user_id) {
      alert('ID ученика не найден');
      return;
    }
    
    try {
      // Получаем информацию о пользователе для контактов
      const userResponse = await api.get(`/users/${student.user_id}`);
      const userData = userResponse.data;
      
      const message = `Связаться с родителями ${student.student}?\n\n` +
        `Email: ${userData.email || 'не указан'}\n` +
        `Телефон: ${userData.phone || 'не указан'}\n\n` +
        `Проблемы: низкая успеваемость (${student.score}%), ${student.errors} ошибок`;
      
      if (window.confirm(message)) {
        if (userData.email) {
          window.location.href = `mailto:${userData.email}?subject=Успеваемость ${student.student}&body=${encodeURIComponent(message)}`;
        } else {
          alert('Email родителя не указан в системе');
        }
      }
    } catch (err) {
      alert('Не удалось получить контактную информацию');
    }
  };

  // Создание группового занятия
  const handleCreateGroupLesson = () => {
    if (commonErrors.length === 0) {
      alert('Нет данных об ошибках для создания занятия');
      return;
    }
    
    const topErrors = commonErrors.slice(0, 3);
    const topics = topErrors.map(e => e.topic).join(', ');
    
    const confirmed = window.confirm(
      `Создать групповое занятие по проблемным темам?\n\n` +
      `Темы: ${topics}\n` +
      `Затронуто учеников: ${topErrors.reduce((sum, e) => sum + e.students, 0)}`
    );
    
    if (confirmed) {
      // Здесь можно добавить API вызов для создания группового задания
      alert(`Групповое занятие создано по темам: ${topics}`);
    }
  };

  // Фильтрация студентов
  const filteredClassData = filterStatus === 'all' 
    ? classData 
    : classData.filter(s => s.status === filterStatus);

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 flex">
        <button
          onClick={() => setCurrentView('analytics')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'analytics'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <BarChart3 className="w-5 h-5 inline mr-2" />
          Аналитика класса
        </button>
        <button
          onClick={() => setCurrentView('tests')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'tests'
              ? 'bg-green-50 text-green-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <FileText className="w-5 h-5 inline mr-2" />
          Создание тестов
        </button>
      </div>

      {/* Tests View */}
      {currentView === 'tests' && <TestCreator />}

      {/* Analytics View */}
      {currentView === 'analytics' && (
        <>
      {/* Header Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900">Панель учителя</h2>
            <p className="text-gray-600">Аналитика и управление классом</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedClass || ''}
              onChange={(e) => setSelectedClass(e.target.value || null)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Все классы</option>
              <option value="9А">Класс 9А</option>
              <option value="9Б">Класс 9Б</option>
              <option value="10А">Класс 10А</option>
            </select>
            <button 
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Filter className="w-4 h-4" />
              Фильтры
            </button>
            <button 
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Экспорт
            </button>
          </div>
        </div>
        
        {/* Фильтры */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">Статус:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">Все</option>
                <option value="excellent">Отлично</option>
                <option value="good">Хорошо</option>
                <option value="average">Средне</option>
                <option value="needs-help">Нужна помощь</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="text-center py-8">
            <p className="text-gray-500">Загрузка аналитики...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Quick Stats */}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Всего учеников</p>
                <p className="text-3xl text-gray-900 mt-1">{totalStudents}</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Средний балл</p>
                <p className="text-3xl text-gray-900 mt-1">{averageScore}%</p>
              </div>
              <TrendingDown className="w-10 h-10 text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Нужна помощь</p>
                <p className="text-3xl text-gray-900 mt-1">{needsHelpCount}</p>
              </div>
              <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Завершено тем</p>
                <p className="text-3xl text-gray-900 mt-1">
                  {classData.length > 0 ? Math.round(classData.reduce((acc, s) => acc + s.topics, 0) / classData.length) : 0}
                </p>
              </div>
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xl">
                ✓
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Student Performance Table */}
      {!loading && !error && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Успеваемость учеников</h3>
          {classData.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">Нет данных о студентах</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-gray-700">Ученик</th>
                    <th className="text-center py-3 px-4 text-gray-700">Средний балл</th>
                    <th className="text-center py-3 px-4 text-gray-700">Изучено тем</th>
                    <th className="text-center py-3 px-4 text-gray-700">Ошибок</th>
                    <th className="text-center py-3 px-4 text-gray-700">Статус</th>
                    <th className="text-right py-3 px-4 text-gray-700">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredClassData.map((student, index) => (
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white">
                        {student.student.charAt(0)}
                      </div>
                      <span className="text-gray-900">{student.student}</span>
                    </div>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className={`text-lg ${
                      student.score >= 85 ? 'text-green-600' :
                      student.score >= 70 ? 'text-blue-600' :
                      student.score >= 60 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {student.score}%
                    </span>
                  </td>
                  <td className="text-center py-4 px-4 text-gray-900">{student.topics}</td>
                  <td className="text-center py-4 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      student.errors < 10 ? 'bg-green-100 text-green-700' :
                      student.errors < 15 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {student.errors}
                    </span>
                  </td>
                  <td className="text-center py-4 px-4">
                    {getStatusBadge(student.status)}
                  </td>
                  <td className="text-right py-4 px-4">
                    <button 
                      onClick={() => loadStudentDetails(student)}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      Подробнее →
                    </button>
                  </td>
                </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Common Errors Analysis */}
      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-gray-900 mb-4">Частые ошибки класса (NLP анализ)</h3>
            {commonErrors.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Нет данных об ошибках</p>
              </div>
            ) : (
              <div className="space-y-4">
                {commonErrors.map((error, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="text-gray-900">{error.topic}</h4>
                    <p className="text-sm text-gray-600">
                      {error.students} учеников • {error.errorType}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs ${
                    error.frequency > 80 ? 'bg-red-100 text-red-700' :
                    error.frequency > 50 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {error.frequency}% частота
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-red-500 to-orange-500"
                    style={{ width: `${error.frequency}%` }}
                  />
                </div>
                </div>
                ))}
              </div>
            )}
            <button 
              onClick={handleCreateGroupLesson}
              className="mt-4 w-full py-2 px-4 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
            >
              Создать групповое занятие по проблемным темам
            </button>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-gray-900 mb-4">Производительность по темам</h3>
            {topicPerformance.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Нет данных о производительности</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topicPerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="topic" 
                stroke="#6b7280"
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
                tick={{ fontSize: 12 }}
              />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Bar dataKey="avgScore" fill="#3b82f6" name="Средний балл %" radius={[8, 8, 0, 0]} />
                  <Bar dataKey="completion" fill="#8b5cf6" name="Завершение %" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      {/* Students Needing Help */}
      {!loading && !error && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <h3 className="text-gray-900">Группа риска - требуется внимание</h3>
          </div>
          {classData.filter(s => s.status === 'needs-help').length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">Нет студентов, требующих помощи</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {classData
                .filter(s => s.status === 'needs-help')
                .map((student, index) => (
              <div key={index} className="p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-red-200 rounded-full flex items-center justify-center text-red-700">
                      {student.student.charAt(0)}
                    </div>
                    <div>
                      <h4 className="text-gray-900">{student.student}</h4>
                      <p className="text-sm text-gray-600">{student.score}% • {student.errors} ошибок</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <button 
                    onClick={() => handleAssignExtraLessons(student)}
                    className="w-full py-2 px-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
                  >
                    Назначить дополнительные занятия
                  </button>
                  <button 
                    onClick={() => handleContactParents(student)}
                    className="w-full py-2 px-3 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium"
                  >
                    Связаться с родителями
                  </button>
                </div>
                </div>
                ))}
            </div>
          )}
        </div>
      )}
        </>
      )}

      {/* Модальное окно с детальной информацией об ученике */}
      {selectedStudent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">
                Детальная информация: {selectedStudent.student}
              </h2>
              <button
                onClick={() => {
                  setSelectedStudent(null);
                  setStudentDetails(null);
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6">
              {loadingDetails ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">Загрузка данных...</p>
                </div>
              ) : studentDetails ? (
                <div className="space-y-6">
                  {/* Основная статистика */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Target className="w-5 h-5 text-blue-600" />
                        <span className="text-sm text-gray-600">Точность</span>
                      </div>
                      <p className="text-2xl font-bold text-blue-600">
                        {studentDetails.accuracy_rate?.toFixed(1) || 0}%
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <BookOpen className="w-5 h-5 text-green-600" />
                        <span className="text-sm text-gray-600">Выполнено заданий</span>
                      </div>
                      <p className="text-2xl font-bold text-green-600">
                        {studentDetails.total_tasks_completed || 0}
                      </p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp className="w-5 h-5 text-purple-600" />
                        <span className="text-sm text-gray-600">Изучено тем</span>
                      </div>
                      <p className="text-2xl font-bold text-purple-600">
                        {Object.keys(studentDetails.topic_mastery || {}).length}
                      </p>
                    </div>
                  </div>

                  {/* Мастерство по темам */}
                  {studentDetails.topic_mastery && Object.keys(studentDetails.topic_mastery).length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Мастерство по темам</h3>
                      <div className="space-y-3">
                        {Object.entries(studentDetails.topic_mastery)
                          .sort((a, b) => b[1] - a[1])
                          .map(([topic, mastery]: [string, any]) => (
                            <div key={topic}>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-sm text-gray-700">{topic}</span>
                                <span className="text-sm font-medium text-gray-900">
                                  {(mastery * 100).toFixed(0)}%
                                </span>
                              </div>
                              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${
                                    mastery >= 0.7 ? 'bg-green-500' :
                                    mastery >= 0.5 ? 'bg-yellow-500' :
                                    'bg-red-500'
                                  }`}
                                  style={{ width: `${mastery * 100}%` }}
                                />
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Частые ошибки */}
                  {studentDetails.error_frequency && Object.keys(studentDetails.error_frequency).length > 0 && (
                    <div className="bg-red-50 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Частые ошибки</h3>
                      <div className="space-y-2">
                        {Object.entries(studentDetails.error_frequency)
                          .sort((a: any, b: any) => b[1] - a[1])
                          .slice(0, 5)
                          .map(([errorType, count]: [string, any]) => (
                            <div key={errorType} className="flex items-center justify-between">
                              <span className="text-sm text-gray-700">{errorType}</span>
                              <span className="text-sm font-medium text-red-600">{count} раз</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* История заданий */}
                  {studentDetails.task_history && studentDetails.task_history.length > 0 && (
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Последние задания ({studentDetails.task_history.length})
                      </h3>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {studentDetails.task_history.slice(-10).reverse().map((task: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div className="flex-1">
                              <span className="text-sm text-gray-700">
                                {task.topic || 'Без темы'}
                              </span>
                              {task.question && (
                                <p className="text-xs text-gray-500 truncate max-w-md">
                                  {task.question.substring(0, 60)}...
                                </p>
                              )}
                            </div>
                            <span className={`text-xs px-2 py-1 rounded ${
                              task.is_correct 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-red-100 text-red-700'
                            }`}>
                              {task.is_correct ? '✓' : '✗'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Дополнительная информация */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Стиль обучения</h4>
                      <p className="text-sm text-gray-600">
                        {studentDetails.learning_style || 'Не определен'}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Эмоциональное состояние</h4>
                      <p className="text-sm text-gray-600">
                        {studentDetails.emotional_state || 'Нейтральное'}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">Не удалось загрузить детальную информацию</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
