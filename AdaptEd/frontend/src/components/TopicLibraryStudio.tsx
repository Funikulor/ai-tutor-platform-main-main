import { useCallback, useEffect, useMemo, useState } from 'react';
import { BookOpen, GraduationCap, Link2, Plus, Trash2 } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';

export interface CatalogTopicLite {
  id: number;
  name: string;
  library_material_ids?: string[];
  library_course_ids?: string[];
}

interface PickerRow {
  id: string;
  title: string;
  topic: string;
  subject: string;
  type?: string;
}

interface TopicLibraryStudioProps {
  topic: CatalogTopicLite;
  subjectTitle: string;
  sectionName: string;
  onClose: () => void;
  onSaved: () => void;
}

type CpType = 'single_choice' | 'numeric' | 'short_text';

interface LessonCheckpointDraft {
  type: CpType;
  question: string;
  options?: string[];
  correct_index?: number;
  correct_answer?: string;
  acceptable_answers?: string[];
}

interface LessonDraft {
  id: string;
  title: string;
  content: string;
  checkpoint: LessonCheckpointDraft;
}

function newLessonId(courseId: string, index: number): string {
  return `les-${courseId}-${index}-${Math.random().toString(36).slice(2, 8)}`;
}

function emptyLesson(courseId: string, index: number): LessonDraft {
  return {
    id: newLessonId(courseId, index),
    title: `Шаг ${index + 1}`,
    content: '',
    checkpoint: {
      type: 'single_choice',
      question: '',
      options: ['', '', '', ''],
      correct_index: 0,
    },
  };
}

