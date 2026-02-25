import { useState, useEffect } from 'react';
import { MaterialViewer } from './MaterialViewer';
import { BookOpen, Video, FileText, ChevronRight, Search, Star, CheckCircle } from 'lucide-react';
import { motion } from 'motion/react';
import api from '../services/api';
import { fetchMaterials } from '../services/materials';

export interface Material {
  id: string;
  type: 'article' | 'video' | 'pdf';
  title: string;
  description: string;
  subject: string;
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration?: string;
  rating: number;
  content?: string;
  videoUrl?: string;
  pdfUrl?: string;
}

interface LibraryTabProps {
  selectedMaterialId?: string;
  onStudyComplete?: (topic: string) => void;
}

export function LibraryTab({ selectedMaterialId, onStudyComplete }: LibraryTabProps) {
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<'all' | 'article' | 'video' | 'pdf'>('all');
  const [materials, setMaterials] = useState<Material[]>([]);
  const [materialsLoading, setMaterialsLoading] = useState(true);
  const [topicMastery, setTopicMastery] = useState<Record<string, number>>({});
  const [materialRatings, setMaterialRatings] = useState<Record<string, number>>({});

  useEffect(() => {
    loadMaterials();
    loadStudyProgress();
    loadMaterialRatings();
  }, []);

  useEffect(() => {
    if (!selectedMaterialId || materials.length === 0) return;
    const material = materials.find((m) => m.id === selectedMaterialId);
    if (material) {
      setSelectedMaterial(material);
    }
  }, [selectedMaterialId, materials]);

  const loadMaterials = async () => {
    setMaterialsLoading(true);
    try {
      const data = await fetchMaterials();
      setMaterials(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading materials:', err);
      setMaterials([]);
    } finally {
      setMaterialsLoading(false);
    }
  };

  const loadStudyProgress = async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) return;

      const response = await api.get(`/study/progress/${userId}`);
      const data = response.data;

      setTopicMastery(data.topic_mastery || {});
    } catch (err) {
      console.error('Error loading study progress:', err);
    }
  };

  const loadMaterialRatings = async () => {
    try {
      const response = await api.get('/materials/ratings');
      setMaterialRatings(response.data.ratings || {});
    } catch (err) {
      console.error('Error loading material ratings:', err);
    }
  };

  const handleStudyComplete = (topic: string) => {
    loadStudyProgress();
    if (onStudyComplete) {
      onStudyComplete(topic);
    }
  };

  const getTopicMastery = (topic: string): number => {
    return topicMastery[topic] ? Math.round(topicMastery[topic] * 100) : 0;
  };

  const isMaterialStudied = (material: Material): boolean => {
    return getTopicMastery(material.topic) >= 30;
  };

  const subjects = ['all', ...Array.from(new Set(materials.map(m => m.subject)))];

  const filteredMaterials = materials.filter(material => {
    const matchesSubject = selectedSubject === 'all' || material.subject === selectedSubject;
    const matchesType = selectedType === 'all' || material.type === selectedType;
    const matchesSearch = material.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         material.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSubject && matchesType && matchesSearch;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video className="w-5 h-5" />;
      case 'pdf': return <FileText className="w-5 h-5" />;
      default: return <BookOpen className="w-5 h-5" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'video': return 'bg-red-100 text-red-600 border-red-200';
      case 'pdf': return 'bg-orange-100 text-orange-600 border-orange-200';
      default: return 'bg-blue-100 text-blue-600 border-blue-200';
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'Начальный';
      case 'intermediate': return 'Средний';
      case 'advanced': return 'Продвинутый';
      default: return difficulty;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-700';
      case 'intermediate': return 'bg-yellow-100 text-yellow-700';
      case 'advanced': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (selectedMaterial) {
    return (
      <MaterialViewer 
        material={selectedMaterial} 
        onBack={() => setSelectedMaterial(null)}
        onStudyComplete={handleStudyComplete}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
            <BookOpen className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-white text-3xl mb-2">Библиотека знаний</h1>
            <p className="text-blue-100">Учебные материалы, видеоуроки и справочники по всем предметам</p>
          </div>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-blue-100 text-sm">Всего материалов</p>
            <p className="text-2xl text-white mt-1">{materials.length}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-blue-100 text-sm">Предметов</p>
            <p className="text-2xl text-white mt-1">{subjects.length - 1}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
            <p className="text-blue-100 text-sm">Средний рейтинг</p>
            <p className="text-2xl text-white mt-1">4.7 ⭐</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск материалов..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Subject Filter */}
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">Все предметы</option>
            {subjects.filter(s => s !== 'all').map(subject => (
              <option key={subject} value={subject}>{subject}</option>
            ))}
          </select>

          {/* Type Filter */}
          <div className="flex gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setSelectedType('all')}
              className={`px-4 py-2 rounded-md text-sm transition-all ${
                selectedType === 'all' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600'
              }`}
            >
              Все
            </button>
            <button
              onClick={() => setSelectedType('article')}
              className={`px-4 py-2 rounded-md text-sm transition-all ${
                selectedType === 'article' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600'
              }`}
            >
              Статьи
            </button>
            <button
              onClick={() => setSelectedType('video')}
              className={`px-4 py-2 rounded-md text-sm transition-all ${
                selectedType === 'video' ? 'bg-white shadow-sm text-red-600' : 'text-gray-600'
              }`}
            >
              Видео
            </button>
            <button
              onClick={() => setSelectedType('pdf')}
              className={`px-4 py-2 rounded-md text-sm transition-all ${
                selectedType === 'pdf' ? 'bg-white shadow-sm text-orange-600' : 'text-gray-600'
              }`}
            >
              PDF
            </button>
          </div>
        </div>
      </div>

      {/* Materials Grid */}
      {materialsLoading && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-sm text-gray-500">
          Загружаем материалы...
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredMaterials.map((material, index) => (
          <motion.div
            key={material.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => setSelectedMaterial(material)}
            className="bg-white rounded-xl border-2 border-gray-200 hover:border-blue-400 hover:shadow-lg transition-all cursor-pointer group"
          >
            <div className="p-6">
              {/* Type Badge */}
              <div className="flex items-center justify-between mb-4">
                <div className={`px-3 py-1.5 rounded-lg border-2 ${getTypeColor(material.type)}`}>
                  <div className="flex items-center gap-2">
                    {getTypeIcon(material.type)}
                    <span className="text-sm capitalize">{material.type === 'article' ? 'Статья' : material.type === 'video' ? 'Видео' : 'PDF'}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-yellow-500">
                  <Star className="w-4 h-4 fill-current" />
                  <span className="text-sm text-gray-700">
                    {materialRatings[material.id] !== undefined 
                      ? materialRatings[material.id] 
                      : material.rating}
                  </span>
                </div>
              </div>

              {/* Content */}
              <h3 className="text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                {material.title}
              </h3>
              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {material.description}
              </p>

              {/* Meta Info */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">
                  {material.subject}
                </span>
                <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                  {material.topic}
                </span>
                <span className={`px-2 py-1 rounded text-xs ${getDifficultyColor(material.difficulty)}`}>
                  {getDifficultyLabel(material.difficulty)}
                </span>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">{material.duration}</span>
                  {isMaterialStudied(material) && (
                    <div className="flex items-center gap-1 text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-xs font-semibold">Изучено</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 text-blue-600 group-hover:gap-3 transition-all">
                  <span className="text-sm">
                    {isMaterialStudied(material) ? 'Повторить' : 'Изучить'}
                  </span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
              
            </div>
          </motion.div>
        ))}
      </div>

      {filteredMaterials.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600">Материалы не найдены</p>
          <p className="text-sm text-gray-500 mt-2">Попробуйте изменить фильтры поиска</p>
        </div>
      )}
    </div>
  );
}
