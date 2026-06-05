# AdaptEd — техническая документация проекта

> **Сначала читайте [LEARNING_GUIDE.md](./LEARNING_GUIDE.md)** — обучающее руководство по порядку, с аналогиями и сценариями «от кнопки до базы».  
> Этот файл — **справочник** для защиты: архитектура, код, API, глоссарий.

Полное описание технической части платформы **AdaptEd** (в интерфейсе — **EduAI Platform**) для подготовки к защите диплома: архитектура, код, API, данные, ИИ-контур и **глоссарий терминов**.

**Версия документа:** соответствует состоянию репозитория на момент подготовки.  
**Связанные материалы:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md), `AdaptEd/README.md`, `START_HERE.md`, `docs/appendices_for_thesis.md`, BPMN в `docs/bpmn/`.

---

## Содержание

1. [Назначение и цели системы](#1-назначение-и-цели-системы)
2. [Архитектура](#2-архитектура)
3. [Технологический стек](#3-технологический-стек)
4. [Структура репозитория](#4-структура-репозитория)
5. [Backend (серверная часть)](#5-backend-серверная-часть)
6. [Frontend (клиентская часть)](#6-frontend-клиентская-часть)
7. [База данных и хранение](#7-база-данных-и-хранение)
8. [Авторизация и безопасность](#8-авторизация-и-безопасность)
9. [REST API](#9-rest-api)
10. [Многоагентная система](#10-многоагентная-система)
11. [Когнитивный профиль и персонализация](#11-когнитивный-профиль-и-персонализация)
12. [AI-ассистент (LLM)](#12-ai-ассистент-llm)
13. [Основные бизнес-процессы](#13-основные-бизнес-процессы)
14. [Развёртывание и эксплуатация](#14-развёртывание-и-эксплуатация)
15. [Ограничения и направления развития](#15-ограничения-и-направления-развития)
16. [Вопросы комиссии — краткие ответы](#16-вопросы-комиссии--краткие-ответы)
17. [Глоссарий терминов](#17-глоссарий-терминов)

---

## 1. Назначение и цели системы

**AdaptEd** — веб-платформа **адаптивного обучения** для школьников (ориентир: 5–9 класс). Система:

- выдаёт и проверяет задания, тесты, домашнюю работу;
- ведёт **когнитивный профиль** ученика (ошибки, темы, прогресс);
- использует **многоагентную архитектуру** для анализа ответов и мотивации;
- предоставляет **AI-чат** и подсказки через внешние LLM;
- разделяет роли: **ученик**, **учитель**, **родитель**, **администратор**.

На защите формулировка: *«Клиент-серверная информационная система с REST API, реляционной СУБД и контуром интеллектуальных агентов для персонализации обучения»*.

---

## 2. Архитектура

### 2.1. Общая схема

```
┌─────────────────────────────────────────────────────────────────┐
│  Браузер пользователя                                            │
│  React SPA (Vite) — кабинеты ученика / учителя / админа          │
│  axios → HTTP + JSON + Authorization: Bearer <token>             │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API (HTTPS в проде)
┌────────────────────────────▼────────────────────────────────────┐
│  FastAPI (Python) — app.py                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ routes/     │→ │ services/    │→ │ agents/ + orchestrator  │ │
│  │ auth, tests │  │ assistant,   │  │ Profiler, ErrorAnalyzer │ │
│  │ homework... │  │ analytics    │  │ Mentor, TaskGenerator...│ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
│         │                  │                    │                  │
│         └──────────────────┼────────────────────┘                  │
│                            ▼                                      │
│              SQLAlchemy → PostgreSQL / SQLite                       │
│              personalization_store → JSON payload в БД             │
│              persistent_storage (fallback JSON-файл)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼────────────────────────────────────┐
│  Внешние сервисы: ProxyAPI / Hugging Face (LLM), Railway (хостинг)│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2. Архитектурный стиль

| Подход | Как реализовано в проекте |
|--------|---------------------------|
| **Клиент-сервер** | React отдельно, API на FastAPI |
| **REST** | Ресурсы по URL, методы GET/POST/PUT/DELETE |
| **Многослойность** | routes → services/agents → models → БД |
| **Stateless API** | Сессия в подписанном токене, не в памяти сервера |
| **Многоагентность** | Оркестратор координирует специализированных агентов |

### 2.3. Роли пользователей

| Роль | Код в БД | Возможности |
|------|----------|-------------|
| Ученик | `student` | Задания, библиотека, ДЗ, тесты, чат, свой прогресс |
| Учитель | `teacher` | Класс, аналитика, создание тестов/ДЗ, «долги» по темам |
| Родитель | `parent` | Доступ к данным своего ребёнка (ограниченно) |
| Администратор | `admin` | Пользователи, структура контента, библиотека, настройки |

Админ в UI может переключать «вид» кабинета (ученик/учитель/админ) для демонстрации — `App.tsx`.

---

## 3. Технологический стек

### 3.1. Backend

| Компонент | Технология | Файл / папка |
|-----------|------------|--------------|
| Язык | Python 3 | `AdaptEd/backend/` |
| Web-фреймворк | **FastAPI** | `app.py` |
| ASGI-сервер | **uvicorn** | запуск, `Procfile` |
| Валидация данных | **Pydantic** v2 | `models/` |
| ORM | **SQLAlchemy** 2.x | `utils/db.py`, `models/*_db.py` |
| HTTP-клиент к LLM | **requests**, **httpx** | `services/assistant.py` |
| Самостоятельно размещаемые модели (опц.) | **transformers**, **accelerate** | `assistant.py` при `ASSISTANT_PROVIDER=local` |
| Миграции (зависимость) | Alembic в requirements | рекомендуется для прода |
| Тесты | pytest | `tests/` |

### 3.2. Frontend

| Компонент | Технология |
|-----------|------------|
| UI-библиотека | **React** 18 |
| Язык | **TypeScript** |
| Сборщик | **Vite** 6 |
| Стили | **Tailwind CSS** |
| UI-компоненты | **Radix UI** |
| HTTP | **axios** |
| Графики | **recharts** |
| Формулы в чате | **KaTeX**, remark-math, rehype-katex |
| Уведомления | **sonner** |

### 3.3. Инфраструктура

| Компонент | Назначение |
|-----------|------------|
| **Railway** | Хостинг backend + frontend |
| **PostgreSQL** | Продакшен-БД (`DATABASE_URL`) |
| **SQLite** | Возможен для прототипа (если задан URL) |
| Переменные `.env` | Секреты, ключи API, CORS |

---

## 4. Структура репозитория

```
ai-tutor-platform-main-main/
├── START_HERE.md              # Быстрый запуск
├── TROUBLESHOOTING.md         # Диагностика
└── AdaptEd/
    ├── README.md
    ├── backend/
    │   ├── app.py               # Точка входа FastAPI
    │   ├── requirements.txt
    │   ├── routes/              # HTTP API
    │   ├── agents/              # ИИ-агенты + orchestrator
    │   ├── services/            # Бизнес-сервисы
    │   ├── models/              # Pydantic + SQLAlchemy
    │   ├── utils/               # db, auth, batched_saver, storage
    │   ├── data/                # Курсы (MD), library JSON
    │   ├── scripts/             # seed, create_admin
    │   ├── seed_credentials.txt # Тестовые учётные записи
    │   └── tests/
    ├── frontend/
    │   ├── src/
    │   │   ├── App.tsx
    │   │   ├── components/      # Dashboards, Auth, Chat...
    │   │   └── services/        # api.ts, auth.ts
    │   ├── package.json
    │   └── vite.config.ts
    └── docs/
        ├── TECHNICAL_REFERENCE.md   # Этот документ
        ├── appendices_for_thesis.md
        └── bpmn/                      # BPMN-диаграммы
```

---

## 5. Backend (серверная часть)

### 5.1. Точка входа — `app.py`

При старте:

1. Загружает `.env` (`python-dotenv`).
2. Логирует конфигурацию AI (`ASSISTANT_PROVIDER`, ключи ProxyAPI/HF).
3. Вызывает `init_db()` — создание таблиц и дозапись колонок.
4. Инициализирует `AssistantService`.
5. Подключает **CORS** (whitelist + regex `*.up.railway.app`).
6. Регистрирует роутеры: `auth`, `lessons`, `users`, `agents`, `assistant`, `homework`, `tests`, `materials`, `monitoring`.
7. При наличии `frontend/build` — раздаёт статику SPA.
8. **Lifespan:** при остановке — `flush` профилей и батчеров.

Служебные эндпоинты:

- `GET /health` — проверка живости API.
- `GET /debug`, `GET /batcher-stats` — только при `DEBUG=1`.

### 5.2. Маршруты (`routes/`)

| Модуль | Префикс / примеры | Назначение |
|--------|-------------------|------------|
| `auth.py` | `/auth/login`, `/auth/me` | Регистрация, вход, профиль |
| `agents.py` | `/agents/submit-task`, `/agents/dashboard/{id}` | Агенты, адаптивные задания |
| `assistant.py` | `/assistant/chat`, `/assistant/hint` | LLM-чат, подсказки, документы |
| `homework.py` | `/homeworks`, `/progress/{id}`, `/recommendations/{id}` | ДЗ, прогресс, рекомендации, админка |
| `tests.py` | `/tests`, `/tests/{id}/submit` | Тесты |
| `materials.py` | `/materials`, `/library/courses` | Библиотека материалов |
| `monitoring.py` | `/teacher/class-rating`, `/student/debts` | Мониторинг класса, «долги» |
| `lessons.py` | `/tasks`, `/tasks/check` | Базовые математические задачи |
| `users.py` | `/users/{id}` | Управление пользователями |

Полный список — в Swagger: `/docs`.

### 5.3. Сервисы (`services/`)

| Сервис | Файл | Роль |
|--------|------|------|
| **AssistantService** | `assistant.py` | Вызов LLM, профили личности, документы |
| **StudentAnalyticsService** | `student_analytics.py` | Связь чата/тестов с AdaptiveEducatorAgent |
| **curriculum_catalog** | `curriculum_catalog.py` | Каталог предмет → раздел → тема |

### 5.4. Утилиты (`utils/`)

| Модуль | Назначение |
|--------|------------|
| `db.py` | Engine, Session, `init_db()`, `get_db()` |
| `auth_service.py` | Регистрация, хеш пароля, токены |
| `batched_saver.py` | Пакетное сохранение профилей (производительность) |
| `personalization_store.py` | CRUD JSON-профилей в таблицах БД |
| `persistent_storage.py` | Fallback JSON-файл для users и др. |
| `orchestrator_singleton.py` | Единый экземпляр `AgentOrchestrator` |
| `answer_parse.py` | Сравнение числовых ответов, дроби |

---

## 6. Frontend (клиентская часть)

### 6.1. Точка входа

- `main.tsx` — монтирование React.
- `App.tsx` — проверка авторизации, выбор дашборда по роли.

### 6.2. Основные компоненты

| Компонент | Назначение |
|-----------|------------|
| `Auth.tsx` | Вход и регистрация |
| `StudentDashboard.tsx` | Кабинет ученика: обзор, задания, чат, библиотека, ДЗ |
| `TeacherDashboard.tsx` | Кабинет учителя |
| `AdminPanel.tsx` | Администрирование |
| `AdaptiveTask.tsx` | Решение адаптивного задания |
| `AIChatPanel.tsx`, `ChatTab.tsx` | AI-чат |
| `HomeworkTab.tsx` | Домашние работы |
| `LibraryTab.tsx`, `CourseViewer.tsx` | Библиотека и курсы |
| `KnowledgeGraph.tsx` | Граф знаний по темам |
| `TestCreator.tsx` | Создание тестов (учитель) |
| `RecommendationPanel.tsx` | Рекомендации материалов |

### 6.3. Сервисы клиента

**`services/api.ts`**

- `API_BASE_URL` = `VITE_API_URL` (указывается при сборке фронта).
- Interceptor: добавляет `Authorization: Bearer <token>`.
- При 401 (кроме login/register) — очистка `localStorage`, редирект на `/`.

**`services/auth.ts`**

- `login`, `register`, `getCurrentUser`, `logout`.
- Сохраняет `token`, `user_id`, `role` в `localStorage`.

---

## 7. База данных и хранение

### 7.1. Подключение

Файл `utils/db.py`:

- `DATABASE_URL` из окружения (PostgreSQL на Railway).
- `create_all()` при старте + ручные `ALTER TABLE` для новых колонок (совместимость без Alembic).

### 7.2. Основные таблицы

| Таблица | Содержание |
|---------|------------|
| `users` | Учётные записи: email, password_hash, role, class_id, avatar_seed |
| `tests`, `test_questions`, `test_submissions` | Тесты и результаты |
| `homeworks`, `homework_submissions` | Домашние задания |
| `documents` | Загруженные документы для ассистента |
| `chat_sessions` | Сессии AI-чата |
| `curriculum_subjects`, `curriculum_sections`, `curriculum_topics`, `curriculum_topic_tasks` | Иерархия учебного контента |
| `student_debts`, `remedial_assignments` | «Долги» по темам, доработки |
| `cognitive_profiles` | JSON когнитивного профиля |
| `student_analytics` | JSON аналитики AdaptiveEducator |
| `personality_profiles` | JSON стиля общения с LLM |

### 7.3. Иерархия контента

```
Предмет (subject)
  └── Раздел (section)
        └── Тема (topic)
              └── Учебный элемент (задание, материал, курс)
```

Связь с библиотекой: поля `library_material_ids`, `library_course_ids` в темах.

### 7.4. Двойное хранение

- **Транзакционные данные** — SQL (пользователи, тесты, ДЗ).
- **Профили персонализации** — JSON в колонке `payload` (таблицы `*_records`).
- **persistent_storage** — резервный JSON-файл при отсутствии БД (legacy/fallback).

---

## 8. Авторизация и безопасность

### 8.1. Регистрация и пароль

- Пароль хешируется: **SHA-256** (`auth_service.hash_password`).
- В БД хранится `password_hash`, не открытый пароль.

### 8.2. Bearer-токен (доступ)

Формат: `payload_base64.signature_base64`

**Payload:**

```json
{
  "user_id": "student_001",
  "role": "student",
  "iat": 1716560000,
  "exp": 1719152000
}
```

- Подпись: **HMAC-SHA256** с секретом `AUTH_SECRET_KEY` (или `SECRET_KEY`).
- Срок жизни: по умолчанию **720 часов** (~30 дней), `AUTH_TOKEN_TTL_HOURS`.
- **Stateless:** сервер не обязан хранить сессию в RAM.

### 8.3. Передача токена

```http
Authorization: Bearer <access_token>
```

### 8.4. Контроль доступа (RBAC)

- `get_current_user` — извлечение пользователя из токена.
- `require_roles("teacher", "admin")` — только указанные роли.
- `assert_can_view_user_data` — ученик видит только свои данные.

### 8.5. CORS

Разрешённые origin + regex для `https://*.up.railway.app`. Дополнительно — `CORS_ORIGINS` в env.

---

## 9. REST API

### 9.1. Что такое REST API в проекте

**REST API** — интерфейс обмена данными по **HTTP**, где:

- каждый URL — **ресурс** (`/tests`, `/homeworks`);
- действие — **метод** (GET читает, POST создаёт/выполняет);
- данные — обычно **JSON**;
- результат — **код статуса** (200, 401, 403, 404, 500).

### 9.2. Пример полного цикла: логин → защищённый запрос

**Шаг 1 — вход**

```http
POST /auth/login
Content-Type: application/json

{"email": "student_001@school.ru", "password": "***"}
```

**Шаг 2 — ответ**

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "student_001",
  "role": "student",
  "full_name": "Иван Иванов",
  "email": "student_001@school.ru"
}
```

**Шаг 3 — клиент сохраняет** `access_token` в `localStorage`.

**Шаг 4 — любой защищённый запрос**

```http
GET /auth/me
Authorization: Bearer eyJ...
```

**Шаг 5 — сервер** проверяет подпись и `exp`, возвращает профиль или 401.

### 9.3. Ключевые группы эндпоинтов

См. раздел 5.2 и Swagger `/docs`.

---

## 10. Многоагентная система

### 10.1. Паттерн

Все агенты наследуют `BaseAgent` (`agents/base_agent.py`):

- метод `process(input_data) -> dict`;
- опционально очередь сообщений `AgentMessage`.

**AgentOrchestrator** (`agents/orchestrator.py`) — единая координация, без дублирования логики.

### 10.2. Состав агентов

| Агент | Класс | Функция |
|-------|-------|---------|
| Анализатор ошибок | `ErrorAnalyzerAgent` | Классификация типа ошибки |
| Профилировщик | `ProfilerAgent` | Когнитивный профиль, очки, уровень |
| Наставник | `MentorAgent` | Мотивационные сообщения (rule-based) |
| Генератор заданий | `TaskGeneratorAgent` | Подбор заданий из банка по профилю |
| Аналитика учителя | `TeacherAnalyticsAgent` | Отчёты по классу |
| Адаптивный педагог | `AdaptiveEducatorAgent` | Аналитика чата и тестов |

### 10.3. Сценарий: отправка задания

`POST /agents/submit-task` → `orchestrator.process_task_submission()`:

1. **Проверка ответа** — строка или `numeric_answers_equal()` (дроби, допуск 0.001).
2. Если неверно → **ErrorAnalyzer** → `ErrorTag` + рекомендация.
3. **Profiler** → обновление `CognitiveProfile`.
4. **Mentor** → сообщение ученику.
5. Параллельно — запись в **StudentAnalytics**.

### 10.4. Типы ошибок (`ErrorTag`)

| Код | Смысл |
|-----|--------|
| `missing_formula` | Не применена формула |
| `concept_confusion` | Путаница в понятиях |
| `carelessness` | Невнимательность, описка |
| `logic_gap` | Пробел в логике |
| `calculation_error` | Арифметическая ошибка |
| `not_attempted` | Нет попытки |

---

## 11. Когнитивный профиль и персонализация

### 11.1. Модель `CognitiveProfile`

Ключевые поля (`models/cognitive_profile.py`):

| Поле | Описание |
|------|----------|
| `topic_mastery` | Освоение темы 0.0–1.0 |
| `error_history`, `error_frequency` | История и частота ошибок |
| `task_history` | Попытки заданий |
| `material_study_history` | Изучение материалов |
| `accuracy_rate` | Доля правильных ответов |
| `points`, `level`, `achievements` | Геймификация |
| `current_emotional_state` | Для тона наставника |
| `learning_velocity` | Скорость обучения |

### 11.2. Батчинг сохранений

`BatchedSaver` (`utils/batched_saver.py`):

- накапливает изменения профиля;
- сохраняет пакетом раз в ~5 с или при `flush`;
- при остановке сервера — `flush_all` в `app.py` lifespan.

### 11.3. Рекомендации материалов

`GET /recommendations/{user_id}` — rule-based: слабые темы из профиля + сопоставление с библиотекой.  
**Полноценный RAG** (векторный поиск) — заявлено как направление развития в дипломе.

---

## 12. AI-ассистент (LLM)

### 12.1. AssistantService

Файл `services/assistant.py`.

| Провайдер | Переменные окружения | Описание |
|-----------|---------------------|----------|
| `proxyapi` | `PROXYAPI_KEY`, `PROXYAPI_URL`, `PROXYAPI_MODEL` | OpenAI-compatible HTTP (ProxyAPI, NeuroAPI) |
| `hf_api` | `HF_API_TOKEN`, `HF_MODEL` | Hugging Face Inference |
| `local` | transformers | Модель через transformers (тяжёлый режим) |

Выбор: `ASSISTANT_PROVIDER` или автоматически по наличию ключей.

### 12.2. Возможности API

| Эндпоинт | Назначение |
|----------|------------|
| `POST /assistant/chat` | Диалог с историей |
| `POST /assistant/hint` | Подсказка по заданию |
| `POST /assistant/motivation` | Мотивационное сообщение |
| `POST /assistant/documents/upload` | Загрузка материалов |
| CRUD `/assistant/chats/...` | Сессии чата |

### 12.3. PersonalityProfile

Стиль общения ассистента (черты, тон) — сохраняется в БД, влияет на промпт к LLM.

### 12.4. Ограничение

Без ключей API пользователь видит сообщение: *«ответ ассистента временно недоступен»* — не техническая ошибка в UI, а штатный fallback.

---

## 13. Основные бизнес-процессы

### 13.1. Адаптивное задание

1. Ученик открывает вкладку заданий → `POST /agents/generate-adaptive-task` или `generate-tasks`.
2. Решает → `POST /agents/submit-task`.
3. UI показывает результат, сообщение наставника, обновляет статистику.

### 13.2. Тест и домашняя работа

1. Учитель: `POST /tests/manual` или `/tests/generate`, назначение через homework/tests routes.
2. Ученик: `POST /tests/{id}/submit`.
3. Результат в БД + обновление профиля и аналитики.

### 13.3. Изучение материала

1. `POST /study/material` — время, процент прохождения.
2. Profiler обновляет `material_study_history`.
3. `GET /recommendations/{user_id}` — следующие материалы.

### 13.4. AI-чат

1. `POST /assistant/chat` с `user_id`, текстом, опционально `chat_id`.
2. AssistantService формирует промпт (профиль, контекст).
3. Запрос к LLM → ответ → сохранение в `chat_sessions`.

### 13.5. BPMN

Диаграммы в `AdaptEd/docs/bpmn/` (PNG, SVG, `.bpmn`) — для приложения А диплома.

---

## 14. Развёртывание и эксплуатация

### 14.1. Развертывание сервиса

**Backend:**

```bash
cd AdaptEd/backend
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd AdaptEd/frontend
npm install
npm run dev
```

- API: URL бэкенда (через `VITE_API_URL`)
- UI: URL фронтенда
- Docs: `/docs` на backend  

### 14.2. Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `DATABASE_URL` | PostgreSQL (обязательно для полного функционала) |
| `AUTH_SECRET_KEY` | Подпись токенов |
| `PROXYAPI_KEY` / `HF_API_TOKEN` | Ключи LLM |
| `ASSISTANT_PROVIDER` | `proxyapi` / `hf_api` / `local` |
| `VITE_API_URL` | URL бэкенда при **сборке** фронта |
| `CORS_ORIGINS` | Дополнительные origin |
| `DEBUG` | Включает `/debug`, `/batcher-stats` |

### 14.3. Railway

- Отдельные сервисы frontend и backend.
- После смены `VITE_API_URL` — **пересборка** фронта.
- Сид пользователей: `python -m scripts.seed_from_credentials --reset` из `backend/`.

### 14.4. Тестовые учётные записи

Файл `AdaptEd/backend/seed_credentials.txt` — email/пароли для демо и защиты.

---

## 15. Ограничения и направления развития

| Текущее состояние | Рекомендация |
|-------------------|--------------|
| SHA-256 для паролей | bcrypt / argon2 |
| `create_all` без Alembic-ревизий | Alembic в репозитории |
| Рекомендации rule-based | Векторный RAG, embeddings |
| Stateless токен без revoke | Blacklist или короткий TTL + refresh |
| Генерация заданий из банка | LLM-генерация с валидацией |
| Часть логики в JSON payload | Нормализация схемы профиля в таблицы |

---

## 16. Вопросы комиссии — краткие ответы

**Почему FastAPI?**  
Асинхронность, автодокументация OpenAPI, Pydantic, удобство для AI-backend.

**Чем отличается от LMS?**  
Замкнутый цикл: ответ → тип ошибки → профиль → сложность и рекомендации + AI-наставник.

**Где машинное обучение?**  
Гибрид: эвристики и rule-based агенты + внешний LLM для текста; не end-to-end нейросеть на классификации ошибок.

**Как масштабируется?**  
Пул соединений Postgres, stateless API; узкое место — вызовы LLM (таймаут фронта 120 с).

**Безопасность данных?**  
RBAC, Bearer-токен, секреты в env, HTTPS в проде.

---

## 17. Глоссарий терминов

Термины отсортированы по алфавиту (русский → пояснение).

### А

**API (Application Programming Interface)** — интерфейс, через который программы обмениваются данными. В проекте: HTTP-запросы к FastAPI.

**ASGI (Asynchronous Server Gateway Interface)** — стандарт для асинхронных Python веб-серверов. Uvicorn работает поверх ASGI.

**Адаптивное обучение** — подстройка сложности, тем и материалов под конкретного ученика на основе его ответов и профиля.

**Агент (в ИТ)** — программный модуль с определённой ролью, обрабатывающий входные данные и возвращающий результат (`BaseAgent`, `ProfilerAgent` и др.).

**Аутентификация** — проверка «кто ты» (логин + пароль → токен).

**Авторизация** — проверка «что тебе можно» (роль student/teacher/admin).

### Б

**Backend (бэкенд)** — серверная часть: FastAPI, БД, агенты, логика. Папка `AdaptEd/backend/`.

**Батчинг (batching)** — сохранение данных пакетами, а не после каждого клика (`BatchedSaver`).

**Bearer-токен** — строка доступа в заголовке `Authorization: Bearer <token>`. Кто предъявил токен — тот авторизован.

**BPMN (Business Process Model and Notation)** — нотация для описания бизнес-процессов. Схемы в `docs/bpmn/`.

### В

**Валидация** — проверка корректности данных. Pydantic на backend, TypeScript на frontend.

### Г

**Геймификация** — очки, уровни, достижения в `CognitiveProfile`.

### Д

**Деплой (deployment)** — размещение приложения на сервере (Railway).

**DTO / модель данных** — структура полей запроса/ответа (Pydantic `BaseModel`).

### З

**Запрос HTTP** — обращение клиента к серверу (метод + URL + заголовки + тело).

### И

**Интерцептор (interceptor)** — перехватчик axios: добавляет токен ко всем запросам (`api.ts`).

### К

**Клиент-сервер** — браузер (клиент) запрашивает данные у API (сервер).

**Когнитивный профиль** — модель знаний и поведения ученика: темы, ошибки, история (`CognitiveProfile`).

**CORS (Cross-Origin Resource Sharing)** — политика браузера: можно ли фронту с домена/URL обращаться к API на домене backend. Настраивается в `app.py`.

**CRUD** — Create, Read, Update, Delete — базовые операции над данными.

### Л

**LLM (Large Language Model)** — большая языковая модель (GPT-4o и аналоги через ProxyAPI).

**LocalStorage** — хранилище браузера; в проекте хранит `token`, `user_id`, `role`.

### М

**Middleware** — промежуточный слой в FastAPI (CORS, принудительные заголовки).

**Миграция БД** — изменение схемы таблиц (рекомендуется Alembic).

**Многоагентная система** — несколько специализированных агентов + оркестратор.

### О

**ORM (Object-Relational Mapping)** — SQLAlchemy: работа с БД через Python-классы, а не сырой SQL.

**Оркестратор** — `AgentOrchestrator`, координирует вызовы агентов.

### П

**Payload (полезная нагрузка)** — содержимое токена или JSON-тела запроса.

**Персонализация** — подстройка контента и сложности под профиль ученика.

**PostgreSQL** — реляционная СУБД для продакшена.

**Pydantic** — библиотека валидации и сериализации моделей в Python.

**ProxyAPI** — прокси-доступ к OpenAI-compatible API (ключ `PROXYAPI_KEY`).

### Р

**RBAC (Role-Based Access Control)** — доступ по ролям (`require_roles`, `assert_can_view_user_data`).

**REST (Representational State Transfer)** — стиль API: ресурсы по URL, методы HTTP, JSON, коды статуса.

**React** — библиотека для построения UI (компоненты, состояние).

**RAG (Retrieval-Augmented Generation)** — генерация ответа LLM с опорой на найденные документы. В проекте — направление развития, не полная реализация.

### С

**Сессия (в веб)** — в проекте реализована через токен, а не серверную сессию в памяти (stateless).

**SPA (Single Page Application)** — одностраничное приложение: React без перезагрузки страницы при навигации.

**SQLAlchemy** — ORM для Python.

**SQLite** — лёгкая файловая СУБД (возможна для прототипа).

**Stateless** — сервер не хранит состояние входа между запросами; всё в токене.

**Swagger / OpenAPI** — автодокументация API: `/docs` на FastAPI.

### Т

**Токен доступа (access token)** — строка после логина для последующих запросов.

**TypeScript** — типизированный JavaScript на фронтенде.

### Ф

**Frontend (фронтенд)** — клиентская часть: React, `AdaptEd/frontend/`.

**FastAPI** — Python-фреймворк для REST API.

### Х

**Хеш пароля** — необратимое преобразование пароля для хранения в БД (SHA-256 в проекте).

**HTTP** — протокол передачи данных в веб (GET, POST, …).

**HTTPS** — HTTP с шифрованием (обязателен в проде для токенов).

**HTTP-заголовок** — метаданные запроса (`Authorization`, `Content-Type`).

**HTTP-метод** — GET (читать), POST (создать/действие), PUT/PATCH (обновить), DELETE (удалить).

**HTTP-код статуса** — 200 OK, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error.

### Э

**Эндпоинт (endpoint)** — конкретный URL API, например `POST /auth/login`.

**JSON (JavaScript Object Notation)** — текстовый формат данных `{"key": "value"}`.

**JWT-подобный токен** — подписанный payload; в проекте свой формат из двух частей, идея как у JWT.

### Env и инфраструктура

**`.env`** — файл переменных окружения (ключи, URL БД); не коммитится в git.

**`DATABASE_URL`** — строка подключения к PostgreSQL.

**`VITE_API_URL`** — URL бэкенда, встраивается при `npm run build`.

**Railway** — облачный хостинг для деплоя.

**Uvicorn** — ASGI-сервер для запуска FastAPI.

**Vite** — сборщик и dev-сервер для React.

### Специфичные для проекта

**AdaptEd / EduAI Platform** — название системы в документации и UI.

**CognitiveProfile** — Pydantic-модель когнитивного профиля.

**ErrorTag** — перечисление типов ошибок ученика.

**AgentOrchestrator** — координатор агентов.

**AssistantService** — сервис работы с LLM.

**persistent_storage** — JSON-хранилище fallback.

**personalization_store** — загрузка/сохранение профилей в таблицах БД.

**seed_credentials.txt** — файл с тестовыми логинами для сида БД.

---

## Приложение: карта «термин → где в коде»

| Термин | Где смотреть |
|--------|----------------|
| REST API | `routes/*.py`, `/docs` |
| Bearer-токен | `utils/auth_service.py`, `services/api.ts` |
| Когнитивный профиль | `models/cognitive_profile.py`, `agents/profiler_agent.py` |
| Оркестратор | `agents/orchestrator.py` |
| LLM-чат | `services/assistant.py`, `routes/assistant.py` |
| БД | `utils/db.py`, `models/user_db.py` |
| Кабинет ученика | `components/StudentDashboard.tsx` |

---

*Документ подготовлен для защиты ВКР. При изменении кода обновляйте соответствующие разделы.*
