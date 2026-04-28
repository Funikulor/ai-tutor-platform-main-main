import { useState, useEffect, useCallback } from 'react';
import {
  Video,
  FileText,
  ChevronRight,
  Search,
  Star,
  GraduationCap,
  Layers,
  Plus,
} from 'lucide-react';
import { motion } from 'motion/react';
import api from '../services/api';
import { toast } from 'sonner';
import type { Material } from './LibraryTab';
import {
  fetchMaterials,
  fetchLibraryCourses,
  createLibraryMaterial,
  type LibraryCourse,
} from '../services/materials';
import { MaterialAdminEditor } from './MaterialAdminEditor';
import { CourseAdminEditor } from './CourseAdminEditor';

export function AdminLibraryEditor() {
  const [librarySection, setLibrarySection] = useState<'courses' | 'materials'>('courses');
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null);
  const [courseEditor, setCourseEditor] = useState<null | { mode: 'edit'; id: string } | { mode: 'new' }>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<'all' | 'article' | 'video' | 'pdf'>('all');
  const [materials, setMaterials] = useState<Material[]>([]);
  const [courses, setCourses] = useState<LibraryCourse[]>([]);
  const [materialsLoading, setMaterialsLoading] = useState(true);
  const [coursesLoading, setCoursesLoading] = useState(true);
  const [materialRatings, setMaterialRatings] = useState<Record<string, number>>({});
  const [showNewMaterialModal, setShowNewMaterialModal] = useState(false);
  const [newMatTitle, setNewMatTitle] = useState('');
  const [newMatCreating, setNewMatCreating] = useState(false);

  const loadMaterials = useCallback(async () => {
    setMaterialsLoading(true);
    try {
      const data = await fetchMaterials();
      setMaterials(Array.isArray(data) ? data : []);
    } catch {
      setMaterials([]);
    } finally {
      setMaterialsLoading(false);
    }
  }, []);

  const loadCourses = useCallback(async () => {
    setCoursesLoading(true);
    try {
      const data = await fetchLibraryCourses();
      setCourses(Array.isArray(data) ? data : []);
    } catch {
      setCourses([]);
    } finally {
      setCoursesLoading(false);
    }
  }, []);

  const loadMaterialRatings = useCallback(async () => {
    try {
      const response = await api.get('/materials/ratings');
      setMaterialRatings(response.data.ratings || {});
    } catch {
      setMaterialRatings({});
    }
  }, []);

  useEffect(() => {
    loadMaterials();
    loadCourses();
    loadMaterialRatings();
  }, [loadMaterials, loadCourses, loadMaterialRatings]);

  const q = searchQuery.toLowerCase();

  const filteredCourses = courses.filter((c) => {
    const subOk = selectedSubject === 'all' || c.subject === selectedSubject;
    const searchOk =
      !q ||
      c.title.toLowerCase().includes(q) ||
      c.description.toLowerCase().includes(q) ||
      c.topic.toLowerCase().includes(q);
    return subOk && searchOk;
  });

  const filteredMaterials = materials.filter((material) => {
    const matchesSubject = selectedSubject === 'all' || material.subject === selectedSubject;
    const matchesType = selectedType === 'all' || material.type === selectedType;
    const matchesSearch =
      material.title.toLowerCase().includes(q) ||
      material.description.toLowerCase().includes(q);
    return matchesSubject && matchesType && matchesSearch;
  });

  const subjects = [
    'all',
    ...Array.from(
      new Set([
        ...materials.map((m) => m.subject),
        ...courses.map((c) => c.subject),
      ])
    ),
  ];

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video':
        return <Video className="w-5 h-5" />;
      case 'pdf':
        return <FileText className="w-5 h-5" />;
      default:
        return <BookOpen className="w-5 h-5" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'video':
        return 'bg-red-100 text-red-600 border-red-200';
      case 'pdf':
        return 'bg-orange-100 text-orange-600 border-orange-200';
      default:
        return 'bg-blue-100 text-blue-600 border-blue-200';
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'Начальный';
      case 'intermediate':
        return 'Средний';
      case 'advanced':
        return 'Продвинутый';
      default:
        return difficulty;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-700';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-700';
      case 'advanced':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleCreateMaterial = async () => {
    const t = newMatTitle.trim();
    if (!t) {
      toast.error('Введите название');
      return;
    }
    setNewMatCreating(true);
    try {
      await createLibraryMaterial({
        title: t,
        description: '',
        content: '',
        subject: 'Математика',
        topic: t.slice(0, 80),
        type: 'article',
        difficulty: 'beginner',
        duration: '15 мин',
      });
      toast.success('Материал создан — откройте его в списке и редактируйте текст');
      setShowNewMaterialModal(false);
      setNewMatTitle('');
      await loadMaterials();
    } catch (e: unknown) {
      console.error(e);
      toast.error('Не удалось создать материал');
    } finally {
      setNewMatCreating(false);
    }
  };

  if (courseEditor) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-6">
        <CourseAdminEditor
          courseId={courseEditor.mode === 'edit' ? courseEditor.id : null}
          startFresh={courseEditor.mode === 'new'}
          onBack={() => setCourseEditor(null)}
          onSaved={() => {
            void loadCourses();
          }}
        />
      </div>
    );
  }

  if (selectedMaterial) {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm sm:p-6">
        <MaterialAdminEditor
          material={selectedMaterial}
          onBack={() => setSelectedMaterial(null)}
          onSaved={() => {
            void loadMaterials();
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setLibrarySection('courses')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
            librarySection === 'courses'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          <GraduationCap className="h-5 w-5" />
          Мини-курсы
        </button>
        <button
          type="button"
          onClick={() => setLibrarySection('materials')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
            librarySection === 'materials'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          <Layers className="h-5 w-5" />
          Статьи, видео, PDF
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        {librarySection === 'courses' && (
          <button
            type="button"
            onClick={() => setCourseEditor({ mode: 'new' })}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Новый курс
          </button>
        )}
        {librarySection === 'materials' && (
          <button
            type="button"
            onClick={() => setShowNewMaterialModal(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" />
            Новый материал
          </button>
        )}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row">
          <div className="relative flex-1">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder={librarySection === 'courses' ? 'Поиск курсов…' : 'Поиск материалов…'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-11 w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="all">Все предметы</option>
            {subjects
              .filter((s) => s !== 'all')
              .map((subject) => (
                <option key={subject} value={subject}>
                  {subject}
                </option>
              ))}
          </select>
          {librarySection === 'materials' ? (
            <div className="flex flex-wrap gap-2 rounded-lg bg-gray-100 p-1">
              {(['all', 'article', 'video', 'pdf'] as const).map((tp) => (
                <button
                  key={tp}
                  type="button"
                  onClick={() => setSelectedType(tp)}
                  className={`rounded-md px-3 py-2 text-sm transition-all ${
                    selectedType === tp ? 'bg-white text-indigo-600 shadow-sm' : 'text-gray-600'
                  }`}
                >
                  {tp === 'all' ? 'Все' : tp === 'article' ? 'Статьи' : tp === 'video' ? 'Видео' : 'PDF'}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {librarySection === 'courses' && (
        <>
          {coursesLoading && (
            <div className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-500">Загружаем курсы…</div>
          )}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {filteredCourses.map((c, index) => (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                onClick={() => setCourseEditor({ mode: 'edit', id: c.id })}
                className="group cursor-pointer overflow-hidden rounded-xl border-2 border-gray-200 bg-white transition-all hover:border-indigo-400 hover:shadow-lg"
              >
                <div className="h-2 bg-gradient-to-r from-indigo-500 to-violet-500" />
                <div className="p-6">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 text-indigo-900">
                      <GraduationCap className="h-6 w-6 shrink-0" />
                      <span className="text-xs font-bold uppercase tracking-wide">Мини-курс</span>
                    </div>
                    <span className={`rounded px-2 py-1 text-xs ${getDifficultyColor(c.difficulty)}`}>
                      {getDifficultyLabel(c.difficulty)}
                    </span>
                  </div>
                  <h3 className="mb-2 text-lg font-bold text-gray-950 group-hover:text-indigo-800">{c.title}</h3>
                  <p className="mb-4 line-clamp-3 text-sm leading-relaxed text-gray-700">{c.description}</p>
                  <div className="mb-4 flex flex-wrap gap-2">
                    <span className="rounded bg-purple-50 px-2 py-1 text-xs text-purple-800">{c.subject}</span>
                    <span className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-800">{c.topic}</span>
                    <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700">
                      {c.lessons?.length ?? 0} шагов
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-t border-gray-100 pt-3 text-sm text-indigo-600">
                    <span className="font-medium">Редактировать</span>
                    <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
          {!coursesLoading && filteredCourses.length === 0 && (
            <div className="rounded-xl border border-gray-200 bg-white py-12 text-center text-gray-600">
              Курсы не найдены. Создайте новый курс кнопкой выше.
            </div>
          )}
        </>
      )}

      {librarySection === 'materials' && (
        <>
          {materialsLoading && (
            <div className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-500">Загружаем материалы…</div>
          )}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredMaterials.map((material, index) => (
              <motion.div
                key={material.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.06 }}
                onClick={() => setSelectedMaterial(material)}
                className="group cursor-pointer rounded-xl border-2 border-gray-200 bg-white transition-all hover:border-blue-400 hover:shadow-lg"
              >
                <div className="p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <div className={`rounded-lg border-2 px-3 py-1.5 ${getTypeColor(material.type)}`}>
                      <div className="flex items-center gap-2">
                        {getTypeIcon(material.type)}
                        <span className="text-sm capitalize">
                          {material.type === 'article' ? 'Статья' : material.type === 'video' ? 'Видео' : 'PDF'}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 text-yellow-500">
                      <Star className="h-4 w-4 fill-current" />
                      <span className="text-sm text-gray-700">
                        {materialRatings[material.id] !== undefined ? materialRatings[material.id] : material.rating}
                      </span>
                    </div>
                  </div>
                  <h3 className="mb-2 text-gray-900 group-hover:text-blue-600">{material.title}</h3>
                  <p className="mb-4 line-clamp-2 text-sm text-gray-600">{material.description}</p>
                  <div className="mb-4 flex flex-wrap gap-2">
                    <span className="rounded bg-purple-50 px-2 py-1 text-xs text-purple-700">{material.subject}</span>
                    <span className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">{material.topic}</span>
                    <span className={`rounded px-2 py-1 text-xs ${getDifficultyColor(material.difficulty)}`}>
                      {getDifficultyLabel(material.difficulty)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-t border-gray-200 pt-4 text-sm text-blue-600">
                    <span>Редактировать текст</span>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
          {!materialsLoading && filteredMaterials.length === 0 && (
            <div className="py-12 text-center text-gray-600">
              <BookOpen className="mx-auto mb-4 h-16 w-16 text-gray-300" />
              Материалы не найдены
            </div>
          )}
        </>
      )}

      {showNewMaterialModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Новый материал</h3>
            <p className="mt-1 text-sm text-gray-500">После создания откроется редактор — текст сохраняется автоматически.</p>
            <input
              value={newMatTitle}
              onChange={(e) => setNewMatTitle(e.target.value)}
              placeholder="Название"
              className="mt-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowNewMaterialModal(false)}
                className="rounded-lg px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
              >
                Отмена
              </button>
              <button
                type="button"
                disabled={newMatCreating}
                onClick={() => void handleCreateMaterial()}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {newMatCreating ? 'Создание…' : 'Создать'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
