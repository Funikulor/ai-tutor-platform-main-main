# Материалы для приложений ВКР AdaptEd

## Приложение А. BPMN-модели

- `docs/bpmn/AdaptEd_AS_IS_StudentLearning.bpmn`
  AS-IS: персонализированный цикл обучения ученика.
- `docs/bpmn/AdaptEd_AS_IS_TestHomeworkLifecycle.bpmn`
  AS-IS: создание, назначение и прохождение теста/домашнего задания.
- `docs/bpmn/AdaptEd_AS_IS_MaterialStudy.bpmn`
  AS-IS: изучение материала и обновление прогресса.
- `docs/bpmn/AdaptEd_AS_IS_AdminOperations.bpmn`
  AS-IS: администрирование платформы.
- `docs/bpmn/AdaptEd_TO_BE_ContentRecommendations.bpmn`
  TO-BE: единый контур публикации материалов, retrieval и рекомендаций.
- Для каждой схемы также подготовлены графические версии:
  `*.svg` и `*.png` в той же папке `docs/bpmn`.

## Приложение Б. Модели данных

- Концептуальная иерархия контента:
  `предмет -> раздел -> тема -> учебный элемент`
- Когнитивный профиль:
  `topic_mastery`, `error_history`, `task_history`, `material_study_history`, `points`, `level`
- Основные сущности реляционной части:
  `users`, `tests`, `test_questions`, `test_submissions`, `homeworks`, `homework_submissions`, `documents`

## Приложение В. Архитектура

- Frontend:
  `React`, `TypeScript`, `Vite`
- Backend:
  `FastAPI`, `SQLAlchemy`, `Pydantic`
- Хранилища:
  `SQLite/PostgreSQL` для транзакционных данных и `persistent_storage`/JSON для части профилей и документов
- AI-контур:
  `OpenAI`, `ProxyAPI`, `Ollama`, `local pipeline`

## Приложение Г. Интерфейсы

- Авторизация
- Кабинет ученика
- Панель учителя
- Панель администратора
- Экран домашней работы
- AI-чат

## Приложение Д. API и тестирование

- Ключевые группы API:
  `auth`, `agents`, `assistant`, `homework`, `tests`, `materials`
- Сквозные сценарии для проверки:
  вход пользователя, генерация адаптивного задания, отправка ответа, прохождение теста, выдача рекомендаций, просмотр аналитики, работа админ-панели

## Практическое замечание

- BPMN-файлы можно открыть в `Camunda Modeler` и при необходимости пересоздать изображения, но базовые `PNG` и `SVG` уже экспортированы.
- Текст диплома уже ссылается на приложения А-Д, поэтому этот файл можно использовать как чек-лист финальной сборки материалов.
