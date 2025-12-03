import { useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Users, TrendingDown, AlertCircle, Download, Filter } from 'lucide-react';

export function TeacherDashboard() {
  const [selectedClass, setSelectedClass] = useState('9А');

  // Class performance data
  const classData = [
    { student: 'Иванов А.', score: 92, topics: 18, errors: 5, status: 'excellent' },
    { student: 'Петрова М.', score: 88, topics: 17, errors: 8, status: 'good' },
    { student: 'Сидоров П.', score: 75, topics: 15, errors: 12, status: 'average' },
    { student: 'Козлова Е.', score: 65, topics: 14, errors: 18, status: 'needs-help' },
    { student: 'Новиков Д.', score: 58, topics: 12, errors: 25, status: 'needs-help' },
    { student: 'Федорова А.', score: 85, topics: 16, errors: 9, status: 'good' },
    { student: 'Смирнов И.', score: 79, topics: 15, errors: 11, status: 'average' },
    { student: 'Морозова К.', score: 91, topics: 18, errors: 6, status: 'excellent' }
  ];

  // Common errors across class
  const commonErrors = [
    { topic: 'Теорема Пифагора', students: 12, errorType: 'Концептуальная', frequency: 85 },
    { topic: 'Квадратные уравнения', students: 8, errorType: 'Вычислительная', frequency: 62 },
    { topic: 'Тригонометрия', students: 15, errorType: 'Концептуальная', frequency: 95 },
    { topic: 'Проценты', students: 5, errorType: 'Опечатки', frequency: 38 }
  ];

  // Topic performance
  const topicPerformance = [
    { topic: 'Линейные уравнения', avgScore: 88, completion: 95 },
    { topic: 'Квадратные уравнения', avgScore: 75, completion: 80 },
    { topic: 'Теорема Пифагора', avgScore: 62, completion: 70 },
    { topic: 'Тригонометрия', avgScore: 55, completion: 60 },
    { topic: 'Проценты', avgScore: 82, completion: 90 }
  ];

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

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900">Панель учителя</h2>
            <p className="text-gray-600">Аналитика и управление классом</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="9А">Класс 9А</option>
              <option value="9Б">Класс 9Б</option>
              <option value="10А">Класс 10А</option>
            </select>
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Filter className="w-4 h-4" />
              Фильтры
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Download className="w-4 h-4" />
              Экспорт
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Всего учеников</p>
              <p className="text-3xl text-gray-900 mt-1">{classData.length}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Средний балл</p>
              <p className="text-3xl text-gray-900 mt-1">
                {Math.round(classData.reduce((acc, s) => acc + s.score, 0) / classData.length)}%
              </p>
            </div>
            <TrendingDown className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Нужна помощь</p>
              <p className="text-3xl text-gray-900 mt-1">
                {classData.filter(s => s.status === 'needs-help').length}
              </p>
            </div>
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Завершено тем</p>
              <p className="text-3xl text-gray-900 mt-1">
                {Math.round(classData.reduce((acc, s) => acc + s.topics, 0) / classData.length)}
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xl">
              ✓
            </div>
          </div>
        </div>
      </div>

      {/* Student Performance Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Успеваемость учеников</h3>
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
              {classData.map((student, index) => (
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
                    <button className="text-blue-600 hover:text-blue-700 text-sm">
                      Подробнее →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Common Errors Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Частые ошибки класса (NLP анализ)</h3>
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
          <button className="mt-4 w-full py-2 px-4 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm">
            Создать групповое занятие по проблемным темам
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Производительность по темам</h3>
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
        </div>
      </div>

      {/* Students Needing Help */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <h3 className="text-gray-900">Группа риска - требуется внимание</h3>
        </div>
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
                  <button className="w-full py-2 px-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm">
                    Назначить дополнительные занятия
                  </button>
                  <button className="w-full py-2 px-3 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors text-sm">
                    Связаться с родителями
                  </button>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