export function TopicLibraryStudio({
  topic,
  subjectTitle,
  sectionName,
  onClose,
  onSaved,
}: TopicLibraryStudioProps) {
  const [pickerMats, setPickerMats] = useState<PickerRow[]>([]);
  const [pickerCourses, setPickerCourses] = useState<PickerRow[]>([]);
  const [pickerLoading, setPickerLoading] = useState(true);
  const [matSearch, setMatSearch] = useState('');
  const [courseSearch, setCourseSearch] = useState('');
  const [materialIds, setMaterialIds] = useState<string[]>(() => [
    ...(topic.library_material_ids || []),
  ]);
  const [courseIds, setCourseIds] = useState<string[]>(() => [...(topic.library_course_ids || [])]);
  const [savingLinks, setSavingLinks] = useState(false);

  const [quickTitle, setQuickTitle] = useState('');
  const [quickDesc, setQuickDesc] = useState('');
  const [quickContent, setQuickContent] = useState('');
  const [quickCreating, setQuickCreating] = useState(false);

  const [courseDraftId, setCourseDraftId] = useState(() => `course-admin-${Date.now()}`);
  const [courseTitle, setCourseTitle] = useState(() => `Мини-курс: ${topic.name}`);
  const [courseDesc, setCourseDesc] = useState('');
  const [courseDifficulty, setCourseDifficulty] = useState<'beginner' | 'intermediate' | 'advanced'>(
    'beginner'
  );
  const [courseMinutes, setCourseMinutes] = useState<number>(30);
  const [lessons, setLessons] = useState<LessonDraft[]>(() => [
    emptyLesson(`course-admin-${Date.now()}`, 0),
  ]);
  const [courseSaving, setCourseSaving] = useState(false);

  const loadPicker = useCallback(async () => {
    setPickerLoading(true);
    try {
      const { data } = await api.get<{ materials: PickerRow[]; courses: PickerRow[] }>(
        '/admin/library/picker'
      );
      setPickerMats(data.materials || []);
      setPickerCourses(data.courses || []);
    } catch {
      toast.error('Не удалось загрузить справочник библиотеки');
      setPickerMats([]);
      setPickerCourses([]);
    } finally {
      setPickerLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPicker();
  }, [loadPicker]);

  useEffect(() => {
    setMaterialIds([...(topic.library_material_ids || [])]);
    setCourseIds([...(topic.library_course_ids || [])]);
  }, [topic.id]);

  const filteredMats = useMemo(() => {
    const q = matSearch.trim().toLowerCase();
    if (!q) return pickerMats;
    return pickerMats.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        (m.topic || '').toLowerCase().includes(q) ||
        (m.subject || '').toLowerCase().includes(q)
    );
  }, [pickerMats, matSearch]);

  const filteredCourses = useMemo(() => {
    const q = courseSearch.trim().toLowerCase();
    if (!q) return pickerCourses;
    return pickerCourses.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.topic || '').toLowerCase().includes(q) ||
        (c.subject || '').toLowerCase().includes(q)
    );
  }, [pickerCourses, courseSearch]);

  const toggleMat = (id: string) => {
    setMaterialIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const toggleCourse = (id: string) => {
    setCourseIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const saveLinks = async () => {
    setSavingLinks(true);
    try {
      await api.put(`/admin/content/topic/${topic.id}/library`, {
        material_ids: materialIds,
        course_ids: courseIds,
      });
      toast.success('Привязки к теме сохранены');
      onSaved();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Не удалось сохранить привязки');
    } finally {
      setSavingLinks(false);
    }
  };

  const createQuickMaterial = async () => {
    const title = quickTitle.trim();
    if (!title) {
      toast.info('Укажите название материала');
      return;
    }
    setQuickCreating(true);
    try {
      const { data } = await api.post<{ id: string }>('/admin/library/materials', {
        title,
        description: quickDesc.trim(),
        content: quickContent,
        subject: subjectTitle,
        topic: topic.name,
        type: 'article',
        difficulty: 'beginner',
        duration: '15 мин',
      });
      const newId = data.id;
      if (newId) {
        const nextMats = [...materialIds, newId];
        setMaterialIds(nextMats);
        await api.put(`/admin/content/topic/${topic.id}/library`, {
          material_ids: nextMats,
          course_ids: courseIds,
        });
        toast.success('Материал создан и привязан к теме');
        setQuickTitle('');
        setQuickDesc('');
        setQuickContent('');
        loadPicker();
        onSaved();
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Не удалось создать материал');
    } finally {
      setQuickCreating(false);
    }
  };

  const buildCoursePayload = (): Record<string, unknown> | null => {
    const title = courseTitle.trim();
    if (!title) {
      toast.info('Укажите название курса');
      return null;
    }
    const cid = courseDraftId.trim() || `course-admin-${Date.now()}`;
    const outLessons: Array<Record<string, unknown>> = [];
    for (let i = 0; i < lessons.length; i++) {
      const L = lessons[i];
      const q = (L.checkpoint?.question || '').trim();
      if (!L.title.trim() || !q) {
        toast.info(`Заполните название и вопрос проверки у шага ${i + 1}`);
        return null;
      }
      const ch = L.checkpoint;
      let checkpoint: Record<string, unknown> = { type: ch.type, question: q };
      if (ch.type === 'single_choice') {
        const opts = (ch.options || []).map((o) => String(o).trim()).filter(Boolean);
        if (opts.length < 2) {
          toast.info(`Шаг ${i + 1}: нужно минимум 2 варианта ответа`);
          return null;
        }
        const ci = Number(ch.correct_index);
        if (Number.isNaN(ci) || ci < 0 || ci >= opts.length) {
          toast.info(`Шаг ${i + 1}: укажите корректный номер правильного варианта (0…${opts.length - 1})`);
          return null;
        }
        checkpoint = { ...checkpoint, options: opts, correct_index: ci };
      } else if (ch.type === 'numeric') {
        const ca = String(ch.correct_answer ?? '').trim();
        if (!ca) {
          toast.info(`Шаг ${i + 1}: укажите правильный ответ (число)`);
          return null;
        }
        checkpoint = { ...checkpoint, correct_answer: ca };
      } else {
        const acc = (ch.acceptable_answers || []).filter((a) => String(a).trim());
        if (!acc.length) {
          toast.info(`Шаг ${i + 1}: добавьте хотя бы один допустимый ответ`);
          return null;
        }
        checkpoint = {
          ...checkpoint,
          acceptable_answers: acc.map((a) => String(a).trim().toLowerCase()),
        };
      }
      outLessons.push({
        id: L.id || newLessonId(cid, i),
        title: L.title.trim(),
        content: L.content || '',
        checkpoint,
      });
    }
    return {
      id: cid,
      title,
      description: courseDesc.trim() || topic.name,
      subject: subjectTitle,
      topic: `${sectionName}: ${topic.name}`,
      difficulty: courseDifficulty,
      estimated_minutes: Math.max(5, courseMinutes || 30),
      lessons: outLessons,
    };
  };

  const saveNewCourse = async () => {
    const payload = buildCoursePayload();
    if (!payload) return;
    setCourseSaving(true);
    try {
      await api.post('/admin/library/courses', payload);
      const cid = String(payload.id);
      const nextCourses = [...courseIds, cid];
      setCourseIds(nextCourses);
      await api.put(`/admin/content/topic/${topic.id}/library`, {
        material_ids: materialIds,
        course_ids: nextCourses,
      });
      toast.success('Мини-курс сохранён и привязан к теме');
      await loadPicker();
      onSaved();
      const nextId = `course-admin-${Date.now()}`;
      setCourseDraftId(nextId);
      setLessons([emptyLesson(nextId, 0)]);
      setCourseTitle(`Мини-курс: ${topic.name}`);
      setCourseDesc('');
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Не удалось сохранить курс');
    } finally {
      setCourseSaving(false);
    }
  };

  const updateLesson = (index: number, patch: Partial<LessonDraft>) => {
    setLessons((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };
      return next;
    });
  };

  const updateCheckpoint = (index: number, patch: Record<string, unknown>) => {
    setLessons((prev) => {
      const next = [...prev];
      const L = next[index];
      next[index] = {
        ...L,
        checkpoint: { ...L.checkpoint, ...patch } as LessonCheckpointDraft,
      };
      return next;
    });
  };

  return (
    <div className="space-y-6 max-h-[min(78vh,720px)] overflow-y-auto pr-1">
      <div className="border-b border-gray-200 pb-3">
        <p className="text-sm text-gray-500 flex items-center gap-2">
          <Link2 className="w-4 h-4 text-indigo-600 shrink-0" aria-hidden />
          {subjectTitle} → {sectionName}
        </p>
        <p className="text-sm text-gray-600 mt-2">
          Выберите материалы и мини-курсы из библиотеки или создайте новые — ученик увидит их в разделе библиотеки «По программе».
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="border border-gray-200 rounded-xl p-4 bg-white">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="w-5 h-5 text-blue-600" />
            <h4 className="font-medium text-gray-900">Материалы библиотеки</h4>
          </div>
          <input
            type="search"
            placeholder="Поиск…"
            value={matSearch}
            onChange={(e) => setMatSearch(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-2"
          />
          {pickerLoading ? (
            <p className="text-sm text-gray-500">Загрузка…</p>
          ) : (
            <ul className="max-h-48 overflow-y-auto space-y-1 text-sm border border-gray-100 rounded-lg p-2">
              {filteredMats.slice(0, 200).map((m) => (
                <li key={m.id}>
                  <label className="flex items-start gap-2 cursor-pointer hover:bg-gray-50 rounded px-1 py-1">
                    <input
                      type="checkbox"
                      checked={materialIds.includes(m.id)}
                      onChange={() => toggleMat(m.id)}
                      className="mt-1"
                    />
                    <span>
                      <span className="font-medium text-gray-800">{m.title}</span>
                      <span className="block text-xs text-gray-500">
                        {m.subject} · {m.topic}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-gray-500 mt-2">Выбрано: {materialIds.length}</p>
        </div>

        <div className="border border-gray-200 rounded-xl p-4 bg-white">
          <div className="flex items-center gap-2 mb-3">
            <GraduationCap className="w-5 h-5 text-violet-600" />
            <h4 className="font-medium text-gray-900">Мини-курсы</h4>
          </div>
          <input
            type="search"
            placeholder="Поиск…"
            value={courseSearch}
            onChange={(e) => setCourseSearch(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-2"
          />
          {pickerLoading ? (
            <p className="text-sm text-gray-500">Загрузка…</p>
          ) : (
            <ul className="max-h-48 overflow-y-auto space-y-1 text-sm border border-gray-100 rounded-lg p-2">
              {filteredCourses.slice(0, 200).map((c) => (
                <li key={c.id}>
                  <label className="flex items-start gap-2 cursor-pointer hover:bg-gray-50 rounded px-1 py-1">
                    <input
                      type="checkbox"
                      checked={courseIds.includes(c.id)}
                      onChange={() => toggleCourse(c.id)}
                      className="mt-1"
                    />
                    <span>
                      <span className="font-medium text-gray-800">{c.title}</span>
                      <span className="block text-xs text-gray-500">
                        {c.subject} · {c.topic}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-gray-500 mt-2">Выбрано: {courseIds.length}</p>
        </div>
      </div>

      <div className="border border-dashed border-blue-200 rounded-xl p-4 bg-blue-50/40">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-blue-600" />
          Быстрая статья в библиотеку
        </h4>
        <div className="grid grid-cols-1 gap-3">
          <input
            type="text"
            placeholder="Заголовок"
            value={quickTitle}
            onChange={(e) => setQuickTitle(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <input
            type="text"
            placeholder="Краткое описание (для карточки)"
            value={quickDesc}
            onChange={(e) => setQuickDesc(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <textarea
            placeholder="Текст урока (Markdown)"
            value={quickContent}
            onChange={(e) => setQuickContent(e.target.value)}
            rows={5}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
          />
          <button
            type="button"
            onClick={createQuickMaterial}
            disabled={quickCreating}
            className="self-start px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {quickCreating ? 'Создание…' : 'Создать и добавить к теме'}
          </button>
        </div>
      </div>

      <div className="border border-dashed border-violet-200 rounded-xl p-4 bg-violet-50/40">
        <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-violet-600" />
          Конструктор мини-курса (шаги + проверка после каждого)
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1">ID курса (латиница, уникально)</label>
            <input
              value={courseDraftId}
              onChange={(e) => setCourseDraftId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Длительность (мин.)</label>
            <input
              type="number"
              min={5}
              value={courseMinutes}
              onChange={(e) => setCourseMinutes(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-600 mb-1">Название</label>
            <input
              value={courseTitle}
              onChange={(e) => setCourseTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-600 mb-1">Описание</label>
            <textarea
              value={courseDesc}
              onChange={(e) => setCourseDesc(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Сложность</label>
            <select
              value={courseDifficulty}
              onChange={(e) =>
                setCourseDifficulty(e.target.value as 'beginner' | 'intermediate' | 'advanced')
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="beginner">Базовый</option>
              <option value="intermediate">Средний</option>
              <option value="advanced">Продвинутый</option>
            </select>
          </div>
        </div>

        <div className="space-y-4">
          {lessons.map((les, idx) => (
            <div key={les.id} className="border border-gray-200 rounded-lg p-3 bg-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-800">Шаг {idx + 1}</span>
                {lessons.length > 1 ? (
                  <button
                    type="button"
                    onClick={() => setLessons((p) => p.filter((_, i) => i !== idx))}
                    className="text-red-600 text-xs inline-flex items-center gap-1 hover:underline"
                  >
                    <Trash2 className="w-3 h-3" />
                    Удалить шаг
                  </button>
                ) : null}
              </div>
              <input
                placeholder="Заголовок шага"
                value={les.title}
                onChange={(e) => updateLesson(idx, { title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-2"
              />
              <textarea
                placeholder="Содержание (Markdown)"
                value={les.content}
                onChange={(e) => updateLesson(idx, { content: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono mb-2"
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-gray-600">Тип проверки</label>
                  <select
                    value={les.checkpoint.type}
                    onChange={(e) => {
                      const t = e.target.value as CpType;
                      if (t === 'single_choice') {
                        updateCheckpoint(idx, {
                          type: t,
                          options: ['', '', '', ''],
                          correct_index: 0,
                        });
                      } else if (t === 'numeric') {
                        updateCheckpoint(idx, {
                          type: t,
                          correct_answer: '',
                        });
                      } else {
                        updateCheckpoint(idx, {
                          type: t,
                          acceptable_answers: [''],
                        });
                      }
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mt-0.5"
                  >
                    <option value="single_choice">Выбор из вариантов</option>
                    <option value="numeric">Числовой ответ</option>
                    <option value="short_text">Короткий текст</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs text-gray-600">Вопрос после шага</label>
                  <input
                    value={les.checkpoint.question}
                    onChange={(e) => updateCheckpoint(idx, { question: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mt-0.5"
                  />
                </div>
              </div>
              {les.checkpoint.type === 'single_choice' ? (
                <div className="mt-2 space-y-2">
                  <p className="text-xs text-gray-600">Варианты (пустые строки будут убраны)</p>
                  {(les.checkpoint.options || ['', '', '', '']).map((opt, oi) => (
                    <input
                      key={oi}
                      value={opt}
                      onChange={(e) => {
                        const opts = [...(les.checkpoint.options || ['', '', '', ''])];
                        opts[oi] = e.target.value;
                        updateCheckpoint(idx, { options: opts });
                      }}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded text-sm"
                      placeholder={`Вариант ${oi + 1}`}
                    />
                  ))}
                  <div>
                    <label className="text-xs text-gray-600">Индекс правильного (0 — первый)</label>
                    <input
                      type="number"
                      min={0}
                      value={les.checkpoint.correct_index ?? 0}
                      onChange={(e) =>
                        updateCheckpoint(idx, { correct_index: parseInt(e.target.value, 10) || 0 })
                      }
                      className="w-32 px-3 py-1.5 border border-gray-300 rounded text-sm mt-0.5"
                    />
                  </div>
                </div>
              ) : null}
              {les.checkpoint.type === 'numeric' ? (
                <div className="mt-2">
                  <label className="text-xs text-gray-600">Правильный ответ</label>
                  <input
                    value={les.checkpoint.correct_answer ?? ''}
                    onChange={(e) => updateCheckpoint(idx, { correct_answer: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mt-0.5"
                  />
                </div>
              ) : null}
              {les.checkpoint.type === 'short_text' ? (
                <div className="mt-2">
                  <label className="text-xs text-gray-600">
                    Допустимые ответы (каждый с новой строки, без учёта регистра)
                  </label>
                  <textarea
                    value={(les.checkpoint.acceptable_answers || ['']).join('\n')}
                    onChange={(e) =>
                      updateCheckpoint(idx, {
                        acceptable_answers: e.target.value.split('\n').map((s) => s.trim()),
                      })
                    }
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mt-0.5 font-mono"
                  />
                </div>
              ) : null}
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          <button
            type="button"
            onClick={() =>
              setLessons((p) => [...p, emptyLesson(courseDraftId.trim() || 'course', p.length)])
            }
            className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
          >
            + Шаг
          </button>
          <button
            type="button"
            onClick={saveNewCourse}
            disabled={courseSaving}
            className="px-4 py-2 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700 disabled:opacity-50"
          >
            {courseSaving ? 'Сохранение…' : 'Сохранить мини-курс и добавить к теме'}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 pt-2 border-t border-gray-200">
        <button
          type="button"
          onClick={saveLinks}
          disabled={savingLinks}
          className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {savingLinks ? 'Сохранение…' : 'Сохранить привязки к теме'}
        </button>
        <button
          type="button"
          onClick={onClose}
          className="px-5 py-2.5 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
        >
          Закрыть
        </button>
      </div>
    </div>
  );
}
