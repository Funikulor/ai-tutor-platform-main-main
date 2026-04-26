import { useState, useEffect } from 'react';
import { Plus, Wand2, Trash2, Save, Eye, Copy, Download, Loader2 } from 'lucide-react';
import { generateTest, createManualTest, updateTest } from '../services/tests';
import api from '../services/api';
import { toast } from 'sonner';

interface Question {
  id: string;
  type: 'single' | 'multiple' | 'text' | 'numeric';
  question: string;
  points: number;
  options?: string[];
  correctAnswer?: string | string[] | number;
  explanation?: string;
}

interface Test {
  title: string;
  description: string;
  subject: string;
  grade: string;
  difficulty: 'easy' | 'medium' | 'hard';
  timeLimit: number;
  questions: Question[];
}

interface TestCreatorProps {
  onSaved?: () => void;
}

export function TestCreator({ onSaved }: TestCreatorProps) {
  const [mode, setMode] = useState<'create' | 'generate'>('create');
  const [test, setTest] = useState<Test>({
    title: '',
    description: '',
    subject: 'Математика',
    grade: '9',
    difficulty: 'medium',
    timeLimit: 45,
    questions: []
  });

  const [generateSettings, setGenerateSettings] = useState({
    topic: '',
    questionCount: 10,
    difficulty: 'medium' as 'easy' | 'medium' | 'hard',
    includeExplanations: true
  });

  const [showPreview, setShowPreview] = useState(false);
  const [noTimeLimit, setNoTimeLimit] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [students, setStudents] = useState<Array<{user_id: string; full_name: string}>>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');
  const [isAdaptive, setIsAdaptive] = useState(false);
  const [savedTestId, setSavedTestId] = useState<number | null>(null);

  // Загружаем список учеников при монтировании
  useEffect(() => {
    const loadStudents = async () => {
      try {
        const response = await api.get('/all');
        const allUsers = response.data || [];
        const studentsList = allUsers
          .filter((u: any) => u.role === 'student')
          .map((u: any) => ({ user_id: u.user_id, full_name: u.full_name || u.email || u.user_id }));
        setStudents(studentsList);
      } catch (error) {
        console.error('Ошибка загрузки учеников:', error);
      }
    };
    loadStudents();
  }, []);

  // Генерация тестов с помощью AI
  const handleGenerate = async () => {
    if (!generateSettings.topic.trim()) {
      alert('Пожалуйста, укажите тему для генерации');
      return;
    }

    setIsGenerating(true);
    try {
      const creatorId = localStorage.getItem('user_id') || undefined;
      const topics = generateSettings.topic.split(',').map(t => t.trim()).join(', ');
      
      const testData = await generateTest({
        topic: topics,
        difficulty: generateSettings.difficulty,
        question_count: generateSettings.questionCount,
        creator_id: creatorId,
        user_id: isAdaptive && selectedStudentId ? selectedStudentId : undefined,
        subject: test.subject,
        grade: test.grade,
        include_explanations: generateSettings.includeExplanations,
      });

      // Конвертируем вопросы из API в формат компонента
      const convertedQuestions: Question[] = (testData.questions || []).map((q: any, index: number) => {
        const questionType = q.question_type || (q.options && q.options.length > 1 ? 'single' : 'text');
        let correctAnswer: string | string[] | number;
        
        if (questionType === 'single' || questionType === 'multiple') {
          if (questionType === 'multiple' && Array.isArray(q.correct_index)) {
            correctAnswer = q.correct_index.map((idx: number) => q.options[idx]);
          } else {
            correctAnswer = q.options[q.correct_index] || q.options[0];
          }
        } else if (questionType === 'numeric') {
          correctAnswer = parseFloat(q.options[0] || '0');
        } else {
          correctAnswer = q.options[0] || '';
        }

        return {
          id: `q-${q.id || index}`,
          type: questionType as Question['type'],
          question: q.question,
          points: generateSettings.difficulty === 'easy' ? 5 : generateSettings.difficulty === 'medium' ? 10 : 15,
          options: q.options || [],
          correctAnswer,
          explanation: q.explanation,
        };
      });

      const topicLabel = (testData.topic || topics || '').trim();
      setTest({
        ...test,
        title: testData.title || `Тест: ${topics}`,
        description: topicLabel || test.description,
        questions: convertedQuestions
      });
      
      setSavedTestId(testData.id);
      onSaved?.();
      toast.success(`Тест сгенерирован: ${convertedQuestions.length} вопросов`, { duration: 5000 });
    } catch (error: any) {
      console.error('Ошибка генерации теста:', error);
      
      // Извлекаем сообщение об ошибке из разных форматов
      let errorMessage = 'Неизвестная ошибка';
      
      if (error?.response?.data) {
        const data = error.response.data;
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
        } else {
          errorMessage = JSON.stringify(data);
        }
      } else if (error?.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      alert(`Ошибка генерации теста: ${errorMessage}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const addQuestion = () => {
    const newQuestion: Question = {
      id: `q-${Date.now()}`,
      type: 'single',
      question: '',
      points: 10,
      options: ['', '', '', ''],
      correctAnswer: ''
    };
    setTest({ ...test, questions: [...test.questions, newQuestion] });
  };

  const updateQuestion = (id: string, updates: Partial<Question>) => {
    setTest({
      ...test,
      questions: test.questions.map(q => q.id === id ? { ...q, ...updates } : q)
    });
  };

  const deleteQuestion = (id: string) => {
    setTest({
      ...test,
      questions: test.questions.filter(q => q.id !== id)
    });
  };

  const updateQuestionOption = (questionId: string, optionIndex: number, value: string) => {
    setTest({
      ...test,
      questions: test.questions.map(q => {
        if (q.id === questionId && q.options) {
          const newOptions = [...q.options];
          newOptions[optionIndex] = value;
          return { ...q, options: newOptions };
        }
        return q;
      })
    });
  };

  const saveTest = async () => {
    if (!test.title.trim()) {
      alert('Пожалуйста, укажите название теста');
      return;
    }
    if (test.questions.length === 0) {
      alert('Добавьте хотя бы один вопрос');
      return;
    }

    try {
      const creatorId = localStorage.getItem('user_id') || undefined;
      
      // Конвертируем вопросы в формат API
      const apiQuestions = test.questions.map(q => {
        const options = q.options || [];
        let correctIndex = 0;
        let correctAnswer: string | number | string[] | number[] | undefined = undefined;

        if (q.type === 'single') {
          const singleAnswer = String(q.correctAnswer || '');
          correctIndex = Math.max(0, options.findIndex(opt => opt === singleAnswer));
          correctAnswer = [correctIndex];
        } else if (q.type === 'multiple') {
          const multipleAnswers = Array.isArray(q.correctAnswer) ? q.correctAnswer as string[] : [];
          const indexes = multipleAnswers
            .map(answer => options.findIndex(opt => opt === answer))
            .filter(idx => idx >= 0);
          correctIndex = indexes[0] ?? 0;
          correctAnswer = indexes;
        } else if (q.type === 'numeric') {
          correctAnswer = Number(q.correctAnswer || 0);
        } else {
          correctAnswer = String(q.correctAnswer || '');
        }

        return {
          question: q.question,
          options: q.type === 'single' || q.type === 'multiple' ? options : [String(q.correctAnswer || '')],
          correct_index: correctIndex,
          question_type: q.type,
          correct_answer: correctAnswer,
          explanation: q.explanation,
          points: q.points,
        };
      });

      if (savedTestId != null) {
        // Обновляем уже существующий тест (например, сгенерированный или открытый для редактирования)
        await updateTest(savedTestId, {
          title: test.title,
          topic: test.description || test.subject,
          difficulty: test.difficulty,
          questions: apiQuestions,
        });
        onSaved?.();
        toast.success(
          `Тест «${test.title}» сохранён. Вопросов: ${test.questions.length}, баллов: ${test.questions.reduce((sum, q) => sum + q.points, 0)}`,
          { duration: 5000 }
        );
      } else {
        const testData = await createManualTest({
          title: test.title,
          topic: test.description || test.subject,
          difficulty: test.difficulty,
          creator_id: creatorId,
          questions: apiQuestions,
        });
        setSavedTestId(testData.id);
        onSaved?.();
        toast.success(
          `Тест «${test.title}» создан. Вопросов: ${test.questions.length}, баллов: ${test.questions.reduce((sum, q) => sum + q.points, 0)}`,
          { duration: 5000 }
        );
      }
    } catch (error: any) {
      console.error('Ошибка сохранения теста:', error);
      
      // Извлекаем сообщение об ошибке из разных форматов
      let errorMessage = 'Неизвестная ошибка';
      
      if (error?.response?.data) {
        const data = error.response.data;
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
        } else {
          errorMessage = JSON.stringify(data);
        }
      } else if (error?.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      alert(`Ошибка сохранения теста: ${errorMessage}`);
    }
  };

  const duplicateTest = () => {
    const duplicatedTest = {
      ...test,
      title: `${test.title} (копия)`,
      questions: test.questions.map(q => ({
        ...q,
        id: `q-${Date.now()}-${Math.random()}`,
      })),
    };
    setTest(duplicatedTest);
    setSavedTestId(null);
    alert('Тест продублирован! Вы можете отредактировать его и сохранить как новый.');
  };

  const exportTest = () => {
    const exportData = {
      title: test.title,
      description: test.description,
      subject: test.subject,
      grade: test.grade,
      difficulty: test.difficulty,
      timeLimit: noTimeLimit ? null : test.timeLimit,
      questions: test.questions.map(q => ({
        type: q.type,
        question: q.question,
        points: q.points,
        options: q.options,
        correctAnswer: q.correctAnswer,
        explanation: q.explanation,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${test.title.replace(/[^a-z0-9]/gi, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    alert('Тест экспортирован в JSON файл!');
  };

  const totalPoints = test.questions.reduce((sum, q) => sum + q.points, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-gray-900">Создание тестов</h2>
            <p className="text-gray-600">Создавайте тесты вручную или генерируйте с помощью AI</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setMode('create')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                mode === 'create' 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Plus className="w-4 h-4" />
              Создать вручную
            </button>
            <button
              onClick={() => setMode('generate')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                mode === 'generate' 
                  ? 'bg-purple-600 text-white shadow-md' 
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Wand2 className="w-4 h-4" />
              Генерировать AI
            </button>
          </div>
        </div>
      </div>

      {/* Ручной режим: полные настройки */}
      {mode === 'create' && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-1 text-gray-900">Настройки теста</h3>
          <p className="mb-4 text-sm text-gray-500">Заполняются до добавления вопросов и сохранения</p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm text-gray-700">Название теста</label>
              <input
                type="text"
                value={test.title}
                onChange={(e) => setTest({ ...test, title: e.target.value })}
                placeholder="Например: Контрольная работа по алгебре"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm text-gray-700">Предмет</label>
              <select
                value={test.subject}
                onChange={(e) => setTest({ ...test, subject: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              >
                <option value="Математика">Математика</option>
                <option value="Физика">Физика</option>
                <option value="Химия">Химия</option>
                <option value="Русский язык">Русский язык</option>
                <option value="Литература">Литература</option>
                <option value="История">История</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm text-gray-700">Класс</label>
              <select
                value={test.grade}
                onChange={(e) => setTest({ ...test, grade: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              >
                {[5, 6, 7, 8, 9, 10, 11].map((grade) => (
                  <option key={grade} value={grade}>
                    {grade} класс
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm text-gray-700">Сложность</label>
              <select
                value={test.difficulty}
                onChange={(e) => setTest({ ...test, difficulty: e.target.value as Test['difficulty'] })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              >
                <option value="easy">Легкий</option>
                <option value="medium">Средний</option>
                <option value="hard">Сложный</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="mb-2 block text-sm text-gray-700">Описание</label>
              <textarea
                value={test.description}
                onChange={(e) => setTest({ ...test, description: e.target.value })}
                placeholder="Краткое описание теста и его целей"
                rows={3}
                className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm text-gray-700">Время на выполнение</label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="noTimeLimit"
                    checked={noTimeLimit}
                    onChange={(e) => setNoTimeLimit(e.target.checked)}
                    className="h-4 w-4 rounded text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <label htmlFor="noTimeLimit" className="text-sm text-gray-700">
                    Без ограничения времени
                  </label>
                </div>
                {!noTimeLimit && (
                  <input
                    type="number"
                    value={test.timeLimit}
                    onChange={(e) => setTest({ ...test, timeLimit: parseInt(e.target.value, 10) || 0 })}
                    min="1"
                    placeholder="Минуты"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Режим AI: только то, что уходит в запрос генерации */}
      {mode === 'generate' && (
        <div className="rounded-xl border border-purple-200 bg-gradient-to-br from-purple-50/80 to-white p-6 shadow-sm">
          <h3 className="text-gray-900">Контекст для AI</h3>
          <p className="mt-1 text-sm text-gray-600">
            Предмет и класс передаются в генератор вместе с темами ниже. Название, описание, сложность в каталоге и время на тест появятся{' '}
            <strong>после</strong> генерации вопросов — их можно уточнить перед сохранением.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Предмет</label>
              <select
                value={test.subject}
                onChange={(e) => setTest({ ...test, subject: e.target.value })}
                className="w-full rounded-lg border border-purple-200 bg-white px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
              >
                <option value="Математика">Математика</option>
                <option value="Физика">Физика</option>
                <option value="Химия">Химия</option>
                <option value="Русский язык">Русский язык</option>
                <option value="Литература">Литература</option>
                <option value="История">История</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Класс</label>
              <select
                value={test.grade}
                onChange={(e) => setTest({ ...test, grade: e.target.value })}
                className="w-full rounded-lg border border-purple-200 bg-white px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
              >
                {[5, 6, 7, 8, 9, 10, 11].map((grade) => (
                  <option key={grade} value={grade}>
                    {grade} класс
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* AI Generation Panel */}
      {mode === 'generate' && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border border-purple-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Wand2 className="w-6 h-6 text-purple-600" />
            <h3 className="text-gray-900">AI Генерация вопросов</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm text-gray-700 mb-2">Темы (через запятую)</label>
              <input
                type="text"
                value={generateSettings.topic}
                onChange={(e) => setGenerateSettings({ ...generateSettings, topic: e.target.value })}
                placeholder="Теорема Пифагора, Квадратные уравнения"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-2">Количество вопросов</label>
              <input
                type="number"
                value={generateSettings.questionCount}
                onChange={(e) => setGenerateSettings({ ...generateSettings, questionCount: parseInt(e.target.value) || 1 })}
                min="1"
                max="50"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-700 mb-2">Сложность вопросов</label>
              <select
                value={generateSettings.difficulty}
                onChange={(e) => setGenerateSettings({ ...generateSettings, difficulty: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="easy">Легкие</option>
                <option value="medium">Средние</option>
                <option value="hard">Сложные</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="includeExplanations"
                checked={generateSettings.includeExplanations}
                onChange={(e) => setGenerateSettings({ ...generateSettings, includeExplanations: e.target.checked })}
                className="w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
              />
              <label htmlFor="includeExplanations" className="text-sm text-gray-700">
                Включить объяснения к ответам
              </label>
            </div>
          </div>
          
          {/* Адаптивная генерация */}
          <div className="mb-4 p-4 bg-white rounded-lg border border-purple-200">
            <div className="flex items-center gap-2 mb-3">
              <input
                type="checkbox"
                id="isAdaptive"
                checked={isAdaptive}
                onChange={(e) => {
                  setIsAdaptive(e.target.checked);
                  if (!e.target.checked) setSelectedStudentId('');
                }}
                className="w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
              />
              <label htmlFor="isAdaptive" className="text-sm font-semibold text-gray-900">
                Адаптивная генерация (под слабые темы и интересы ученика)
              </label>
            </div>
            {isAdaptive && (
              <div>
                <label className="block text-sm text-gray-700 mb-2">Выберите ученика:</label>
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">-- Выберите ученика --</option>
                  {students.map((student) => (
                    <option key={student.user_id} value={student.user_id}>
                      {student.full_name}
                    </option>
                  ))}
                </select>
                {selectedStudentId && (
                  <p className="mt-2 text-xs text-gray-600">
                    Тест будет сгенерирован с учетом слабых тем и интересов выбранного ученика
                  </p>
                )}
              </div>
            )}
          </div>
          
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full px-4 py-2 text-white rounded-lg transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: 'linear-gradient(to right, rgb(147, 51, 234), rgb(59, 130, 246))'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'linear-gradient(to right, rgb(126, 34, 206), rgb(37, 99, 235))';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'linear-gradient(to right, rgb(147, 51, 234), rgb(59, 130, 246))';
            }}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Генерация вопросов...
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4" />
                Сгенерировать вопросы
              </>
            )}
          </button>
        </div>
      )}

      {/* Questions List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-gray-900">Вопросы теста ({test.questions.length})</h3>
            <p className="text-sm text-gray-600">Общий балл: {totalPoints} баллов</p>
          </div>
          {mode === 'create' && (
            <button
              onClick={addQuestion}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Добавить вопрос
            </button>
          )}
        </div>

        <div className="space-y-4">
          {test.questions.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <p className="text-gray-500">
                {mode === 'generate' 
                  ? 'Настройте параметры и нажмите "Сгенерировать вопросы"' 
                  : 'Добавьте первый вопрос для начала создания теста'}
              </p>
            </div>
          ) : (
            test.questions.map((question, index) => (
              <div key={question.id} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
                        Вопрос {index + 1}
                      </span>
                      <select
                        value={question.type}
                        onChange={(e) => updateQuestion(question.id, { type: e.target.value as Question['type'] })}
                        className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="single">Один вариант</option>
                        <option value="multiple">Несколько вариантов</option>
                        <option value="text">Текстовый ответ</option>
                        <option value="numeric">Числовой ответ</option>
                      </select>
                      <input
                        type="number"
                        value={question.points}
                        onChange={(e) => updateQuestion(question.id, { points: parseInt(e.target.value) || 0 })}
                        className="w-20 px-2 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                        placeholder="Баллы"
                      />
                      <span className="text-sm text-gray-600">баллов</span>
                    </div>
                    <textarea
                      value={question.question}
                      onChange={(e) => updateQuestion(question.id, { question: e.target.value })}
                      placeholder="Введите текст вопроса"
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none mb-3"
                    />

                    {/* Options for single/multiple choice */}
                    {(question.type === 'single' || question.type === 'multiple') && question.options && (
                      <div className="space-y-2">
                        <p className="text-sm text-gray-700">Варианты ответов:</p>
                        {question.options.map((option, optIndex) => (
                          <div key={optIndex} className="flex items-center gap-2">
                            <input
                              type={question.type === 'single' ? 'radio' : 'checkbox'}
                              name={`correct-${question.id}`}
                              checked={
                                question.type === 'single' 
                                  ? question.correctAnswer === option
                                  : Array.isArray(question.correctAnswer) && question.correctAnswer.includes(option)
                              }
                              onChange={() => {
                                if (question.type === 'single') {
                                  updateQuestion(question.id, { correctAnswer: option });
                                } else {
                                  const current = (question.correctAnswer as string[]) || [];
                                  const newAnswer = current.includes(option)
                                    ? current.filter(a => a !== option)
                                    : [...current, option];
                                  updateQuestion(question.id, { correctAnswer: newAnswer });
                                }
                              }}
                              className="w-4 h-4"
                            />
                            <input
                              type="text"
                              value={option}
                              onChange={(e) => updateQuestionOption(question.id, optIndex, e.target.value)}
                              placeholder={`Вариант ${optIndex + 1}`}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>
                        ))}
                        <p className="text-xs text-gray-500">Отметьте правильный(е) ответ(ы)</p>
                      </div>
                    )}

                    {/* Numeric answer */}
                    {question.type === 'numeric' && (
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">Правильный ответ:</label>
                        <input
                          type="number"
                          value={question.correctAnswer as number || ''}
                          onChange={(e) => updateQuestion(question.id, { correctAnswer: parseFloat(e.target.value) })}
                          placeholder="Введите числовой ответ"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    )}

                    {/* Text answer */}
                    {question.type === 'text' && (
                      <div>
                        <label className="block text-sm text-gray-700 mb-1">Примерный правильный ответ:</label>
                        <textarea
                          value={question.correctAnswer as string || ''}
                          onChange={(e) => updateQuestion(question.id, { correctAnswer: e.target.value })}
                          placeholder="Введите примерный ответ для проверки"
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                        />
                      </div>
                    )}

                    {/* Explanation */}
                    <div className="mt-3">
                      <label className="block text-sm text-gray-700 mb-1">Объяснение (необязательно):</label>
                      <textarea
                        value={question.explanation || ''}
                        onChange={(e) => updateQuestion(question.id, { explanation: e.target.value })}
                        placeholder="Добавьте объяснение правильного ответа"
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      />
                    </div>
                  </div>
                  <button
                    onClick={() => deleteQuestion(question.id)}
                    className="ml-4 px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* После AI-генерации: карточка теста перед сохранением (под вопросами, рядом с кнопкой «Сохранить») */}
      {mode === 'generate' && test.questions.length > 0 && (
        <div className="rounded-xl border border-purple-200 bg-white p-6 shadow-sm">
          <h3 className="text-gray-900">Оформление теста</h3>
          <p className="mt-1 text-sm text-gray-600">
            Уточните название и описание для каталога. Сложность здесь — для карточки сохранённого теста (отдельно от сложности вопросов при генерации).
          </p>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <label className="mb-2 block text-sm text-gray-700">Название теста</label>
              <input
                type="text"
                value={test.title}
                onChange={(e) => setTest({ ...test, title: e.target.value })}
                placeholder="Например: Контрольная по темам генерации"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm text-gray-700">Сложность (в каталоге тестов)</label>
              <select
                value={test.difficulty}
                onChange={(e) => setTest({ ...test, difficulty: e.target.value as Test['difficulty'] })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
              >
                <option value="easy">Легкий</option>
                <option value="medium">Средний</option>
                <option value="hard">Сложный</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm text-gray-700">Время на выполнение</label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="noTimeLimitAi"
                    checked={noTimeLimit}
                    onChange={(e) => setNoTimeLimit(e.target.checked)}
                    className="h-4 w-4 rounded text-purple-600 focus:ring-2 focus:ring-purple-500"
                  />
                  <label htmlFor="noTimeLimitAi" className="text-sm text-gray-700">
                    Без ограничения времени
                  </label>
                </div>
                {!noTimeLimit && (
                  <input
                    type="number"
                    value={test.timeLimit}
                    onChange={(e) => setTest({ ...test, timeLimit: parseInt(e.target.value, 10) || 0 })}
                    min="1"
                    placeholder="Минуты"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
                  />
                )}
              </div>
            </div>
            <div className="md:col-span-2">
              <label className="mb-2 block text-sm text-gray-700">Описание</label>
              <textarea
                value={test.description}
                onChange={(e) => setTest({ ...test, description: e.target.value })}
                placeholder="Краткое описание для себя и коллег"
                rows={2}
                className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      {test.questions.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="text-gray-900">
              <p>Тест готов к публикации</p>
              <p className="text-sm text-gray-600">
                {test.questions.length} вопросов • {totalPoints} баллов • {noTimeLimit ? 'Без ограничения времени' : `${test.timeLimit} минут`}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
              >
                <Eye className="w-4 h-4" />
                {showPreview ? 'Скрыть' : 'Предпросмотр'}
              </button>
              <button
                onClick={duplicateTest}
                className="px-4 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                Дублировать
              </button>
              <button
                onClick={exportTest}
                className="px-4 py-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200 transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Экспорт
              </button>
              {savedTestId != null && (
                <span className="text-sm text-gray-500">
                  Тест уже в списке — можно редактировать и сохранить изменения.
                </span>
              )}
              <button
                onClick={saveTest}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                {savedTestId != null ? 'Сохранить изменения' : 'Сохранить тест'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview */}
      {showPreview && test.questions.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Предпросмотр теста</h3>
          <div className="border border-gray-300 rounded-lg p-6 bg-gray-50">
            <div className="mb-6">
              <h2 className="text-2xl text-gray-900 mb-2">{test.title}</h2>
              <p className="text-gray-600 mb-2">{test.description}</p>
              <div className="flex gap-4 text-sm text-gray-600">
                <span>Предмет: {test.subject}</span>
                <span>Класс: {test.grade}</span>
                <span>Время: {noTimeLimit ? 'Без ограничения' : `${test.timeLimit} мин`}</span>
                <span>Всего баллов: {totalPoints}</span>
              </div>
            </div>
            <div className="space-y-6">
              {test.questions.map((question, index) => (
                <div key={question.id} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold leading-none text-white shadow-sm [text-shadow:0_1px_2px_rgba(0,0,0,0.35)]">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-gray-900">{question.question}</p>
                        <span className="text-sm text-gray-600">{question.points} б.</span>
                      </div>
                      {(question.type === 'single' || question.type === 'multiple') && question.options && (
                        <div className="space-y-2 mt-3">
                          {question.options.map((option, optIndex) => (
                            <div key={optIndex} className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200">
                              <input
                                type={question.type === 'single' ? 'radio' : 'checkbox'}
                                disabled
                                className="w-4 h-4"
                              />
                              <span className="text-gray-700">{option}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {question.type === 'text' && (
                        <textarea
                          disabled
                          placeholder="Текстовый ответ..."
                          rows={3}
                          className="mt-3 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg resize-none"
                        />
                      )}
                      {question.type === 'numeric' && (
                        <input
                          disabled
                          type="number"
                          placeholder="Числовой ответ..."
                          className="mt-3 w-48 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg"
                        />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}