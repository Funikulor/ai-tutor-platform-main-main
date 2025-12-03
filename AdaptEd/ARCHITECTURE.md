# Архитектура AdaptEd - Многоагентная система

## Обзор

AdaptEd теперь построена на многоагентной архитектуре с 5 специализированными ИИ-агентами, которые работают совместно для обеспечения персонализированного обучения.

## Архитектурная схема

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Ученик      │  │  Учитель     │  │  Задания     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Backend API (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Agent Orchestrator                          │  │
│  └──────────┬───────────────────────────────────────────┘  │
│             │                                                 │
│  ┌──────────▼────────────┬────────────┬──────────┐         │
│  │ ErrorAnalyzerAgent    │ Profiler   │ TaskGen  │         │
│  │ (анализ ошибок)       │ Agent      │ Agent    │         │
│  └──────────┬────────────┴────────────┴──────────┘         │
│             │                       │                        │
│  ┌──────────▼──────────┐  ┌────────▼──────────┐            │
│  │ MentorAgent          │  │ TeacherAnalytics │            │
│  │ (наставник)          │  │ Agent            │            │
│  └──────────────────────┘  └──────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

## ИИ-Агенты

### 1. ErrorAnalyzerAgent (Агент анализа ошибок)

**Назначение:** Анализирует ошибки ученика и определяет их тип

**Функции:**
- Определение типа ошибки (carelessness, calculation_error, missing_formula, concept_confusion, logic_gap)
- Генерация обоснования ошибки
- Предложение способов исправления

**Протокол взаимодействия:**
```python
# Входные данные
{
    'task_id': int,
    'question': str,
    'user_answer': int,
    'correct_answer': int
}

# Выходные данные
{
    'error_type': str,
    'justification': str,
    'suggested_remediation': str
}
```

### 2. ProfilerAgent (Агент профилирования)

**Назначение:** Создает и обновляет когнитивный профиль ученика

**Хранит:**
- Стиль обучения (visual, auditory, kinesthetic, reading)
- История ошибок
- Эмоциональное состояние
- Мотивация (баллы, уровни, достижения)
- Прогресс по темам

**Функции:**
- Обновление статистики
- Определение стиля обучения
- Управление мотивацией
- Генерация инсайтов

**Протокол взаимодействия:**
```python
# Входные данные
{
    'user_id': str,
    'task_attempt': TaskAttempt,
    'error_analysis': dict
}

# Выходные данные
{
    'profile': CognitiveProfile,
    'insights': dict
}
```

### 3. TaskGeneratorAgent (Агент генерации заданий)

**Назначение:** Создает персонализированные задания

**Функции:**
- Определение уровня сложности
- Генерация заданий с учетом типичных ошибок
- Создание подсказок

**База заданий:**
- Задания по темам (addition, subtraction, multiplication, division, mixed)
- Разные уровни сложности (beginner, intermediate, advanced)

**Протокол взаимодействия:**
```python
# Входные данные
{
    'user_id': str,
    'profile': CognitiveProfile,
    'topic': str,
    'count': int
}

# Выходные данные
{
    'tasks': List[Dict],
    'difficulty': str,
    'reasoning': str
}
```

### 4. MentorAgent (Агент-наставник)

**Назначение:** Обеспечивает эмпатичное общение с учеником

**Функции:**
- Генерация мотивирующих сообщений
- Адаптация тона под эмоциональное состояние
- Предложение вариантов помощи

**Типы сообщений:**
- Celebratory (празднование успеха)
- Encouraging (поддержка при ошибках)
- Supportive (поддержка при затруднениях)

**Протокол взаимодействия:**
```python
# Входные данные
{
    'user_id': str,
    'profile': CognitiveProfile,
    'task_result': str  # 'correct' / 'wrong' / 'timeout'
}

# Выходные данные
{
    'message': str,
    'tone': str,
    'suggestions': List[Dict],
    'encouragement_level': int
}
```

### 5. TeacherAnalyticsAgent (Агент аналитики для учителя)

**Назначение:** Генерирует отчеты и аналитику для учителей

**Функции:**
- Сводный отчет по классу
- Детальный анализ по ученикам
- Выявление отстающих
- Рекомендации по вмешательству

**Типы отчетов:**
1. **summary** - общая статистика класса
2. **detailed** - индивидуальные профили
3. **struggling** - отстающие ученики

**Протокол взаимодействия:**
```python
# Входные данные
{
    'class_id': str,
    'report_type': str
}

# Выходные данные
{
    'report_type': str,
    'class_statistics': dict,
    'individual_profiles': List[Dict],
    'recommendations': List[Dict]
}
```

## Модель когнитивного профиля

```python
class CognitiveProfile:
    user_id: str
    topic_mastery: Dict[str, float]  # 0.0 - 1.0
    error_history: List[ErrorAnalysis]
    error_frequency: Dict[ErrorTag, int]
    learning_style: LearningStyle
    content_preferences: List[ContentPreference]
    current_emotional_state: EmotionalState
    task_history: List[TaskAttempt]
    total_tasks_completed: int
    correct_tasks_count: int
    accuracy_rate: float
    assigned_tasks: Dict[str, List[int]]
    points: int
    level: int
    achievements: List[str]
```

## Цикл обратной связи

```
1. Ученик выполняет задание
   ↓
2. ErrorAnalyzerAgent анализирует ошибки
   ↓
3. ProfilerAgent обновляет профиль
   ↓
4. MentorAgent генерирует мотивирующее сообщение
   ↓
5. TaskGeneratorAgent создает следующие задания
   ↓
6. Цикл повторяется с улучшенной персонализацией
```

## Система мотивации

**Баллы:**
- Правильный ответ: +10 очков
- Уровень: points // 100 + 1 (максимум 10)

**Достижения:**
- "first_steps" - при 50+ очках
- "steady_progress" - при 200+ очках
- "high_achiever" - при точности 80%+

## API Endpoints

### Для учеников:
- `POST /agents/submit-task` - отправка задания
- `POST /agents/generate-tasks` - генерация заданий
- `GET /agents/dashboard/{user_id}` - дашборд ученика
- `GET /agents/profile/{user_id}` - полный профиль

### Для учителей:
- `GET /agents/teacher-report` - отчет для учителя
- `POST /agents/assign-tasks` - назначение заданий

## Масштабирование

**Текущая архитектура:**
- In-memory хранение профилей
- Синхронное взаимодействие агентов

**Планируемые улучшения:**
1. Интеграция с LLM API (OpenAI, Yandex GPT)
2. База данных для персистентного хранения
3. Message queue для асинхронного взаимодействия агентов
4. Микросервисная архитектура (каждый агент = отдельный сервис)
5. Кэширование для оптимизации производительности

## Тестирование

Для тестирования системы:

```bash
# Запустить backend
cd AdaptEd/backend
uvicorn app:app --reload

# Запустить frontend
cd AdaptEd/frontend
streamlit run app.py

# Открыть в браузере
http://localhost:8501
```

## Метрики эффективности

1. **Снижение частоты однотипных ошибок** - отслеживается через `error_frequency`
2. **Рост уровня знаний** - отслеживается через `accuracy_rate`
3. **Удовлетворенность** - через `emotional_state` и `encouragement_level`
4. **Прогресс мотивации** - через `points`, `level`, `achievements`

## Лицензия

MIT License

