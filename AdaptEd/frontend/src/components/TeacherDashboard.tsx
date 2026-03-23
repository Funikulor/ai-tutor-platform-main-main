import { useEffect, useMemo, useRef, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Users, TrendingUp, AlertCircle, Download, Filter, BarChart3, FileText, PenSquare, ClipboardList, X, Phone } from 'lucide-react';
import { TeacherTestsTab } from './TeacherTestsTab';
import api from '../services/api';
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
  const [tablePage, setTablePage] = useState(0);
  const performanceTableRef = useRef<HTMLDivElement>(null);

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
        const [analyticsResponse, usersResponse] = await Promise.all([
          api.get<ClassAnalyticsResponse>('/teacher/class-analytics', {
            params: selectedClass && selectedClass !== 'all' ? { class_id: selectedClass } : undefined,
          }),
          api.get<UserRow[]>('/all'),
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
      excellent: 'bg-green-100 text-green-700',
      good: 'bg-blue-100 text-blue-700',
      average: 'bg-yellow-100 text-yellow-700',
      'needs-help': 'bg-red-100 text-red-700'
    };
    const labels = {
      excellent: 'Отлично',
      good: 'Хорошо',
      average: 'Средне',
      'needs-help': 'Нужна помощь'
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs ${styles[status as keyof typeof styles]}`}>
        {labels[status as keyof typeof labels]}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-1 flex flex-wrap gap-1">
        <button
          onClick={() => setCurrentView('analytics')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'analytics'
              ? 'bg-blue-50 text-blue-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <BarChart3 className="w-5 h-5 inline mr-2" />
          Аналитика класса
        </button>
        <button
          onClick={() => setCurrentView('create-tests')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'create-tests'
              ? 'bg-green-50 text-green-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <PenSquare className="w-5 h-5 inline mr-2" />
          Создание тестов
        </button>
        <button
          onClick={() => setCurrentView('created-tests')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'created-tests'
              ? 'bg-green-50 text-green-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <FileText className="w-5 h-5 inline mr-2" />
          Созданные тесты
        </button>
        <button
          onClick={() => setCurrentView('results')}
          className={`flex-1 py-3 px-4 rounded-lg transition-all ${
            currentView === 'results'
              ? 'bg-purple-50 text-purple-600'
              : 'text-gray-600 hover:bg-gray-50'
          }`}
        >
          <ClipboardList className="w-5 h-5 inline mr-2" />
          Результаты учеников
        </button>
      </div>

      {currentView === 'create-tests' && <TeacherTestsTab mode="create" preselectedStudentId={preselectedStudentId} />}
      {currentView === 'created-tests' && <TeacherTestsTab mode="manage" preselectedStudentId={preselectedStudentId} />}
      {currentView === 'results' && <TeacherTestsTab mode="results" preselectedStudentId={preselectedStudentId} />}

      {/* Analytics View */}
      {currentView === 'analytics' && (
        <>
      {/* Header Controls */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900">Панель учителя</h2>
            <p className="text-gray-600">Аналитика и управление классом</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">Все классы</option>
              {availableClasses.map((classId) => (
                <option key={classId} value={classId}>
                  Класс {classId}
                </option>
              ))}
            </select>
            <button
              onClick={() => setFiltersOpen((v) => !v)}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Filter className="w-4 h-4" />
              Фильтры
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download className="w-4 h-4" />
              Экспорт
            </button>
          </div>
        </div>
        {filtersOpen && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | StudentStatus)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">Все статусы</option>
              <option value="excellent">Отлично</option>
              <option value="good">Хорошо</option>
              <option value="average">Средне</option>
              <option value="needs-help">Нужна помощь</option>
            </select>
            <input
              type="number"
              min={0}
              max={100}
              value={minScoreFilter}
              onChange={(e) => setMinScoreFilter(Math.max(0, Math.min(100, Number(e.target.value) || 0)))}
              placeholder="Мин. средний балл"
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Всего учеников</p>
              <p className="text-3xl text-gray-900 mt-1">{visibleStudents.length}</p>
            </div>
            <Users className="w-10 h-10 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Средний балл</p>
              <p className="text-3xl text-gray-900 mt-1">
                {averageScore}%
              </p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500" />
          </div>
        </div>

        <button
          type="button"
          onClick={handleFocusNeedsHelp}
          disabled={needsHelpTotalInClass === 0}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-left w-full transition-colors hover:border-red-200 hover:bg-red-50/40 disabled:opacity-50 disabled:hover:bg-white disabled:hover:border-gray-200 disabled:cursor-not-allowed"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Нужна помощь</p>
              <p className="text-3xl text-gray-900 mt-1">
                {needsHelpTotalInClass}
              </p>
              {needsHelpTotalInClass > 0 && (
                <p className="text-xs text-red-600 mt-1">Нажмите, чтобы показать в таблице</p>
              )}
            </div>
            <AlertCircle className="w-10 h-10 text-red-500 shrink-0" />
          </div>
        </button>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Завершено тем</p>
              <p className="text-3xl text-gray-900 mt-1">
                {visibleStudents.length > 0
                  ? Math.round(visibleStudents.reduce((acc, s) => acc + s.topics, 0) / visibleStudents.length)
                  : 0}
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xl">
              ✓
            </div>
          </div>
        </div>
      </div>

      {/* Student Performance Table */}
      <div ref={performanceTableRef} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 scroll-mt-4">
        <h3 className="text-gray-900">Успеваемость учеников</h3>
        <p className="text-sm text-gray-500 mt-1 mb-4">
          Ученики со статусом «Нужна помощь» подсвечены; карточка «Нужна помощь» выше отфильтрует таблицу.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-gray-700">Ученик</th>
                <th className="text-center py-3 px-4 text-gray-700">Средний балл</th>
                <th className="text-center py-3 px-4 text-gray-700">Изучено тем</th>
                <th className="text-center py-3 px-4 text-gray-700">Ошибок</th>
                <th className="text-center py-3 px-4 text-gray-700">Статус</th>
                <th className="text-right py-3 px-4 text-gray-700">Действия</th>
              </tr>
            </thead>
            <tbody>
              {paginatedStudents.map((student) => (
                <tr
                  key={student.user_id}
                  className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                    student.status === 'needs-help' ? 'bg-red-50/60' : ''
                  }`}
                >
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center text-white ${
                          student.status === 'needs-help'
                            ? 'bg-gradient-to-br from-red-400 to-red-600'
                            : 'bg-gradient-to-br from-blue-400 to-purple-500'
                        }`}
                      >
                        {student.student.charAt(0)}
                      </div>
                      <span className="text-gray-900">{student.student}</span>
                    </div>
                  </td>
                  <td className="text-center py-4 px-4">
                    <span className={`text-lg ${
                      student.score >= 85 ? 'text-green-600' :
                      student.score >= 70 ? 'text-blue-600' :
                      student.score >= 60 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {student.score}%
                    </span>
                  </td>
                  <td className="text-center py-4 px-4 text-gray-900">{student.topics}</td>
                  <td className="text-center py-4 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      student.errors < 10 ? 'bg-green-100 text-green-700' :
                      student.errors < 15 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {student.errors}
                    </span>
                  </td>
                  <td className="text-center py-4 px-4">
                    {getStatusBadge(student.status)}
                  </td>
                  <td className="text-right py-4 px-4">
                    <div className="flex flex-wrap items-center justify-end gap-2">
                      {student.status === 'needs-help' && (
                        <>
                          <button
                            type="button"
                            title="Назначить до занятия"
                            onClick={() => handleAssignBeforeLesson(student)}
                            disabled={assigningStudentId === student.user_id}
                            className="inline-flex items-center justify-center p-2 rounded-lg border border-red-200 text-red-700 bg-white hover:bg-red-50 disabled:opacity-60"
                          >
                            <PenSquare className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            title="Контакт родителя"
                            onClick={() => handleShowParentContact(student)}
                            className="inline-flex items-center justify-center p-2 rounded-lg border border-red-200 text-red-700 bg-white hover:bg-red-50"
                          >
                            <Phone className="w-4 h-4" />
                          </button>
                        </>
                      )}
                      <button
                        type="button"
                        onClick={() => setDetailStudent(student)}
                        className="text-blue-600 hover:text-blue-700 text-sm whitespace-nowrap"
                      >
                        Подробнее →
                      </button>
                    </div>
                  </td>
                </tr>
            ))}
            {!loading && visibleStudents.length === 0 && (
              <tr>
                <td className="py-6 px-4 text-gray-500" colSpan={6}>
                  Данные по классу пока отсутствуют
                </td>
              </tr>
            )}
            </tbody>
          </table>
        </div>
        {!loading && visibleStudents.length > TABLE_PAGE_SIZE && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600">
            <span>
              Страница {tablePage + 1} из {tablePageCount} ({visibleStudents.length} учеников)
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={tablePage <= 0}
                onClick={() => setTablePage((p) => Math.max(0, p - 1))}
                className="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Назад
              </button>
              <button
                type="button"
                disabled={tablePage >= tablePageCount - 1}
                onClick={() => setTablePage((p) => Math.min(tablePageCount - 1, p + 1))}
                className="px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Вперёд
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Common Errors Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Частые ошибки класса (NLP анализ)</h3>
          <div className="space-y-4">
            {commonErrors.map((error, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="text-gray-900">{error.topic}</h4>
                    <p className="text-sm text-gray-600">
                      {error.students} учеников • {error.errorType}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs ${
                    error.frequency > 80 ? 'bg-red-100 text-red-700' :
                    error.frequency > 50 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {error.frequency}% частота
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-red-500 to-orange-500"
                    style={{ width: `${error.frequency}%` }}
                  />
                </div>
              </div>
            ))}
            {!loading && commonErrors.length === 0 && (
              <p className="text-sm text-gray-500">Частые ошибки пока не выявлены.</p>
            )}
          </div>
          <button
            type="button"
            onClick={() =>
              toast.info('Функция планирования группового занятия пока в разработке. Используйте назначение тестов для отдельных учеников.')
            }
            className="mt-4 w-full py-2 px-4 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm"
          >
            Создать групповое занятие по проблемным темам
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Производительность по темам</h3>
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
              <Bar dataKey="avgScore" fill="#3b82f6" name="Средний балл %" radius={[8, 8, 0, 0]} />
              <Bar dataKey="completion" fill="#8b5cf6" name="Завершение %" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          {!loading && topicPerformance.length === 0 && (
            <p className="mt-3 text-sm text-gray-500">Недостаточно данных для графика тем.</p>
          )}
        </div>
      </div>

      {/* Modal: Подробнее об ученике */}
      {detailStudent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDetailStudent(null)}>
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Подробнее: {detailStudent.student}</h3>
              <button type="button" onClick={() => setDetailStudent(null)} className="p-1 text-gray-500 hover:text-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <p><span className="text-gray-600">Успеваемость:</span> <strong>{detailStudent.score}%</strong></p>
              <p><span className="text-gray-600">Изучено тем:</span> <strong>{detailStudent.topics}</strong></p>
              <p><span className="text-gray-600">Количество ошибок:</span> <strong>{detailStudent.errors}</strong></p>
              <p><span className="text-gray-600">Статус:</span> <span className={detailStudent.status === 'excellent' ? 'text-green-600' : detailStudent.status === 'good' ? 'text-blue-600' : detailStudent.status === 'average' ? 'text-yellow-600' : 'text-red-600'}>
                {detailStudent.status === 'excellent' ? 'Отлично' : detailStudent.status === 'good' ? 'Хорошо' : detailStudent.status === 'average' ? 'Удовлетворительно' : 'Требуется внимание'}
              </span></p>
              {parentContactsByStudentId[detailStudent.user_id] && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-gray-600 font-medium mb-1">Контакт родителя</p>
                  <p>{parentContactsByStudentId[detailStudent.user_id].full_name}</p>
                  <p><a href={`tel:${parentContactsByStudentId[detailStudent.user_id].phone}`} className="text-blue-600 hover:underline">{parentContactsByStudentId[detailStudent.user_id].phone}</a></p>
                </div>
              )}
              {detailStudent.status === 'needs-help' && (
                <div className="mt-4 pt-4 border-t border-gray-200 flex flex-col gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      handleAssignBeforeLesson(detailStudent);
                      setDetailStudent(null);
                    }}
                    disabled={assigningStudentId === detailStudent.user_id}
                    className="w-full py-2 px-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm disabled:opacity-60"
                  >
                    {assigningStudentId === detailStudent.user_id ? 'Назначаем...' : 'Назначить до занятия'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleShowParentContact(detailStudent)}
                    className="w-full py-2 px-3 bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors text-sm"
                  >
                    Связаться с родителями
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
}
