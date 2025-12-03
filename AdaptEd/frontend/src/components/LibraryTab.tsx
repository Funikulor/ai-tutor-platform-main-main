import { useState } from 'react';
import { MaterialViewer } from './MaterialViewer';
import { BookOpen, Video, FileText, ChevronRight, Search, Filter, Star } from 'lucide-react';
import { motion } from 'motion/react';

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
}

export function LibraryTab({ selectedMaterialId }: LibraryTabProps) {
  const [selectedMaterial, setSelectedMaterial] = useState<Material | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<'all' | 'article' | 'video' | 'pdf'>('all');

  // База учебных материалов
  const materials: Material[] = [
    {
      id: 'math-algebra-basics',
      type: 'article',
      title: 'Основы алгебры: полное руководство',
      description: 'Систематизация базовых знаний по алгебре: уравнения, неравенства, функции',
      subject: 'Математика',
      topic: 'Алгебра',
      difficulty: 'beginner',
      duration: '15 мин',
      rating: 4.8,
      content: `# Основы алгебры: полное руководство

## Введение

Алгебра - это раздел математики, изучающий общие свойства действий над различными величинами и решение уравнений.

## 1. Линейные уравнения

Линейное уравнение имеет вид: **ax + b = 0**, где a ≠ 0

### Примеры:
- 2x + 5 = 13
- 3x - 7 = 2x + 1

### Алгоритм решения:
1. Перенести все члены с x в левую часть, остальные в правую
2. Привести подобные слагаемые
3. Разделить обе части на коэффициент при x

**Пример решения:**
2x + 5 = 13
2x = 13 - 5
2x = 8
x = 4

## 2. Квадратные уравнения

Квадратное уравнение имеет вид: **ax² + bx + c = 0**, где a ≠ 0

### Формула корней:
x = (-b ± √(b² - 4ac)) / 2a

### Дискриминант:
D = b² - 4ac

- Если D > 0, уравнение имеет два корня
- Если D = 0, уравнение имеет один корень
- Если D < 0, уравнение не имеет действительных корней

**Пример:**
x² - 5x + 6 = 0
D = 25 - 24 = 1
x₁ = (5 + 1) / 2 = 3
x₂ = (5 - 1) / 2 = 2

## 3. Системы уравнений

Система двух линейных уравнений с двумя неизвестными:
{
  a₁x + b₁y = c₁
  a₂x + b₂y = c₂
}

### Методы решения:
1. **Метод подстановки**: выразить одну переменную через другую
2. **Метод сложения**: умножить уравнения на числа и сложить
3. **Графический метод**: найти точку пересечения прямых

## 4. Неравенства

Неравенство - это соотношение вида a < b, a > b, a ≤ b или a ≥ b

**Важно:** При умножении или делении неравенства на отрицательное число знак неравенства меняется на противоположный!

## Практические задания

1. Решите уравнение: 3x + 7 = 22
2. Решите квадратное уравнение: x² - 7x + 12 = 0
3. Решите неравенство: 2x - 5 < 9

## Полезные советы

✓ Всегда проверяйте решение подстановкой
✓ Не забывайте указывать единицы измерения
✓ Рисуйте схемы и графики для наглядности
✓ Практикуйтесь регулярно

Удачи в изучении алгебры! 🎓`
    },
    {
      id: 'math-pythagorean',
      type: 'article',
      title: 'Теорема Пифагора: теория и примеры',
      description: 'Подробное объяснение теоремы с практическими примерами и визуализацией',
      subject: 'Математика',
      topic: 'Геометрия',
      difficulty: 'intermediate',
      duration: '20 мин',
      rating: 4.9,
      content: `# Теорема Пифагора

## Формулировка теоремы

В прямоугольном треугольнике квадрат гипотенузы равен сумме квадратов катетов.

**c² = a² + b²**

где:
- c - гипотенуза (сторона напротив прямого угла)
- a и b - катеты (стороны, образующие прямой угол)

## Примеры решения задач

### Задача 1
Катеты прямоугольного треугольника равны 3 см и 4 см. Найти гипотенузу.

**Решение:**
c² = 3² + 4²
c² = 9 + 16 = 25
c = 5 см

### Задача 2
Гипотенуза равна 13 см, один катет равен 5 см. Найти второй катет.

**Решение:**
13² = 5² + b²
169 = 25 + b²
b² = 144
b = 12 см

## Применение в жизни

- Строительство (проверка прямых углов)
- Навигация (расчет расстояний)
- Физика (расчет векторов)

Практикуйся и теорема станет твоим надежным помощником! 📐`
    },
    {
      id: 'math-advanced-problems',
      type: 'video',
      title: 'Решение задач повышенной сложности',
      description: 'Видеокурс от ведущих преподавателей с пошаговым разбором сложных задач',
      subject: 'Математика',
      topic: 'Смешанные темы',
      difficulty: 'advanced',
      duration: '45 мин',
      rating: 4.7,
      videoUrl: 'https://example.com/video'
    },
    {
      id: 'math-quadratic-eq',
      type: 'article',
      title: 'Методы решения квадратных уравнений',
      description: 'Дискриминант, формула корней, теорема Виета',
      subject: 'Математика',
      topic: 'Алгебра',
      difficulty: 'intermediate',
      duration: '25 мин',
      rating: 4.6,
      content: `# Методы решения квадратных уравнений

## Формула через дискриминант

D = b² - 4ac
x₁,₂ = (-b ± √D) / 2a

## Теорема Виета

Для уравнения x² + px + q = 0:
- x₁ + x₂ = -p
- x₁ · x₂ = q

## Примеры и практика

Подробные примеры решения различных квадратных уравнений с объяснением каждого шага.`
    },
    {
      id: 'math-fractions-pdf',
      type: 'pdf',
      title: 'Дроби: от простого к сложному',
      description: 'Полный справочник по работе с обыкновенными и десятичными дробями',
      subject: 'Математика',
      topic: 'Арифметика',
      difficulty: 'beginner',
      duration: '30 мин',
      rating: 4.9,
      pdfUrl: '/materials/fractions.pdf'
    },
    {
      id: 'physics-kinematics',
      type: 'article',
      title: 'Основы кинематики',
      description: 'Движение, скорость, ускорение - базовые понятия механики',
      subject: 'Физика',
      topic: 'Механика',
      difficulty: 'beginner',
      duration: '20 мин',
      rating: 4.5,
      content: `# Основы кинематики

Кинематика - раздел механики, изучающий движение тел без учета причин этого движения.

## Основные понятия

- **Путь (s)** - длина траектории
- **Перемещение** - вектор от начальной до конечной точки
- **Скорость (v)** - изменение положения за единицу времени
- **Ускорение (a)** - изменение скорости за единицу времени

Формулы и примеры следуют далее...`
    },
    {
      id: 'russian-punctuation',
      type: 'article',
      title: 'Пунктуация: запятые в сложных предложениях',
      description: 'Правила постановки запятых, разбор сложных случаев',
      subject: 'Русский язык',
      topic: 'Пунктуация',
      difficulty: 'intermediate',
      duration: '15 мин',
      rating: 4.4,
      content: `# Пунктуация в сложных предложениях

## Сложносочиненные предложения

Части соединяются союзами: и, а, но, или, да

**Запятая ставится** перед союзами а, но, да (=но)

Примеры и правила далее...`
    }
  ];

  // Инициализация выбранного материала при загрузке
  useState(() => {
    if (selectedMaterialId) {
      const material = materials.find(m => m.id === selectedMaterialId);
      if (material) {
        setSelectedMaterial(material);
      }
    }
  });

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
                  <span className="text-sm text-gray-700">{material.rating}</span>
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
                <span className="text-sm text-gray-500">{material.duration}</span>
                <div className="flex items-center gap-2 text-blue-600 group-hover:gap-3 transition-all">
                  <span className="text-sm">Изучить</span>
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
