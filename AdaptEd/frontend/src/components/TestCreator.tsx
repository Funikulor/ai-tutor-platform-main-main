import { useState } from 'react';
import { Plus, Wand2, Trash2, Save, Eye, Copy, Download } from 'lucide-react';

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

export function TestCreator() {
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

  // Генерация тестов с помощью AI
  const handleGenerate = () => {
    const topics = generateSettings.topic.split(',').map(t => t.trim());
    const generatedQuestions: Question[] = [];

    for (let i = 0; i < generateSettings.questionCount; i++) {
      const topic = topics[i % topics.length];
      const questionTypes: Question['type'][] = ['single', 'multiple', 'text', 'numeric'];
      const type = questionTypes[Math.floor(Math.random() * questionTypes.length)];

      let question: Question = {
        id: `q-${Date.now()}-${i}`,
        type,
        question: `Сгенерированный вопрос ${i + 1} по теме "${topic}"`,
        points: generateSettings.difficulty === 'easy' ? 5 : generateSettings.difficulty === 'medium' ? 10 : 15,
      };

      if (type === 'single' || type === 'multiple') {
        question.options = [
          `Вариант ответа A для "${topic}"`,
          `Вариант ответа B для "${topic}"`,
          `Вариант ответа C для "${topic}"`,
          `Вариант ответа D для "${topic}"`
        ];
        question.correctAnswer = type === 'single' ? question.options[0] : [question.options[0], question.options[1]];
      } else if (type === 'numeric') {
        question.correctAnswer = Math.floor(Math.random() * 100);
      } else {
        question.correctAnswer = `Пример правильного ответа для вопроса по теме "${topic}"`;
      }

      if (generateSettings.includeExplanations) {
        question.explanation = `Объяснение: это автоматически сгенерированное объяснение для вопроса по теме "${topic}".`;
      }

      generatedQuestions.push(question);
    }

    setTest({
      ...test,
      title: `Тест: ${generateSettings.topic}`,
      description: `Автоматически сгенерированный тест по теме "${generateSettings.topic}"`,
      questions: generatedQuestions
    });
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

  const saveTest = () => {
    console.log('Сохранение теста:', test);
    alert(`Тест "${test.title}" успешно сохранен!\n\nВопросов: ${test.questions.length}\nОбщий балл: ${test.questions.reduce((sum, q) => sum + q.points, 0)}`);
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
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Plus className="w-4 h-4" />
              Создать вручную
            </button>
            <button
              onClick={() => setMode('generate')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                mode === 'generate' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Wand2 className="w-4 h-4" />
              Генерировать AI
            </button>
          </div>
        </div>
      </div>

      {/* Test Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Настройки теста</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-700 mb-2">Название теста</label>
            <input
              type="text"
              value={test.title}
              onChange={(e) => setTest({ ...test, title: e.target.value })}
              placeholder="Например: Контрольная работа по алгебре"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-2">Предмет</label>
            <select
              value={test.subject}
              onChange={(e) => setTest({ ...test, subject: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
            <label className="block text-sm text-gray-700 mb-2">Класс</label>
            <select
              value={test.grade}
              onChange={(e) => setTest({ ...test, grade: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {[5, 6, 7, 8, 9, 10, 11].map(grade => (
                <option key={grade} value={grade}>{grade} класс</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-2">Сложность</label>
            <select
              value={test.difficulty}
              onChange={(e) => setTest({ ...test, difficulty: e.target.value as Test['difficulty'] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="easy">Легкий</option>
              <option value="medium">Средний</option>
              <option value="hard">Сложный</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-700 mb-2">Описание</label>
            <textarea
              value={test.description}
              onChange={(e) => setTest({ ...test, description: e.target.value })}
              placeholder="Краткое описание теста и его целей"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-2">Время на выполнение</label>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="noTimeLimit"
                  checked={noTimeLimit}
                  onChange={(e) => setNoTimeLimit(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <label htmlFor="noTimeLimit" className="text-sm text-gray-700">
                  Без ограничения времени
                </label>
              </div>
              {!noTimeLimit && (
                <input
                  type="number"
                  value={test.timeLimit}
                  onChange={(e) => setTest({ ...test, timeLimit: parseInt(e.target.value) || 0 })}
                  min="1"
                  placeholder="Минуты"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              )}
            </div>
          </div>
        </div>
      </div>

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
          <button
            onClick={handleGenerate}
            className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all flex items-center justify-center gap-2"
          >
            <Wand2 className="w-4 h-4" />
            Сгенерировать вопросы
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
              <button className="px-4 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-2">
                <Copy className="w-4 h-4" />
                Дублировать
              </button>
              <button className="px-4 py-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200 transition-colors flex items-center gap-2">
                <Download className="w-4 h-4" />
                Экспорт
              </button>
              <button
                onClick={saveTest}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Сохранить тест
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
                    <span className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0">
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

