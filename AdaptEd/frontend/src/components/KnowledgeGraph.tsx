import { useState } from 'react';
import { CheckCircle, AlertCircle, Circle, ChevronRight, ChevronDown } from 'lucide-react';

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

export function KnowledgeGraph() {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['math', 'algebra']));

  const knowledgeData: KnowledgeNode = {
    id: 'math',
    name: 'Математика',
    level: 'subject',
    masteryLevel: 75,
    status: 'learning',
    children: [
      {
        id: 'algebra',
        name: 'Алгебра',
        level: 'section',
        masteryLevel: 82,
        status: 'learning',
        children: [
          {
            id: 'equations',
            name: 'Уравнения',
            level: 'topic',
            masteryLevel: 90,
            status: 'mastered',
            children: [
              {
                id: 'linear-eq',
                name: 'Линейные уравнения',
                level: 'element',
                masteryLevel: 95,
                status: 'mastered',
                errorCount: 2,
                lastAttempt: '2025-11-29'
              },
              {
                id: 'quadratic-eq',
                name: 'Квадратные уравнения',
                level: 'element',
                masteryLevel: 62,
                status: 'learning',
                errorCount: 8,
                lastAttempt: '2025-11-28'
              }
            ]
          },
          {
            id: 'functions',
            name: 'Функции',
            level: 'topic',
            masteryLevel: 78,
            status: 'learning',
            children: [
              {
                id: 'linear-func',
                name: 'Линейная функция',
                level: 'element',
                masteryLevel: 88,
                status: 'mastered',
                errorCount: 3,
                lastAttempt: '2025-11-27'
              },
              {
                id: 'quadratic-func',
                name: 'Квадратичная функция',
                level: 'element',
                masteryLevel: 68,
                status: 'learning',
                errorCount: 6,
                lastAttempt: '2025-11-26'
              }
            ]
          }
        ]
      },
      {
        id: 'geometry',
        name: 'Геометрия',
        level: 'section',
        masteryLevel: 68,
        status: 'learning',
        children: [
          {
            id: 'triangles',
            name: 'Треугольники',
            level: 'topic',
            masteryLevel: 70,
            status: 'learning',
            children: [
              {
                id: 'pythagoras',
                name: 'Теорема Пифагора',
                level: 'element',
                masteryLevel: 45,
                status: 'needs-work',
                errorCount: 12,
                lastAttempt: '2025-11-30'
              },
              {
                id: 'triangle-area',
                name: 'Площадь треугольника',
                level: 'element',
                masteryLevel: 85,
                status: 'mastered',
                errorCount: 2,
                lastAttempt: '2025-11-25'
              }
            ]
          },
          {
            id: 'trigonometry',
            name: 'Тригонометрия',
            level: 'topic',
            masteryLevel: 38,
            status: 'needs-work',
            children: [
              {
                id: 'sin-cos',
                name: 'Синус и косинус',
                level: 'element',
                masteryLevel: 38,
                status: 'needs-work',
                errorCount: 15,
                lastAttempt: '2025-11-24'
              }
            ]
          }
        ]
      }
    ]
  };

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
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-gray-900">Граф знаний</h2>
            <p className="text-gray-600">Визуализация вашего прогресса по темам</p>
          </div>
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
            <span className="text-gray-900">{knowledgeData.masteryLevel}%</span>
          </div>
          <div className="h-3 bg-white rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500"
              style={{ width: `${knowledgeData.masteryLevel}%` }}
            />
          </div>
        </div>
      </div>

      {/* Knowledge Tree */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Структура знаний</h3>
        <div className="space-y-2">
          {renderNode(knowledgeData)}
        </div>
      </div>

      {/* Problem Areas */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Области, требующие внимания</h3>
        <div className="space-y-3">
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-red-900">Теорема Пифагора</h4>
                <p className="text-sm text-red-700">12 ошибок • Уровень освоения: 45%</p>
              </div>
              <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                Практиковать
              </button>
            </div>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-yellow-900">Тригонометрия</h4>
                <p className="text-sm text-yellow-700">15 ошибок • Уровень освоения: 38%</p>
              </div>
              <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors">
                Практиковать
              </button>
            </div>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-orange-900">Квадратные уравнения</h4>
                <p className="text-sm text-orange-700">8 ошибок • Уровень освоения: 62%</p>
              </div>
              <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors">
                Практиковать
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
