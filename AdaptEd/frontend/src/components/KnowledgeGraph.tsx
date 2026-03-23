import { useState, useEffect, useCallback } from 'react';
import { CheckCircle, AlertCircle, Circle, ChevronRight, ChevronDown, RefreshCw } from 'lucide-react';
import api from '../services/api';

interface KnowledgeNode {
  id: string;
  name: string;
  level: 'subject' | 'section' | 'topic' | 'element';
  masteryLevel: number; // 0-100
  status: 'mastered' | 'learning' | 'needs-work' | 'not-started';
  children?: KnowledgeNode[];
  errorCount?: number;
  lastAttempt?: string;
}

interface ProblemArea {
  name: string;
  masteryLevel: number;
  errorCount: number;
  status: string;
}

export function KnowledgeGraph() {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['math']));
  const [knowledgeData, setKnowledgeData] = useState<KnowledgeNode | null>(null);
  const [problemAreas, setProblemAreas] = useState<ProblemArea[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadKnowledgeGraph = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.get(`/knowledge-graph/${userId}`);
      const data = response.data;

      if (data.knowledgeGraph) {
        setKnowledgeData(data.knowledgeGraph);
        setOverallProgress(data.overallProgress || 0);
      }
      if (data.problemAreas) {
        setProblemAreas(data.problemAreas);
      }
    } catch (err: any) {
      console.error('Error loading knowledge graph:', err);
      setError(err.response?.data?.detail || 'Не удалось загрузить граф знаний');
      // Используем пустые данные при ошибке
      const emptyData: KnowledgeNode = {
        id: 'math',
        name: 'Математика',
        level: 'subject',
        masteryLevel: 0,
        status: 'not-started',
        children: []
      };
      setKnowledgeData(emptyData);
      setOverallProgress(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadKnowledgeGraph();
  }, [loadKnowledgeGraph]);

  const toggleNode = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'mastered':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'learning':
        return <Circle className="w-5 h-5 text-blue-600 fill-blue-200" />;
      case 'needs-work':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'mastered':
        return 'bg-green-100 border-green-300';
      case 'learning':
        return 'bg-blue-100 border-blue-300';
      case 'needs-work':
        return 'bg-red-100 border-red-300';
      default:
        return 'bg-gray-100 border-gray-300';
    }
  };

  const getMasteryBarColor = (masteryLevel: number) => {
    if (masteryLevel >= 80) return 'bg-green-500';
    if (masteryLevel >= 60) return 'bg-blue-500';
    if (masteryLevel >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const renderNode = (node: KnowledgeNode, depth: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const indentClass = `ml-${depth * 6}`;

    return (
      <div key={node.id} className="mb-2">
        <div
          className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${getStatusColor(node.status)}`}
          style={{ marginLeft: `${depth * 24}px` }}
          onClick={() => hasChildren && toggleNode(node.id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 flex-1">
              {hasChildren && (
                <div className="text-gray-600">
                  {isExpanded ? (
                    <ChevronDown className="w-5 h-5" />
                  ) : (
                    <ChevronRight className="w-5 h-5" />
                  )}
                </div>
              )}
              {!hasChildren && <div className="w-5" />}
              
              {getStatusIcon(node.status)}
              
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-gray-900">{node.name}</h4>
                  {node.errorCount !== undefined && node.errorCount > 0 && (
                    <span className="px-2 py-0.5 bg-red-200 text-red-800 rounded text-xs">
                      {node.errorCount} ошибок
                    </span>
                  )}
                  {node.lastAttempt && (
                    <span className="text-xs text-gray-500">
                      {node.lastAttempt}
                    </span>
                  )}
                </div>
                
                {/* Mastery Progress Bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${getMasteryBarColor(node.masteryLevel)}`}
                      style={{ width: `${node.masteryLevel}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-700 min-w-[3rem]">
                    {node.masteryLevel}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Render children if expanded */}
        {isExpanded && hasChildren && (
          <div className="mt-2">
            {node.children!.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-gray-900">Граф знаний</h2>
            <p className="text-gray-600">Прогресс по темам из адаптивных заданий и изученных материалов</p>
          </div>
          <button
            type="button"
            onClick={() => loadKnowledgeGraph()}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-sm text-gray-600">Освоено</span>
            </div>
            <div className="flex items-center gap-2">
              <Circle className="w-5 h-5 text-blue-600 fill-blue-200" />
              <span className="text-sm text-gray-600">В процессе</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <span className="text-sm text-gray-600">Требует внимания</span>
            </div>
          </div>
        </div>

        {/* Overall Progress */}
        <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-700">Общий прогресс</span>
            <span className="text-gray-900">{overallProgress}%</span>
          </div>
          <div className="h-3 bg-white rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="text-center py-8">
            <p className="text-gray-500">Загрузка графа знаний...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Knowledge Tree */}
      {!loading && !error && knowledgeData && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Структура знаний</h3>
          {!knowledgeData.children || knowledgeData.children.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p className="mb-2">Пока нет тем с прогрессом.</p>
              <p className="text-sm">
                Решайте задания во вкладке «Адаптивные задания» или изучайте материалы в «Библиотеке» — проценты по темам появятся здесь.
              </p>
            </div>
          ) : (
            <div className="space-y-2">{renderNode(knowledgeData)}</div>
          )}
        </div>
      )}

      {/* Problem Areas */}
      {!loading && !error && problemAreas.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Области, требующие внимания</h3>
          <div className="space-y-3">
            {problemAreas.map((area, index) => {
              const getColorClass = (status: string) => {
                if (status === 'needs-work' || area.masteryLevel < 50) {
                  return {
                    bg: 'bg-red-50',
                    border: 'border-red-200',
                    text: 'text-red-900',
                    textSm: 'text-red-700',
                    button: 'bg-red-600 hover:bg-red-700'
                  };
                } else if (area.masteryLevel < 70) {
                  return {
                    bg: 'bg-yellow-50',
                    border: 'border-yellow-200',
                    text: 'text-yellow-900',
                    textSm: 'text-yellow-700',
                    button: 'bg-yellow-600 hover:bg-yellow-700'
                  };
                } else {
                  return {
                    bg: 'bg-orange-50',
                    border: 'border-orange-200',
                    text: 'text-orange-900',
                    textSm: 'text-orange-700',
                    button: 'bg-orange-600 hover:bg-orange-700'
                  };
                }
              };
              
              const colors = getColorClass(area.status);
              
              return (
                <div key={index} className={`p-4 ${colors.bg} rounded-lg border ${colors.border}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className={colors.text}>{area.name}</h4>
                      <p className={`text-sm ${colors.textSm}`}>
                        {area.errorCount} {area.errorCount === 1 ? 'ошибка' : area.errorCount < 5 ? 'ошибки' : 'ошибок'} • Уровень освоения: {area.masteryLevel}%
                      </p>
                    </div>
                    <button className={`px-4 py-2 ${colors.button} text-white rounded-lg transition-colors`}>
                      Практиковать
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
