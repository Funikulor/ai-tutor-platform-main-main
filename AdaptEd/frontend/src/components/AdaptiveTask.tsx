import React, { useState, useEffect, useRef } from 'react';
import { CheckCircle, XCircle, Brain, Clock, Zap, AlertCircle, Sparkles } from 'lucide-react';
import api from '../services/api';

// Сохраняем задание между переключениями вкладок
const savedTaskState = {
  task: null as Task | null,
  submitted: false,
  result: null as any,
  userAnswer: '',
  useThematic: false
};

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
  isThematic?: boolean;
}

// Функция для преобразования текста с математическими формулами в JSX
const formatMathText = (text: string): React.ReactElement[] => {
  // Сначала обрабатываем LaTeX
  let cleaned = text
    .replace(/\\\(/g, '')
    .replace(/\\\)/g, '')
    .replace(/\\\[/g, '')
    .replace(/\\\]/g, '')
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)')
    .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
    .replace(/\\sqrt\[([^\]]+)\]\{([^}]+)\}/g, 'корень $1 степени из ($2)')
    .replace(/\^\{([^}]+)\}/g, '^$1')
    .replace(/\^(\d+)/g, (match, num) => {
      const superscripts: { [key: string]: string } = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
      };
      return superscripts[num] || `^${num}`;
    })
    .replace(/\{|\}/g, '')
    // Заменяем * на символ умножения (но не в URL или других контекстах)
    .replace(/(\d+|\w+)\s*\*\s*(\d+|\w+)/g, (match, left, right, offset, string) => {
      // Проверяем, не является ли это частью URL или другого контекста
      const before = offset > 0 ? string[offset - 1] : ' ';
      const after = offset + match.length < string.length ? string[offset + match.length] : ' ';
      if (before === ':' || after === ':') {
        return match; // Не заменяем в URL
      }
      return `${left} · ${right}`;
    });
  
  // Обрабатываем дроби - ищем все паттерны вида: (выражение) / (выражение) или (выражение) / число или число / (выражение)
  const parts: (string | React.ReactElement)[] = [];
  let lastIndex = 0;
  
  // Улучшенный паттерн для дробей - используем универсальный паттерн, который находит все дроби
  // Ищем: (любое выражение) / (любое выражение) или число / число или (выражение) / число
  // Паттерн ищет все возможные комбинации: (a)/b, a/(b), (a)/(b), a/b
  const fractionPattern = /(\([^()]+\)|[a-zA-Z]?\d+[a-zA-Z]*|\d+)\s*\/\s*(\([^()]+\)|[a-zA-Z]?\d+[a-zA-Z]*|\d+)/g;
  
  const matches: Array<{index: number, length: number, numerator: string, denominator: string}> = [];
  let match;
  
  // Ищем все дроби в тексте
  while ((match = fractionPattern.exec(cleaned)) !== null) {
    let numerator = match[1].trim();
    let denominator = match[2].trim();
    
    // Пропускаем, если это часть URL или другого контекста
    const beforeChar = match.index > 0 ? cleaned[match.index - 1] : ' ';
    const afterChar = match.index + match[0].length < cleaned.length 
      ? cleaned[match.index + match[0].length] 
      : ' ';
    
    if (beforeChar === ':' || afterChar === ':') {
      continue;
    }
    
    // Убираем скобки, если они есть (но сохраняем содержимое)
    if (numerator.startsWith('(') && numerator.endsWith(')')) {
      numerator = numerator.slice(1, -1).trim();
    }
    if (denominator.startsWith('(') && denominator.endsWith(')')) {
      denominator = denominator.slice(1, -1).trim();
    }
    
    if (numerator && denominator) {
      // Проверяем, не пересекается ли с уже найденными дробями
      const overlaps = matches.some(m => {
        const matchStart = match.index;
        const matchEnd = match.index + match[0].length;
        const mStart = m.index;
        const mEnd = m.index + m.length;
        return (matchStart >= mStart && matchStart < mEnd) ||
               (mStart >= matchStart && mStart < matchEnd);
      });
      
      if (!overlaps) {
        matches.push({
          index: match.index,
          length: match[0].length,
          numerator: numerator,
          denominator: denominator
        });
      }
    }
  }
  
  // Выделяем числа в тексте (кроме тех, что уже в дробях)
  const numberPattern = /\b\d+\b/g;
  const numberMatches: Array<{index: number, length: number, value: string}> = [];
  let numMatch;
  
  while ((numMatch = numberPattern.exec(cleaned)) !== null) {
    // Проверяем, не входит ли число в уже найденную дробь
    const inFraction = matches.some(frac => 
      numMatch.index >= frac.index && numMatch.index < frac.index + frac.length
    );
    
    if (!inFraction) {
      numberMatches.push({
        index: numMatch.index,
        length: numMatch[0].length,
        value: numMatch[0]
      });
    }
  }
  
  // Объединяем дроби и числа, сортируем по позиции
  const allElements = [
    ...matches.map(m => ({ ...m, type: 'fraction' as const })),
    ...numberMatches.map(m => ({ ...m, type: 'number' as const }))
  ].sort((a, b) => a.index - b.index);
  
  // Строим результат
  if (allElements.length === 0) {
    return [<span key="text">{cleaned}</span>];
  }
  
  allElements.forEach((element, idx) => {
    // Добавляем текст до элемента
    if (element.index > lastIndex) {
      parts.push(cleaned.substring(lastIndex, element.index));
    }
    
    if (element.type === 'fraction') {
      const frac = element as typeof matches[0];
      // Создаем визуальную дробь
      parts.push(
        <span 
          key={`frac-${idx}`} 
          className="inline-flex flex-col items-center mx-1 my-0.5" 
          style={{ 
            verticalAlign: 'middle',
            lineHeight: '1.2',
            fontSize: '1em',
            display: 'inline-flex'
          }}
        >
          <span 
            className="text-base leading-none border-b-2 border-gray-800 pb-0.5 px-1 font-semibold text-center"
            style={{ minHeight: '1.2em', display: 'block', fontWeight: '600' }}
          >
            {frac.numerator}
          </span>
          <span 
            className="text-base leading-none mt-0.5 px-1 text-center font-semibold"
            style={{ minHeight: '1.2em', display: 'block', fontWeight: '600' }}
          >
            {frac.denominator}
          </span>
        </span>
      );
      lastIndex = frac.index + frac.length;
    } else {
      // Выделяем число жирным
      const num = element as typeof numberMatches[0];
      parts.push(
        <strong key={`num-${idx}`} className="font-semibold" style={{ fontWeight: '600' }}>
          {num.value}
        </strong>
      );
      lastIndex = num.index + num.length;
    }
  });
  
  // Добавляем оставшийся текст
  if (lastIndex < cleaned.length) {
    parts.push(cleaned.substring(lastIndex));
  }
  
  return parts.map((part, index) => 
    typeof part === 'string' ? <span key={`text-${index}`}>{part}</span> : part
  );
};

