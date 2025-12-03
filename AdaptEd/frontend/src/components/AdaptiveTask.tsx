import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Brain, Clock, Zap, AlertCircle } from 'lucide-react';

interface Task {
  id: number;
  topic: string;
  difficulty: number;
  type: 'multiple-choice' | 'text' | 'numeric';
  question: string;
  options?: string[];
  correctAnswer: string;
  explanation: string;
  generatedVariant: number;
}

export function AdaptiveTask({ onComplete }: { onComplete: (result: any) => void }) {
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [startTime, setStartTime] = useState(Date.now());

  // Simulate adaptive task generation
  const generateTask = () => {
    const tasks: Task[] = [
      {
        id: 1,
        topic: 'Теорема Пифагора',
        difficulty: 3,
        type: 'numeric',
        question: 'Найдите длину гипотенузы прямоугольного треугольника, если катеты равны 3 см и 4 см.',
        correctAnswer: '5',
        explanation: 'По теореме Пифагора: c² = a² + b² = 3² + 4² = 9 + 16 = 25, следовательно c = 5 см',
        generatedVariant: 1
      },
      {
        id: 2,
        topic: 'Квадратные уравнения',
        difficulty: 4,
        type: 'multiple-choice',
        question: 'Решите уравнение: x² - 5x + 6 = 0',
        options: ['x₁ = 2, x₂ = 3', 'x₁ = 1, x₂ = 6', 'x₁ = -2, x₂ = -3', 'x₁ = 0, x₂ = 5'],
        correctAnswer: 'x₁ = 2, x₂ = 3',
        explanation: 'Используем формулу корней квадратного уравнения или разложение на множители: (x-2)(x-3) = 0',
        generatedVariant: 2
      },
      {
        id: 3,
        topic: 'Проценты',
        difficulty: 2,
        type: 'numeric',
        question: 'Товар стоил 2000 рублей. После скидки 15% его цена стала равна. Какова новая цена?',
        correctAnswer: '1700',
        explanation: 'Скидка: 2000 × 0.15 = 300 рублей. Новая цена: 2000 - 300 = 1700 рублей',
        generatedVariant: 3
      },
      {
        id: 4,
        topic: 'Линейные уравнения',
        difficulty: 2,
        type: 'text',
        question: 'Решите уравнение: 3x + 7 = 22. Объясните ход решения.',
        correctAnswer: '3x = 15, x = 5',
        explanation: 'Переносим 7 в правую часть: 3x = 22 - 7 = 15. Делим обе части на 3: x = 5',
        generatedVariant: 1
      }
    ];

    const randomTask = tasks[Math.floor(Math.random() * tasks.length)];
    setCurrentTask(randomTask);
    setUserAnswer('');
    setSubmitted(false);
    setResult(null);
    setStartTime(Date.now());
  };

  useEffect(() => {
    generateTask();
  }, []);

  const analyzeAnswer = () => {
    if (!currentTask) return;

    setLoading(true);
    
    // Simulate NLP analysis with delay
    setTimeout(() => {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      const isCorrect = userAnswer.toLowerCase().includes(currentTask.correctAnswer.toLowerCase());
      
      let errorType = null;
      let errorAnalysis = null;

      if (!isCorrect) {
        // Simulate error classification
        const errorTypes = ['conceptual', 'computational', 'typo'];
        errorType = errorTypes[Math.floor(Math.random() * errorTypes.length)];
        
        errorAnalysis = {
          type: errorType,
          topic: currentTask.topic,
          description: 
            errorType === 'conceptual' 
              ? `Концептуальная ошибка в понимании темы "${currentTask.topic}". Рекомендуется повторить базовые принципы.`
              : errorType === 'computational'
              ? `Вычислительная ошибка. Проверьте арифметические операции.`
              : `Опечатка или неточность в записи ответа.`,
          recommendation: `Изучите материалы по теме "${currentTask.topic}" в разделе рекомендаций.`
        };
      }

      const analysisResult = {
        correct: isCorrect,
        timeSpent,
        errorType,
        errorAnalysis,
        explanation: currentTask.explanation
      };

      setResult(analysisResult);
      setSubmitted(true);
      setLoading(false);
      onComplete(analysisResult);
    }, 1500);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (userAnswer.trim()) {
      analyzeAnswer();
    }
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 2) return 'text-green-600 bg-green-50';
    if (difficulty <= 3) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty <= 2) return 'Легкий';
    if (difficulty <= 3) return 'Средний';
    return 'Сложный';
  };

  if (!currentTask) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Генерация адаптивного задания...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Task Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-gray-900">Адаптивное задание</h3>
              <p className="text-sm text-gray-500">{currentTask.topic}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-sm ${getDifficultyColor(currentTask.difficulty)}`}>
              {getDifficultyLabel(currentTask.difficulty)}
            </span>
            <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">
              <Zap className="w-4 h-4 inline mr-1" />
              Вариант #{currentTask.generatedVariant}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>~5-7 мин</span>
          </div>
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>AI анализирует ответ с помощью NLP</span>
          </div>
        </div>
      </div>

      {/* Task Content */}
      <div className="p-6">
        <div className="mb-6">
          <p className="text-gray-900 text-lg mb-4">{currentTask.question}</p>
          
          {currentTask.type === 'multiple-choice' && currentTask.options && !submitted && (
            <div className="space-y-2">
              {currentTask.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => setUserAnswer(option)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    userAnswer === option
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-600 mr-3 text-sm">
                    {String.fromCharCode(65 + index)}
                  </span>
                  {option}
                </button>
              ))}
            </div>
          )}

          {(currentTask.type === 'numeric' || currentTask.type === 'text') && !submitted && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {currentTask.type === 'numeric' ? (
                <input
                  type="text"
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="Введите ответ (число)"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              ) : (
                <textarea
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  placeholder="Введите развернутый ответ с пояснением..."
                  rows={5}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              )}
            </form>
          )}

          {/* Result Display */}
          {submitted && result && (
            <div className={`p-6 rounded-lg border-2 ${
              result.correct 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-start gap-4">
                {result.correct ? (
                  <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-600 flex-shrink-0" />
                )}
                <div className="flex-1">
                  <h4 className={`text-lg mb-2 ${result.correct ? 'text-green-900' : 'text-red-900'}`}>
                    {result.correct ? 'Правильно!' : 'Неправильно'}
                  </h4>
                  
                  {!result.correct && result.errorAnalysis && (
                    <div className="mb-4 p-4 bg-white rounded-lg border border-red-200">
                      <p className="text-red-900 mb-2">
                        <strong>Анализ ошибки:</strong> {result.errorAnalysis.description}
                      </p>
                      <p className="text-red-700 text-sm">{result.errorAnalysis.recommendation}</p>
                    </div>
                  )}
                  
                  <div className="p-4 bg-white rounded-lg border border-gray-200">
                    <p className="text-gray-900">
                      <strong>Объяснение:</strong> {result.explanation}
                    </p>
                  </div>

                  <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Время: {result.timeSpent} сек
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          {!submitted ? (
            <>
              <button
                onClick={currentTask.type === 'multiple-choice' ? analyzeAnswer : handleSubmit}
                disabled={!userAnswer.trim() || loading}
                className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Brain className="w-5 h-5 animate-pulse" />
                    Анализ ответа...
                  </span>
                ) : (
                  'Отправить ответ'
                )}
              </button>
              <button
                onClick={generateTask}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
              >
                Другое задание
              </button>
            </>
          ) : (
            <button
              onClick={generateTask}
              className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              Следующее задание
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
