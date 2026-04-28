import { useEffect, useMemo, useRef, useState } from 'react';
import { fetchHomeworks, Homework } from '../services/homework';
import { BookOpen, CheckCircle, ChevronDown, ChevronRight, Clock, Loader2, MessageCircle, Send } from 'lucide-react';
import {
  getTest,
  getTestSubmission,
  QuestionResult,
  submitTest,
  SubmittedAnswerPayload,
  TestDetail,
  TestSubmissionDetail,
} from '../services/tests';
import { toast } from 'sonner';

function statusLabel(status: string) {
  switch (status) {
    case 'new':
      return 'Новое';
    case 'in_progress':
      return 'В процессе';
    case 'submitted':
      return 'Отправлено';
    case 'checked':
      return 'Проверено';
    default:
      return status;
  }
}

function statusColor(status: string) {
  switch (status) {
    case 'new':
      return 'bg-blue-100 text-blue-700';
    case 'in_progress':
      return 'bg-amber-100 text-amber-700';
    case 'submitted':
      return 'bg-purple-100 text-purple-700';
    case 'checked':
      return 'bg-green-100 text-green-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export function HomeworkTab() {
  const [homeworks, setHomeworks] = useState<Homework[]>([]);
  const [loading, setLoading] = useState(false);
  const [testSubmitLoading, setTestSubmitLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [assignmentTests, setAssignmentTests] = useState<Record<number, TestDetail>>({});
  const [assignmentTestErrors, setAssignmentTestErrors] = useState<Record<number, string>>({});
  const [submissionResults, setSubmissionResults] = useState<Record<number, TestSubmissionDetail | null>>({});
  const [expandedHomeworks, setExpandedHomeworks] = useState<Record<number, boolean>>({});
  const testAttemptStartedAt = useRef<Record<number, number>>({});
  const [submissionElapsedSeconds, setSubmissionElapsedSeconds] = useState<Record<number, number>>({});
  const [draftAnswers, setDraftAnswers] = useState<Record<number, Record<number, {
    selected_option_indexes: number[];
    answer_text: string;
    answer_number: string;
    student_explanation: string;
  }>>>({});
  const userId = localStorage.getItem('user_id') || 'student';

  const normalizeSubject = (subject?: string) => {
    const value = (subject || '').trim();
    return value || 'Без предмета';
  };

  const groupedHomeworks = useMemo(() => {
    const groups: Record<string, Homework[]> = {};
    homeworks.forEach((hw) => {
      const key = normalizeSubject(hw.subject);
      if (!groups[key]) groups[key] = [];
      groups[key].push(hw);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b, 'ru'));
  }, [homeworks]);

  const buildEmptyDrafts = (test: TestDetail) =>
    test.questions.reduce<Record<number, {
      selected_option_indexes: number[];
      answer_text: string;
      answer_number: string;
      student_explanation: string;
    }>>((acc, question) => {
      acc[question.id] = {
        selected_option_indexes: [],
        answer_text: '',
        answer_number: '',
        student_explanation: '',
      };
      return acc;
    }, {});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHomeworks(userId);
      setHomeworks(data);
      const testHomeworks = data.filter((hw) => (hw.kind || 'test') === 'test' && hw.test_id);

      const testsMap: Record<number, TestDetail> = {};
      const errorsMap: Record<number, string> = {};
      const nextDrafts: Record<number, Record<number, {
        selected_option_indexes: number[];
        answer_text: string;
        answer_number: string;
        student_explanation: string;
      }>> = {};

      await Promise.all(
        testHomeworks.map(async (hw) => {
          try {
            const test = await getTest(hw.test_id!);
            testsMap[hw.id] = test;
            nextDrafts[hw.id] = buildEmptyDrafts(test);
          } catch (e: unknown) {
            const detail =
              typeof e === 'object' && e !== null && 'response' in e
                ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
                : undefined;
            errorsMap[hw.id] =
              typeof detail === 'string'
                ? detail
                : 'Не удалось загрузить тест. Возможно, он удалён — попросите учителя назначить задание заново.';
          }
        })
      );

      const resultEntries = await Promise.all(
        testHomeworks
          .filter((hw) => hw.latest_test_submission_id)
          .map(async (hw) => ({
            homeworkId: hw.id,
            submission: await getTestSubmission(hw.latest_test_submission_id!),
          }))
      );

      const resultsMap: Record<number, TestSubmissionDetail | null> = {};
      resultEntries.forEach(({ homeworkId, submission }) => {
        resultsMap[homeworkId] = submission;
      });

      setAssignmentTests(testsMap);
      setAssignmentTestErrors(errorsMap);
      setSubmissionResults(resultsMap);
      setDraftAnswers((prev) => ({ ...nextDrafts, ...prev }));
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Не удалось загрузить домашки');
    } finally {
      setLoading(false);
    }
  };

  const isOverdue = (homework: Homework) => {
    if (!homework.due_date) return false;
    if (homework.status === 'submitted' || homework.status === 'checked') return false;
    return new Date(homework.due_date).getTime() < Date.now();
  };

  const toggleHomework = (homeworkId: number) => {
    setExpandedHomeworks((prev) => {
      const nextOpen = !prev[homeworkId];
      if (nextOpen && !testAttemptStartedAt.current[homeworkId]) {
        testAttemptStartedAt.current[homeworkId] = Date.now();
      }
      return { ...prev, [homeworkId]: nextOpen };
    });
  };

  useEffect(() => {
    load();
  }, []);

  const updateDraft = (
    homeworkId: number,
    questionId: number,
    updater: (current: {
      selected_option_indexes: number[];
      answer_text: string;
      answer_number: string;
      student_explanation: string;
    }) => {
      selected_option_indexes: number[];
      answer_text: string;
      answer_number: string;
      student_explanation: string;
    }
  ) => {
    setDraftAnswers((prev) => {
      const byHomework = prev[homeworkId] || {};
      const current = byHomework[questionId] || {
        selected_option_indexes: [],
        answer_text: '',
        answer_number: '',
        student_explanation: '',
      };
      return {
        ...prev,
        [homeworkId]: {
          ...byHomework,
          [questionId]: updater(current),
        },
      };
    });
  };

  const toggleOption = (homeworkId: number, questionId: number, optionIndex: number, multiple?: boolean) => {
    updateDraft(homeworkId, questionId, (current) => {
      if (!multiple) {
        return { ...current, selected_option_indexes: [optionIndex] };
      }
      const selected = current.selected_option_indexes.includes(optionIndex)
        ? current.selected_option_indexes.filter((idx) => idx !== optionIndex)
        : [...current.selected_option_indexes, optionIndex];
      return { ...current, selected_option_indexes: selected };
    });
  };

  const buildPayload = (homeworkId: number, test: TestDetail): SubmittedAnswerPayload[] =>
    test.questions.map((question) => {
      const draft = draftAnswers[homeworkId]?.[question.id];
      return {
        question_id: question.id,
        selected_option_indexes: draft?.selected_option_indexes || [],
        answer_text: draft?.answer_text || undefined,
        answer_number: draft?.answer_number ? Number(draft.answer_number) : undefined,
        student_explanation: draft?.student_explanation || undefined,
      };
    });

  const isAnswerComplete = (homeworkId: number, question: TestDetail['questions'][number]) => {
    const draft = draftAnswers[homeworkId]?.[question.id];
    if (!draft) return false;
    if (question.question_type === 'text') return Boolean(draft.answer_text.trim());
    if (question.question_type === 'numeric') return Boolean(draft.answer_number.trim());
    return draft.selected_option_indexes.length > 0;
  };

  const openAiDiscussion = ({
    homework,
    test,
    submission,
    questionResult,
  }: {
    homework: Homework;
    test: TestDetail;
    submission?: TestSubmissionDetail | null;
    questionResult?: QuestionResult;
  }) => {
    const detail = {
      context: {
        homework_id: homework.id,
        test_id: test.id,
        test_submission_id: submission?.id,
        question_id: questionResult?.question_id,
        label: questionResult
          ? `вопрос: ${questionResult.question}`
          : `тест: ${test.title}`,
      },
      message: questionResult
        ? `Помоги разобрать вопрос "${questionResult.question}". Почему мой ответ ${questionResult.is_correct ? 'считается верным' : 'неверный'} и как надо рассуждать?`
        : `Помоги разобрать тест "${test.title}" и мои ошибки.`,
    };
    window.dispatchEvent(new CustomEvent('ai-chat-context', { detail }));
    toast.success('Контекст теста передан в AI-чат');
  };

  const handleSubmitTestHomework = async (hw: Homework) => {
    const test = assignmentTests[hw.id];
    if (!test) {
      toast.error('Тест для этого задания не найден');
      return;
    }
    if (test.questions.some((question) => !isAnswerComplete(hw.id, question))) {
      toast.error('Ответьте на все вопросы перед отправкой');
      return;
    }

    setTestSubmitLoading(hw.id);
    setError(null);
    try {
      const started = testAttemptStartedAt.current[hw.id];
      const elapsedSec =
        started != null ? Math.max(1, Math.round((Date.now() - started) / 1000)) : undefined;
      const result = await submitTest(test.id, {
        user_id: userId,
        homework_id: hw.id,
        time_spent_seconds: elapsedSec,
        answers: buildPayload(hw.id, test),
      });
      const elapsed =
        result.time_spent_seconds != null && result.time_spent_seconds > 0
          ? Math.round(Number(result.time_spent_seconds))
          : elapsedSec;
      if (elapsed != null) {
        setSubmissionElapsedSeconds((prev) => ({ ...prev, [hw.id]: elapsed }));
      }
      const detailedSubmission = await getTestSubmission(result.submission_id);
      setSubmissionResults((prev) => ({ ...prev, [hw.id]: detailedSubmission }));
      setHomeworks((prev) =>
        prev.map((item) =>
          item.id === hw.id
            ? {
                ...item,
                status: 'submitted',
                latest_submission_id: result.submission_id,
                latest_test_submission_id: result.submission_id,
              }
            : item
        )
      );
      toast.success(`Тест отправлен. Результат: ${result.earned_points}/${result.max_points} балл. (${result.score}%)`);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Не удалось отправить тест');
    } finally {
      setTestSubmitLoading(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Мои домашние задания</h2>
        </div>
        <button
          onClick={load}
          className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
          disabled={loading}
        >
          Обновить
        </button>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

      {loading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          Загружаем домашние задания...
        </div>
      )}

      {!loading && homeworks.length === 0 && (
        <div className="p-4 bg-white border border-dashed border-gray-300 rounded-lg text-gray-600 text-sm">
          Домашних заданий пока нет.
        </div>
      )}

      <div className="space-y-5">
        {groupedHomeworks.map(([subjectName, subjectHomeworks]) => (
          <section key={subjectName} className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border border-blue-100 bg-blue-50/70 px-3 py-2">
              <h3 className="text-sm font-semibold text-blue-900">{subjectName}</h3>
              <span className="text-xs text-blue-700">{subjectHomeworks.length} шт.</span>
            </div>
            {subjectHomeworks.map((hw) => (
              <div key={hw.id} className={`bg-white border rounded-xl p-4 shadow-sm ${isOverdue(hw) ? 'border-red-200' : 'border-gray-200'}`}>
            <button
              type="button"
              onClick={() => toggleHomework(hw.id)}
              className="flex w-full items-start justify-between gap-3 text-left"
            >
              <div className="flex items-start gap-3">
                <div className="mt-1 text-gray-400">
                  {expandedHomeworks[hw.id] ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                </div>
                <div>
                  <p className="text-sm text-gray-500">{normalizeSubject(hw.subject)}</p>
                  <h3 className="text-lg font-semibold text-gray-900">{hw.title}</h3>
                  <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-gray-500">
                    {hw.due_date && (
                      <div className={`flex items-center gap-2 ${isOverdue(hw) ? 'text-red-600 font-medium' : ''}`}>
                        <Clock className="w-4 h-4" />
                        Дедлайн: {new Date(hw.due_date).toLocaleDateString('ru-RU')}
                        {isOverdue(hw) && <span className="text-xs uppercase">Просрочено</span>}
                      </div>
                    )}
                    {assignmentTests[hw.id] && (
                      <span>
                        Максимум: {assignmentTests[hw.id].max_points ?? assignmentTests[hw.id].questions.reduce((sum, question) => sum + Number(question.points || 1), 0)} балл.
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${isOverdue(hw) ? 'bg-red-100 text-red-700' : statusColor(hw.status)}`}>
                {isOverdue(hw) ? 'Просрочено' : statusLabel(hw.status)}
              </span>
            </button>

            {expandedHomeworks[hw.id] && (() => {
              const test = assignmentTests[hw.id];
              const result = submissionResults[hw.id];
              const isTestAssignment = (hw.kind || 'test') === 'test' && !!test;

              if (isTestAssignment && test) {
                return (
                  <div className="mt-4 space-y-4">
                    <div className="text-sm text-gray-700">
                      Тип: {hw.assignment_type === 'control'
                        ? 'Контрольная работа'
                        : hw.assignment_type === 'quiz'
                        ? 'Проверочная'
                        : 'Домашняя работа'} • Вопросов: {test.questions.length}
                    </div>
                    {(hw.status === 'submitted' || hw.status === 'checked') && result && (
                      <div className="p-4 rounded-xl bg-green-50 border border-green-200 space-y-3">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-sm text-green-700">Результат отправлен учителю</div>
                            <div className="text-lg font-semibold text-gray-900">
                              {result.earned_points ?? 0} из {result.max_points ?? test.max_points ?? 0} балл. • {result.correct_count ?? 0} из {result.total_questions ?? test.questions.length} правильных • {result.score}%
                            </div>
                            {submissionElapsedSeconds[hw.id] != null && (
                              <div className="mt-1 flex items-center gap-1 text-sm text-gray-600">
                                <Clock className="h-4 w-4" />
                                Время на тест: {submissionElapsedSeconds[hw.id]} сек
                              </div>
                            )}
                          </div>
                          <button
                            type="button"
                            onClick={() => openAiDiscussion({ homework: hw, test, submission: result })}
                            className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-white border border-green-300 rounded-lg hover:bg-green-100"
                          >
                            <MessageCircle className="w-4 h-4" />
                            Обсудить с AI
                          </button>
                        </div>
                        {result.summary && <p className="text-sm text-gray-700">{result.summary}</p>}
                        <div className="space-y-3">
                          {result.question_results.map((questionResult, idx) => (
                            <div
                              key={questionResult.question_id}
                              className={`p-3 rounded-lg border ${
                                questionResult.is_correct
                                  ? 'bg-white border-green-200'
                                  : 'bg-red-50 border-red-200'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <p className="text-sm font-medium text-gray-900">
                                    {idx + 1}. {questionResult.question}
                                  </p>
                                  <p className="text-xs text-gray-600 mt-1">
                                    Ваш ответ:{' '}
                                    {Array.isArray(questionResult.student_answer)
                                      ? questionResult.selected_option_texts?.join(', ') || String(questionResult.student_answer)
                                      : String(questionResult.student_answer ?? '—')}
                                  </p>
                                  <p className="text-xs text-gray-600">
                                    Правильный ответ: {questionResult.correct_answer_text || '—'}
                                  </p>
                                  {questionResult.student_explanation && (
                                    <p className="text-xs text-gray-600">
                                      Как вы решали: {questionResult.student_explanation}
                                    </p>
                                  )}
                                  {questionResult.question_explanation && (
                                    <p className="text-sm text-gray-700 mt-2">{questionResult.question_explanation}</p>
                                  )}
                                  <p className="text-xs text-gray-500 mt-1">
                                    Баллы: {questionResult.earned_points ?? 0}/{questionResult.max_points ?? questionResult.points ?? 0}
                                  </p>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => openAiDiscussion({ homework: hw, test, submission: result, questionResult })}
                                  className="text-sm text-blue-600 hover:text-blue-700"
                                >
                                  Спросить AI
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {(hw.status !== 'submitted' && hw.status !== 'checked') && test.questions.map((question, qIdx) => (
                      <div key={question.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
                        <p className="text-sm text-gray-900">{qIdx + 1}. {question.question}</p>
                        {(question.question_type === 'single' || !question.question_type) && (
                          <div className="space-y-2">
                            {question.options.map((option, optIdx) => (
                              <label key={optIdx} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                                <input
                                  type="radio"
                                  name={`hw-${hw.id}-q-${question.id}`}
                                  checked={(draftAnswers[hw.id]?.[question.id]?.selected_option_indexes || [])[0] === optIdx}
                                  onChange={() => toggleOption(hw.id, question.id, optIdx)}
                                  disabled={testSubmitLoading === hw.id}
                                />
                                <span>{option}</span>
                              </label>
                            ))}
                          </div>
                        )}
                        {question.question_type === 'multiple' && (
                          <div className="space-y-2">
                            {question.options.map((option, optIdx) => (
                              <label key={optIdx} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={(draftAnswers[hw.id]?.[question.id]?.selected_option_indexes || []).includes(optIdx)}
                                  onChange={() => toggleOption(hw.id, question.id, optIdx, true)}
                                  disabled={testSubmitLoading === hw.id}
                                />
                                <span>{option}</span>
                              </label>
                            ))}
                          </div>
                        )}
                        {question.question_type === 'text' && (
                          <textarea
                            value={draftAnswers[hw.id]?.[question.id]?.answer_text || ''}
                            onChange={(e) =>
                              updateDraft(hw.id, question.id, (current) => ({ ...current, answer_text: e.target.value }))
                            }
                            rows={3}
                            className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Введите ответ"
                            disabled={testSubmitLoading === hw.id}
                          />
                        )}
                        {question.question_type === 'numeric' && (
                          <input
                            type="number"
                            value={draftAnswers[hw.id]?.[question.id]?.answer_number || ''}
                            onChange={(e) =>
                              updateDraft(hw.id, question.id, (current) => ({ ...current, answer_number: e.target.value }))
                            }
                            className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Введите число"
                            disabled={testSubmitLoading === hw.id}
                          />
                        )}
                        <textarea
                          value={draftAnswers[hw.id]?.[question.id]?.student_explanation || ''}
                          onChange={(e) =>
                            updateDraft(hw.id, question.id, (current) => ({ ...current, student_explanation: e.target.value }))
                          }
                          rows={2}
                          className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="Объясните, как вы решали этот вопрос"
                          disabled={testSubmitLoading === hw.id}
                        />
                      </div>
                    ))}
                    <div className="flex items-center justify-between">
                      <button
                        onClick={() => handleSubmitTestHomework(hw)}
                        disabled={
                          testSubmitLoading === hw.id ||
                          hw.status === 'submitted' ||
                          hw.status === 'checked'
                        }
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg disabled:opacity-50 hover:bg-blue-700 transition"
                      >
                        {testSubmitLoading === hw.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Send className="w-4 h-4" />
                        )}
                        Отправить тест
                      </button>
                      {(hw.status === 'submitted' || hw.status === 'checked') && (
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-1 text-green-600 text-sm">
                            <CheckCircle className="w-4 h-4" />
                            Отправлено
                          </div>
                          <p className="text-xs text-gray-500">Ответы видны учителю в разделе «Проверка работ».</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              if (
                (hw.kind || 'test') === 'test' &&
                (hw.test_id == null || hw.test_id === undefined)
              ) {
                return (
                  <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                    Задание создано без привязки к тесту в базе. Учителю нужно назначить тест через «Назначить тест ученику»
                    или «Назначить ДЗ» у сохранённого теста — тогда у задания появится связь с тестом, и его можно будет пройти.
                  </div>
                );
              }
              if (assignmentTestErrors[hw.id]) {
                return (
                  <div className="mt-4 space-y-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                    <p className="font-medium">Тест недоступен</p>
                    <p>{assignmentTestErrors[hw.id]}</p>
                    <p className="text-red-700/90">
                      Если тест удалили или база сброшена, попросите учителя удалить это задание и назначить тест снова.
                    </p>
                  </div>
                );
              }
              return (
                <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                  Это домашнее задание еще не привязано к тесту. Для нового сценария назначайте ученикам тесты как ДЗ.
                </div>
              );
            })()}
              </div>
            ))}
          </section>
        ))}
      </div>
    </div>
  );
}






