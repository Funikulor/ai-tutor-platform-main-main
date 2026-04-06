import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Plus, Trash2, Loader2, Check } from 'lucide-react';
import type {
  AdminLibraryCourseFull,
  AdminLibraryLessonFull,
  AdminLibraryCheckpoint,
} from '../services/materials';
import { fetchAdminLibraryCourse, saveAdminLibraryCourse, deleteAdminLibraryCourse } from '../services/materials';
import { toast } from 'sonner';

function normalizeCourse(raw: AdminLibraryCourseFull): AdminLibraryCourseFull {
  const lessons = (raw.lessons || []).map((l) => ({
    id: String(l.id || `les-${Math.random().toString(36).slice(2)}`),
    title: l.title || '',
    content: l.content || '',
    checkpoint: { ...(l.checkpoint || {}) } as AdminLibraryCheckpoint,
  }));
  return {
    id: String(raw.id),
    title: raw.title || '',
    description: raw.description || '',
    subject: raw.subject || 'Математика',
    topic: raw.topic || '',
    difficulty: raw.difficulty || 'beginner',
    estimated_minutes: raw.estimated_minutes ?? 30,
    lessons: lessons.length ? lessons : [emptyLesson(0)],
  };
}

function emptyLesson(i: number): AdminLibraryLessonFull {
  return {
    id: `les-${Date.now()}-${i}`,
    title: `Шаг ${i + 1}`,
    content: '',
    checkpoint: {
      type: 'single_choice',
      question: '',
      options: ['Вариант 1', 'Вариант 2', 'Вариант 3', 'Вариант 4'],
      correct_index: 0,
    },
  };
}

function newEmptyCourse(): AdminLibraryCourseFull {
  const id = `course-admin-${Date.now()}`;
  return {
    id,
    title: 'Новый мини-курс',
    description: '',
    subject: 'Математика',
    topic: '',
    difficulty: 'beginner',
    estimated_minutes: 30,
    lessons: [emptyLesson(0)],
  };
}

interface CourseAdminEditorProps {
  courseId: string | null;
  startFresh?: boolean;
  onBack: () => void;
  onSaved: () => void;
}

