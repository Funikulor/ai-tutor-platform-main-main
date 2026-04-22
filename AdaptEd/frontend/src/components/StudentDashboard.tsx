import { useState, useEffect } from 'react';
import { AdaptiveTask } from './AdaptiveTask';
import { ProgressStats } from './ProgressStats';
import { RecommendationPanel } from './RecommendationPanel';
import { ChatTab } from './ChatTab';
import { AIChatPanel } from './AIChatPanel';
import { LibraryTab } from './LibraryTab';
import { HomeworkTab } from './HomeworkTab';
import { Brain, TrendingUp, Target, BookOpen, MessageCircle, Library, ClipboardCheck } from 'lucide-react';
import api from '../services/api';

interface ProgressData {
  totalTopics: number;
  completedTopics: number;
  studiedTopics?: number;
  masteredTopics?: number;
  currentStreak: number;
  totalPoints: number;
  earnedPoints?: number;
  maxPoints?: number;
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
    earned_points?: number;
    max_points?: number;
  }>;
}

export function StudentDashboard() {
  const [currentView, setCurrentView] = useState<'overview' | 'task' | 'chat' | 'library' | 'homework'>('overview');
  const [lastError, setLastError] = useState<any>(null);
  const [isChatMinimized, setIsChatMinimized] = useState(false);
  const [selectedMaterialId, setSelectedMaterialId] = useState<string | undefined>(undefined);
  const [studentProgress, setStudentProgress] = useState<ProgressData>({
    totalTopics: 0,
    completedTopics: 0,
    studiedTopics: 0,
    masteredTopics: 0,
    currentStreak: 0,
    totalPoints: 0,
    earnedPoints: 0,
    maxPoints: 0,
    averageAccuracy: 0,
    weakTopics: [],
    recentActivities: []
  });
  const [weeklyData, setWeeklyData] = useState<Array<{day: string; score: number; tasks: number}>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProgressData();
  }, []);

  const loadProgressData = async () => {
    try {
      setLoading(true);
      setError(null);
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.get(`/progress/${userId}`);
      const data = response.data;

      if (data.progress) {
        setStudentProgress(data.progress);
      }
      if (data.weeklyData) {
        setWeeklyData(data.weeklyData);
      }
    } catch (err: any) {
      console.error('Error loading progress data:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить данные прогресса');
      // Используем значения по умолчанию при ошибке
      setStudentProgress({
        totalTopics: 0,
        completedTopics: 0,
        studiedTopics: 0,
        masteredTopics: 0,
        currentStreak: 0,
        totalPoints: 0,
        earnedPoints: 0,
        maxPoints: 0,
        averageAccuracy: 0,
        weakTopics: [],
        recentActivities: []
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMaterialClick = (materialId: string) => {
    setSelectedMaterialId(materialId);
    setCurrentView('library');
  };

  const handleTaskComplete = (result: any) => {
    if (!result.correct) {
      setLastError(result.analysis);
    }
    // Обновляем данные прогресса после выполнения задания
    loadProgressData();
  };

  const handleStudyComplete = (topic: string) => {
    // Обновляем прогресс после изучения материала
    loadProgressData();
  };
  
  // Обработка навигации к заданиям из MaterialViewer
  useEffect(() => {
    const handleNavigateToTasks = (event: CustomEvent) => {
      const topic = event.detail?.topic;
      if (topic) {
        setCurrentView('task');
        // Можно сохранить тему для генерации заданий
        localStorage.setItem('selectedTopic', topic);
      }
    };
    
    window.addEventListener('navigateToTasks', handleNavigateToTasks as EventListener);
    return () => {
      window.removeEventListener('navigateToTasks', handleNavigateToTasks as EventListener);
    };
  }, []);

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
          onClick={() => setCurrentView('homework')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'homework'
              ? 'bg-green-50 text-green-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <ClipboardCheck className="w-5 h-5 inline mr-2" />
          Домашка
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
        <>
          {loading && (
            <div className="text-center py-8">
              <p className="text-gray-500">Загрузка данных...</p>
            </div>
          )}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-600">{error}</p>
            </div>
          )}
          {!loading && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100">Изучено тем</p>
                    <p className="text-3xl mt-2">{studentProgress.studiedTopics ?? studentProgress.completedTopics}</p>
                    <p className="text-xs mt-2 text-blue-100">
                      Освоено: {studentProgress.masteredTopics ?? 0}
                    </p>
                  </div>
                  <BookOpen className="w-12 h-12 text-blue-200 opacity-80" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100">Точность</p>
                    <p className="text-3xl mt-2">{studentProgress.averageAccuracy.toFixed(1)}%</p>
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
                    <p className="text-3xl mt-2">{studentProgress.earnedPoints ?? 0}/{studentProgress.maxPoints ?? 0}</p>
                    <p className="text-xs mt-2 text-orange-100">
                      Внутренние очки профиля: {studentProgress.totalPoints}
                    </p>
                  </div>
                  <Brain className="w-12 h-12 text-orange-200 opacity-80" />
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Main Content Area */}
      {currentView === 'overview' && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ProgressStats progress={studentProgress} weeklyData={weeklyData} />
          </div>
          <div>
            <RecommendationPanel error={lastError} onMaterialClick={handleMaterialClick} />
          </div>
        </div>
      )}

      {currentView === 'task' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <AdaptiveTask 
              key="adaptive-task" 
              onComplete={handleTaskComplete}
            />
          </div>
          <div>
            <RecommendationPanel error={lastError} onMaterialClick={handleMaterialClick} />
          </div>
        </div>
      )}

      {currentView === 'library' && (
        <div>
          <LibraryTab 
            selectedMaterialId={selectedMaterialId} 
            onStudyComplete={handleStudyComplete}
          />
        </div>
      )}

      {currentView === 'homework' && (
        <div>
          <HomeworkTab />
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
          viewerRole="student"
        />
      )}
    </div>
  );
}