// Функция для красивого форматирования объяснения
const formatExplanation = (text: string): React.ReactElement[] => {
  if (!text) return [<span key="empty">Подробное объяснение решения будет добавлено позже.</span>];
  
  // Очищаем от markdown более тщательно
  let cleaned = text
    .replace(/\*\*([^*]+)\*\*/g, '$1') // **текст** -> текст
    .replace(/#{1,6}\s*/g, '') // Убираем заголовки ###
    .replace(/---+/g, '') // Убираем ---
    .replace(/`([^`]+)`/g, '$1') // `код` -> код
    .replace(/\*\s+/g, '• ') // Списки * -> •
    .replace(/\*\*/g, '') // Убираем оставшиеся **
    .replace(/###/g, '') // Убираем ###
    .replace(/#/g, '') // Убираем #
    .replace(/`/g, '') // Убираем обратные кавычки
    .replace(/\n{3,}/g, '\n\n') // Убираем лишние пустые строки
    .trim();
  
  // Разбиваем на строки
  const lines = cleaned.split('\n').filter(line => line.trim());
  
  if (lines.length === 0) {
    return [<span key="empty">Подробное объяснение решения будет добавлено позже.</span>];
  }
  
  const parts: React.ReactElement[] = [];
  
  lines.forEach((line, index) => {
    const trimmedLine = line.trim();
    
    // Пропускаем пустые строки
    if (!trimmedLine) return;
    
    // Обрабатываем шаги с эмодзи или номерами
    const stepMatch = trimmedLine.match(/^(🔹|📝|✅|✓|•|Шаг\s*\d+|Step\s*\d+)[:.\s]*(.+)$/i);
    if (stepMatch) {
      const emoji = stepMatch[1].match(/[🔹📝✅✓•]/)?.[0] || '🔹';
      const stepText = stepMatch[2].trim();
      
      parts.push(
        <div key={`step-${index}`} className="mb-3 flex items-start gap-3">
          <span className="text-xl flex-shrink-0 mt-0.5">{emoji}</span>
          <span className="flex-1 text-gray-800 leading-relaxed">
            {formatMathText(stepText)}
          </span>
        </div>
      );
      return;
    }
    
    // Обрабатываем обычный текст
    if (trimmedLine.length > 0) {
      parts.push(
        <p key={`line-${index}`} className="mb-2 text-gray-800 leading-relaxed">
          {formatMathText(trimmedLine)}
        </p>
      );
    }
  });
  
  return parts.length > 0 ? parts : [<span key="fallback">{formatMathText(cleaned)}</span>];
};