export function CourseAdminEditor({ courseId, startFresh, onBack, onSaved }: CourseAdminEditorProps) {
  const [draft, setDraft] = useState<AdminLibraryCourseFull | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeLessonIdx, setActiveLessonIdx] = useState(0);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const skipSaveRef = useRef(true);
  const onSavedRef = useRef(onSaved);
  onSavedRef.current = onSaved;

  useEffect(() => {
    let cancelled = false;
    setLoadError(null);
    setLoading(true);
    skipSaveRef.current = true;
    if (startFresh || !courseId) {
      setDraft(newEmptyCourse());
      setActiveLessonIdx(0);
      setLoading(false);
      return;
    }
    fetchAdminLibraryCourse(courseId)
      .then((c) => {
        if (cancelled) return;
        setDraft(normalizeCourse(c));
        setActiveLessonIdx(0);
      })
      .catch(() => {
        if (!cancelled) setLoadError('Не удалось загрузить курс');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [courseId, startFresh]);

  useEffect(() => {
    if (!draft) return;
    const t = setTimeout(() => {
      void (async () => {
        if (skipSaveRef.current) {
          skipSaveRef.current = false;
          return;
        }
        if (!draft.title?.trim() || !draft.lessons?.length) return;
        setSaveState('saving');
        try {
          await saveAdminLibraryCourse(draft);
          setSaveState('saved');
          onSavedRef.current();
        } catch (e: unknown) {
          console.error(e);
          setSaveState('error');
          toast.error('Не удалось сохранить курс');
        }
      })();
    }, 900);
    return () => clearTimeout(t);
  }, [draft]);

  useEffect(() => {
    if (saveState !== 'saved') return;
    const u = setTimeout(() => setSaveState('idle'), 2000);
    return () => clearTimeout(u);
  }, [saveState]);

  const updateLesson = (idx: number, part: Partial<AdminLibraryLessonFull>) => {
    setDraft((d) => {
      if (!d) return d;
      const lessons = [...d.lessons];
      lessons[idx] = { ...lessons[idx], ...part };
      return { ...d, lessons };
    });
  };

  const updateCheckpoint = (idx: number, part: Partial<AdminLibraryCheckpoint>) => {
    setDraft((d) => {
      if (!d) return d;
      const lessons = [...d.lessons];
      const ch = { ...(lessons[idx].checkpoint || {}), ...part };
      lessons[idx] = { ...lessons[idx], checkpoint: ch };
      return { ...d, lessons };
    });
  };

  const addLesson = () => {
    setDraft((d) => {
      if (!d) return d;
      const next = emptyLesson(d.lessons.length);
      return { ...d, lessons: [...d.lessons, next] };
    });
    setActiveLessonIdx((i) => i + 1);
  };

  const removeLesson = (idx: number) => {
    setDraft((d) => {
      if (!d || d.lessons.length < 2) return d;
      const lessons = d.lessons.filter((_, j) => j !== idx);
      return { ...d, lessons };
    });
    setActiveLessonIdx((i) => {
      if (i === idx) return Math.max(0, idx - 1);
      if (i > idx) return i - 1;
      return i;
    });
  };

  const handleDeleteCourse = async () => {
    if (!draft?.id) return;
    if (!confirm('Удалить этот курс из черновиков админки? (Встроенные курсы из файлов проекта не удаляются.)')) return;
    try {
      await deleteAdminLibraryCourse(draft.id);
      toast.success('Курс удалён из хранилища админки');
      onBack();
      onSavedRef.current();
    } catch {
      toast.error('Удаление доступно только для курсов, созданных через админку');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-20 text-gray-600">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        Загрузка курса…
      </div>
    );
  }

  if (loadError || !draft) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
        <p>{loadError || 'Нет данных'}</p>
        <button type="button" onClick={onBack} className="mt-4 text-sm font-medium text-indigo-700 underline">
          Назад
        </button>
      </div>
    );
  }

  const lesson = draft.lessons[activeLessonIdx];
  const cp = lesson?.checkpoint || {};
  const cpType = cp.type || 'single_choice';

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 pb-4">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm font-medium text-indigo-700 hover:text-indigo-900"
        >
          <ArrowLeft className="h-4 w-4" />
          К списку курсов
        </button>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            {saveState === 'saving' && (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                Сохранение…
              </>
            )}
            {saveState === 'saved' && (
              <>
                <Check className="h-4 w-4 text-emerald-600" />
                Сохранено
              </>
            )}
            {saveState === 'error' && <span className="text-rose-600">Ошибка</span>}
            {saveState === 'idle' && <span className="text-gray-400">Автосохранение</span>}
          </div>
          <button
            type="button"
            onClick={() => void handleDeleteCourse()}
            className="rounded-lg border border-rose-200 px-3 py-1.5 text-sm text-rose-700 hover:bg-rose-50"
          >
            Удалить из админки
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-3 rounded-xl border border-gray-200 bg-gray-50/80 p-4">
          <h3 className="text-xs font-bold uppercase tracking-wide text-gray-500">Шаги курса</h3>
          <ul className="space-y-1">
            {draft.lessons.map((l, idx) => (
              <li key={l.id}>
                <button
                  type="button"
                  onClick={() => setActiveLessonIdx(idx)}
                  className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition ${
                    idx === activeLessonIdx ? 'bg-indigo-600 text-white' : 'bg-white text-gray-800 hover:bg-gray-100'
                  }`}
                >
                  <span className="truncate">{idx + 1}. {l.title || 'Без названия'}</span>
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={addLesson}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-indigo-300 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-50"
          >
            <Plus className="h-4 w-4" />
            Добавить шаг
          </button>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block md:col-span-2">
              <span className="text-xs font-semibold text-gray-500">Название курса</span>
              <input
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block md:col-span-2">
              <span className="text-xs font-semibold text-gray-500">Описание</span>
              <textarea
                value={draft.description}
                onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                rows={2}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold text-gray-500">Предмет</span>
              <input
                value={draft.subject}
                onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold text-gray-500">Тема (тег)</span>
              <input
                value={draft.topic}
                onChange={(e) => setDraft({ ...draft, topic: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
            <label className="block">
              <span className="text-xs font-semibold text-gray-500">Сложность</span>
              <select
                value={draft.difficulty}
                onChange={(e) => setDraft({ ...draft, difficulty: e.target.value })}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="beginner">Начальный</option>
                <option value="intermediate">Средний</option>
                <option value="advanced">Продвинутый</option>
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-semibold text-gray-500">Минут (оценка)</span>
              <input
                type="number"
                min={5}
                value={draft.estimated_minutes ?? ''}
                onChange={(e) =>
                  setDraft({ ...draft, estimated_minutes: parseInt(e.target.value, 10) || 0 })
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
          </div>

          {lesson ? (
            <div className="rounded-xl border border-indigo-100 bg-white p-4 shadow-sm space-y-4">
              <div className="flex items-center justify-between gap-2">
                <h4 className="font-semibold text-gray-900">Редактирование шага</h4>
                {draft.lessons.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeLesson(activeLessonIdx)}
                    className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-rose-600 hover:bg-rose-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    Удалить шаг
                  </button>
                )}
              </div>
              <label className="block">
                <span className="text-xs font-semibold text-gray-500">Заголовок шага</span>
                <input
                  value={lesson.title}
                  onChange={(e) => updateLesson(activeLessonIdx, { title: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </label>
              <label className="block">
                <span className="text-xs font-semibold text-gray-500">Текст урока (Markdown)</span>
                <textarea
                  value={lesson.content || ''}
                  onChange={(e) => updateLesson(activeLessonIdx, { content: e.target.value })}
                  rows={12}
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm"
                />
              </label>

              <div className="border-t border-gray-100 pt-4 space-y-3">
                <p className="text-sm font-medium text-gray-800">Контрольный вопрос после шага</p>
                <label className="block">
                  <span className="text-xs font-semibold text-gray-500">Тип</span>
                  <select
                    value={cpType}
                    onChange={(e) => {
                      const t = e.target.value;
                      if (t === 'single_choice') {
                        updateCheckpoint(activeLessonIdx, {
                          type: t,
                          options: ['', '', '', ''],
                          correct_index: 0,
                          correct_answer: undefined,
                          acceptable_answers: undefined,
                        });
                      } else if (t === 'numeric') {
                        updateCheckpoint(activeLessonIdx, {
                          type: t,
                          options: undefined,
                          correct_index: undefined,
                          correct_answer: '',
                          acceptable_answers: undefined,
                        });
                      } else {
                        updateCheckpoint(activeLessonIdx, {
                          type: 'short_text',
                          options: undefined,
                          correct_index: undefined,
                          correct_answer: undefined,
                          acceptable_answers: [''],
                        });
                      }
                    }}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  >
                    <option value="single_choice">Один вариант</option>
                    <option value="numeric">Число</option>
                    <option value="short_text">Короткий текст</option>
                  </select>
                </label>
                <label className="block">
                  <span className="text-xs font-semibold text-gray-500">Формулировка вопроса</span>
                  <textarea
                    value={cp.question || ''}
                    onChange={(e) => updateCheckpoint(activeLessonIdx, { question: e.target.value })}
                    rows={2}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </label>

                {cpType === 'single_choice' && (
                  <>
                    {(cp.options || ['', '', '', '']).map((opt, oi) => (
                      <label key={oi} className="block">
                        <span className="text-xs font-semibold text-gray-500">Вариант {oi + 1}</span>
                        <input
                          value={opt}
                          onChange={(e) => {
                            const opts = [...(cp.options || ['', '', '', ''])];
                            opts[oi] = e.target.value;
                            updateCheckpoint(activeLessonIdx, { options: opts });
                          }}
                          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                        />
                      </label>
                    ))}
                    <label className="block">
                      <span className="text-xs font-semibold text-gray-500">Индекс верного (0 — первый)</span>
                      <input
                        type="number"
                        min={0}
                        value={cp.correct_index ?? 0}
                        onChange={(e) =>
                          updateCheckpoint(activeLessonIdx, { correct_index: parseInt(e.target.value, 10) || 0 })
                        }
                        className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      />
                    </label>
                  </>
                )}

                {cpType === 'numeric' && (
                  <label className="block">
                    <span className="text-xs font-semibold text-gray-500">Правильный ответ (число или дробь)</span>
                    <input
                      value={cp.correct_answer ?? ''}
                      onChange={(e) => updateCheckpoint(activeLessonIdx, { correct_answer: e.target.value })}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    />
                  </label>
                )}

                {cpType === 'short_text' && (
                  <label className="block">
                    <span className="text-xs font-semibold text-gray-500">
                      Допустимые ответы (через запятую, без учёта регистра)
                    </span>
                    <input
                      value={(cp.acceptable_answers || []).join(', ')}
                      onChange={(e) =>
                        updateCheckpoint(activeLessonIdx, {
                          acceptable_answers: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                        })
                      }
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    />
                  </label>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
