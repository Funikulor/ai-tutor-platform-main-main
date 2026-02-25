import { useState, useEffect } from 'react';
import { MaterialViewer } from './MaterialViewer';
import { BookOpen, Video, FileText, ChevronRight, Search, Filter, Star, CheckCircle } from 'lucide-react';
import { motion } from 'motion/react';
import api from '../services/api';

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
  const [studiedMaterials, setStudiedMaterials] = useState<Set<string>>(new Set());
  const [topicMastery, setTopicMastery] = useState<Record<string, number>>({});
  const [materialRatings, setMaterialRatings] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadStudyProgress();
    loadMaterialRatings();
  }, []);
  
  const loadStudyProgress = async () => {
    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) return;
      
      const response = await api.get(`/study/progress/${userId}`);
      const data = response.data;
      
      // Получаем список изученных материалов из истории
      const studied = new Set<string>();
      if (data.topics_studied) {
        // Здесь можно получить список material_id из истории, но пока используем topic_mastery
        // В реальной системе нужно хранить material_id в истории изучения
      }
      
      setStudiedMaterials(studied);
      setTopicMastery(data.topic_mastery || {});
    } catch (err) {
      console.error('Error loading study progress:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const loadMaterialRatings = async () => {
    try {
      const response = await api.get('/materials/ratings');
      setMaterialRatings(response.data.ratings || {});
    } catch (err) {
      console.error('Error loading material ratings:', err);
      // При ошибке используем рейтинги по умолчанию из материалов
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
    // Проверяем по теме - если мастерство >= 30%, считаем что материал изучен
    return getTopicMastery(material.topic) >= 30;
  };

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
      content: `# 🎯 Основы алгебры: твой путь к успеху

Привет! Добро пожаловать в увлекательный мир алгебры! 🌟 

Алгебра — это не просто скучные формулы и уравнения. Это мощный инструмент, который помогает решать реальные задачи: от расчета скидок в магазине до проектирования зданий. Давай разберемся вместе!

---

## 📚 Что такое алгебра?

**Алгебра** — это раздел математики, который изучает общие свойства действий над числами и переменными, а также способы решения уравнений и неравенств.

💡 **Простыми словами:** алгебра помогает находить неизвестные числа, когда мы знаем их отношения друг с другом.

---

## 1️⃣ Линейные уравнения — основа основ

### Что это такое?

**Линейное уравнение** — это уравнение вида **ax + b = 0**, где:
- **x** — неизвестная переменная (то, что мы ищем)
- **a** и **b** — известные числа, причем **a ≠ 0**

### 🎨 Примеры из жизни:

- **Задача про покупки:** У тебя есть 100 рублей. Ты купил несколько ручек по 15 рублей и у тебя осталось 25 рублей. Сколько ручек ты купил?
  - Уравнение: **15x + 25 = 100**, где x — количество ручек

- **Задача про возраст:** Через 5 лет Маше будет в 2 раза больше лет, чем сейчас. Сколько ей сейчас?
  - Уравнение: **x + 5 = 2x**, где x — текущий возраст

### 📝 Алгоритм решения (пошагово):

1. **Шаг 1:** Перенеси все члены с **x** в левую часть, а числа — в правую
   - Помни: при переносе знак меняется на противоположный!

2. **Шаг 2:** Приведи подобные слагаемые (сложи/вычти числа с x и отдельно числа)

3. **Шаг 3:** Раздели обе части на коэффициент при x

### ✨ Разберем пример подробно:

**Задача:** Реши уравнение **2x + 5 = 13**

**Решение:**

\`\`\`
Шаг 1: Переносим число 5 в правую часть (меняем знак)
2x = 13 - 5

Шаг 2: Вычитаем
2x = 8

Шаг 3: Делим обе части на 2
x = 8 / 2
x = 4
\`\`\`

✅ **Проверка:** Подставляем x = 4 в исходное уравнение:
- 2 · 4 + 5 = 8 + 5 = 13 ✓ Правильно!

---

## 2️⃣ Квадратные уравнения — следующий уровень

### Что это такое?

**Квадратное уравнение** — это уравнение вида **ax² + bx + c = 0**, где:
- **x²** — переменная во второй степени
- **a**, **b**, **c** — известные числа, причем **a ≠ 0**

### 🔑 Ключевая формула — дискриминант:

**D = b² - 4ac**

Дискриминант — это твой помощник! Он показывает, сколько решений у уравнения:

| Условие | Количество корней | Что это значит |
|---------|-------------------|----------------|
| **D > 0** | Два корня | Уравнение имеет два разных решения |
| **D = 0** | Один корень | Оба решения совпадают |
| **D < 0** | Нет корней | Решений нет (в действительных числах) |

### 📐 Формула корней:

\`\`\`
x₁,₂ = (-b ± √D) / 2a
\`\`\`

### 💡 Разберем пример:

**Задача:** Реши уравнение **x² - 5x + 6 = 0**

**Решение:**

\`\`\`
Шаг 1: Находим дискриминант
a = 1, b = -5, c = 6
D = (-5)² - 4 · 1 · 6
D = 25 - 24 = 1

Шаг 2: Так как D > 0, у нас два корня
x₁ = (5 + √1) / 2 = (5 + 1) / 2 = 6 / 2 = 3
x₂ = (5 - √1) / 2 = (5 - 1) / 2 = 4 / 2 = 2

Ответ: x₁ = 3, x₂ = 2
\`\`\`

✅ **Проверка:**
- Для x = 3: 3² - 5·3 + 6 = 9 - 15 + 6 = 0 ✓
- Для x = 2: 2² - 5·2 + 6 = 4 - 10 + 6 = 0 ✓

---

## 3️⃣ Системы уравнений — работаем с несколькими неизвестными

### Что это такое?

**Система уравнений** — это несколько уравнений, которые нужно решить одновременно.

### 📊 Пример системы:

\`\`\`
{
  2x + 3y = 12
  x - y = 1
}
\`\`\`

### 🎯 Три основных метода решения:

#### Метод 1: Подстановка
1. Вырази одну переменную через другую из одного уравнения
2. Подставь это выражение во второе уравнение
3. Реши полученное уравнение
4. Найди вторую переменную

#### Метод 2: Сложение
1. Умножь уравнения на числа так, чтобы коэффициенты при одной переменной стали противоположными
2. Сложи уравнения — одна переменная исчезнет!
3. Реши полученное уравнение
4. Найди вторую переменную

#### Метод 3: Графический
1. Построй графики обоих уравнений
2. Найди точку их пересечения — это и есть решение!

---

## 4️⃣ Неравенства — когда нужно сравнить

### Что это такое?

**Неравенство** — это соотношение вида:
- **a < b** (a меньше b)
- **a > b** (a больше b)
- **a ≤ b** (a меньше или равно b)
- **a ≥ b** (a больше или равно b)

### ⚠️ Важное правило!

**При умножении или делении неравенства на отрицательное число знак неравенства меняется на противоположный!**

**Пример:**
- Если **-2x > 6**, то **x < -3** (знак изменился!)

---

## 🎮 Практические задания для закрепления

Попробуй решить эти задачи самостоятельно:

1. **Реши уравнение:** 3x + 7 = 22
   - 💡 Подсказка: начни с переноса числа 7

2. **Реши квадратное уравнение:** x² - 7x + 12 = 0
   - 💡 Подсказка: найди дискриминант, затем корни

3. **Реши неравенство:** 2x - 5 < 9
   - 💡 Подсказка: перенеси -5 в правую часть

---

## 💎 Полезные советы для успеха

✓ **Всегда проверяй решение** — подставь найденное значение обратно в уравнение

✓ **Не забывай про знаки** — особенно при переносе слагаемых через знак равенства

✓ **Рисуй схемы** — визуализация помогает понять задачу

✓ **Практикуйся регулярно** — чем больше решаешь, тем лучше понимаешь

✓ **Не бойся ошибок** — они помогают учиться!

---

## 🚀 Что дальше?

Отлично! Ты освоил основы алгебры. Теперь:

1. **Перейди к адаптивным заданиям** — закрепи знания на практике
2. **Изучи другие темы** — квадратные уравнения, функции, системы
3. **Практикуйся регулярно** — решай задачи каждый день

**Помни:** алгебра — это навык, который развивается с практикой. Чем больше решаешь, тем легче становится! 💪

Удачи в изучении! Ты справишься! 🎓✨

---

## 📖 Дополнительные материалы

Если хочешь углубиться в тему, изучи:

- Квадратные уравнения (продвинутый уровень)
- Системы уравнений (методы решения)
- Неравенства и их свойства

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
      content: `# 📐 Теорема Пифагора: магия прямоугольных треугольников

Привет! Сегодня мы изучим одну из самых знаменитых теорем в математике — **теорему Пифагора**. Эта теорема не только красива, но и невероятно полезна в реальной жизни! 🎯

---

## 🎓 Что такое теорема Пифагора?

### Формулировка:

> **В прямоугольном треугольнике квадрат гипотенузы равен сумме квадратов катетов.**

### 📐 Математическая запись:

\`\`\`
c² = a² + b²
\`\`\`

**Где:**
- **c** — гипотенуза (самая длинная сторона, напротив прямого угла)
- **a** и **b** — катеты (две стороны, образующие прямой угол 90°)

### 🎨 Визуализация:

Представь прямоугольный треугольник. Гипотенуза — это "диагональ", а катеты — это "стороны" угла. Теорема говорит: если построить квадраты на каждой стороне, то площадь квадрата на гипотенузе будет равна сумме площадей квадратов на катетах!

---

## 💡 Примеры решения задач

### Задача 1: Найти гипотенузу

**Условие:** Катеты прямоугольного треугольника равны 3 см и 4 см. Найти гипотенузу.

**Решение:**

\`\`\`
Шаг 1: Записываем формулу
c² = a² + b²

Шаг 2: Подставляем известные значения
c² = 3² + 4²

Шаг 3: Вычисляем квадраты
c² = 9 + 16
c² = 25

Шаг 4: Извлекаем корень
c = √25 = 5 см

Ответ: гипотенуза равна 5 см
\`\`\`

✅ **Проверка:** 3² + 4² = 9 + 16 = 25 = 5² ✓

---

### Задача 2: Найти катет

**Условие:** Гипотенуза равна 13 см, один катет равен 5 см. Найти второй катет.

**Решение:**

\`\`\`
Шаг 1: Записываем формулу
c² = a² + b²

Шаг 2: Выражаем неизвестный катет
b² = c² - a²

Шаг 3: Подставляем значения
b² = 13² - 5²
b² = 169 - 25
b² = 144

Шаг 4: Извлекаем корень
b = √144 = 12 см

Ответ: второй катет равен 12 см
\`\`\`

✅ **Проверка:** 5² + 12² = 25 + 144 = 169 = 13² ✓

---

## 🌍 Применение в реальной жизни

Теорема Пифагора используется везде! Вот несколько примеров:

### 🏗️ Строительство
- Проверка прямых углов при строительстве
- Расчет длины диагоналей в прямоугольных конструкциях
- Планировка участков и зданий

### 🧭 Навигация
- Расчет кратчайшего расстояния между точками
- GPS и картография
- Определение расстояний на местности

### ⚡ Физика
- Расчет векторов и их модулей
- Механика и кинематика
- Электрические цепи

### 💻 Компьютерная графика
- Расчет расстояний между объектами
- 3D-моделирование
- Игровая физика

---

## 🎯 Полезные тройки Пифагора

Запомни эти популярные комбинации — они часто встречаются в задачах:

| Катет a | Катет b | Гипотенуза c |
|---------|---------|--------------|
| 3 | 4 | 5 |
| 5 | 12 | 13 |
| 8 | 15 | 17 |
| 7 | 24 | 25 |

💡 **Совет:** Если видишь эти числа в задаче, сразу применяй теорему Пифагора!

---

## ⚠️ Важные моменты

✓ Теорема работает **только для прямоугольных треугольников** (с углом 90°)

✓ Гипотенуза **всегда самая длинная** сторона треугольника

✓ При вычислениях не забывай про единицы измерения (см, м, км)

✓ Всегда проверяй ответ подстановкой в формулу

---

## 🚀 Практикуйся!

Теперь попробуй решить задачи самостоятельно:

1. Катеты равны 6 см и 8 см. Найди гипотенузу.
2. Гипотенуза равна 10 см, один катет равен 6 см. Найди второй катет.
3. Можешь ли ты построить прямоугольный треугольник со сторонами 2, 3, 4? Почему?

---

**Помни:** Теорема Пифагора — это не просто формула, это ключ к пониманию пространства вокруг нас! 📐✨

Удачи в изучении! 💪`
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
