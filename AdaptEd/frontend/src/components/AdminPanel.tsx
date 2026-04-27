import { useState, useEffect, useCallback } from 'react';
import { Plus, Edit, Trash2, Upload, BookOpen, Users, Settings, Database, X, Library, Loader2, RefreshCw, Shield, Cpu, HardDrive, ChevronLeft } from 'lucide-react';
import api from '../services/api';
import { avatarInitial } from '../utils/avatar';
import { toast } from 'sonner';
import { TopicLibraryStudio } from './TopicLibraryStudio';
import { AdminLibraryEditor } from './AdminLibraryEditor';

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState<'content' | 'users' | 'system'>('content');
  /** Контент: библиотека (как у ученика) или дерево тем программы */
  const [contentMode, setContentMode] = useState<'library' | 'structure'>('library');
  const [systemStats, setSystemStats] = useState({
    totalUsers: 0,
    totalTasks: 0,
    totalMaterials: 0,
    aiQueries: 0,
    storageUsed: 'N/A',
    uptime: '99.8%'
  });
  const [users, setUsers] = useState<Array<{
    id: string;
    name: string;
    email: string;
    role: string;
    status: string;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contentStructure, setContentStructure] = useState<Array<{
    id: number;
    subject: string;
    sections: Array<{
      id: number;
      name: string;
      topics: Array<{
        id: number;
        name: string;
        elements: number;
        tasks: number;
        description?: string;
        teacher_notes?: string;
        grade_hint?: string;
        library_material_ids?: string[];
        library_course_ids?: string[];
      }>;
    }>;
  }>>([]);

  // Modal states
  const [showUserModal, setShowUserModal] = useState(false);
  const [showSubjectModal, setShowSubjectModal] = useState(false);
  const [showSectionModal, setShowSectionModal] = useState(false);
  const [showTopicModal, setShowTopicModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showEditSubjectModal, setShowEditSubjectModal] = useState(false);
  const [showEditSectionModal, setShowEditSectionModal] = useState(false);
  const [showEditTopicModal, setShowEditTopicModal] = useState(false);
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const [addTaskTopic, setAddTaskTopic] = useState<{ id: number; name: string; sectionId: number } | null>(null);
  const [topicCatalogTasks, setTopicCatalogTasks] = useState<Array<{ id: number; title: string; description?: string }>>([]);
  const [topicCatalogTasksLoading, setTopicCatalogTasksLoading] = useState(false);
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedResult, setSeedResult] = useState<{ created: number; credentials: Array<{ role: string; name: string; email: string; password: string; class_id?: string | null; parent_fio?: string | null; parent_phone?: string | null }> } | null>(null);
  const [libraryStudioCtx, setLibraryStudioCtx] = useState<{
    topic: {
      id: number;
      name: string;
      library_material_ids?: string[];
      library_course_ids?: string[];
    };
    subjectTitle: string;
    sectionName: string;
  } | null>(null);

  // Form states
  const [editingUser, setEditingUser] = useState<any>(null);
  const [editingSubject, setEditingSubject] = useState<any>(null);
  const [editingSection, setEditingSection] = useState<any>(null);
  const [editingTopic, setEditingTopic] = useState<any>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);

  // System settings state
  const [systemSettings, setSystemSettings] = useState({
    adaptation_strategy: 'balanced',
    target_mastery_percent: 80,
    attempts_before_strategy_change: 3,
    gigachat_api_key: '',
    pinecone_api_key: '',
    pinecone_index: ''
  });

  useEffect(() => {
    loadAdminData();
    loadSystemSettings();
  }, []);

  useEffect(() => {
    if (activeTab !== 'content') {
      setContentMode('library');
    }
  }, [activeTab]);

  const loadTopicCatalogTasks = useCallback(async (topicId: number) => {
    setTopicCatalogTasksLoading(true);
    try {
      const { data } = await api.get<{ tasks: Array<{ id: number; title: string; description?: string }> }>(
        `/admin/content/topic/${topicId}/tasks`
      );
      setTopicCatalogTasks(data.tasks || []);
    } catch {
      setTopicCatalogTasks([]);
    } finally {
      setTopicCatalogTasksLoading(false);
    }
  }, []);

  useEffect(() => {
    if (showEditTopicModal && editingTopic?.id != null) {
      loadTopicCatalogTasks(editingTopic.id);
    } else {
      setTopicCatalogTasks([]);
    }
  }, [showEditTopicModal, editingTopic?.id, loadTopicCatalogTasks]);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [statsResponse, usersResponse, contentResponse] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/admin/content-structure')
      ]);
      
      setSystemStats(statsResponse.data);
      setUsers(usersResponse.data);
      setContentStructure(contentResponse.data.structure || []);
    } catch (err: any) {
      console.error('Error loading admin data:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  };

  const loadSystemSettings = async () => {
    try {
      const response = await api.get('/admin/settings');
      setSystemSettings({ ...systemSettings, ...response.data });
    } catch (err) {
      console.error('Error loading settings:', err);
    }
  };

  // User management handlers
  const handleCreateUser = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.post('/admin/users', {
        email: formData.get('email'),
        password: formData.get('password'),
        full_name: formData.get('full_name'),
        role: formData.get('role'),
        class_id: formData.get('class_id') || null,
        phone: formData.get('phone') || null,
        parent_fio: formData.get('parent_fio') || null,
        parent_phone: formData.get('parent_phone') || null
      });
      toast.success('Пользователь успешно создан');
      setShowUserModal(false);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при создании пользователя');
    }
  };

  const handleEditUser = (user: any) => {
    setEditingUser(user);
    setShowEditUserModal(true);
  };

  const handleUpdateUser = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const newPassword = (formData.get('new_password') as string)?.trim();
    try {
      await api.put(`/admin/users/${editingUser.id}`, {
        full_name: formData.get('full_name'),
        email: formData.get('email'),
        role: formData.get('role'),
        class_id: formData.get('class_id') || null,
        phone: formData.get('phone') || null,
        parent_fio: formData.get('parent_fio') || null,
        parent_phone: formData.get('parent_phone') || null,
        is_active: formData.get('is_active') === 'true'
      });
      if (newPassword && newPassword.length >= 6) {
        await api.put(`/admin/users/${editingUser.id}/password`, { new_password: newPassword });
        toast.success('Пользователь и пароль успешно обновлены');
      } else {
        toast.success('Пользователь успешно обновлен');
      }
      setShowEditUserModal(false);
      setEditingUser(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при обновлении пользователя');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Вы уверены, что хотите деактивировать этого пользователя?')) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success('Пользователь деактивирован');
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при удалении пользователя');
    }
  };

  // Content management handlers
  const handleCreateSubject = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.post('/admin/content/subject', {
        subject: formData.get('subject')
      });
      toast.success('Предмет успешно создан');
      setShowSubjectModal(false);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при создании предмета');
    }
  };

  const handleEditSubject = (subject: any) => {
    setEditingSubject(subject);
    setShowEditSubjectModal(true);
  };

  const handleUpdateSubject = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.put(`/admin/content/subject/${editingSubject.id}`, {
        subject: formData.get('subject')
      });
      toast.success('Предмет успешно обновлен');
      setShowEditSubjectModal(false);
      setEditingSubject(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при обновлении предмета');
    }
  };

  const handleDeleteSubject = async (subjectId: number) => {
    if (!confirm('Вы уверены, что хотите удалить этот предмет? Все разделы и темы будут удалены.')) return;
    try {
      await api.delete(`/admin/content/subject/${subjectId}`);
      toast.success('Предмет успешно удален');
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при удалении предмета');
    }
  };

  const handleCreateSection = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.post('/admin/content/section', {
        subject_id: selectedSubjectId,
        name: formData.get('name')
      });
      toast.success('Раздел успешно создан');
      setShowSectionModal(false);
      setSelectedSubjectId(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при создании раздела');
    }
  };

  const handleEditSection = (section: any, subjectId: number) => {
    setEditingSection(section);
    setSelectedSubjectId(subjectId);
    setShowEditSectionModal(true);
  };

  const handleUpdateSection = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.put(`/admin/content/section/${editingSection.id}`, {
        name: formData.get('name')
      });
      toast.success('Раздел успешно обновлен');
      setShowEditSectionModal(false);
      setEditingSection(null);
      setSelectedSubjectId(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при обновлении раздела');
    }
  };

  const handleDeleteSection = async (sectionId: number) => {
    if (!confirm('Вы уверены, что хотите удалить этот раздел? Все темы будут удалены.')) return;
    try {
      await api.delete(`/admin/content/section/${sectionId}`);
      toast.success('Раздел успешно удален');
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при удалении раздела');
    }
  };

  const handleCreateTopic = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.post('/admin/content/topic', {
        section_id: selectedSectionId,
        name: formData.get('name'),
        description: (formData.get('description') as string) || '',
        teacher_notes: (formData.get('teacher_notes') as string) || '',
        grade_hint: (formData.get('grade_hint') as string) || '',
        elements: parseInt(String(formData.get('elements') || '0'), 10) || 0,
      });
      toast.success('Тема успешно создана');
      setShowTopicModal(false);
      setSelectedSectionId(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при создании темы');
    }
  };

  const handleEditTopic = (topic: any, sectionId: number) => {
    setEditingTopic(topic);
    setSelectedSectionId(sectionId);
    setShowEditTopicModal(true);
  };

  const openTopicFromLibrary = (topicId: number) => {
    for (const sub of contentStructure) {
      for (const sec of sub.sections) {
        const t = sec.topics.find((x) => x.id === topicId);
        if (t) {
          handleEditTopic(t, sec.id);
          setContentMode('structure');
          return;
        }
      }
    }
    toast.error('Тема не найдена в каталоге. Нажмите «Обновить данные».');
  };

  const handleAddTask = (topic: any, sectionId: number) => {
    setAddTaskTopic({ id: topic.id, name: topic.name, sectionId });
    setShowAddTaskModal(true);
  };

  const handleSeedDb = async () => {
    setSeedLoading(true);
    setSeedResult(null);
    try {
      const { data } = await api.post<{ message: string; created: number; credentials: Array<{ role: string; name: string; email: string; password: string; class_id?: string | null; parent_fio?: string | null; parent_phone?: string | null }> }>('/admin/seed');
      setSeedResult({ created: data.created, credentials: data.credentials || [] });
      toast.success(data.message || `Создано пользователей: ${data.created}`);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при заполнении БД');
    } finally {
      setSeedLoading(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!addTaskTopic) return;
    const formData = new FormData(e.currentTarget);
    try {
      await api.post(`/admin/content/topic/${addTaskTopic.id}/task`, {
        title: formData.get('task_title'),
        description: formData.get('task_description') || null
      });
      toast.success('Задание добавлено');
      setShowAddTaskModal(false);
      if (addTaskTopic) await loadTopicCatalogTasks(addTaskTopic.id);
      setAddTaskTopic(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при добавлении задания');
    }
  };

  const handleUpdateTopic = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.put(`/admin/content/topic/${editingTopic.id}`, {
        name: formData.get('name'),
        elements: parseInt(formData.get('elements') as string) || 0,
        tasks: parseInt(formData.get('tasks') as string) || 0,
        description: (formData.get('description') as string) || '',
        teacher_notes: (formData.get('teacher_notes') as string) || '',
        grade_hint: (formData.get('grade_hint') as string) || '',
      });
      toast.success('Тема успешно обновлена');
      setShowEditTopicModal(false);
      setEditingTopic(null);
      setSelectedSectionId(null);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при обновлении темы');
    }
  };

  const handleDeleteTopic = async (topicId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту тему?')) return;
    try {
      await api.delete(`/admin/content/topic/${topicId}`);
      toast.success('Тема успешно удалена');
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при удалении темы');
    }
  };

  const handleDeleteCatalogTask = async (topicId: number, taskId: number) => {
    if (!confirm('Удалить это задание из каталога темы?')) return;
    try {
      await api.delete(`/admin/content/topic/${topicId}/task/${taskId}`);
      toast.success('Задание удалено');
      await loadTopicCatalogTasks(topicId);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Не удалось удалить задание');
    }
  };

  const handleUploadMaterial = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    try {
      await api.post('/admin/materials/upload', {
        title: formData.get('title'),
        content: formData.get('content'),
        topic: formData.get('topic') || null,
        subject: formData.get('subject') || null
      });
      toast.success('Материал успешно загружен');
      setShowUploadModal(false);
      loadAdminData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при загрузке материала');
    }
  };

  const handleSaveSettings = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const raw = (name: string) => formData.get(name);
    const num = (name: string, def: number) => {
      const v = raw(name);
      if (v === null || v === undefined || v === '') return def;
      const n = parseInt(String(v), 10);
      return Number.isNaN(n) ? def : n;
    };
    const str = (name: string, def: string | null = null) => {
      const v = raw(name);
      if (v === null || v === undefined) return def;
      const s = String(v).trim();
      return s === '' ? def : s;
    };
    try {
      const payload: Record<string, unknown> = {
        ...systemSettings,
        adaptation_strategy: str('adaptation_strategy') ?? systemSettings.adaptation_strategy,
        target_mastery_percent: num('target_mastery_percent', systemSettings.target_mastery_percent),
        attempts_before_strategy_change: num('attempts_before_strategy_change', systemSettings.attempts_before_strategy_change),
        gigachat_api_key: str('gigachat_api_key') ?? systemSettings.gigachat_api_key ?? '',
        pinecone_api_key: str('pinecone_api_key') ?? systemSettings.pinecone_api_key ?? '',
        pinecone_index: str('pinecone_index') ?? systemSettings.pinecone_index ?? ''
      };
      await api.post('/admin/settings', payload);
      toast.success('Настройки успешно сохранены');
      loadSystemSettings();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка при сохранении настроек');
    }
  };

  // Modal component
  const Modal = ({
    isOpen,
    onClose,
    title,
    children,
    wide,
  }: {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    wide?: boolean;
  }) => {
    if (!isOpen) return null;
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 p-4 backdrop-blur-sm">
        <div
          className={`max-h-[90vh] w-full overflow-y-auto rounded-2xl border border-slate-200/90 bg-white shadow-2xl shadow-slate-900/25 ${
            wide ? 'max-w-5xl' : 'max-w-2xl'
          }`}
        >
          <div className="flex items-center justify-between gap-3 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white px-5 py-4 sm:px-6">
            <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              aria-label="Закрыть"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="p-5 sm:p-6">{children}</div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8 pb-10">
      <div className="relative overflow-hidden rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-100 via-slate-50 to-violet-100 shadow-md">
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-fuchsia-300/35 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-10 h-48 w-48 rounded-full bg-indigo-300/35 blur-3xl" />
        <div className="relative flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
          <div className="flex gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-md shadow-indigo-500/25">
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-widest text-indigo-700">Администрирование</p>
              <h2 className="mt-0.5 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">Панель администратора</h2>
              <p className="mt-1 max-w-xl text-sm text-slate-700">
                Каталог тем, пользователи, тестовый seed и параметры адаптации — централизованно.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              loadAdminData();
              loadSystemSettings();
            }}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 self-start rounded-xl border border-indigo-300 bg-white/95 px-4 py-2.5 text-sm font-medium text-indigo-900 shadow-sm transition hover:bg-indigo-100 disabled:opacity-50 sm:self-center"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Обновить данные
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-rose-800 shadow-sm">
          <p className="font-medium">Не удалось загрузить данные</p>
          <p className="mt-1 text-sm text-rose-700/90">{error}</p>
        </div>
      )}

      {!error && (
        <div className="relative grid grid-cols-2 gap-3 lg:grid-cols-6">
          {loading && (
            <div className="absolute -top-1 right-0 z-10 flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 ring-1 ring-indigo-100">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Обновление
            </div>
          )}
          {loading ? (
            [0, 1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="h-[88px] animate-pulse rounded-2xl border border-slate-100 bg-slate-100/80"
              />
            ))
          ) : (
            <>
              <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm transition hover:border-indigo-200 hover:shadow-md">
                <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-indigo-500/10 blur-xl" />
                <div className="relative flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Пользователи</p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{systemStats.totalUsers}</p>
                  </div>
                  <Users className="h-8 w-8 text-indigo-500 opacity-80" />
                </div>
              </div>
              <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm transition hover:border-violet-200 hover:shadow-md">
                <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-violet-500/10 blur-xl" />
                <div className="relative flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Задания</p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{systemStats.totalTasks}</p>
                  </div>
                  <BookOpen className="h-8 w-8 text-violet-500 opacity-80" />
                </div>
              </div>
              <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm transition hover:border-teal-200 hover:shadow-md">
                <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-teal-500/10 blur-xl" />
                <div className="relative flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Материалы</p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{systemStats.totalMaterials}</p>
                  </div>
                  <Upload className="h-8 w-8 text-teal-500 opacity-80" />
                </div>
              </div>
              <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm transition hover:border-amber-200 hover:shadow-md">
                <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-amber-500/10 blur-xl" />
                <div className="relative flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">AI запросы</p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{systemStats.aiQueries}</p>
                  </div>
                  <Cpu className="h-8 w-8 text-amber-500 opacity-80" />
                </div>
              </div>
              <div className="group relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white p-4 shadow-sm transition hover:border-slate-300 hover:shadow-md">
                <div className="relative flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Хранилище</p>
                    <p className="mt-1 text-lg font-semibold text-slate-900">{systemStats.storageUsed}</p>
                  </div>
                  <HardDrive className="h-8 w-8 text-slate-400" />
                </div>
              </div>
              <div className="group relative overflow-hidden rounded-2xl border border-emerald-200/80 bg-gradient-to-br from-emerald-50 to-white p-4 shadow-sm transition hover:shadow-md">
                <div className="relative flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-emerald-700/80">Аптайм</p>
                    <p className="mt-1 text-2xl font-semibold tabular-nums text-emerald-700">{systemStats.uptime}</p>
                  </div>
                  <Database className="h-8 w-8 text-emerald-600 opacity-90" />
                </div>
              </div>
            </>
          )}
        </div>
      )}

      <div className="rounded-2xl border border-slate-300/90 bg-slate-100 p-1.5 shadow-sm">
        <div className="grid grid-cols-1 gap-1 sm:grid-cols-3">
          <button
            type="button"
            onClick={() => setActiveTab('content')}
            className={`flex flex-col items-start gap-0.5 rounded-xl px-4 py-3 text-left transition-all ${
              activeTab === 'content'
                ? 'bg-white shadow-md ring-2 ring-indigo-500/15'
                : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
            }`}
          >
            <span className="flex items-center gap-2 font-medium text-slate-900">
              <BookOpen className={`h-5 w-5 ${activeTab === 'content' ? 'text-indigo-600' : 'text-slate-400'}`} />
              Контент
            </span>
            <span className="pl-7 text-xs text-slate-500">Библиотека как у ученика и структура тем</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('users')}
            className={`flex flex-col items-start gap-0.5 rounded-xl px-4 py-3 text-left transition-all ${
              activeTab === 'users'
                ? 'bg-white shadow-md ring-2 ring-indigo-500/15'
                : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
            }`}
          >
            <span className="flex items-center gap-2 font-medium text-slate-900">
              <Users className={`h-5 w-5 ${activeTab === 'users' ? 'text-indigo-600' : 'text-slate-400'}`} />
              Пользователи
            </span>
            <span className="pl-7 text-xs text-slate-500">Роли, классы, seed</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('system')}
            className={`flex flex-col items-start gap-0.5 rounded-xl px-4 py-3 text-left transition-all ${
              activeTab === 'system'
                ? 'bg-white shadow-md ring-2 ring-indigo-500/15'
                : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
            }`}
          >
            <span className="flex items-center gap-2 font-medium text-slate-900">
              <Settings className={`h-5 w-5 ${activeTab === 'system' ? 'text-indigo-600' : 'text-slate-400'}`} />
              Система
            </span>
            <span className="pl-7 text-xs text-slate-500">Адаптация и API</span>
          </button>
        </div>
      </div>

      {/* Content Management */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          {contentMode === 'library' ? (
            <AdminLibraryEditor
              onEditCatalogTopic={openTopicFromLibrary}
            />
          ) : null}

          {contentMode === 'structure' ? (
          <div className="rounded-2xl border border-slate-200/90 bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-slate-100 bg-slate-50/80 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
                <button
                  type="button"
                  onClick={() => setContentMode('library')}
                  className="inline-flex w-fit items-center gap-2 rounded-xl border border-indigo-200 bg-white px-3 py-2 text-sm font-medium text-indigo-800 shadow-sm transition hover:bg-indigo-50"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Библиотека: курсы и материалы
                </button>
                <div className="hidden h-8 w-px bg-slate-200 sm:block" />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">Структура программы</h3>
                  <p className="mt-0.5 text-sm text-slate-600">Предмет → раздел → тема, привязка к библиотеке и задания каталога</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-emerald-700"
                >
                  <Upload className="h-4 w-4" />
                  Загрузить материалы
                </button>
                <button
                  type="button"
                  onClick={() => setShowSubjectModal(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
                >
                  <Plus className="h-4 w-4" />
                  Новый предмет
                </button>
              </div>
            </div>

            <div className="border-b border-indigo-100 bg-indigo-50/40 px-5 py-4 text-sm leading-relaxed text-slate-700 sm:px-6">
              <p>
                <span className="font-semibold text-slate-900">Назначение:</span> методический каталог (что изучаем, текст для ученика, заметки учителю, класс). Кнопка{' '}
                <span className="font-medium text-indigo-700">«Библиотека»</span> привязывает материалы и мини-курсы — они появятся у ученика в разделе{' '}
                <span className="font-medium">«По программе»</span>. <span className="font-medium">«+ Задание»</span> — элементы плана в каталоге, это не тесты в БД.
              </p>
              <p className="mt-2 text-xs text-slate-600">
                Хранение: при Postgres — таблицы <code className="rounded bg-white px-1.5 py-0.5 text-[11px] ring-1 ring-slate-200">curriculum_*</code>; без БД —{' '}
                <code className="rounded bg-white px-1.5 py-0.5 text-[11px] ring-1 ring-slate-200">data.json</code>.
              </p>
            </div>

            <div className="p-5 sm:p-6">

            <div className="space-y-4">
              {contentStructure.length === 0 && (
                <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/80 py-10 text-center text-sm text-slate-600">
                  Каталог пуст. Обновите страницу — подставится шаблон «Математика».
                </p>
              )}
              {contentStructure.map((subject) => (
                <div key={subject.id} className="overflow-hidden rounded-xl border border-slate-200/90 shadow-sm">
                  <div className="flex items-center justify-between border-b border-slate-200/80 bg-gradient-to-r from-indigo-50/90 via-white to-violet-50/80 px-4 py-3 sm:px-5">
                    <div className="flex flex-wrap items-center gap-3">
                      <BookOpen className="h-6 w-6 shrink-0 text-indigo-600" />
                      <h4 className="font-semibold text-slate-900">{subject.subject}</h4>
                      <span className="rounded-lg bg-white/90 px-2.5 py-0.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200/80">
                        {subject.sections.length} разделов
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleEditSubject(subject)}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded transition-colors"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleDeleteSubject(subject.id)}
                        className="p-2 text-red-600 hover:bg-red-100 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3 bg-slate-50/30 p-4 sm:p-5">
                    {subject.sections.map((section) => (
                      <div key={section.id} className="ml-1 border-l-2 border-indigo-200 pl-4 sm:ml-2 sm:pl-5">
                        <div className="flex items-center justify-between mb-2">
                          <h5 className="text-gray-800">{section.name}</h5>
                          <span className="text-sm text-gray-500">
                            {section.topics.length} тем
                          </span>
                        </div>
                        <div className="ml-4 space-y-2">
                          {section.topics.map((topic) => (
                            <div
                              key={topic.id}
                              className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100"
                            >
                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-2">
                                  <p className="text-gray-900 font-medium">{topic.name}</p>
                                  {topic.grade_hint ? (
                                    <span className="text-xs px-2 py-0.5 bg-white border border-gray-200 rounded text-gray-600">
                                      {topic.grade_hint}
                                    </span>
                                  ) : null}
                                </div>
                                {topic.description ? (
                                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{topic.description}</p>
                                ) : (
                                  <p className="text-xs text-gray-400 mt-1">Нет краткого описания для детей — добавьте в «Редактировать»</p>
                                )}
                                <p className="text-xs text-gray-500 mt-1">
                                  {topic.elements} эл. • {topic.tasks} заданий в каталоге
                                  {(topic.library_material_ids?.length || topic.library_course_ids?.length) ? (
                                    <span className="ml-1 text-indigo-600">
                                      • библиотека:{' '}
                                      {(topic.library_material_ids?.length || 0) + (topic.library_course_ids?.length || 0)}{' '}
                                      привязок
                                    </span>
                                  ) : null}
                                </p>
                              </div>
                              <div className="flex flex-wrap gap-2 shrink-0">
                                <button
                                  type="button"
                                  onClick={() =>
                                    setLibraryStudioCtx({
                                      topic: {
                                        id: topic.id,
                                        name: topic.name,
                                        library_material_ids: topic.library_material_ids,
                                        library_course_ids: topic.library_course_ids,
                                      },
                                      subjectTitle: subject.subject,
                                      sectionName: section.name,
                                    })
                                  }
                                  className="px-3 py-1.5 text-sm text-indigo-700 hover:bg-indigo-50 rounded transition-colors inline-flex items-center gap-1"
                                >
                                  <Library className="w-4 h-4" />
                                  Библиотека
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleEditTopic(topic, section.id)}
                                  className="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                >
                                  Редактировать
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleAddTask(topic, section.id)}
                                  className="px-3 py-1.5 text-sm text-green-600 hover:bg-green-50 rounded transition-colors"
                                >
                                  + Задание
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleDeleteTopic(topic.id)}
                                  className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                                >
                                  Удалить
                                </button>
                              </div>
                            </div>
                          ))}
                          <button 
                            onClick={() => {
                              setSelectedSectionId(section.id);
                              setShowTopicModal(true);
                            }}
                            className="w-full py-2 text-sm text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                          >
                            + Добавить тему
                          </button>
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button 
                            onClick={() => handleEditSection(section, subject.id)}
                            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          >
                            Редактировать раздел
                          </button>
                          <button 
                            onClick={() => handleDeleteSection(section.id)}
                            className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                          >
                            Удалить раздел
                          </button>
                        </div>
                      </div>
                    ))}
                    <button 
                      onClick={() => {
                        setSelectedSubjectId(subject.id);
                        setShowSectionModal(true);
                      }}
                      className="w-full py-2 text-sm text-purple-600 border border-purple-200 rounded-lg hover:bg-purple-50 transition-colors"
                    >
                      + Добавить раздел
                    </button>
                  </div>
                </div>
              ))}
            </div>
            </div>
          </div>
          ) : null}
        </div>
      )}

      {/* User Management */}
      {activeTab === 'users' && (
        <div className="overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-sm">
          <div className="flex flex-col gap-4 border-b border-slate-100 bg-slate-50/80 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Пользователи</h3>
              <p className="mt-0.5 text-sm text-slate-600">Роли, активация, сброс пароля, тестовый seed</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleSeedDb}
                disabled={seedLoading}
                className="inline-flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-800 transition hover:bg-emerald-100 disabled:opacity-60"
              >
                {seedLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Заполняем…
                  </>
                ) : (
                  'Заполнить БД тестовыми данными'
                )}
              </button>
              <button
                type="button"
                onClick={() => setShowUserModal(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
              >
                <Plus className="h-4 w-4" />
                Новый пользователь
              </button>
            </div>
          </div>

          <div className="p-4 sm:p-6">
            {loading ? (
              <div className="flex flex-col items-center justify-center gap-3 py-16">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                <p className="text-sm text-slate-600">Загружаем список…</p>
              </div>
            ) : users.length === 0 ? (
              <p className="rounded-xl border border-dashed border-slate-200 py-12 text-center text-sm text-slate-600">Пользователей пока нет</p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-100">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/90 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <th className="py-3 pl-4 pr-2">Пользователь</th>
                      <th className="px-2 py-3">Email</th>
                      <th className="px-2 py-3 text-center">Роль</th>
                      <th className="px-2 py-3 text-center">Статус</th>
                      <th className="py-3 pl-2 pr-4 text-right">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id} className="border-b border-slate-100 transition-colors hover:bg-slate-50/80">
                        <td className="py-3.5 pl-4 pr-2">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-200 text-slate-900 shadow-sm ring-1 ring-slate-300/90">
                              <span className="select-none text-[15px] font-bold leading-none tracking-tight">
                                {avatarInitial(user.name)}
                              </span>
                            </div>
                            <span className="font-medium text-slate-900">{user.name}</span>
                          </div>
                        </td>
                        <td className="px-2 py-3.5 text-slate-600">{user.email}</td>
                        <td className="px-2 py-3.5 text-center">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${
                              user.role === 'teacher'
                                ? 'bg-violet-50 text-violet-800 ring-violet-200/80'
                                : user.role === 'admin'
                                  ? 'bg-rose-50 text-rose-800 ring-rose-200/80'
                                  : 'bg-sky-50 text-sky-800 ring-sky-200/80'
                            }`}
                          >
                            {user.role === 'teacher' ? 'Учитель' : user.role === 'admin' ? 'Админ' : 'Ученик'}
                          </span>
                        </td>
                        <td className="px-2 py-3.5 text-center">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${
                              user.status === 'active'
                                ? 'bg-emerald-50 text-emerald-800 ring-emerald-200/80'
                                : 'bg-slate-100 text-slate-600 ring-slate-200/80'
                            }`}
                          >
                            {user.status === 'active' ? 'Активен' : 'Неактивен'}
                          </span>
                        </td>
                        <td className="py-3.5 pl-2 pr-4 text-right">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => handleEditUser(user)}
                              className="rounded-lg p-2 text-indigo-600 transition hover:bg-indigo-50"
                              title="Редактировать"
                            >
                              <Edit className="h-4 w-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteUser(user.id)}
                              className="rounded-lg p-2 text-rose-600 transition hover:bg-rose-50"
                              title="Деактивировать"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* System Settings */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
            <h3 className="text-lg font-semibold text-slate-900">Адаптивность обучения</h3>
            <p className="mt-1 text-sm text-slate-600">Влияет на логику подбора сложности и пороги освоения.</p>
            <form onSubmit={handleSaveSettings} className="mt-6 space-y-6">
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Стратегия адаптации</label>
                <select
                  name="adaptation_strategy"
                  defaultValue={systemSettings.adaptation_strategy}
                  className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="aggressive">Агрессивная (быстрое повышение сложности)</option>
                  <option value="balanced">Сбалансированная (рекомендуется)</option>
                  <option value="gentle">Щадящая (постепенное повышение)</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Целевой уровень освоения темы (%)</label>
                <input
                  type="range"
                  name="target_mastery_percent"
                  min="60"
                  max="100"
                  defaultValue={systemSettings.target_mastery_percent}
                  className="h-2 w-full cursor-pointer accent-indigo-600"
                />
                <div className="mt-1 flex justify-between text-xs text-slate-500">
                  <span>60%</span>
                  <span className="font-semibold text-indigo-600">{systemSettings.target_mastery_percent}%</span>
                  <span>100%</span>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Попыток до смены стратегии</label>
                <input
                  type="number"
                  name="attempts_before_strategy_change"
                  defaultValue={systemSettings.attempts_before_strategy_change}
                  min="1"
                  max="10"
                  className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <button
                type="submit"
                className="w-full rounded-xl bg-indigo-600 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700"
              >
                Сохранить параметры адаптации
              </button>
            </form>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
            <h3 className="text-lg font-semibold text-slate-900">Интеграции API</h3>
            <p className="mt-1 text-sm text-slate-600">Ключи храните в безопасности; после сохранения проверьте работу RAG/чата.</p>
            <form onSubmit={handleSaveSettings} className="mt-6 space-y-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h4 className="font-medium text-slate-900">GigaChat</h4>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-emerald-200/80">
                    Поле в БД
                  </span>
                </div>
                <p className="mb-3 text-sm text-slate-600">Ключ для сценариев с GigaChat (если используется)</p>
                <input
                  type="password"
                  name="gigachat_api_key"
                  placeholder="••••••••"
                  defaultValue={systemSettings.gigachat_api_key}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <h4 className="font-medium text-slate-900">Pinecone</h4>
                  <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 ring-1 ring-emerald-200/80">
                    Векторный индекс
                  </span>
                </div>
                <p className="mb-3 text-sm text-slate-600">API-ключ и имя индекса для RAG</p>
                <div className="space-y-2">
                  <input
                    type="password"
                    name="pinecone_api_key"
                    placeholder="API ключ"
                    defaultValue={systemSettings.pinecone_api_key}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                  <input
                    type="text"
                    name="pinecone_index"
                    placeholder="Название индекса"
                    defaultValue={systemSettings.pinecone_index}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full rounded-xl border border-slate-200 bg-slate-900 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                Сохранить ключи API
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modals */}
      <Modal isOpen={showUserModal} onClose={() => setShowUserModal(false)} title="Добавить пользователя">
        <form onSubmit={handleCreateUser} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Имя</label>
            <input type="text" name="full_name" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Email</label>
            <input type="email" name="email" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Пароль</label>
            <input type="password" name="password" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Роль</label>
            <select name="role" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
              <option value="student">Ученик</option>
              <option value="teacher">Учитель</option>
              <option value="admin">Администратор</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Класс (опционально)</label>
            <input type="text" name="class_id" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Телефон (опционально)</label>
            <input type="text" name="phone" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">ФИО родителя (для ученика)</label>
            <input type="text" name="parent_fio" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Иванова Мария Петровна" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Телефон родителя (для ученика)</label>
            <input type="text" name="parent_phone" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="+7 999 123-45-67" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Создать
            </button>
            <button type="button" onClick={() => setShowUserModal(false)} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Отмена
            </button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showEditUserModal} onClose={() => { setShowEditUserModal(false); setEditingUser(null); }} title="Редактировать пользователя">
        {editingUser && (
          <form onSubmit={handleUpdateUser} className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-2">Имя</label>
              <input type="text" name="full_name" defaultValue={editingUser.name} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Email</label>
              <input type="email" name="email" defaultValue={editingUser.email} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Новый пароль</label>
              <input type="password" name="new_password" minLength={6} placeholder="Оставьте пустым, чтобы не менять" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
              <p className="text-xs text-gray-500 mt-1">Минимум 6 символов. Админ может менять пароль любого пользователя, включая свой.</p>
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Роль</label>
              <select name="role" defaultValue={editingUser.role} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="student">Ученик</option>
                <option value="teacher">Учитель</option>
                <option value="admin">Администратор</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Класс (опционально)</label>
              <input type="text" name="class_id" defaultValue={(editingUser as any).class_id} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Телефон (опционально)</label>
              <input type="text" name="phone" defaultValue={(editingUser as any).phone} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">ФИО родителя (для ученика)</label>
              <input type="text" name="parent_fio" defaultValue={(editingUser as any).parent_fio} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Телефон родителя (для ученика)</label>
              <input type="text" name="parent_phone" defaultValue={(editingUser as any).parent_phone} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Статус</label>
              <select name="is_active" defaultValue={editingUser.status === 'active' ? 'true' : 'false'} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                <option value="true">Активен</option>
                <option value="false">Неактивен</option>
              </select>
            </div>
            <div className="flex gap-3">
              <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Сохранить
              </button>
              <button type="button" onClick={() => { setShowEditUserModal(false); setEditingUser(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Отмена
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal isOpen={showSubjectModal} onClose={() => setShowSubjectModal(false)} title="Создать предмет">
        <form onSubmit={handleCreateSubject} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Название предмета</label>
            <input type="text" name="subject" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Создать
            </button>
            <button type="button" onClick={() => setShowSubjectModal(false)} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Отмена
            </button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showEditSubjectModal} onClose={() => { setShowEditSubjectModal(false); setEditingSubject(null); }} title="Редактировать предмет">
        {editingSubject && (
          <form onSubmit={handleUpdateSubject} className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-2">Название предмета</label>
              <input type="text" name="subject" defaultValue={editingSubject.subject} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="flex gap-3">
              <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Сохранить
              </button>
              <button type="button" onClick={() => { setShowEditSubjectModal(false); setEditingSubject(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Отмена
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal isOpen={showSectionModal} onClose={() => { setShowSectionModal(false); setSelectedSubjectId(null); }} title="Создать раздел">
        <form onSubmit={handleCreateSection} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Название раздела</label>
            <input type="text" name="name" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Создать
            </button>
            <button type="button" onClick={() => { setShowSectionModal(false); setSelectedSubjectId(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Отмена
            </button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showEditSectionModal} onClose={() => { setShowEditSectionModal(false); setEditingSection(null); setSelectedSubjectId(null); }} title="Редактировать раздел">
        {editingSection && (
          <form onSubmit={handleUpdateSection} className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-2">Название раздела</label>
              <input type="text" name="name" defaultValue={editingSection.name} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="flex gap-3">
              <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Сохранить
              </button>
              <button type="button" onClick={() => { setShowEditSectionModal(false); setEditingSection(null); setSelectedSubjectId(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Отмена
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal
        wide
        isOpen={showTopicModal}
        onClose={() => { setShowTopicModal(false); setSelectedSectionId(null); }}
        title="Создать тему"
      >
        <form onSubmit={handleCreateTopic} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Название темы</label>
            <input type="text" name="name" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Класс / возраст (для себя и фильтров)</label>
            <select
              name="grade_hint"
              defaultValue=""
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Не указано</option>
              <option value="1–4 класс">1–4 класс</option>
              <option value="5 класс">5 класс</option>
              <option value="6 класс">6 класс</option>
              <option value="7 класс">7 класс</option>
              <option value="8 класс">8 класс</option>
              <option value="9 класс">9 класс</option>
              <option value="10–11 класс">10–11 класс</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Текст для детей (кратко: о чём тема)</label>
            <textarea
              name="description"
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Например: решаем линейные уравнения и задачи на движение"
            />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Методичка / заметки учителю (не показываются ученику в этом интерфейсе)</label>
            <textarea
              name="teacher_notes"
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Цели урока, опоры, типичные ошибки…"
            />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Оценочное число «элементов» (материалов) вручную</label>
            <input
              type="number"
              name="elements"
              min={0}
              defaultValue={0}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Создать
            </button>
            <button type="button" onClick={() => { setShowTopicModal(false); setSelectedSectionId(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Отмена
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        wide
        isOpen={showEditTopicModal}
        onClose={() => { setShowEditTopicModal(false); setEditingTopic(null); setSelectedSectionId(null); }}
        title="Редактировать тему"
      >
        {editingTopic && (
          <form onSubmit={handleUpdateTopic} className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-2">Название темы</label>
              <input type="text" name="name" defaultValue={editingTopic.name} required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Класс / возраст</label>
              <select
                name="grade_hint"
                defaultValue={editingTopic.grade_hint || ''}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Не указано</option>
                {editingTopic.grade_hint &&
                !['1–4 класс', '5 класс', '6 класс', '7 класс', '8 класс', '9 класс', '10–11 класс'].includes(
                  editingTopic.grade_hint
                ) ? (
                  <option value={editingTopic.grade_hint}>{editingTopic.grade_hint} (своё)</option>
                ) : null}
                <option value="1–4 класс">1–4 класс</option>
                <option value="5 класс">5 класс</option>
                <option value="6 класс">6 класс</option>
                <option value="7 класс">7 класс</option>
                <option value="8 класс">8 класс</option>
                <option value="9 класс">9 класс</option>
                <option value="10–11 класс">10–11 класс</option>
              </select>
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Текст для детей</label>
              <textarea
                name="description"
                rows={4}
                defaultValue={editingTopic.description || ''}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Методичка для учителя</label>
              <textarea
                name="teacher_notes"
                rows={3}
                defaultValue={editingTopic.teacher_notes || ''}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Количество элементов</label>
              <input type="number" name="elements" defaultValue={editingTopic.elements} min="0" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Счётчик заданий в каталоге (можно подправить вручную)</label>
              <input type="number" name="tasks" defaultValue={editingTopic.tasks} min="0" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
            </div>

            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-gray-800 text-sm font-medium">Карточки заданий в каталоге</h4>
                <button
                  type="button"
                  onClick={() => loadTopicCatalogTasks(editingTopic.id)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Обновить список
                </button>
              </div>
              {topicCatalogTasksLoading ? (
                <p className="text-sm text-gray-500">Загрузка…</p>
              ) : topicCatalogTasks.length === 0 ? (
                <p className="text-sm text-gray-500">Пока нет. Нажмите «+ Задание» в списке тем.</p>
              ) : (
                <ul className="space-y-2 max-h-48 overflow-y-auto">
                  {topicCatalogTasks.map((t) => (
                    <li
                      key={t.id}
                      className="flex items-start justify-between gap-2 text-sm bg-white border border-gray-100 rounded p-2"
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-gray-800">{t.title}</p>
                        {t.description ? <p className="text-gray-600 text-xs mt-0.5">{t.description}</p> : null}
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteCatalogTask(editingTopic.id, t.id)}
                        className="text-red-600 text-xs shrink-0 hover:underline"
                      >
                        Удалить
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="flex gap-3">
              <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Сохранить
              </button>
              <button type="button" onClick={() => { setShowEditTopicModal(false); setEditingTopic(null); setSelectedSectionId(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Отмена
              </button>
            </div>
          </form>
        )}
      </Modal>

      <Modal isOpen={!!seedResult} onClose={() => setSeedResult(null)} title="Учётные записи после заполнения БД">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Создано пользователей: {seedResult?.created ?? 0}. Сохраните список — пароли больше не показываются.</p>
          <pre className="bg-gray-100 p-4 rounded-lg text-xs overflow-auto max-h-96 whitespace-pre-wrap">
            {seedResult?.credentials.map((c) => `${c.role}: ${c.name}\n  Email: ${c.email}\n  Пароль: ${c.password}${c.class_id ? `\n  Класс: ${c.class_id}` : ''}${c.parent_fio || c.parent_phone ? `\n  Родитель: ${[c.parent_fio, c.parent_phone].filter(Boolean).join(', ')}` : ''}`).join('\n\n')}
          </pre>
          <button
            type="button"
            onClick={() => {
              const text = seedResult?.credentials.map((c) => `${c.role}: ${c.name}\n  Email: ${c.email}\n  Пароль: ${c.password}${c.class_id ? `\n  Класс: ${c.class_id}` : ''}${c.parent_fio || c.parent_phone ? `\n  Родитель: ${[c.parent_fio, c.parent_phone].filter(Boolean).join(', ')}` : ''}`).join('\n\n') ?? '';
              navigator.clipboard.writeText(text);
              toast.success('Список скопирован в буфер обмена');
            }}
            className="w-full py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
          >
            Копировать список
          </button>
          <button type="button" onClick={() => setSeedResult(null)} className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Закрыть
          </button>
        </div>
      </Modal>

      <Modal isOpen={showAddTaskModal} onClose={() => { setShowAddTaskModal(false); setAddTaskTopic(null); }} title={addTaskTopic ? `Добавить задание: ${addTaskTopic.name}` : 'Добавить задание'}>
        <form onSubmit={handleCreateTask} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Название задания</label>
            <input type="text" name="task_title" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Например: Решить квадратное уравнение" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Описание (опционально)</label>
            <textarea name="task_description" rows={3} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" placeholder="Условие или подсказка" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              Добавить
            </button>
            <button type="button" onClick={() => { setShowAddTaskModal(false); setAddTaskTopic(null); }} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Отмена
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        wide
        isOpen={!!libraryStudioCtx}
        onClose={() => setLibraryStudioCtx(null)}
        title={libraryStudioCtx ? `Учебный контент: ${libraryStudioCtx.topic.name}` : ''}
      >
        {libraryStudioCtx ? (
          <TopicLibraryStudio
            key={libraryStudioCtx.topic.id}
            topic={libraryStudioCtx.topic}
            subjectTitle={libraryStudioCtx.subjectTitle}
            sectionName={libraryStudioCtx.sectionName}
            onClose={() => setLibraryStudioCtx(null)}
            onSaved={() => {
              loadAdminData();
            }}
          />
        ) : null}
      </Modal>

      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Загрузить материал">
        <form onSubmit={handleUploadMaterial} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Название материала</label>
            <input type="text" name="title" required className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Содержание</label>
            <textarea name="content" required rows={6} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Предмет (опционально)</label>
            <input type="text" name="subject" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-gray-700 mb-2">Тема (опционально)</label>
            <input type="text" name="topic" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="flex-1 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              Загрузить
            </button>
            <button type="button" onClick={() => setShowUploadModal(false)} className="flex-1 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
              Отмена
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
