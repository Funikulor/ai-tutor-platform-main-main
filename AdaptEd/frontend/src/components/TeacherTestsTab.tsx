import { useEffect, useState } from 'react';
import { PlusCircle, Loader2, Wand2, ListPlus } from 'lucide-react';
import {
  createManualTest,
  generateTest,
  listTests,
  getTest,
  deleteTest,
  ManualQuestion,
  TestDetail,
  TestSummary,
} from '../services/tests';

const DIFFICULTIES = [
  { value: 'easy', label: 'Легкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'hard', label: 'Сложный' },
];

export function TeacherTestsTab() {
  const [manualTitle, setManualTitle] = useState('');
  const [manualTopic, setManualTopic] = useState('');
  const [manualDifficulty, setManualDifficulty] = useState('medium');
  const [manualQuestions, setManualQuestions] = useState<ManualQuestion[]>([
    { question: '', options: ['', '', '', ''], correct_index: 0, explanation: '' },
  ]);
  const [genTopic, setGenTopic] = useState('');
  const [genDifficulty, setGenDifficulty] = useState('medium');
  const [genCount, setGenCount] = useState(5);
  const [loadingManual, setLoadingManual] = useState(false);
  const [loadingGen, setLoadingGen] = useState(false);
  const [genStatus, setGenStatus] = useState<string | null>(null);
  const [tests, setTests] = useState<TestSummary[]>([]);
  const [selectedTest, setSelectedTest] = useState<TestDetail | null>(null);
  const [errorManual, setErrorManual] = useState<string | null>(null);
  const [errorGen, setErrorGen] = useState<string | null>(null);

  const formatError = (e: any) => {
    const detail = e?.response?.data?.detail ?? e?.message ?? e;
    if (Array.isArray(detail)) {
      return detail.map((d) => (typeof d === 'string' ? d : d?.msg || '')).filter(Boolean).join('; ') || 'Не удалось выполнить запрос';
    }
    if (typeof detail === 'object') {
      return detail?.msg || JSON.stringify(detail);
    }
    return detail || 'Не удалось выполнить запрос';
  };

  const creatorId = localStorage.getItem('user_id') || 'admin_001';

  const loadTests = async () => {
    try {
      // сначала пробуем с фильтром
      let data = await listTests({ creator_id: creatorId || undefined });
      // если пришло пусто — пробуем без фильтра
      if (!data || data.length === 0) {
        data = await listTests();
      }
      setTests(data);
      // авто-выбор последнего теста (если есть)
      if (data.length > 0) {
        const last = data[data.length - 1];
        handleSelectTest(last.id);
      } else {
        // не трогаем selectedTest, если он уже есть, чтобы не терять только что созданный
        if (!selectedTest) {
          setSelectedTest(null);
        }
      }
      return data;
    } catch (e: any) {
      const msg = formatError(e) || 'Не удалось загрузить тесты';
      setErrorManual(msg);
      setErrorGen(msg);
      return [];
    }
  };

  const handleSelectTest = async (id: number) => {
    try {
      const full = await getTest(id);
      setSelectedTest(full);
    } catch (e: any) {
      const msg = formatError(e) || 'Не удалось загрузить тест';
      setErrorManual(msg);
      setErrorGen(msg);
    }
  };

  const handleDeleteTest = async (id: number) => {
    if (!confirm('Удалить тест?')) return;
    try {
      await deleteTest(id);
      setSelectedTest(null);
      await loadTests();
    } catch (e: any) {
      const msg = formatError(e) || 'Не удалось удалить тест';
      setErrorManual(msg);
      setErrorGen(msg);
    }
  };

  useEffect(() => {
    loadTests();
  }, []);

  const addQuestion = () => {
    setManualQuestions((prev) => [...prev, { question: '', options: ['', '', '', ''], correct_index: 0, explanation: '' }]);
  };

  const updateQuestion = (idx: number, field: keyof ManualQuestion, value: any) => {
    setManualQuestions((prev) =>
      prev.map((q, i) =>
        i === idx
          ? {
              ...q,
              [field]: value,
            }
          : q
      )
    );
  };

  const updateOption = (qIdx: number, optIdx: number, value: string) => {
    setManualQuestions((prev) =>
      prev.map((q, i) =>
        i === qIdx
          ? {
              ...q,
              options: q.options.map((o, oi) => (oi === optIdx ? value : o)),
            }
          : q
      )
    );
  };

  const handleCreateManual = async () => {
    if (!manualTitle.trim() || manualQuestions.some((q) => !q.question.trim())) {
      setErrorManual('Заполните заголовок и тексты вопросов');
      return;
    }
    setErrorManual(null);
    setLoadingManual(true);
    try {
      const test = await createManualTest({
        title: manualTitle,
        topic: manualTopic || undefined,
        difficulty: manualDifficulty,
        creator_id: creatorId,
        questions: manualQuestions,
      });
      setSelectedTest(test);
      await loadTests();
    } catch (e: any) {
      setErrorManual(formatError(e) || 'Не удалось создать тест');
    } finally {
      setLoadingManual(false);
    }
  };

  const handleGenerate = async () => {
    const topic = genTopic.trim();
    const payload = {
      topic,
      difficulty: genDifficulty || 'medium',
      question_count: genCount || 5,
      creator_id: creatorId || undefined,
      user_id: creatorId || undefined,
    };
    if (!payload.topic) {
      setErrorGen('Укажите тему для генерации');
      return;
    }
    setErrorGen(null);
    setGenStatus('Отправляем запрос на генерацию...');
    setLoadingGen(true);
    try {
      console.log('[tests] generate payload', payload);
      const test = await generateTest(payload);
      console.log('[tests] generate response', test);
      let savedTest = test as any;

      // Если бэкенд вернул сырой объект без id, пробуем сами сохранить через /tests/manual
      if (!savedTest || !savedTest.id) {
        const genQuestions = (savedTest?.questions || []) as any[];
        const manualQuestions: ManualQuestion[] = genQuestions.map((q) => ({
          question: q.question || '',
          options: q.options || [],
          correct_index:
            typeof q.correct_index === 'number'
              ? q.correct_index
              : typeof q.correct_answer === 'number'
              ? q.correct_answer
              : 0,
          explanation: q.explanation,
        }));
        if (manualQuestions.length > 0) {
          try {
            console.log('[tests] fallback saving manual test');
            const manualSaved = await createManualTest({
              title: savedTest?.title || payload.topic || 'Сгенерированный тест',
              topic: savedTest?.topic || payload.topic,
              difficulty: savedTest?.difficulty || payload.difficulty,
              creator_id: payload.creator_id,
              questions: manualQuestions,
            });
            savedTest = manualSaved;
            console.log('[tests] fallback saved manual', manualSaved);
          } catch (err) {
            console.log('[tests] fallback manual save error', err);
          }
        }
      }

      const data = await loadTests();
      if (savedTest && savedTest.id) {
        setSelectedTest(savedTest);
        setGenStatus(`Сгенерировано: ${savedTest?.title || payload.topic}`);
      } else if (data && data.length > 0) {
        const last = data[data.length - 1];
        setSelectedTest(last as any);
        setGenStatus(`Сгенерировано и сохранено: ${last.title || payload.topic}`);
      } else {
        setErrorGen('Сервис вернул пустой ответ, тест не сохранён');
        setGenStatus('Ответ без теста');
      }
    } catch (e: any) {
      setErrorGen(formatError(e) || 'Не удалось сгенерировать тест');
      setGenStatus('Ошибка при генерации (см. сообщение выше)');
    } finally {
      setLoadingGen(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ListPlus className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Тесты</h2>
        </div>
        <button
          onClick={loadTests}
          className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          Обновить список
        </button>
      </div>

      {errorManual && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{errorManual}</div>}
      {errorGen && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{errorGen}</div>}
      {genStatus && <div className="p-2 bg-blue-50 text-blue-700 rounded-lg text-xs">{genStatus}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Manual creation */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-gray-900 font-semibold">
            <PlusCircle className="w-4 h-4 text-blue-600" />
            Создать тест вручную
          </div>
          <input
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
            placeholder="Заголовок"
            value={manualTitle}
            onChange={(e) => setManualTitle(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              placeholder="Тема (опционально)"
              value={manualTopic}
              onChange={(e) => setManualTopic(e.target.value)}
            />
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={manualDifficulty}
              onChange={(e) => setManualDifficulty(e.target.value)}
            >
              {DIFFICULTIES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            {manualQuestions.map((q, qi) => (
              <div key={qi} className="border border-gray-200 rounded-lg p-3 space-y-2 bg-gray-50">
                <input
                  className="w-full border border-gray-200 rounded px-2 py-1 text-sm"
                  placeholder={`Вопрос ${qi + 1}`}
                  value={q.question}
                  onChange={(e) => updateQuestion(qi, 'question', e.target.value)}
                />
                <div className="grid grid-cols-2 gap-2">
                  {q.options.map((opt, oi) => (
                    <div key={oi} className="flex items-center gap-2">
                      <input
                        className="flex-1 border border-gray-200 rounded px-2 py-1 text-sm"
                        placeholder={`Вариант ${oi + 1}`}
                        value={opt}
                        onChange={(e) => updateOption(qi, oi, e.target.value)}
                      />
                      <input
                        type="radio"
                        name={`correct-${qi}`}
                        checked={q.correct_index === oi}
                        onChange={() => updateQuestion(qi, 'correct_index', oi)}
                      />
                    </div>
                  ))}
                </div>
                <input
                  className="w-full border border-gray-200 rounded px-2 py-1 text-sm"
                  placeholder="Объяснение (опционально)"
                  value={q.explanation || ''}
                  onChange={(e) => updateQuestion(qi, 'explanation', e.target.value)}
                />
              </div>
            ))}
            <button
              onClick={addQuestion}
              className="inline-flex items-center gap-2 text-sm text-blue-600"
            >
              <PlusCircle className="w-4 h-4" />
              Добавить вопрос
            </button>
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleCreateManual}
              disabled={loadingManual}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 inline-flex items-center gap-2"
            >
              {loadingManual ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
              Создать
            </button>
          </div>
        </div>

        {/* AI generation (расширенный блок, если нужно настроить) */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center gap-2 text-gray-900 font-semibold">
            <Wand2 className="w-4 h-4 text-purple-600" />
            Сгенерировать тест (расширенные настройки)
          </div>
          <input
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
            placeholder="Тема"
            value={genTopic}
            onChange={(e) => setGenTopic(e.target.value)}
          />
          <div className="grid grid-cols-2 gap-2">
            <select
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={genDifficulty}
              onChange={(e) => setGenDifficulty(e.target.value)}
            >
              {DIFFICULTIES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={1}
              max={20}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
              value={genCount}
              onChange={(e) => setGenCount(Number(e.target.value))}
            />
          </div>
          {/* Кнопка генерации отдельно, всегда видима */}
          <div className="flex justify-end pt-2">
            <button
              onClick={handleGenerate}
              disabled={loadingGen}
              className="px-4 py-2 bg-purple-600 text-white border border-purple-600 rounded-lg hover:bg-purple-700 transition disabled:opacity-50 inline-flex items-center gap-2"
              style={{ backgroundColor: '#7c3aed', color: '#fff', borderColor: '#6d28d9' }}
            >
              {loadingGen ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              Сгенерировать
            </button>
          </div>
        </div>
      </div>

      {/* Tests list */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
        <div className="flex items-center gap-2 text-gray-900 font-semibold">
          <ListPlus className="w-4 h-4 text-gray-700" />
          Список тестов (созданные/сгенерированные)
        </div>
        {tests.length === 0 && <div className="text-sm text-gray-600">Пока нет тестов</div>}
        <div className="space-y-2">
          {tests.map((t) => (
            <div
              key={t.id}
              className="p-3 border border-gray-200 rounded-lg flex items-center justify-between hover:bg-gray-50 cursor-pointer"
              onClick={() => handleSelectTest(t.id)}
            >
              <div>
                <div className="text-gray-900 font-semibold">{t.title}</div>
                <div className="text-xs text-gray-500">
                  Тема: {t.topic || '—'} • Сложность: {t.difficulty || '—'} • Источник: {t.source || '—'}
                </div>
              </div>
              <div className="text-xs text-gray-500">{t.created_at ? new Date(t.created_at).toLocaleString('ru-RU') : ''}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Selected test */}
      {selectedTest && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-gray-900 font-semibold">Тест: {selectedTest.title}</div>
            <button
              onClick={() => selectedTest?.id && handleDeleteTest(selectedTest.id)}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Удалить
            </button>
          </div>
          <div className="text-xs text-gray-500">
            Тема: {selectedTest.topic || '—'} • Сложность: {selectedTest.difficulty || '—'} • Источник: {selectedTest.source || '—'}
          </div>
          <div className="space-y-2">
            {selectedTest.questions?.map((q, idx) => (
              <div key={q.id || idx} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="text-sm text-gray-900 mb-1">{idx + 1}. {q.question}</div>
                <ul className="text-sm text-gray-700 list-disc pl-5 space-y-1">
                  {q.options.map((opt, oi) => (
                    <li key={oi} className={oi === q.correct_index ? 'text-green-700' : ''}>
                      {opt} {oi === q.correct_index ? '(правильный)' : ''}
                    </li>
                  ))}
                </ul>
                {q.explanation && <div className="text-xs text-gray-600 mt-1">Объяснение: {q.explanation}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

