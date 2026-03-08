import { useEffect, useMemo, useState } from 'react';
import { Eye, Loader2, ListPlus, Save, Send, Trash2 } from 'lucide-react';
import api from '../services/api';
import {
  getTestSubmission,
  listTests,
  getTest,
  deleteTest,
  updateTest,
  assignTestAsHomework,
  listTestSubmissions,
  ManualQuestion,
  TestSubmissionDetail,
  TestDetail,
  TestSummary,
} from '../services/tests';
import { toast } from 'sonner';
import { TestCreator } from './TestCreator';

type AssignmentType = 'homework' | 'control' | 'quiz';

interface StudentUser {
  user_id: string;
  full_name: string;
}

interface TeacherTestsTabProps {
  preselectedStudentId?: string | null;
}

export function TeacherTestsTab({ preselectedStudentId = null }: TeacherTestsTabProps) {
  const creatorId = localStorage.getItem('user_id') || '';

  const [tests, setTests] = useState<TestSummary[]>([]);
  const [selectedTest, setSelectedTest] = useState<TestDetail | null>(null);
  const [editQuestions, setEditQuestions] = useState<ManualQuestion[]>([]);
  const [students, setStudents] = useState<StudentUser[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);
  const [assignmentType, setAssignmentType] = useState<AssignmentType>('homework');
  const [dueDate, setDueDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [submissions, setSubmissions] = useState<Array<{
    id: number;
    user_id: string;
    score: number;
    correct_count?: number;
    total_questions?: number;
    summary?: string;
    feedback?: string;
    created_at?: string;
  }>>([]);
  const [selectedSubmission, setSelectedSubmission] = useState<TestSubmissionDetail | null>(null);
  const [submissionLoading, setSubmissionLoading] = useState<number | null>(null);

  const [editTitle, setEditTitle] = useState('');
  const [editTopic, setEditTopic] = useState('');
  const [editDifficulty, setEditDifficulty] = useState('');

  const studentNameById = useMemo(() => {
    const map: Record<string, string> = {};
    students.forEach((s) => {
      map[s.user_id] = s.full_name;
    });
    return map;
  }, [students]);

  const loadTests = async () => {
    setLoading(true);
    try {
      let data = await listTests({ creator_id: creatorId || undefined });
      if (!data.length) {
        data = await listTests();
      }
      setTests(data);
      if (data.length && !selectedTest) {
        await handleSelectTest(data[0].id);
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Не удалось загрузить тесты');
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async () => {
    try {
      const response = await api.get('/all');
      const allUsers = Array.isArray(response.data) ? response.data : [];
      const list = allUsers
        .filter((u: any) => u.role === 'student')
        .map((u: any) => ({
          user_id: u.user_id,
          full_name: u.full_name || u.email || u.user_id,
        }));
      setStudents(list);
    } catch {
      // no-op
    }
  };

  const handleSelectTest = async (id: number) => {
    try {
      const full = await getTest(id);
      setSelectedTest(full);
      setEditTitle(full.title || '');
      setEditTopic(full.topic || '');
      setEditDifficulty(full.difficulty || 'medium');
      setEditQuestions(
        full.questions.map((q) => ({
          question: q.question,
          options: [...q.options],
          correct_index: q.correct_index,
          question_type: q.question_type || 'single',
          correct_answer: q.correct_answer,
          explanation: q.explanation,
        }))
      );
      const subs = await listTestSubmissions(id);
      setSubmissions(subs);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Не удалось загрузить тест');
    }
  };

  const handleSave = async () => {
    if (!selectedTest) return;
    setSaving(true);
    try {
      const normalizedQuestions = editQuestions.map((question) => ({
        ...question,
        question_type: question.question_type || 'single',
        correct_answer:
          question.question_type === 'single'
            ? [question.correct_index]
            : question.question_type === 'multiple'
            ? (Array.isArray(question.correct_answer) ? question.correct_answer : [question.correct_index])
            : question.question_type === 'numeric'
            ? Number(question.correct_answer ?? 0)
            : String(question.correct_answer ?? question.options?.[0] ?? ''),
      }));
      const updated = await updateTest(selectedTest.id, {
        title: editTitle.trim() || selectedTest.title,
        topic: editTopic || undefined,
        difficulty: editDifficulty || undefined,
        questions: normalizedQuestions,
      });
      setSelectedTest(updated);
      setEditQuestions(
        updated.questions.map((q) => ({
          question: q.question,
          options: [...q.options],
          correct_index: q.correct_index,
          question_type: q.question_type || 'single',
          correct_answer: q.correct_answer,
          explanation: q.explanation,
        }))
      );
      setTests((prev) =>
        prev.map((t) =>
          t.id === updated.id
            ? { ...t, title: updated.title, topic: updated.topic, difficulty: updated.difficulty }
            : t
        )
      );
      toast.success('Тест обновлен');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Не удалось сохранить изменения');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedTest) return;
    if (!confirm('Удалить тест?')) return;
    try {
      await deleteTest(selectedTest.id);
      setSelectedTest(null);
      setSubmissions([]);
      await loadTests();
      toast.success('Тест удален');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Не удалось удалить тест');
    }
  };

  const toggleStudent = (id: string) => {
    setSelectedStudentIds((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]));
  };

  const handleAssign = async () => {
    if (!selectedTest) return;
    if (!selectedStudentIds.length) {
      toast.error('Выберите хотя бы одного ученика');
      return;
    }
    setAssigning(true);
    try {
      const result = await assignTestAsHomework(
        selectedTest.id,
        selectedStudentIds,
        dueDate ? new Date(dueDate).toISOString() : undefined,
        assignmentType
      );
      toast.success(`Назначено: ${result.assigned_count}`);
      setSelectedStudentIds([]);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Не удалось назначить тест');
    } finally {
      setAssigning(false);
    }
  };

  const updateQuestion = (index: number, updater: (question: ManualQuestion) => ManualQuestion) => {
    setEditQuestions((prev) => prev.map((question, qIdx) => (qIdx === index ? updater(question) : question)));
  };

  const handleOpenSubmission = async (submissionId: number) => {
    setSubmissionLoading(submissionId);
    try {
      const detailed = await getTestSubmission(submissionId);
      setSelectedSubmission(detailed);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Не удалось загрузить отправку');
    } finally {
      setSubmissionLoading(null);
    }
  };

  const addQuestion = () => {
    setEditQuestions((prev) => [
      ...prev,
      {
        question: '',
        options: ['', '', '', ''],
        correct_index: 0,
        question_type: 'single',
        correct_answer: [0],
        explanation: '',
      },
    ]);
  };

  const removeQuestion = (index: number) => {
    setEditQuestions((prev) => prev.filter((_, qIdx) => qIdx !== index));
  };

  useEffect(() => {
    loadTests();
    loadStudents();
  }, []);

  useEffect(() => {
    if (preselectedStudentId && students.some((student) => student.user_id === preselectedStudentId)) {
      setSelectedStudentIds((prev) => (prev.includes(preselectedStudentId) ? prev : [...prev, preselectedStudentId]));
    }
  }, [preselectedStudentId, students]);

  return (
    <div className="space-y-6">
      <TestCreator onSaved={() => loadTests()} />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ListPlus className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Созданные тесты учителя</h2>
        </div>
        <button
          onClick={loadTests}
          className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          Обновить
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-xl p-4 lg:col-span-1">
          <div className="text-sm text-gray-500 mb-3">Список тестов</div>
          {loading && (
            <div className="text-sm text-gray-500 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Загружаем...
            </div>
          )}
          <div className="space-y-2 max-h-[500px] overflow-auto">
            {tests.map((t) => (
              <button
                key={t.id}
                onClick={() => handleSelectTest(t.id)}
                className={`w-full text-left p-3 border rounded-lg transition ${
                  selectedTest?.id === t.id ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                <div className="text-sm font-semibold text-gray-900">{t.title}</div>
                <div className="text-xs text-gray-500">{t.topic || '—'} • {t.difficulty || '—'}</div>
              </button>
            ))}
            {!loading && tests.length === 0 && (
              <div className="text-sm text-gray-500">Тесты пока не найдены. Создайте тест во вкладке "Создание тестов".</div>
            )}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-4 lg:col-span-2">
          {!selectedTest && <div className="text-sm text-gray-500">Выберите тест слева</div>}
          {selectedTest && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="text-gray-900 font-semibold">Управление тестом</div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Сохранить
                  </button>
                  <button
                    onClick={handleDelete}
                    className="px-3 py-2 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100 inline-flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Удалить
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Название"
                />
                <input
                  value={editTopic}
                  onChange={(e) => setEditTopic(e.target.value)}
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Тема"
                />
                <input
                  value={editDifficulty}
                  onChange={(e) => setEditDifficulty(e.target.value)}
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  placeholder="Сложность"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm text-gray-700">Вопросы ({editQuestions.length})</div>
                  <button
                    type="button"
                    onClick={addQuestion}
                    className="px-3 py-2 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
                  >
                    Добавить вопрос
                  </button>
                </div>
                {editQuestions.map((q, idx) => (
                  <div key={`${selectedTest.id}-${idx}`} className="p-3 border border-gray-200 rounded-lg bg-gray-50 space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-gray-800">Вопрос {idx + 1}</div>
                      <button
                        type="button"
                        onClick={() => removeQuestion(idx)}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        Удалить вопрос
                      </button>
                    </div>
                    <textarea
                      value={q.question}
                      onChange={(e) => updateQuestion(idx, (current) => ({ ...current, question: e.target.value }))}
                      rows={2}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                    />
                    <div className="space-y-2">
                      {q.options.map((option, optionIdx) => (
                        <div key={optionIdx} className="flex items-center gap-2">
                          <input
                            type="radio"
                            name={`correct-${idx}`}
                            checked={q.correct_index === optionIdx}
                            onChange={() => updateQuestion(idx, (current) => ({ ...current, correct_index: optionIdx }))}
                          />
                          <input
                            value={option}
                            onChange={(e) =>
                              updateQuestion(idx, (current) => ({
                                ...current,
                                options: current.options.map((item, itemIdx) => (itemIdx === optionIdx ? e.target.value : item)),
                              }))
                            }
                            className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm"
                          />
                        </div>
                      ))}
                    </div>
                    <textarea
                      value={q.explanation || ''}
                      onChange={(e) => updateQuestion(idx, (current) => ({ ...current, explanation: e.target.value }))}
                      rows={2}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                      placeholder="Объяснение правильного ответа"
                    />
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-gray-200 space-y-3">
                <div className="text-sm font-semibold text-gray-900">Назначить как ДЗ/КР/проверочную</div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  <select
                    value={assignmentType}
                    onChange={(e) => setAssignmentType(e.target.value as AssignmentType)}
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="homework">Домашняя работа</option>
                    <option value="control">Контрольная работа</option>
                    <option value="quiz">Проверочная</option>
                  </select>
                  <input
                    type="datetime-local"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  />
                  <button
                    onClick={handleAssign}
                    disabled={assigning}
                    className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 inline-flex items-center justify-center gap-2"
                  >
                    {assigning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    Назначить выбранным
                  </button>
                </div>
                <div className="max-h-40 overflow-auto border border-gray-200 rounded-lg p-2 space-y-2">
                  {students.map((student) => (
                    <label key={student.user_id} className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={selectedStudentIds.includes(student.user_id)}
                        onChange={() => toggleStudent(student.user_id)}
                      />
                      <span>{student.full_name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200 space-y-2">
                <div className="text-sm font-semibold text-gray-900">Результаты учеников</div>
                {submissions.length === 0 && <div className="text-sm text-gray-500">Пока нет отправленных работ.</div>}
                {submissions.map((s) => (
                  <div key={s.id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm text-gray-900">
                          {studentNameById[s.user_id] || s.user_id} — {s.score}%
                          {typeof s.correct_count === 'number' && typeof s.total_questions === 'number' && (
                            <span className="text-gray-500"> • {s.correct_count}/{s.total_questions}</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {s.created_at ? new Date(s.created_at).toLocaleString('ru-RU') : ''}
                        </div>
                        {(s.summary || s.feedback) && (
                          <div className="text-xs text-gray-700 mt-1">{s.summary || s.feedback}</div>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleOpenSubmission(s.id)}
                        className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
                      >
                        {submissionLoading === s.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
                        Открыть
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedSubmission && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setSelectedSubmission(null)}>
          <div className="bg-white w-full max-w-4xl rounded-xl shadow-xl max-h-[90vh] overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Работа ученика: {studentNameById[selectedSubmission.user_id] || selectedSubmission.user_id}
                </h3>
                <p className="text-sm text-gray-600">
                  {selectedSubmission.correct_count ?? 0}/{selectedSubmission.total_questions ?? 0} правильных • {selectedSubmission.score}%
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedSubmission(null)}
                className="px-3 py-2 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Закрыть
              </button>
            </div>

            {selectedSubmission.summary && (
              <div className="mb-4 p-4 rounded-lg bg-blue-50 border border-blue-200 text-sm text-gray-700">
                {selectedSubmission.summary}
              </div>
            )}

            <div className="space-y-3">
              {selectedSubmission.question_results.map((result, idx) => (
                <div
                  key={result.question_id}
                  className={`p-4 rounded-xl border ${
                    result.is_correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-sm font-semibold text-gray-900">{idx + 1}. {result.question}</p>
                      <p className="text-xs text-gray-600">
                        Ответ ученика:{' '}
                        {Array.isArray(result.student_answer)
                          ? result.selected_option_texts?.join(', ') || String(result.student_answer)
                          : String(result.student_answer ?? '—')}
                      </p>
                      <p className="text-xs text-gray-600">Правильный ответ: {result.correct_answer_text || '—'}</p>
                      {result.student_explanation && (
                        <p className="text-sm text-gray-700">Как ученик решал: {result.student_explanation}</p>
                      )}
                      {result.question_explanation && (
                        <p className="text-sm text-gray-700">Разбор: {result.question_explanation}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${result.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {result.is_correct ? 'Верно' : 'Ошибка'}
                    </span>
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

