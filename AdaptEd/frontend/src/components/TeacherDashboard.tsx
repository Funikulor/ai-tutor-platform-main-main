import { useEffect, useMemo, useRef, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Users, TrendingUp, AlertCircle, Download, Filter, BarChart3, FileText, PenSquare, ClipboardList, X, Phone, Loader2, Sparkles, Trophy } from 'lucide-react';
import { TeacherTestsTab } from './TeacherTestsTab';
import { AIChatPanel } from './AIChatPanel';
import api from '../services/api';
import { avatarInitial } from '../utils/avatar';
import { toast } from 'sonner';

type StudentStatus = 'excellent' | 'good' | 'average' | 'needs-help';

interface StudentRow {
  student: string;
  score: number;
  topics: number;
  errors: number;
  status: StudentStatus;
  user_id: string;
}

interface CommonErrorRow {
  topic: string;
  students: number;
  errorType: string;
  frequency: number;
}

interface TopicPerformanceRow {
  topic: string;
  avgScore: number;
  completion: number;
}

interface ClassAnalyticsResponse {
  classData?: StudentRow[];
  commonErrors?: CommonErrorRow[];
  topicPerformance?: TopicPerformanceRow[];
  totalStudents?: number;
  averageScore?: number;
  needsHelpCount?: number;
}

interface UserRow {
  user_id: string;
  role: string;
  class_id?: string | null;
  full_name?: string;
  email?: string;
  phone?: string | null;
  parent_fio?: string | null;
  parent_phone?: string | null;
}

interface ParentContact {
  full_name: string;
  phone: string;
}

interface RatingRow {
  rank: number;
  user_id: string;
  student: string;
  rating: number;
  status: string;
  test_score: number;
  homework_score: number;
  debt_score: number;
  debts_open: number;
}

interface StudentCardData {
  student: { user_id: string; full_name?: string; email?: string; class_id?: string };
  stats: { points: number; level: number; accuracy_rate: number; total_tasks: number; correct_tasks: number };
  strengths: Array<{ topic: string; mastery: number }>;
  weaknesses: Array<{ topic: string; mastery: number }>;
  debts: Array<{ id: number; topic: string; status: string; progress: number; due_date?: string | null; priority: number }>;
  rating: { rating: number; status: string; test_score: number; homework_score: number; debt_score: number };
}

const TABLE_PAGE_SIZE = 12;