export function AdaptiveTask({ onComplete }: { onComplete: (result: any) => void }) {
  // Восстанавливаем сохраненное состояние при монтировании
  const [currentTask, setCurrentTask] = useState<Task | null>(savedTaskState.task);
  const [userAnswer, setUserAnswer] = useState(savedTaskState.userAnswer);
  const [submitted, setSubmitted] = useState(savedTaskState.submitted);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(savedTaskState.result);
  const [startTime, setStartTime] = useState(Date.now());
  const [useThematic, setUseThematic] = useState(savedTaskState.useThematic);
  const [error, setError] = useState<string | null>(null);
  const hasInitialized = useRef(false);

  // Генерация задания через API
  const generateTask = async () => {
    try {
      setGenerating(true);
      setError(null);
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.post('/agents/generate-adaptive-task', {
        user_id: userId,
        use_thematic: useThematic
      });

      const taskData = response.data.task;
      
      // Преобразуем данные в нужный формат
      const task: Task = {
        id: taskData.id,
        topic: taskData.topic || 'Общая тема',
        difficulty: taskData.difficulty || 3,
        type: taskData.type || 'numeric',
        question: taskData.question,
        options: taskData.options,
        correctAnswer: taskData.correctAnswer,
        explanation: taskData.explanation,
        generatedVariant: taskData.generatedVariant || 1,
        isThematic: taskData.isThematic || useThematic
      };

      setCurrentTask(task);
      setUserAnswer('');
      setSubmitted(false);
      setResult(null);
      setStartTime(Date.now());
      
      // Очищаем сохраненное состояние при генерации нового задания
      savedTaskState.task = task;
      savedTaskState.submitted = false;
      savedTaskState.result = null;
      savedTaskState.userAnswer = '';
    } catch (err: any) {
      console.error('Error generating task:', err);
      setError(err.response?.data?.detail || 'Не удалось сгенерировать задание');
    } finally {
      setGenerating(false);
    }
  };

  // Сохраняем состояние при изменении
  useEffect(() => {
    savedTaskState.task = currentTask;
    savedTaskState.submitted = submitted;
    savedTaskState.result = result;
    savedTaskState.userAnswer = userAnswer;
    savedTaskState.useThematic = useThematic;
  }, [currentTask, submitted, result, userAnswer, useThematic]);

  // Генерируем задание только если его еще нет и это первая инициализация
  useEffect(() => {
    // Если задание уже есть (было сгенерировано ранее), не генерируем новое
    if (!currentTask && !generating && !hasInitialized.current) {
      hasInitialized.current = true;
      generateTask();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Генерируем только при первой загрузке, если задания еще нет

  const analyzeAnswer = async () => {
    if (!currentTask) return;

    setLoading(true);
    setError(null);
    
    try {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      const userId = localStorage.getItem('user_id');
      
      if (!userId) {
        throw new Error('User ID not found');
      }

      // Отправляем ответ на сервер для анализа и сохранения
      const response = await api.post('/agents/submit-task', {
        user_id: userId,
        task_id: currentTask.id,
        question: currentTask.question,
        user_answer: userAnswer,
        correct_answer: currentTask.correctAnswer,
        topic: currentTask.topic,
        time_spent_seconds: timeSpent
      });

      const isCorrect = response.data.is_correct || false;
      const errorAnalysis = response.data.error_analysis || null;
      const mentorMessage = response.data.mentor_message || null;

      const analysisResult = {
        correct: isCorrect,
        timeSpent,
        errorType: errorAnalysis?.type || null,
        errorAnalysis: errorAnalysis ? {
          type: errorAnalysis.type,
          topic: currentTask.topic,
          description: errorAnalysis.description || errorAnalysis.justification || 'Ошибка в решении',
          recommendation: errorAnalysis.suggested_remediation || `Изучите материалы по теме "${currentTask.topic}" в разделе рекомендаций.`
        } : null,
        explanation: currentTask.explanation,
        mentorMessage: mentorMessage?.message || null
      };

      setResult(analysisResult);
      setSubmitted(true);
      onComplete(analysisResult);
    } catch (err: any) {
      console.error('Error submitting task:', err);
      setError(err.response?.data?.detail || 'Не удалось отправить ответ');
      
      // Fallback: локальная проверка
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      const isCorrect = userAnswer.toLowerCase().trim() === currentTask.correctAnswer.toLowerCase().trim();
      
      const analysisResult = {
        correct: isCorrect,
        timeSpent,
        errorType: isCorrect ? null : 'unknown',
        errorAnalysis: isCorrect ? null : {
          type: 'unknown',
          topic: currentTask.topic,
          description: 'Не удалось проанализировать ошибку',
          recommendation: `Изучите материалы по теме "${currentTask.topic}"`
        },
        explanation: currentTask.explanation
      };

      setResult(analysisResult);
      setSubmitted(true);
      onComplete(analysisResult);
    } finally {
      setLoading(false);
    }
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

  if (generating || !currentTask) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4 animate-pulse" />
        <p className="text-gray-600">Генерация адаптивного задания...</p>
        {useThematic && (
          <p className="text-sm text-purple-600 mt-2">
            <Sparkles className="w-4 h-4 inline mr-1" />
            Создаю задание с интересной тематикой
          </p>
        )}
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
            {currentTask.isThematic && (
              <span className="px-3 py-1 bg-purple-50 text-purple-600 rounded-full text-sm">
                <Sparkles className="w-4 h-4 inline mr-1" />
                Тематическое
              </span>
            )}
            <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm">
              <Zap className="w-4 h-4 inline mr-1" />
              Вариант #{currentTask.generatedVariant}
            </span>
          </div>
        </div>

        {/* Тумблер для выбора стиля заданий */}
        <div className="flex items-center justify-between mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700">Стиль заданий:</span>
            <span className={`text-sm ${useThematic ? 'text-purple-600' : 'text-gray-500'}`}>
              {useThematic ? 'С тематикой и воображением' : 'Обычные задания'}
            </span>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useThematic}
              onChange={(e) => {
                setUseThematic(e.target.checked);
                // Тумблер не регенерирует задание - оно остается как есть
                // Новое задание будет сгенерировано только при нажатии "Следующее задание"
              }}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
          </label>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600 mt-4">
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

      {/* Error Message */}
      {error && (
        <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Task Content */}
      <div className="p-6">
        <div className="mb-6">
          <div className="text-gray-900 text-lg mb-4 whitespace-pre-wrap leading-relaxed">
            {formatMathText(currentTask.question)}
          </div>
          
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
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-600 mr-3 text-sm flex-shrink-0">
                    {String.fromCharCode(65 + index)}
                  </span>
                  <span className="leading-relaxed">{formatMathText(option)}</span>
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

                  {result.mentorMessage && (
                    <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-blue-900">
                        <strong>💬 Сообщение от наставника:</strong> {result.mentorMessage}
                      </p>
                    </div>
                  )}
                  
                  <div className="p-5 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-purple-200 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-2xl">💡</span>
                      <strong className="text-lg text-gray-900">Объяснение решения</strong>
                    </div>
                    <div className="text-gray-800 space-y-2">
                      {(() => {
                        // Сначала проверяем explanation из result
                        let explanation = result.explanation || currentTask?.explanation || '';
                        
                        // Если объяснение пустое или содержит только стандартные фразы, используем из currentTask
                        if (!explanation || !explanation.trim() || 
                            explanation.trim() === 'Решение задания' || 
                            explanation.trim() === 'Проверьте решение самостоятельно' ||
                            explanation.trim() === 'Подробное объяснение решения будет добавлено позже.') {
                          explanation = currentTask?.explanation || '';
                        }
                        
                        // Если все еще пустое, показываем сообщение
                        if (!explanation || !explanation.trim()) {
                          return (
                            <p className="text-gray-600 italic">
                              Подробное объяснение решения будет добавлено позже.
                            </p>
                          );
                        }
                        
                        return formatExplanation(explanation);
                      })()}
                    </div>
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
                className="flex-1 bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold"
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
              className="flex-1 bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 hover:shadow-lg transition-all font-semibold"
            >
              Следующее задание
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
