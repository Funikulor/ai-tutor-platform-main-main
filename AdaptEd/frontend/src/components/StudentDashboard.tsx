import { useState } from 'react';
import { KnowledgeGraph } from './KnowledgeGraph';
import { AdaptiveTask } from './AdaptiveTask';
import { ProgressStats } from './ProgressStats';
import { RecommendationPanel } from './RecommendationPanel';
import { ChatTab } from './ChatTab';
import { AIChatPanel } from './AIChatPanel';
import { LibraryTab } from './LibraryTab';
import { Brain, TrendingUp, Target, BookOpen, MessageCircle, Library } from 'lucide-react';

export function StudentDashboard() {
  const [currentView, setCurrentView] = useState<'overview' | 'task' | 'knowledge' | 'chat' | 'library'>('overview');
  const [lastError, setLastError] = useState<any>(null);
  const [isChatMinimized, setIsChatMinimized] = useState(false);
  const [selectedMaterialId, setSelectedMaterialId] = useState<string | undefined>(undefined);

  const handleMaterialClick = (materialId: string) => {
    setSelectedMaterialId(materialId);
    setCurrentView('library');
  };

  const studentProgress = {
    totalTopics: 24,
    completedTopics: 18,
    currentStreak: 7,
    totalPoints: 1250,
    averageAccuracy: 87,
    weakTopics: [
      { name: 'Теорема Пифагора', progress: 45, errors: 8 },
      { name: 'Квадратные уравнения', progress: 62, errors: 5 },
      { name: 'Тригонометрия', progress: 38, errors: 12 }
    ],
    recentActivities: [
      { date: '2025-11-29', topic: 'Линейные уравнения', score: 92, time: 15 },
      { date: '2025-11-28', topic: 'Проценты', score: 88, time: 12 },
      { date: '2025-11-27', topic: 'Дроби', score: 95, time: 10 }
    ]
  };

  const handleTaskComplete = (result: any) => {
    if (!result.correct) {
      setLastError(result.analysis);
    }
  };

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 flex">
        <button
          onClick={() => setCurrentView('overview')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'overview'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <TrendingUp className="w-5 h-5 inline mr-2" />
          Обзор прогресса
        </button>
        <button
          onClick={() => setCurrentView('task')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'task'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Target className="w-5 h-5 inline mr-2" />
          Адаптивные задания
        </button>
        <button
          onClick={() => setCurrentView('knowledge')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'knowledge'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Brain className="w-5 h-5 inline mr-2" />
          Граф знаний
        </button>
        <button
          onClick={() => setCurrentView('library')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'library'
              ? 'bg-orange-50 text-orange-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Library className="w-5 h-5 inline mr-2" />
          Библиотека
        </button>
        <button
          onClick={() => setCurrentView('chat')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'chat'
              ? 'bg-purple-50 text-purple-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <MessageCircle className="w-5 h-5 inline mr-2" />
          AI Помощник
        </button>
      </div>

      {/* Quick Stats */}
      {currentView === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100">Изучено тем</p>
                <p className="text-3xl mt-2">{studentProgress.completedTopics}/{studentProgress.totalTopics}</p>
              </div>
              <BookOpen className="w-12 h-12 text-blue-200 opacity-80" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100">Точность</p>
                <p className="text-3xl mt-2">{studentProgress.averageAccuracy}%</p>
              </div>
              <Target className="w-12 h-12 text-green-200 opacity-80" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100">Дней подряд</p>
                <p className="text-3xl mt-2">{studentProgress.currentStreak}</p>
              </div>
              <TrendingUp className="w-12 h-12 text-purple-200 opacity-80" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100">Баллы</p>
                <p className="text-3xl mt-2">{studentProgress.totalPoints}</p>
              </div>
              <Brain className="w-12 h-12 text-orange-200 opacity-80" />
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {currentView === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ProgressStats progress={studentProgress} />
          </div>
          <div>
            <RecommendationPanel error={lastError} onMaterialClick={handleMaterialClick} />
          </div>
        </div>
      )}

      {currentView === 'task' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <AdaptiveTask onComplete={handleTaskComplete} />
          </div>
          <div>
            <RecommendationPanel error={lastError} onMaterialClick={handleMaterialClick} />
          </div>
        </div>
      )}

      {currentView === 'knowledge' && (
        <div>
          <KnowledgeGraph />
        </div>
      )}

      {currentView === 'library' && (
        <div>
          <LibraryTab selectedMaterialId={selectedMaterialId} />
        </div>
      )}

      {currentView === 'chat' && (
        <div>
          <ChatTab />
        </div>
      )}

      {/* Floating Chat Button (only visible when not on chat tab) */}
      {currentView !== 'chat' && (
        <AIChatPanel 
          isMinimized={isChatMinimized}
          onToggleMinimize={() => setIsChatMinimized(!isChatMinimized)}
        />
      )}
    </div>
  );
}
