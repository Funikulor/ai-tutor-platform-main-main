import { useState, useEffect, useMemo } from 'react';
import { ArrowLeft, BookMarked, CheckCircle, Circle, Lock, Send, GraduationCap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../services/api';
import { toast } from 'sonner';
import type { LibraryCourse, LibraryLesson } from '../services/materials';

const storageKey = (courseId: string) => `library_course_passed_${courseId}`;

function loadPassed(courseId: string): Set<string> {
  try {
    const raw = localStorage.getItem(storageKey(courseId));
    if (!raw) return new Set();
    const arr = JSON.parse(raw) as string[];
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

function savePassed(courseId: string, passed: Set<string>) {
  localStorage.setItem(storageKey(courseId), JSON.stringify([...passed]));
}

function difficultyLabelRu(difficulty: string): string {
  switch (difficulty) {
    case 'beginner':
      return 'Базовый уровень';
    case 'intermediate':
      return 'Средний уровень';
    case 'advanced':
      return 'Продвинутый';
    default:
      return difficulty;
  }
}

/** Стили для уроков: без @tailwindcss/typography plain `prose` почти не даёт оформления */
const lessonMarkdownComponents: Components = {
  h2: ({ children }) => (
    <h2 className="text-lg font-bold text-gray-950 mt-8 mb-3 pb-2 border-b border-indigo-100 first:mt-0 scroll-mt-4">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold text-indigo-900 mt-6 mb-2 first:mt-0">{children}</h3>
  ),
  p: ({ children }) => <p className="my-3 leading-relaxed text-gray-800">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-indigo-950">{children}</strong>,
  blockquote: ({ children }) => (
    <blockquote className="my-4 border-l-4 border-violet-500 bg-gradient-to-r from-violet-50/90 to-indigo-50/50 pl-4 py-3 pr-4 rounded-r-xl text-gray-800 shadow-sm">
      {children}
    </blockquote>
  ),
  ul: ({ children }) => (
    <ul className="my-4 list-disc pl-5 space-y-2 text-gray-800 marker:text-indigo-500">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="my-4 list-decimal pl-5 space-y-2 text-gray-800 marker:text-indigo-600 marker:font-medium">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-relaxed pl-0.5">{children}</li>,
  hr: () => (
    <hr className="my-8 border-0 h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent" />
  ),
  table: ({ children }) => (
    <div className="my-5 overflow-x-auto rounded-xl border border-gray-200 shadow-sm bg-white">
      <table className="min-w-full text-sm text-left border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-indigo-50 text-indigo-950">{children}</thead>,
  tbody: ({ children }) => <tbody className="divide-y divide-gray-100">{children}</tbody>,
  tr: ({ children }) => <tr className="hover:bg-gray-50/80 transition-colors">{children}</tr>,
  th: ({ children }) => (
    <th className="px-4 py-2.5 font-semibold border-b border-indigo-100">{children}</th>
  ),
  td: ({ children }) => <td className="px-4 py-2.5 text-gray-800 border-b border-gray-100">{children}</td>,
  code: ({ className, children, ...props }) => {
    const inline = !className;
    if (inline) {
      return (
        <code
          className="px-1.5 py-0.5 rounded-md bg-indigo-100/80 text-indigo-900 text-[0.9em] font-mono"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="my-4 p-4 rounded-xl bg-gray-900 text-gray-100 text-sm overflow-x-auto font-mono leading-relaxed">
      {children}
    </pre>
  ),
};

interface CourseViewerProps {
  course: LibraryCourse;
  onBack: () => void;
  onProgress?: () => void;
}

export function CourseViewer({ course, onBack, onProgress }: CourseViewerProps) {
  const lessons = course.lessons || [];
  const [passedIds, setPassedIds] = useState<Set<string>>(() => loadPassed(course.id));
  const [activeIdx, setActiveIdx] = useState(0);
  const [answerDraft, setAnswerDraft] = useState('');
  const [choiceIdx, setChoiceIdx] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setPassedIds(loadPassed(course.id));
  }, [course.id]);

  useEffect(() => {
    setAnswerDraft('');
    setChoiceIdx(null);
  }, [activeIdx, course.id]);

  const canOpen = useMemo(() => {
    return lessons.map((_, i) => {
      if (i === 0) return true;
      return passedIds.has(lessons[i - 1].id);
    });
  }, [lessons, passedIds]);

  useEffect(() => {
    if (!canOpen[activeIdx]) {
      const first = canOpen.findIndex(Boolean);
      if (first >= 0) setActiveIdx(first);
    }
  }, [canOpen, activeIdx]);

  const activeLessonStableId = course.lessons?.[activeIdx]?.id;

  useEffect(() => {
    const list = course.lessons ?? [];
    const les = list[activeIdx];
    const label = les
      ? `Мини-курс: ${course.title} · шаг ${activeIdx + 1} — ${les.title}`
      : `Мини-курс: ${course.title}`;
    window.dispatchEvent(
      new CustomEvent('ai-chat-context', {
        detail: {
          context: {
            library_course_id: course.id,
            library_lesson_index: activeIdx,
            label,
          },
        },
      })
    );
  }, [course.id, course.title, activeIdx, activeLessonStableId]);

  useEffect(() => {
    return () => {
      window.dispatchEvent(new CustomEvent('ai-chat-context', { detail: { context: null } }));
    };
  }, [course.id]);

  const lesson: LibraryLesson | undefined = lessons[activeIdx];
  const cp = lesson?.checkpoint;

  const submitCheckpoint = async () => {
    if (!lesson || !cp?.question) return;
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      toast.error('Войдите в аккаунт');
      return;
    }

    let answer = '';
    if (cp.type === 'single_choice') {
      if (choiceIdx === null) {
        toast.info('Выберите вариант ответа');
        return;
      }
      answer = String(choiceIdx);
    } else {
      answer = answerDraft.trim();
      if (!answer) {
        toast.info('Введите ответ');
        return;
      }
    }

    setSubmitting(true);
    try {
      const { data } = await api.post<{
        is_correct: boolean;
        feedback: string;
      }>('/library/checkpoint', {
        course_id: course.id,
        lesson_id: lesson.id,
        user_id: userId,
        answer,
      });

      if (data.is_correct) {
        toast.success(data.feedback);
        const next = new Set(passedIds);
        next.add(lesson.id);
        setPassedIds(next);
        savePassed(course.id, next);
        onProgress?.();
        if (activeIdx < lessons.length - 1) {
          setActiveIdx(activeIdx + 1);
        }
      } else {
        toast.error(data.feedback);
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Не удалось проверить ответ');
    } finally {
      setSubmitting(false);
    }
  };

  const progressPct =
    lessons.length === 0 ? 0 : Math.round((passedIds.size / lessons.length) * 100);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-5 h-5" />
          К курсам
        </button>
        <div className="flex items-center gap-2 text-sm font-medium text-gray-800">
          <GraduationCap className="w-4 h-4 text-indigo-700" />
          <span>{course.subject}</span>
        </div>
      </div>
      <p className="text-xs text-gray-500 -mt-2 mb-1 max-w-3xl">
        AI-помощник подставляет в чат текст этого шага и формулировку контрольного вопроса — спрашивай, если что-то непонятно.
      </p>

      {/* Светлая карточка + тёмный текст: градиент с белым текстом на части экранов «пропадает» и даёт невидимый заголовок */}
      <div className="rounded-2xl overflow-hidden border-2 border-indigo-200/80 bg-white shadow-md ring-1 ring-gray-100">
        <div className="h-1.5 bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600" aria-hidden />
        <div className="p-6 sm:p-7">
          <h1 className="text-2xl sm:text-[1.65rem] font-bold text-gray-950 tracking-tight leading-snug">
            {course.title}
          </h1>
          <p className="mt-3 text-sm sm:text-[0.9375rem] text-gray-700 max-w-3xl leading-relaxed">
            {course.description}
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs sm:text-sm font-medium">
            {course.estimated_minutes != null && (
              <span className="inline-flex items-center rounded-lg bg-indigo-100 px-3 py-1.5 text-indigo-950 border border-indigo-200/80">
                ~{course.estimated_minutes} мин
              </span>
            )}
            <span className="inline-flex items-center rounded-lg bg-gray-100 px-3 py-1.5 text-gray-900 border border-gray-200">
              {course.subject}
            </span>
            {course.topic ? (
              <span
                className="inline-flex items-center rounded-lg bg-violet-100 px-3 py-1.5 text-violet-950 border border-violet-200/80 max-w-full truncate"
                title={course.topic}
              >
                {course.topic}
              </span>
            ) : null}
            <span className="inline-flex items-center rounded-lg bg-emerald-100 px-3 py-1.5 text-emerald-950 border border-emerald-200/80">
              {difficultyLabelRu(course.difficulty)}
            </span>
            <span className="inline-flex items-center rounded-lg bg-gray-100 px-3 py-1.5 text-gray-900 border border-gray-200">
              Шагов: {lessons.length}
            </span>
            <span className="inline-flex items-center rounded-lg bg-amber-100 px-3 py-1.5 text-amber-950 border border-amber-200/80">
              Пройдено: {progressPct}%
            </span>
          </div>
          <div className="mt-4 h-2.5 rounded-full bg-gray-200 overflow-hidden border border-gray-300/80">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-violet-600 transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <aside className="lg:col-span-1 space-y-2">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide px-2">Шаги курса</p>
          <nav className="bg-white rounded-xl border border-gray-200 p-2 space-y-1">
            {lessons.map((les, i) => {
              const open = canOpen[i];
              const done = passedIds.has(les.id);
              const current = i === activeIdx;
              return (
                <button
                  key={les.id}
                  type="button"
                  disabled={!open}
                  onClick={() => open && setActiveIdx(i)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm flex items-start gap-2 transition-colors ${
                    current
                      ? 'bg-indigo-100 text-gray-950 ring-2 ring-indigo-300 font-semibold'
                      : open
                        ? 'hover:bg-gray-100 text-gray-950'
                        : 'text-gray-600 cursor-not-allowed'
                  }`}
                >
                  {!open ? (
                    <Lock className="w-4 h-4 shrink-0 mt-0.5 text-gray-600" />
                  ) : done ? (
                    <CheckCircle className="w-4 h-4 text-green-700 shrink-0 mt-0.5" />
                  ) : (
                    <Circle className="w-4 h-4 text-gray-500 shrink-0 mt-0.5" />
                  )}
                  <span className={current ? '' : 'font-medium'}>
                    <span className="tabular-nums">{i + 1}. </span>
                    {les.title}
                  </span>
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="lg:col-span-3 space-y-6">
          {!lesson ? (
            <p className="text-gray-500">Нет уроков в курсе.</p>
          ) : (
            <>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-3 mb-4 border-b border-gray-200 pb-3">
                  <BookMarked className="w-6 h-6 shrink-0 text-indigo-700" aria-hidden />
                  <h2 className="text-xl font-bold text-gray-950 leading-snug">{lesson.title}</h2>
                </div>
                <div className="max-w-none text-[15px] text-gray-800">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={lessonMarkdownComponents}>
                    {lesson.content}
                  </ReactMarkdown>
                </div>
              </div>

              {cp?.question && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
                  <p className="text-sm font-semibold text-amber-900 mb-1">Контроль после шага</p>
                  <p className="text-gray-900 mb-4">{cp.question}</p>

                  {cp.type === 'single_choice' && cp.options && (
                    <div className="space-y-2 mb-4">
                      {cp.options.map((opt, idx) => (
                        <label
                          key={idx}
                          className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                            choiceIdx === idx
                              ? 'border-indigo-500 bg-indigo-50'
                              : 'border-gray-200 hover:border-gray-300 bg-white'
                          }`}
                        >
                          <input
                            type="radio"
                            name="checkpoint"
                            className="text-indigo-600"
                            checked={choiceIdx === idx}
                            onChange={() => setChoiceIdx(idx)}
                          />
                          <span className="text-sm text-gray-800">{opt}</span>
                        </label>
                      ))}
                    </div>
                  )}

                  {(cp.type === 'numeric' || cp.type === 'short_text') && (
                    <input
                      type="text"
                      value={answerDraft}
                      onChange={(e) => setAnswerDraft(e.target.value)}
                      placeholder={
                        cp.type === 'numeric' ? 'Ваш ответ (число или дробь, напр. 3/4)' : 'Ваш ответ'
                      }
                      className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg mb-4"
                    />
                  )}

                  <button
                    type="button"
                    onClick={submitCheckpoint}
                    disabled={submitting}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-60"
                  >
                    <Send className="w-4 h-4" />
                    {submitting ? 'Проверка…' : 'Проверить ответ'}
                  </button>
                  <p className="text-xs text-gray-500 mt-3">
                    Верные и неверные ответы учитываются в вашей статистике и графе знаний по теме курса.
                  </p>
                </div>
              )}

              {passedIds.size === lessons.length && lessons.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                  <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
                  <p className="font-semibold text-green-900">Курс пройден</p>
                  <p className="text-sm text-green-800 mt-1">
                    Вы выполнили все контрольные вопросы. Загляните в «Граф знаний», чтобы увидеть обновление по теме.
                  </p>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
