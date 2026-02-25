import { useEffect, useMemo, useState } from 'react';
import { Loader2, ListPlus, Save, Send, Trash2 } from 'lucide-react';
import api from '../services/api';
import {
  listTests,
  getTest,
  deleteTest,
  updateTest,
  assignTestAsHomework,
  listTestSubmissions,
  TestDetail,
  TestSummary,
} from '../services/tests';
import { toast } from 'sonner';

type AssignmentType = 'homework' | 'control' | 'quiz';

interface StudentUser {
  user_id: string;
  full_name: string;
}

export function TeacherTestsTab() {
  const creatorId = localStorage.getItem('user_id') || '';

  const [tests, setTests] = useState<TestSummary[]>([]);
  const [selectedTest, setSelectedTest] = useState<TestDetail | null>(null);
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
    feedback?: string;
    created_at?: string;
  }>>([]);

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
      const updated = await updateTest(selectedTest.id, {
        title: editTitle.trim() || selectedTest.title,
        topic: editTopic || undefined,
        difficulty: editDifficulty || undefined,
        questions: selectedTest.questions.map((q) => ({
          question: q.question,
          options: q.options,
          correct_index: q.correct_index,
          explanation: q.explanation,
        })),
      });
      setSelectedTest(updated);
      setTests((prev) => prev.map((t) => (t.id === updated.id ? { ...t, title: updated.title, topic: updated.topic, difficulty: updated.difficulty } : t)));
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

  useEffect(() => {
    loadTests();
    loadStudents();
  }, []);

  return (
    <div className="space-y-6">
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
                <div className="text-sm text-gray-700">Вопросы ({selectedTest.questions.length})</div>
                {selectedTest.questions.map((q, idx) => (
                  <div key={q.id || idx} className="p-3 border border-gray-200 rounded-lg bg-gray-50">
                    <div className="text-sm text-gray-900 mb-1">{idx + 1}. {q.question}</div>
                    <div className="text-xs text-gray-600">
                      {q.options.map((o, oi) => `${oi === q.correct_index ? '✓ ' : ''}${o}`).join(' | ')}
                    </div>
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
                    <div className="text-sm text-gray-900">
                      {studentNameById[s.user_id] || s.user_id} — {s.score}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {s.created_at ? new Date(s.created_at).toLocaleString('ru-RU') : ''}
                    </div>
                    {s.feedback && <div className="text-xs text-gray-700 mt-1">{s.feedback}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

