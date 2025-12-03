import { useState } from 'react';
import { Plus, Edit, Trash2, Upload, BookOpen, Users, Settings, Database } from 'lucide-react';

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState<'content' | 'users' | 'system'>('content');

  // Mock content structure
  const contentStructure = [
    {
      id: 1,
      subject: 'Математика',
      sections: [
        {
          id: 11,
          name: 'Алгебра',
          topics: [
            { id: 111, name: 'Уравнения', elements: 12, tasks: 48 },
            { id: 112, name: 'Функции', elements: 8, tasks: 35 },
            { id: 113, name: 'Неравенства', elements: 6, tasks: 28 }
          ]
        },
        {
          id: 12,
          name: 'Геометрия',
          topics: [
            { id: 121, name: 'Треугольники', elements: 10, tasks: 42 },
            { id: 122, name: 'Окружности', elements: 7, tasks: 30 }
          ]
        }
      ]
    },
    {
      id: 2,
      subject: 'Физика',
      sections: [
        {
          id: 21,
          name: 'Механика',
          topics: [
            { id: 211, name: 'Кинематика', elements: 9, tasks: 38 },
            { id: 212, name: 'Динамика', elements: 11, tasks: 45 }
          ]
        }
      ]
    }
  ];

  const users = [
    { id: 1, name: 'Иванов Петр', role: 'teacher', email: 'ivanov@school.ru', status: 'active' },
    { id: 2, name: 'Сидорова Мария', role: 'teacher', email: 'sidorova@school.ru', status: 'active' },
    { id: 3, name: 'Александр И.', role: 'student', email: 'alex@student.ru', status: 'active' },
    { id: 4, name: 'Елена П.', role: 'student', email: 'elena@student.ru', status: 'active' }
  ];

  const systemStats = {
    totalUsers: 245,
    totalTasks: 1850,
    totalMaterials: 420,
    aiQueries: 12450,
    storageUsed: '2.3 GB',
    uptime: '99.8%'
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900">Панель администратора</h2>
            <p className="text-gray-600">Управление контентом и пользователями</p>
          </div>
          <Settings className="w-8 h-8 text-gray-400" />
        </div>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Пользователи</p>
          <p className="text-2xl text-gray-900 mt-1">{systemStats.totalUsers}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Задания</p>
          <p className="text-2xl text-gray-900 mt-1">{systemStats.totalTasks}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Материалы</p>
          <p className="text-2xl text-gray-900 mt-1">{systemStats.totalMaterials}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">AI запросы</p>
          <p className="text-2xl text-gray-900 mt-1">{systemStats.aiQueries}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Хранилище</p>
          <p className="text-2xl text-gray-900 mt-1">{systemStats.storageUsed}</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Аптайм</p>
          <p className="text-2xl text-green-600 mt-1">{systemStats.uptime}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 flex">
        <button
          onClick={() => setActiveTab('content')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            activeTab === 'content'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <BookOpen className="w-5 h-5 inline mr-2" />
          Управление контентом
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            activeTab === 'users'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Users className="w-5 h-5 inline mr-2" />
          Управление пользователями
        </button>
        <button
          onClick={() => setActiveTab('system')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            activeTab === 'system'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Database className="w-5 h-5 inline mr-2" />
          Настройки системы
        </button>
      </div>

      {/* Content Management */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-gray-900">Образовательный контент</h3>
              <div className="flex gap-3">
                <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                  <Upload className="w-4 h-4" />
                  Загрузить материалы
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <Plus className="w-4 h-4" />
                  Создать предмет
                </button>
              </div>
            </div>

            {/* Content Structure */}
            <div className="space-y-4">
              {contentStructure.map((subject) => (
                <div key={subject.id} className="border border-gray-200 rounded-lg">
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-6 h-6 text-blue-600" />
                      <h4 className="text-gray-900">{subject.subject}</h4>
                      <span className="px-2 py-1 bg-white rounded text-xs text-gray-600">
                        {subject.sections.length} разделов
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button className="p-2 text-blue-600 hover:bg-blue-100 rounded transition-colors">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-red-600 hover:bg-red-100 rounded transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="p-4 space-y-3">
                    {subject.sections.map((section) => (
                      <div key={section.id} className="ml-4 border-l-2 border-blue-200 pl-4">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-gray-800">{section.name}</h5>
                          <span className="text-sm text-gray-500">
                            {section.topics.length} тем
                          </span>
                        </div>
                        <div className="ml-4 space-y-2">
                          {section.topics.map((topic) => (
                            <div key={topic.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                              <div>
                                <p className="text-gray-800">{topic.name}</p>
                                <p className="text-xs text-gray-500">
                                  {topic.elements} элементов • {topic.tasks} заданий
                                </p>
                              </div>
                              <div className="flex gap-2">
                                <button className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors">
                                  Редактировать
                                </button>
                                <button className="px-3 py-1 text-sm text-green-600 hover:bg-green-50 rounded transition-colors">
                                  + Задание
                                </button>
                              </div>
                            </div>
                          ))}
                          <button className="w-full py-2 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors">
                            + Добавить тему
                          </button>
                        </div>
                      </div>
                    ))}
                    <button className="w-full py-2 text-sm text-purple-600 border border-purple-200 rounded-lg hover:bg-purple-50 transition-colors">
                      + Добавить раздел
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Settings */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-gray-900 mb-4">Настройки AI модулей</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h4 className="text-gray-800 mb-2">NLP модуль</h4>
                <p className="text-sm text-gray-600 mb-3">Анализ ответов и классификация ошибок</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Модель:</span>
                    <span className="text-gray-900">ruBERT-large</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Точность:</span>
                    <span className="text-green-600">94.2%</span>
                  </div>
                  <button className="w-full py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm">
                    Настроить
                  </button>
                </div>
              </div>

              <div className="p-4 border border-gray-200 rounded-lg">
                <h4 className="text-gray-800 mb-2">RAG модуль</h4>
                <p className="text-sm text-gray-600 mb-3">Генерация рекомендаций</p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">LLM:</span>
                    <span className="text-gray-900">GigaChat Pro</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Векторная БД:</span>
                    <span className="text-gray-900">Pinecone</span>
                  </div>
                  <button className="w-full py-2 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors text-sm">
                    Настроить
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Management */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-gray-900">Управление пользователями</h3>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Plus className="w-4 h-4" />
              Добавить пользователя
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-gray-700">Имя</th>
                  <th className="text-left py-3 px-4 text-gray-700">Email</th>
                  <th className="text-center py-3 px-4 text-gray-700">Роль</th>
                  <th className="text-center py-3 px-4 text-gray-700">Статус</th>
                  <th className="text-right py-3 px-4 text-gray-700">Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white">
                          {user.name.charAt(0)}
                        </div>
                        <span className="text-gray-900">{user.name}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-gray-600">{user.email}</td>
                    <td className="text-center py-4 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        user.role === 'teacher' 
                          ? 'bg-purple-100 text-purple-700' 
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {user.role === 'teacher' ? 'Учитель' : 'Ученик'}
                      </span>
                    </td>
                    <td className="text-center py-4 px-4">
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                        Активен
                      </span>
                    </td>
                    <td className="text-right py-4 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Settings */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-gray-900 mb-6">Настройки адаптивности</h3>
            <div className="space-y-6">
              <div>
                <label className="block text-gray-700 mb-2">Стратегия адаптации</label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option>Агрессивная (быстрое повышение сложности)</option>
                  <option>Сбалансированная (рекомендуется)</option>
                  <option>Щадящая (постепенное повышение)</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-700 mb-2">
                  Целевой уровень освоения темы (%)
                </label>
                <input 
                  type="range" 
                  min="60" 
                  max="100" 
                  defaultValue="80"
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-600 mt-1">
                  <span>60%</span>
                  <span>80%</span>
                  <span>100%</span>
                </div>
              </div>

              <div>
                <label className="block text-gray-700 mb-2">
                  Количество попыток перед сменой стратегии
                </label>
                <input 
                  type="number" 
                  defaultValue="3"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Сохранить настройки
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-gray-900 mb-6">Интеграции API</h3>
            <div className="space-y-4">
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-gray-800">GigaChat API</h4>
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                    Подключено
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">API для генерации текста в RAG модуле</p>
                <button className="text-sm text-blue-600 hover:text-blue-700">
                  Изменить API ключ →
                </button>
              </div>

              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-gray-800">Pinecone Vector DB</h4>
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                    Подключено
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">Векторная база данных для RAG</p>
                <button className="text-sm text-blue-600 hover:text-blue-700">
                  Настроить подключение →
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
