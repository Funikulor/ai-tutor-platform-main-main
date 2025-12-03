import { Sparkles, BookOpen, Video, FileText, ExternalLink } from 'lucide-react';

interface ErrorAnalysis {
  type: string;
  topic: string;
  description: string;
  recommendation: string;
}

interface RecommendationPanelProps {
  error: ErrorAnalysis | null;
  onMaterialClick?: (materialId: string) => void;
}

export function RecommendationPanel({ error, onMaterialClick }: RecommendationPanelProps) {
  // RAG-generated recommendations based on error analysis
  const getRecommendations = (error: ErrorAnalysis | null) => {
    if (!error) {
      return {
        title: 'Продолжайте в том же духе!',
        description: 'Вы делаете отличные успехи. Система подберет следующее задание для закрепления материала.',
        materials: [
          {
            type: 'article',
            title: 'Основы алгебры: полное руководство',
            description: 'Систематизация базовых знаний',
            relevance: 85,
            url: '#',
            materialId: 'math-algebra-basics'
          },
          {
            type: 'video',
            title: 'Решение задач повышенной сложности',
            description: 'Видеокурс от ведущих преподавателей',
            relevance: 78,
            url: '#',
            materialId: 'math-advanced-problems'
          }
        ]
      };
    }

    // Simulate RAG retrieval and generation
    const recommendations = {
      'Теорема Пифагора': [
        {
          type: 'article',
          title: 'Теорема Пифагора: теория и примеры',
          description: 'Подробное объяснение теоремы с практическими примерами и визуализацией',
          relevance: 95,
          url: '#',
          materialId: 'math-pythagorean'
        },
        {
          type: 'video',
          title: 'Применение теоремы Пифагора в задачах',
          description: 'Видеоурок с разбором типичных задач',
          relevance: 92,
          url: '#',
          materialId: 'math-advanced-problems'
        },
        {
          type: 'pdf',
          title: 'Сборник задач на теорему Пифагора',
          description: 'PDF с 50 задачами различной сложности',
          relevance: 88,
          url: '#',
          materialId: 'math-fractions-pdf'
        }
      ],
      'Квадратные уравнения': [
        {
          type: 'article',
          title: 'Методы решения квадратных уравнений',
          description: 'Дискриминант, формула корней, теорема Виета',
          relevance: 93,
          url: '#',
          materialId: 'math-quadratic-eq'
        },
        {
          type: 'video',
          title: 'Квадратные уравнения: от простого к сложному',
          description: 'Пошаговый видеокурс',
          relevance: 90,
          url: '#',
          materialId: 'math-advanced-problems'
        }
      ]
    };

    const materials = recommendations[error.topic as keyof typeof recommendations] || [];

    return {
      title: `Рекомендации по теме: ${error.topic}`,
      description: error.description,
      materials
    };
  };

  const recommendations = getRecommendations(error);

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
        return 'bg-red-100 text-red-600';
      case 'pdf':
        return 'bg-orange-100 text-orange-600';
      default:
        return 'bg-blue-100 text-blue-600';
    }
  };

  return (
    <div className="space-y-4">
      {/* RAG System Header */}
      <div className="bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-6 h-6" />
          <h3 className="text-white">AI Рекомендации</h3>
        </div>
        <p className="text-purple-100 text-sm">
          Персонализированные материалы на основе RAG (Retrieval-Augmented Generation)
        </p>
      </div>

      {/* Main Recommendation Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h4 className="text-gray-900 mb-2">{recommendations.title}</h4>
        <p className="text-gray-600 text-sm mb-4">{recommendations.description}</p>

        {error && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
            <p className="text-yellow-900 text-sm">
              <strong>Тип ошибки:</strong> {
                error.type === 'conceptual' ? 'Концептуальная' :
                error.type === 'computational' ? 'Вычислительная' :
                'Опечатка'
              }
            </p>
          </div>
        )}

        {/* Recommended Materials */}
        <div className="space-y-3">
          <h5 className="text-gray-700 text-sm">Рекомендованные материалы:</h5>
          {recommendations.materials.map((material: any, index: number) => (
            <div 
              key={index}
              onClick={() => onMaterialClick?.(material.materialId || material.url)}
              className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${getTypeColor(material.type)}`}>
                  {getTypeIcon(material.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h6 className="text-gray-900 text-sm group-hover:text-blue-600 transition-colors">{material.title}</h6>
                    <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-blue-600 flex-shrink-0 transition-colors" />
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{material.description}</p>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                        style={{ width: `${material.relevance}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {material.relevance}% релевантность
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Explanation */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h5 className="text-gray-900 mb-3">Как работает система RAG</h5>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 text-xs">
              1
            </div>
            <p><strong>Retrieval:</strong> Система находит в базе знаний наиболее релевантные фрагменты теории, связанные с вашей ошибкой</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center flex-shrink-0 text-xs">
              2
            </div>
            <p><strong>Augmented:</strong> Найденные материалы обогащаются контекстом вашего уровня и истории обучения</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 text-xs">
              3
            </div>
            <p><strong>Generation:</strong> LLM генерирует персонализированное объяснение на основе точных данных</p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {error && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h5 className="text-gray-900 mb-3">Быстрые действия</h5>
          <div className="space-y-2">
            <button className="w-full py-2 px-4 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm">
              Пройти диагностический тест
            </button>
            <button className="w-full py-2 px-4 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors text-sm">
              Посмотреть примеры решений
            </button>
            <button className="w-full py-2 px-4 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors text-sm">
              Задать вопрос учителю
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