export function TeacherDashboard() {
  const [selectedClass, setSelectedClass] = useState('all');
  const [currentView, setCurrentView] = useState<'analytics' | 'create-tests' | 'created-tests' | 'results'>('analytics');
  const [preselectedStudentId, setPreselectedStudentId] = useState<string | null>(null);
  const [classData, setClassData] = useState<StudentRow[]>([]);
  const [commonErrors, setCommonErrors] = useState<CommonErrorRow[]>([]);
  const [topicPerformance, setTopicPerformance] = useState<TopicPerformanceRow[]>([]);
  const [availableClasses, setAvailableClasses] = useState<string[]>([]);
  const [parentContactsByStudentId, setParentContactsByStudentId] = useState<Record<string, ParentContact>>({});
  const [loading, setLoading] = useState(false);
  const [assigningStudentId, setAssigningStudentId] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'all' | StudentStatus>('all');
  const [minScoreFilter, setMinScoreFilter] = useState(0);
  const [detailStudent, setDetailStudent] = useState<StudentRow | null>(null);
  const [detailCard, setDetailCard] = useState<StudentCardData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [classRating, setClassRating] = useState<RatingRow[]>([]);
  const [tablePage, setTablePage] = useState(0);
  const performanceTableRef = useRef<HTMLDivElement>(null);
  const [isChatMinimized, setIsChatMinimized] = useState(true);

  const visibleStudents = useMemo(() => {
    return classData.filter((student) => {
      const statusOk = statusFilter === 'all' || student.status === statusFilter;
      const scoreOk = student.score >= minScoreFilter;
      return statusOk && scoreOk;
    });
  }, [classData, statusFilter, minScoreFilter]);

  const averageScore = useMemo(() => {
    if (visibleStudents.length === 0) return 0;
    return Math.round(visibleStudents.reduce((acc, s) => acc + s.score, 0) / visibleStudents.length);
  }, [visibleStudents]);

  const needsHelpTotalInClass = useMemo(
    () => classData.filter((s) => s.status === 'needs-help').length,
    [classData]
  );

  const paginatedStudents = useMemo(() => {
    const start = tablePage * TABLE_PAGE_SIZE;
    return visibleStudents.slice(start, start + TABLE_PAGE_SIZE);
  }, [visibleStudents, tablePage]);

  const tablePageCount = Math.max(1, Math.ceil(visibleStudents.length / TABLE_PAGE_SIZE));

  useEffect(() => {
    setTablePage(0);
  }, [classData, statusFilter, minScoreFilter, selectedClass]);

  useEffect(() => {
    setTablePage((p) => Math.min(p, Math.max(0, tablePageCount - 1)));
  }, [tablePageCount]);

  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true);
      try {
        const [analyticsResponse, usersResponse, ratingResponse] = await Promise.all([
          api.get<ClassAnalyticsResponse>('/teacher/class-analytics', {
            params: selectedClass && selectedClass !== 'all' ? { class_id: selectedClass } : undefined,
          }),
          api.get<UserRow[]>('/all'),
          api.get<{ rows: RatingRow[] }>('/teacher/class-rating', {
            params: selectedClass && selectedClass !== 'all' ? { class_id: selectedClass } : undefined,
          }),
        ]);

        const users = Array.isArray(usersResponse.data) ? usersResponse.data : [];
        const students = users.filter((u) => u.role === 'student');
        const parents = users.filter((u) => u.role === 'parent');

        const classes = Array.from(
          new Set(students.map((s) => s.class_id).filter((v): v is string => !!v))
        ).sort((a, b) => a.localeCompare(b, 'ru'));
        if (classes.length > 0) {
          setAvailableClasses(classes);
          if (selectedClass !== 'all' && !classes.includes(selectedClass)) {
            setSelectedClass(classes[0]);
          }
        }

        const studentClassById: Record<string, string> = {};
        students.forEach((student) => {
          if (student.user_id && student.class_id) {
            studentClassById[student.user_id] = student.class_id;
          }
        });

        const parentsByClass: Record<string, ParentContact[]> = {};
        parents.forEach((parent) => {
          const classId = parent.class_id || '';
          if (!classId) return;
          if (!parentsByClass[classId]) {
            parentsByClass[classId] = [];
          }
          if (parent.phone) {
            parentsByClass[classId].push({
              full_name: parent.full_name || parent.email || parent.user_id,
              phone: parent.phone,
            });
          }
        });

        const allParents = Object.values(parentsByClass).flat();
        const analytics = analyticsResponse.data || {};
        const nextClassData = (analytics.classData || []).map((student) => {
          const status = student.status || (
            student.score >= 85 ? 'excellent' :
            student.score >= 70 ? 'good' :
            student.score >= 60 ? 'average' :
            'needs-help'
          );
          return {
            ...student,
            status,
          };
        });

        const contacts: Record<string, ParentContact> = {};
        const usersById: Record<string, UserRow> = {};
        users.forEach((u) => { if (u.user_id) usersById[u.user_id] = u; });
        nextClassData.forEach((student) => {
          const user = usersById[student.user_id];
          if (user?.parent_fio || user?.parent_phone) {
            contacts[student.user_id] = {
              full_name: user.parent_fio || '',
              phone: user.parent_phone || ''
            };
            return;
          }
          const classId = studentClassById[student.user_id];
          const byClass = classId ? parentsByClass[classId] : [];
          const contact = byClass?.[0] || allParents[0];
          if (contact && student.user_id) {
            contacts[student.user_id] = contact;
          }
        });

        setParentContactsByStudentId(contacts);
        setClassData(nextClassData);
        setCommonErrors(analytics.commonErrors || []);
        setTopicPerformance(analytics.topicPerformance || []);
        setClassRating(ratingResponse.data?.rows || []);
      } catch (error: any) {
        const message = error?.response?.data?.detail || 'Не удалось загрузить аналитику класса';
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    if (currentView === 'analytics') {
      loadAnalytics();
    }
  }, [selectedClass, currentView]);

  const handleExport = () => {
    if (classData.length === 0) {
      toast.info('Нет данных для экспорта');
      return;
    }

    const rows = classData.map((student) => {
      const contact = parentContactsByStudentId[student.user_id];
      return [
        student.student,
        student.score,
        student.topics,
        student.errors,
        student.status,
        contact?.full_name || '',
        contact?.phone || '',
      ];
    });

    const csvHeader = [
      'Ученик',
      'Средний балл',
      'Изучено тем',
      'Ошибок',
      'Статус',
      'Родитель',
      'Телефон родителя',
    ];
    const csvContent = [csvHeader, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','))
      .join('\n');

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics_${selectedClass}_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    toast.success('Экспорт аналитики завершен');
  };

  const handleAssignBeforeLesson = async (student: StudentRow) => {
    setAssigningStudentId(student.user_id);
    setPreselectedStudentId(student.user_id);
    setCurrentView('created-tests');
    toast.info(`Выберите тест и назначьте ${student.student} во вкладке "Созданные тесты"`);
    setTimeout(() => setAssigningStudentId(null), 300);
  };

  const handleShowParentContact = (student: StudentRow) => {
    const contact = parentContactsByStudentId[student.user_id];
    if (!contact) {
      toast.error(`Контакт родителя для ${student.student} не найден`);
      return;
    }
    toast.info(`Родитель: ${contact.full_name} • ${contact.phone}`);
  };

  const handleOpenStudentCard = async (student: StudentRow) => {
    setDetailStudent(student);
    setDetailCard(null);
    setDetailLoading(true);
    try {
      const response = await api.get<StudentCardData>(`/teacher/student-card/${student.user_id}`);
      setDetailCard(response.data);
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Не удалось загрузить карточку ученика';
      toast.error(message);
    } finally {
      setDetailLoading(false);
    }
  };

  const assignAdaptiveRemedial = async (student: StudentRow) => {
    try {
      const topic = window.prompt('Тема для отработки пробела', detailCard?.weaknesses?.[0]?.topic || 'Алгебра');
      if (!topic) return;
      await api.post(`/teacher/students/${student.user_id}/debts/assign-remedial`, {
        topic,
        kind: 'adaptive_task',
        attempts_required: 3,
        notes: 'Отработка пробела через адаптивные задания',
        payload: { topic },
      });
      toast.success('Работа над ошибками назначена');
      await handleOpenStudentCard(student);
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Не удалось назначить работу над ошибками';
      toast.error(message);
    }
  };

  const assignLibrary = async (student: StudentRow, kind: 'material' | 'course') => {
    try {
      const idPrompt = kind === 'material' ? 'ID материала (например m1)' : 'ID курса (например fractions-course)';
      const value = window.prompt(idPrompt, '');
      if (!value) return;
      await api.post(`/teacher/students/${student.user_id}/assign-library`, {
        kind,
        material_id: kind === 'material' ? value : undefined,
        course_id: kind === 'course' ? value : undefined,
        topic: detailCard?.weaknesses?.[0]?.topic || detailStudent?.student || 'Библиотека',
        title: kind === 'material' ? 'Чтение материала' : 'Прохождение курса',
      });
      toast.success(kind === 'material' ? 'Материал назначен' : 'Курс назначен');
      await handleOpenStudentCard(student);
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Не удалось назначить из библиотеки';
      toast.error(message);
    }
  };

  const handleFocusNeedsHelp = () => {
    setStatusFilter('needs-help');
    setMinScoreFilter(0);
    setFiltersOpen(true);
    requestAnimationFrame(() => {
      performanceTableRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      excellent: 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200/80',
      good: 'bg-sky-50 text-sky-800 ring-1 ring-sky-200/80',
      average: 'bg-amber-50 text-amber-800 ring-1 ring-amber-200/80',
      'needs-help': 'bg-rose-50 text-rose-800 ring-1 ring-rose-200/80'
    };
    const labels = {
      excellent: 'Отлично',
      good: 'Хорошо',
      average: 'Средне',
      'needs-help': 'Нужна помощь'
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Навигация и введение */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-gradient-to-br from-slate-50 via-white to-indigo-50/50 shadow-sm">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_60%_at_100%_0%,rgba(99,102,241,0.11),transparent)]" />
        <div className="relative p-5 sm:p-6">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/25">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-widest text-indigo-600">Кабинет учителя</p>
                <h2 className="mt-0.5 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">Работа с классом</h2>
                <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
                  Сводка успеваемости, типовые ошибки, назначение тестов и просмотр результатов — в одном интерфейсе.
                </p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <button
              type="button"
              onClick={() => setCurrentView('analytics')}
              className={`group flex flex-col gap-0.5 rounded-xl border px-4 py-3 text-left transition-all ${
                currentView === 'analytics'
                  ? 'border-indigo-200 bg-white shadow-md ring-2 ring-indigo-500/15'
                  : 'border-transparent bg-white/50 hover:border-slate-200 hover:bg-white hover:shadow-sm'
              }`}
            >
              <span className="flex items-center gap-2 font-medium text-slate-900">
                <BarChart3 className={`h-5 w-5 ${currentView === 'analytics' ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                Аналитика класса
              </span>
              <span className="pl-7 text-xs text-slate-500">Ученики, баллы, темы</span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentView('create-tests')}
              className={`group flex flex-col gap-0.5 rounded-xl border px-4 py-3 text-left transition-all ${
                currentView === 'create-tests'
                  ? 'border-emerald-200 bg-white shadow-md ring-2 ring-emerald-500/15'
                  : 'border-transparent bg-white/50 hover:border-slate-200 hover:bg-white hover:shadow-sm'
              }`}
            >
              <span className="flex items-center gap-2 font-medium text-slate-900">
                <PenSquare className={`h-5 w-5 ${currentView === 'create-tests' ? 'text-emerald-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                Создание тестов
              </span>
              <span className="pl-7 text-xs text-slate-500">Вручную или с ИИ</span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentView('created-tests')}
              className={`group flex flex-col gap-0.5 rounded-xl border px-4 py-3 text-left transition-all ${
                currentView === 'created-tests'
                  ? 'border-teal-200 bg-white shadow-md ring-2 ring-teal-500/15'
                  : 'border-transparent bg-white/50 hover:border-slate-200 hover:bg-white hover:shadow-sm'
              }`}
            >
              <span className="flex items-center gap-2 font-medium text-slate-900">
                <FileText className={`h-5 w-5 ${currentView === 'created-tests' ? 'text-teal-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                Созданные тесты
              </span>
              <span className="pl-7 text-xs text-slate-500">Редактирование и назначение</span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentView('results')}
              className={`group flex flex-col gap-0.5 rounded-xl border px-4 py-3 text-left transition-all ${
                currentView === 'results'
                  ? 'border-violet-200 bg-white shadow-md ring-2 ring-violet-500/15'
                  : 'border-transparent bg-white/50 hover:border-slate-200 hover:bg-white hover:shadow-sm'
              }`}
            >
              <span className="flex items-center gap-2 font-medium text-slate-900">
                <ClipboardList className={`h-5 w-5 ${currentView === 'results' ? 'text-violet-600' : 'text-slate-400 group-hover:text-slate-600'}`} />
                Результаты учеников
              </span>
              <span className="pl-7 text-xs text-slate-500">Попытки и обратная связь</span>
            </button>
          </div>
        </div>
      </div>

      {currentView === 'create-tests' && (
        <div className="rounded-2xl border border-slate-200/90 bg-white px-4 py-5 shadow-sm sm:px-6 sm:py-6">
          <TeacherTestsTab mode="create" preselectedStudentId={preselectedStudentId} />
        </div>
      )}
      {currentView === 'created-tests' && (
        <div className="rounded-2xl border border-slate-200/90 bg-white px-4 py-5 shadow-sm sm:px-6 sm:py-6">
          <TeacherTestsTab mode="manage" preselectedStudentId={preselectedStudentId} />
        </div>
      )}
      {currentView === 'results' && (
        <div className="rounded-2xl border border-slate-200/90 bg-white px-4 py-5 shadow-sm sm:px-6 sm:py-6">
          <TeacherTestsTab mode="results" preselectedStudentId={preselectedStudentId} />
        </div>
      )}

      {/* Analytics View */}
      {currentView === 'analytics' && (
        <>
      <div className="relative rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
        {loading && (
          <div className="absolute right-4 top-4 flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 ring-1 ring-indigo-100">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Обновление данных
          </div>
        )}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Сводка по выбранному классу</h3>
            <p className="mt-1 text-sm text-slate-600">
              Фильтруйте по статусу и баллу, экспортируйте таблицу для отчёта.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="min-w-[160px] rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm text-slate-800 shadow-sm transition focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="all">Все классы</option>
              {availableClasses.map((classId) => (
                <option key={classId} value={classId}>
                  Класс {classId}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setFiltersOpen((v) => !v)}
              className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                filtersOpen
                  ? 'border-indigo-200 bg-indigo-50 text-indigo-800'
                  : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <Filter className="h-4 w-4" />
              Фильтры
            </button>
            <button
              type="button"
              onClick={handleExport}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-600/20 transition hover:bg-indigo-700"
            >
              <Download className="h-4 w-4" />
              Экспорт CSV
            </button>
          </div>
        </div>
        {filtersOpen && (
          <div className="mt-5 grid grid-cols-1 gap-3 rounded-xl border border-slate-100 bg-slate-50/80 p-4 md:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">Статус ученика</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as 'all' | StudentStatus)}
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              >
                <option value="all">Все статусы</option>
                <option value="excellent">Отлично</option>
                <option value="good">Хорошо</option>
                <option value="average">Средне</option>
                <option value="needs-help">Нужна помощь</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-slate-500">Мин. средний балл (%)</label>
              <input
                type="number"
                min={0}
                max={100}
                value={minScoreFilter}
                onChange={(e) => setMinScoreFilter(Math.max(0, Math.min(100, Number(e.target.value) || 0)))}
                placeholder="0"
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm transition hover:border-indigo-200/80 hover:shadow-md">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-indigo-500/10 blur-2xl transition group-hover:bg-indigo-500/15" />
          <div className="relative flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">В зоне фильтра</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">{visibleStudents.length}</p>
              <p className="mt-1 text-sm text-slate-600">учеников</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-600">
              <Users className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm transition hover:border-emerald-200/80 hover:shadow-md">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-emerald-500/10 blur-2xl transition group-hover:bg-emerald-500/15" />
          <div className="relative flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Средний балл</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">{averageScore}%</p>
              <p className="mt-1 text-sm text-slate-600">по отфильтрованным</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600">
              <TrendingUp className="h-6 w-6" />
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleFocusNeedsHelp}
          disabled={needsHelpTotalInClass === 0}
          className="group relative w-full overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 text-left shadow-sm transition hover:border-rose-300 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:border-slate-200 disabled:hover:shadow-sm"
        >
          <div className="absolute -right-4 -top-4 h-20 w-20 rounded-full bg-rose-500/10 blur-2xl group-hover:bg-rose-500/15 disabled:opacity-0" />
          <div className="relative flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Нужна помощь</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">{needsHelpTotalInClass}</p>
              {needsHelpTotalInClass > 0 ? (
                <p className="mt-1 text-xs font-medium text-rose-600">Нажмите — фильтр и таблица</p>
              ) : (
                <p className="mt-1 text-sm text-slate-500">Все в норме</p>
              )}
            </div>
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-rose-100 text-rose-600">
              <AlertCircle className="h-6 w-6" />
            </div>
          </div>
        </button>

        <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm transition hover:border-violet-200/80 hover:shadow-md">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-violet-500/10 blur-2xl transition group-hover:bg-violet-500/15" />
          <div className="relative flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Тем в среднем</p>
              <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900">
                {visibleStudents.length > 0
                  ? Math.round(visibleStudents.reduce((acc, s) => acc + s.topics, 0) / visibleStudents.length)
                  : 0}
              </p>
              <p className="mt-1 text-sm text-slate-600">изучено на ученика</p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-100 text-lg font-bold text-violet-600">
              ✓
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/90 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-5 py-4 sm:px-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Рейтинг класса (только для учителя)</h3>
            <p className="mt-1 text-sm text-slate-600">Формула: тесты + домашка в срок + закрытие долгов.</p>
          </div>
          <Trophy className="h-5 w-5 text-amber-500" />
        </div>
        <div className="overflow-x-auto px-2 pb-2 sm:px-4 sm:pb-4">
          <table className="w-full min-w-[640px] border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="border-b border-slate-200 py-3 pl-4 pr-2 sm:pl-2">#</th>
                <th className="border-b border-slate-200 py-3 px-2">Ученик</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Рейтинг</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Тесты</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Домашка</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Долги</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Статус</th>
              </tr>
            </thead>
            <tbody>
              {classRating.slice(0, 10).map((row) => (
                <tr key={row.user_id} className="hover:bg-slate-50/70">
                  <td className="border-b border-slate-100 py-3 pl-4 pr-2 text-sm text-slate-700 sm:pl-2">{row.rank}</td>
                  <td className="border-b border-slate-100 py-3 px-2 text-sm font-medium text-slate-900">{row.student}</td>
                  <td className="border-b border-slate-100 py-3 px-2 text-center text-sm font-semibold text-slate-900">{row.rating.toFixed(1)}%</td>
                  <td className="border-b border-slate-100 py-3 px-2 text-center text-sm text-slate-700">{row.test_score.toFixed(0)}%</td>
                  <td className="border-b border-slate-100 py-3 px-2 text-center text-sm text-slate-700">{row.homework_score.toFixed(0)}%</td>
                  <td className="border-b border-slate-100 py-3 px-2 text-center text-sm text-slate-700">{row.debt_score.toFixed(0)}%</td>
                  <td className="border-b border-slate-100 py-3 px-2 text-center text-xs text-slate-700">{row.status}</td>
                </tr>
              ))}
              {!loading && classRating.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-sm text-slate-500">Недостаточно данных для рейтинга.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div ref={performanceTableRef} className="scroll-mt-24 rounded-2xl border border-slate-200/90 bg-white shadow-sm">
        <div className="border-b border-slate-100 bg-slate-50/80 px-5 py-4 sm:px-6">
          <h3 className="text-lg font-semibold text-slate-900">Успеваемость учеников</h3>
          <p className="mt-1 text-sm text-slate-600">
            Строки «Нужна помощь» выделены. Быстрые действия: назначить работу, контакт родителя, карточка ученика.
          </p>
        </div>
        <div className="overflow-x-auto px-2 pb-2 sm:px-4 sm:pb-4">
          <table className="w-full min-w-[720px] border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="border-b border-slate-200 py-3 pl-4 pr-2 sm:pl-2">Ученик</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Балл</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Темы</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Ошибки</th>
                <th className="border-b border-slate-200 py-3 px-2 text-center">Статус</th>
                <th className="border-b border-slate-200 py-3 pl-2 pr-4 text-right sm:pr-2">Действия</th>
              </tr>
            </thead>
            <tbody>
              {paginatedStudents.map((student) => (
                <tr
                  key={student.user_id}
                  className={`transition-colors ${
                    student.status === 'needs-help'
                      ? 'bg-rose-50/50 hover:bg-rose-50/80'
                      : 'hover:bg-slate-50/80'
                  }`}
                >
                  <td className="border-b border-slate-100 py-3.5 pl-4 pr-2 sm:pl-2">
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-sm ring-1 ring-black/10 ${
                          student.status === 'needs-help'
                            ? 'bg-rose-100 text-rose-950'
                            : 'bg-sky-100 text-sky-950'
                        }`}
                      >
                        <span className="select-none text-[15px] font-bold leading-none tracking-tight">
                          {avatarInitial(student.student)}
                        </span>
                      </div>
                      <span className="font-medium text-slate-900">{student.student}</span>
                    </div>
                  </td>
                  <td className="border-b border-slate-100 py-3.5 px-2 text-center">
                    <span
                      className={`inline-flex min-w-[3rem] justify-center rounded-lg px-2 py-1 text-sm font-semibold tabular-nums ${
                        student.score >= 85
                          ? 'bg-emerald-50 text-emerald-800'
                          : student.score >= 70
                            ? 'bg-sky-50 text-sky-800'
                            : student.score >= 60
                              ? 'bg-amber-50 text-amber-800'
                              : 'bg-rose-50 text-rose-800'
                      }`}
                    >
                      {student.score}%
                    </span>
                  </td>
                  <td className="border-b border-slate-100 py-3.5 px-2 text-center tabular-nums text-slate-800">{student.topics}</td>
                  <td className="border-b border-slate-100 py-3.5 px-2 text-center">
                    <span
                      className={`inline-flex min-w-[2rem] justify-center rounded-lg px-2 py-0.5 text-xs font-semibold ${
                        student.errors < 10
                          ? 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-100'
                          : student.errors < 15
                            ? 'bg-amber-50 text-amber-800 ring-1 ring-amber-100'
                            : 'bg-rose-50 text-rose-800 ring-1 ring-rose-100'
                      }`}
                    >
                      {student.errors}
                    </span>
                  </td>
                  <td className="border-b border-slate-100 py-3.5 px-2 text-center">{getStatusBadge(student.status)}</td>
                  <td className="border-b border-slate-100 py-3.5 pl-2 pr-4 text-right sm:pr-2">
                    <div className="flex flex-wrap items-center justify-end gap-1.5">
                      {student.status === 'needs-help' && (
                        <>
                          <button
                            type="button"
                            title="Назначить до занятия"
                            onClick={() => handleAssignBeforeLesson(student)}
                            disabled={assigningStudentId === student.user_id}
                            className="inline-flex items-center justify-center rounded-lg border border-rose-200 bg-white p-2 text-rose-700 shadow-sm transition hover:bg-rose-50 disabled:opacity-60"
                          >
                            <PenSquare className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            title="Контакт родителя"
                            onClick={() => handleShowParentContact(student)}
                            className="inline-flex items-center justify-center rounded-lg border border-rose-200 bg-white p-2 text-rose-700 shadow-sm transition hover:bg-rose-50"
                          >
                            <Phone className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      <button
                        type="button"
                        onClick={() => handleOpenStudentCard(student)}
                        className="rounded-lg px-2.5 py-1.5 text-sm font-medium text-indigo-600 transition hover:bg-indigo-50"
                      >
                        Подробнее
                      </button>
                    </div>
                  </td>
                </tr>
            ))}
            {!loading && visibleStudents.length === 0 && (
              <tr>
                <td className="py-12 px-4 text-center text-slate-500" colSpan={6}>
                  <p className="font-medium text-slate-700">Пока нет данных</p>
                  <p className="mt-1 text-sm">Смените класс или дождитесь активности учеников на платформе.</p>
                </td>
              </tr>
            )}
            </tbody>
          </table>
        </div>
        {!loading && visibleStudents.length > TABLE_PAGE_SIZE && (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 text-sm text-slate-600 sm:px-6">
            <span>
              Страница <strong className="text-slate-800">{tablePage + 1}</strong> из {tablePageCount} · всего {visibleStudents.length} уч.
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={tablePage <= 0}
                onClick={() => setTablePage((p) => Math.max(0, p - 1))}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Назад
              </button>
              <button
                type="button"
                disabled={tablePage >= tablePageCount - 1}
                onClick={() => setTablePage((p) => Math.min(tablePageCount - 1, p + 1))}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Вперёд
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
          <div className="mb-5">
            <h3 className="text-lg font-semibold text-slate-900">Типовые ошибки класса</h3>
            <p className="mt-1 text-sm text-slate-600">Агрегат по ответам и классификации — ориентир для повторения тем.</p>
          </div>
          <div className="space-y-3">
            {commonErrors.map((error, index) => (
              <div key={index} className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 transition hover:border-slate-200 hover:bg-white">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <h4 className="font-medium text-slate-900">{error.topic}</h4>
                    <p className="mt-0.5 text-sm text-slate-600">
                      {error.students} уч. · {error.errorType}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                      error.frequency > 80
                        ? 'bg-rose-100 text-rose-800 ring-1 ring-rose-200/80'
                        : error.frequency > 50
                          ? 'bg-amber-100 text-amber-800 ring-1 ring-amber-200/80'
                          : 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200/80'
                    }`}
                  >
                    {error.frequency}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-200/80">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-rose-500 via-orange-400 to-amber-400"
                    style={{ width: `${error.frequency}%` }}
                  />
                </div>
              </div>
            ))}
            {!loading && commonErrors.length === 0 && (
              <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 py-8 text-center text-sm text-slate-500">
                Накопите больше попыток — список типовых ошибок появится автоматически.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Темы: балл и завершение</h3>
            <p className="mt-1 text-sm text-slate-600">Сравнение среднего балла и доли завершения по темам.</p>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topicPerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="topic" 
                stroke="#6b7280"
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
                tick={{ fontSize: 12 }}
              />
              <YAxis stroke="#6b7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Bar dataKey="avgScore" fill="#6366f1" name="Средний балл %" radius={[6, 6, 0, 0]} />
              <Bar dataKey="completion" fill="#8b5cf6" name="Завершение %" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          {!loading && topicPerformance.length === 0 && (
            <p className="mt-4 rounded-lg bg-slate-50 py-6 text-center text-sm text-slate-500">Недостаточно данных для диаграммы.</p>
          )}
        </div>
      </div>

      {/* Modal: Подробнее об ученике */}
      {detailStudent && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
          onClick={() => {
            setDetailStudent(null);
            setDetailCard(null);
          }}
        >
          <div
            className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-2xl shadow-slate-900/20"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-gradient-to-r from-indigo-50/80 to-white px-5 py-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-indigo-600">Карточка ученика</p>
                <h3 className="mt-1 text-lg font-semibold text-slate-900">{detailStudent.student}</h3>
              </div>
              <button
                type="button"
                onClick={() => {
                  setDetailStudent(null);
                  setDetailCard(null);
                }}
                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                aria-label="Закрыть"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4 p-5 text-sm">
              {detailLoading && (
                <div className="rounded-xl bg-slate-50 p-4 text-center text-slate-600">Загрузка карточки ученика...</div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-100">
                  <p className="text-xs text-slate-500">Балл</p>
                  <p className="mt-1 text-xl font-semibold tabular-nums text-slate-900">
                    {detailCard?.rating?.rating ?? detailStudent.score}%
                  </p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-100">
                  <p className="text-xs text-slate-500">Уровень / баллы</p>
                  <p className="mt-1 text-xl font-semibold tabular-nums text-slate-900">
                    {detailCard?.stats?.level ?? 1} / {detailCard?.stats?.points ?? 0}
                  </p>
                </div>
              </div>
              {detailCard && (
                <>
                  <div className="grid grid-cols-3 gap-2 rounded-xl border border-slate-100 bg-slate-50/70 p-3 text-xs">
                    <div>
                      <p className="text-slate-500">Тесты</p>
                      <p className="text-sm font-semibold text-slate-900">{detailCard.rating.test_score.toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Домашка</p>
                      <p className="text-sm font-semibold text-slate-900">{detailCard.rating.homework_score.toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Закрытие долгов</p>
                      <p className="text-sm font-semibold text-slate-900">{detailCard.rating.debt_score.toFixed(1)}%</p>
                    </div>
                  </div>
                  <div className="rounded-xl border border-slate-100 bg-white p-3">
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Слабые темы</p>
                    <div className="flex flex-wrap gap-1.5">
                      {(detailCard.weaknesses || []).slice(0, 6).map((weak) => (
                        <span key={weak.topic} className="rounded-full bg-rose-50 px-2 py-1 text-xs text-rose-700 ring-1 ring-rose-100">
                          {weak.topic} ({weak.mastery}%)
                        </span>
                      ))}
                      {(!detailCard.weaknesses || detailCard.weaknesses.length === 0) && (
                        <span className="text-xs text-slate-500">Критичных слабостей не найдено</span>
                      )}
                    </div>
                  </div>
                  <div className="rounded-xl border border-slate-100 bg-white p-3">
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Долги</p>
                    <div className="space-y-1.5">
                      {(detailCard.debts || []).slice(0, 5).map((debt) => (
                        <div key={debt.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-2 py-1.5">
                          <span className="text-xs text-slate-700">{debt.topic}</span>
                          <span className="text-xs font-medium text-slate-900">{debt.status} · {debt.progress.toFixed(0)}%</span>
                        </div>
                      ))}
                      {(!detailCard.debts || detailCard.debts.length === 0) && (
                        <span className="text-xs text-slate-500">Нет активных долгов</span>
                      )}
                    </div>
                  </div>
                </>
              )}
              <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-3 py-2">
                <span className="text-slate-600">Статус</span>
                {getStatusBadge(detailStudent.status)}
              </div>
              {parentContactsByStudentId[detailStudent.user_id] && (
                <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Родитель</p>
                  <p className="mt-1 font-medium text-slate-900">{parentContactsByStudentId[detailStudent.user_id].full_name}</p>
                  <a
                    href={`tel:${parentContactsByStudentId[detailStudent.user_id].phone}`}
                    className="mt-1 inline-flex text-sm font-medium text-indigo-600 hover:underline"
                  >
                    {parentContactsByStudentId[detailStudent.user_id].phone}
                  </a>
                </div>
              )}
              {(detailStudent.status === 'needs-help' || detailCard) && (
                <div className="flex flex-col gap-2 border-t border-slate-100 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      handleAssignBeforeLesson(detailStudent);
                      setDetailStudent(null);
                    }}
                    disabled={assigningStudentId === detailStudent.user_id}
                    className="w-full rounded-xl bg-rose-600 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-rose-700 disabled:opacity-60"
                  >
                    {assigningStudentId === detailStudent.user_id ? 'Назначаем...' : 'Назначить работу до занятия'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleShowParentContact(detailStudent)}
                    className="w-full rounded-xl border border-rose-200 bg-white py-2.5 text-sm font-medium text-rose-700 transition hover:bg-rose-50"
                  >
                    Показать контакт родителя
                  </button>
                  <button
                    type="button"
                    onClick={() => assignAdaptiveRemedial(detailStudent)}
                    className="w-full rounded-xl border border-indigo-200 bg-indigo-50 py-2.5 text-sm font-medium text-indigo-700 transition hover:bg-indigo-100"
                  >
                    Назначить работу над ошибками
                  </button>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => assignLibrary(detailStudent, 'material')}
                      className="rounded-xl border border-slate-200 bg-white py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Назначить статью
                    </button>
                    <button
                      type="button"
                      onClick={() => assignLibrary(detailStudent, 'course')}
                      className="rounded-xl border border-slate-200 bg-white py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50"
                    >
                      Назначить курс
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
        </>
      )}

      <AIChatPanel
        isMinimized={isChatMinimized}
        onToggleMinimize={() => setIsChatMinimized(!isChatMinimized)}
      />
    </div>
  );
}
