import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, AlertTriangle, Clock } from 'lucide-react';

interface ProgressData {
  totalTopics: number;
  completedTopics: number;
  currentStreak: number;
  totalPoints: number;
  averageAccuracy: number;
  weakTopics: Array<{
    name: string;
    progress: number;
    errors: number;
  }>;
  recentActivities: Array<{
    date: string;
    topic: string;
    score: number;
    time: number;
  }>;
}

export function ProgressStats({ progress }: { progress: ProgressData }) {
  // Weekly progress data
  const weeklyData = [
    { day: 'Пн', score: 85, tasks: 12 },
    { day: 'Вт', score: 78, tasks: 15 },
    { day: 'Ср', score: 92, tasks: 10 },
    { day: 'Чт', score: 88, tasks: 14 },
    { day: 'Пт', score: 90, tasks: 11 },
    { day: 'Сб', score: 87, tasks: 9 },
    { day: 'Вс', score: 94, tasks: 8 }
  ];

  // Topic distribution
  const topicDistribution = [
    { name: 'Освоено', value: progress.completedTopics, color: '#10b981' },
    { name: 'В процессе', value: progress.totalTopics - progress.completedTopics, color: '#3b82f6' }
  ];

  return (
    <div className="space-y-6">
      {/* Recent Activities */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Недавняя активность</h3>
        <div className="space-y-3">
          {progress.recentActivities.map((activity, index) => (
            <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-4 flex-1">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  activity.score >= 90 ? 'bg-green-100 text-green-600' :
                  activity.score >= 70 ? 'bg-blue-100 text-blue-600' :
                  'bg-yellow-100 text-yellow-600'
                }`}>
                  {activity.score}%
                </div>
                <div className="flex-1">
                  <h4 className="text-gray-900">{activity.topic}</h4>
                  <p className="text-sm text-gray-500">{activity.date}</p>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="w-4 h-4" />
                  {activity.time} мин
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Weekly Performance Chart */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-gray-900">Успеваемость за неделю</h3>
            <p className="text-sm text-gray-500">Средний балл и количество заданий</p>
          </div>
          <TrendingUp className="w-6 h-6 text-green-600" />
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={weeklyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="day" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'white', 
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="score" 
              stroke="#3b82f6" 
              strokeWidth={3}
              name="Балл (%)"
              dot={{ fill: '#3b82f6', r: 5 }}
            />
            <Line 
              type="monotone" 
              dataKey="tasks" 
              stroke="#8b5cf6" 
              strokeWidth={3}
              name="Задания"
              dot={{ fill: '#8b5cf6', r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Topics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Weak Topics */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h3 className="text-gray-900">Слабые места</h3>
          </div>
          <div className="space-y-3">
            {progress.weakTopics.map((topic, index) => (
              <div key={index}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-700">{topic.name}</span>
                  <span className="text-sm text-gray-500">{topic.progress}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-500"
                    style={{ width: `${topic.progress}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">{topic.errors} ошибок</p>
              </div>
            ))}
          </div>
        </div>

        {/* Topic Distribution Pie Chart */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Распределение тем</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={topicDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {topicDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex items-center justify-center gap-6 mt-4">
            {topicDistribution.map((item, index) => (
              <div key={index} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-gray-600">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Error Types Analysis */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Типы ошибок (NLP анализ)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={[
            { type: 'Концептуальные', count: 15, color: '#ef4444' },
            { type: 'Вычислительные', count: 8, color: '#f59e0b' },
            { type: 'Опечатки', count: 5, color: '#eab308' },
            { type: 'Неточности', count: 3, color: '#84cc16' }
          ]}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="type" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'white', 
                border: '1px solid #e5e7eb',
                borderRadius: '8px'
              }}
            />
            <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-600 mt-4">
          Система NLP классифицирует каждую ошибку для персонализированных рекомендаций
        </p>
      </div>
    </div>
  );
}
