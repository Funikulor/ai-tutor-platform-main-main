import { useState, useEffect, useCallback } from 'react';
import { AIChatPanel } from './AIChatPanel';
import { AICharacter } from './AICharacter';
import { motion } from 'motion/react';
import { Sparkles, MessageCircle, Lightbulb, Heart } from 'lucide-react';
import api from '../services/api';

export function ChatTab() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [chatProgress, setChatProgress] = useState({
    questionsAsked: 0,
    topicsStudied: 0
  });
  const [loadingProgress, setLoadingProgress] = useState(true);

  const getQuestionsCount = useCallback(() => {
    const savedMessages = localStorage.getItem('ai_chat_messages');
    if (!savedMessages) return 0;
    try {
      const messages = JSON.parse(savedMessages);
      return messages.filter((msg: any) => msg.sender === 'user').length;
    } catch {
      return 0;
    }
  }, []);

  useEffect(() => {
    const loadChatProgress = async () => {
      try {
        const userId = localStorage.getItem('user_id');
        if (!userId) {
          setLoadingProgress(false);
          return;
        }

        const questionsCount = getQuestionsCount();

        // Получаем количество изученных тем из API
        try {
          const progressResponse = await api.get(`/progress/${userId}`);
          const progressData = progressResponse.data;
          const topicsStudied = progressData.progress?.completedTopics || 
                                Object.keys(progressData.progress?.topicMastery || {}).filter(
                                  (topic: string) => progressData.progress?.topicMastery?.[topic] >= 0.7
                                ).length || 0;

          setChatProgress({
            questionsAsked: questionsCount,
            topicsStudied: topicsStudied
          });
        } catch {
          setChatProgress({
            questionsAsked: questionsCount,
            topicsStudied: 0
          });
        }
      } catch {
        // Ignore
      } finally {
        setLoadingProgress(false);
      }
    };

    loadChatProgress();

    const handleMessagesUpdate = () => {
      const questionsCount = getQuestionsCount();
      setChatProgress((prev) => ({ ...prev, questionsAsked: questionsCount }));
    };

    window.addEventListener('storage', handleMessagesUpdate);
    window.addEventListener('ai-chat-updated', handleMessagesUpdate as EventListener);
    // Редкий fallback, если браузер блокирует события
    const interval = setInterval(handleMessagesUpdate, 10000);

    return () => {
      window.removeEventListener('storage', handleMessagesUpdate);
      window.removeEventListener('ai-chat-updated', handleMessagesUpdate as EventListener);
      clearInterval(interval);
    };
  }, [getQuestionsCount]);

  // Обработчик клика по популярной теме
  const handleTopicClick = (topic: string) => {
    // Отправляем сообщение через глобальное событие
    const event = new CustomEvent('chat-send-message', { detail: { message: `Расскажи про ${topic.toLowerCase()}` } });
    window.dispatchEvent(event);
  };

  const features = [
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: 'Задавай любые вопросы',
      description: 'Я помогу с домашними заданиями, объясню сложные темы простым языком'
    },
    {
      icon: <Lightbulb className="w-6 h-6" />,
      title: 'Учись интересно',
      description: 'Превращу учебу в увлекательное приключение с примерами из жизни'
    },
    {
      icon: <Heart className="w-6 h-6" />,
      title: 'Всегда поддержу',
      description: 'Не бойся ошибаться - вместе мы разберемся в любой теме!'
    }
  ];

  return (
    <div className="h-[calc(100vh-12rem)] flex gap-6">
      {/* Left Sidebar - Welcome & Info */}
      {showWelcome && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="w-80 space-y-6"
        >
          {/* AI Character Showcase */}
          <div className="bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl p-6 text-white">
            <div className="flex flex-col items-center text-center">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <AICharacter size="large" emotion="excited" />
              </motion.div>
              <h2 className="text-white mt-4 mb-2">Познакомься с AI-помощником!</h2>
              <p className="text-purple-100 text-sm">
                Я здесь, чтобы помочь тебе учиться весело и легко! 🌟
              </p>
            </div>
          </div>

          {/* Features */}
          <div className="bg-white rounded-2xl shadow-sm border-2 border-purple-200 p-6 space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h3 className="text-gray-900">Что я умею:</h3>
            </div>
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2 }}
                className="flex gap-3 p-3 bg-purple-50 rounded-xl"
              >
                <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-purple-500 flex-shrink-0 shadow-sm">
                  {feature.icon}
                </div>
                <div>
                  <h4 className="text-gray-900 text-sm mb-1">{feature.title}</h4>
                  <p className="text-xs text-gray-600">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Tips */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-6 border-2 border-yellow-200">
            <h3 className="text-gray-900 mb-3">💡 Советы для общения:</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-yellow-500 mt-0.5">•</span>
                <span>Задавай вопросы своими словами - я пойму!</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-500 mt-0.5">•</span>
                <span>Не стесняйся переспрашивать, если непонятно</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-yellow-500 mt-0.5">•</span>
                <span>Делись своими мыслями - нет неправильных вопросов!</span>
              </li>
            </ul>
          </div>

          {/* Hide Welcome Button */}
          <button
            onClick={() => setShowWelcome(false)}
            className="w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Скрыть информацию →
          </button>
        </motion.div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 relative">
        {!showWelcome && (
          <button
            onClick={() => setShowWelcome(true)}
            className="absolute -left-12 top-4 w-10 h-10 bg-white rounded-full shadow-md border-2 border-purple-200 flex items-center justify-center hover:bg-purple-50 transition-colors z-10"
            title="Показать информацию"
          >
            <Sparkles className="w-5 h-5 text-purple-500" />
          </button>
        )}
        
        <div className="h-full">
          <AIChatPanel fullscreen={true} />
        </div>
      </div>

      {/* Right Sidebar - Recent Topics & Quick Actions */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-72 space-y-6"
      >
        {/* Quick Topics */}
        <div className="bg-white rounded-2xl shadow-sm border-2 border-purple-200 p-6">
          <h3 className="text-gray-900 mb-4">🎯 Популярные темы</h3>
          <div className="space-y-2">
            {[
              { emoji: '🔢', topic: 'Математика', count: 156 },
              { emoji: '📚', topic: 'Русский язык', count: 142 },
              { emoji: '🌍', topic: 'География', count: 98 },
              { emoji: '⚗️', topic: 'Химия', count: 87 },
              { emoji: '🎨', topic: 'Искусство', count: 65 }
            ].map((item, index) => (
              <button
                key={index}
                onClick={() => handleTopicClick(item.topic)}
                className="w-full p-3 bg-purple-50 hover:bg-purple-100 rounded-xl transition-all text-left flex items-center justify-between group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{item.emoji}</span>
                  <span className="text-sm text-gray-800 group-hover:text-purple-700">
                    {item.topic}
                  </span>
                </div>
                <span className="text-xs text-gray-500">{item.count}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Your Progress */}
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200">
          <h3 className="text-gray-900 mb-4">📊 Твой прогресс в чате</h3>
          {loadingProgress ? (
            <div className="text-center py-4">
              <p className="text-sm text-gray-500">Загрузка...</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">Задано вопросов</span>
                  <span className="text-green-700 font-semibold">{chatProgress.questionsAsked}</span>
                </div>
                <div className="h-2 bg-white rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-300" 
                    style={{ width: `${Math.min((chatProgress.questionsAsked / 100) * 100, 100)}%` }} 
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">Изучено тем</span>
                  <span className="text-green-700 font-semibold">{chatProgress.topicsStudied}</span>
                </div>
                <div className="h-2 bg-white rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all duration-300" 
                    style={{ width: `${Math.min((chatProgress.topicsStudied / 20) * 100, 100)}%` }} 
                  />
                </div>
              </div>
              <div className="pt-3 border-t border-green-200">
                <p className="text-xs text-gray-600 text-center">
                  {chatProgress.questionsAsked === 0 && chatProgress.topicsStudied === 0
                    ? 'Начни задавать вопросы! 💪'
                    : 'Продолжай в том же духе! 🌟'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Fun Fact */}
        <motion.div
          animate={{ 
            boxShadow: [
              '0 4px 6px rgba(59, 130, 246, 0.1)',
              '0 8px 16px rgba(59, 130, 246, 0.2)',
              '0 4px 6px rgba(59, 130, 246, 0.1)'
            ]
          }}
          transition={{ duration: 3, repeat: Infinity }}
          className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl p-6 border-2 border-blue-200"
        >
          <div className="text-center">
            <div className="text-4xl mb-2">🧠</div>
            <h4 className="text-gray-900 mb-2">Знаешь ли ты?</h4>
            <p className="text-sm text-gray-700">
              Задавая вопросы, ты активируешь больше нейронных связей в мозге, что помогает лучше запоминать информацию!
            </p>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
