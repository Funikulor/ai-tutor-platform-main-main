# Как проверить сохраненные признаки адаптивного педагога-аналитика

## Способы проверки

### 1. Через API Endpoint (рекомендуется)

**GET запрос:**
```bash
curl http://localhost:8000/assistant/analytics/{user_id}
```

**Пример:**
```bash
curl http://localhost:8000/assistant/analytics/student_001
```

**Ответ:**
```json
{
  "student_id": "student_001",
  "academic_traits": {
    "math_level": "средний",
    "weak_topics": ["дроби", "геометрия"],
    "test_accuracy": "75%",
    "typical_errors": ["calculation_error"],
    "task_completion_speed": 120.5
  },
  "behavioral_traits": {
    "learning_style": "визуал",
    "motivation_level": "высокая (активные запросы)",
    "emotional_state": "позитивный",
    "interaction_style": "активный"
  },
  "progress_metrics": {
    "hint_requests_frequency": 5,
    "weekly_progress": {
      "2024-W15": 75.0
    },
    "monthly_progress": {
      "2024-04": 75.0
    },
    "improvement_areas": [],
    "strengths": []
  },
  "data_collection_enabled": true,
  "total_interactions": 42
}
```

### 2. Через Python скрипт

**Проверка конкретного ученика:**
```bash
cd AdaptEd/backend
python check_analytics.py student_001
```

**Интерактивный режим (запросит user_id):**
```bash
python check_analytics.py
```

**Показать всех учеников с данными:**
```bash
python check_analytics.py --all
```

### 3. Через браузер

Откройте в браузере:
```
http://localhost:8000/assistant/analytics/{user_id}
```

Например:
```
http://localhost:8000/assistant/analytics/student_001
```

### 4. Через Swagger UI (интерактивная документация)

1. Откройте `http://localhost:8000/docs`
2. Найдите endpoint `GET /assistant/analytics/{user_id}`
3. Нажмите "Try it out"
4. Введите `user_id` (например, `student_001`)
5. Нажмите "Execute"

## Что проверяется

### Академические признаки:
- ✅ Уровень знаний по предметам
- ✅ Слабые темы
- ✅ Точность в тестах
- ✅ Типичные ошибки
- ✅ Скорость выполнения заданий

### Поведенческие признаки:
- ✅ Стиль обучения (визуал/аудиал/кинестетик)
- ✅ Уровень мотивации
- ✅ Эмоциональное состояние
- ✅ Стиль взаимодействия

### Метрики прогресса:
- ✅ Частота запросов подсказок
- ✅ Недельный прогресс
- ✅ Месячный прогресс
- ✅ Области улучшения
- ✅ Сильные стороны

## Примеры использования

### Проверка после отправки сообщения в чат

1. Отправьте сообщение в чат через интерфейс
2. Подождите ответа
3. Проверьте данные:
   ```bash
   python check_analytics.py <ваш_user_id>
   ```

### Проверка после прохождения теста

1. Пройдите тест
2. Отправьте результат через API:
   ```bash
   curl -X POST http://localhost:8000/assistant/analytics/test-result \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "student_001",
       "subject": "математика",
       "accuracy": 75.0,
       "errors": ["дроби", "уравнения"],
       "time_spent_seconds": 300.0
     }'
   ```
3. Проверьте обновленные данные:
   ```bash
   python check_analytics.py student_001
   ```

## Интерпретация результатов

### Если данных нет:
- Ученик еще не взаимодействовал с системой
- Сбор данных отключен (`data_collection_enabled: false`)
- `user_id` неверный

### Если данных мало:
- Ученик только начал использовать систему
- Нужно больше взаимодействий для сбора данных

### Если данных много:
- Система активно собирает данные
- Можно использовать для персонализации обучения

## Отладка

Если данные не сохраняются:

1. **Проверьте, что backend запущен:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Проверьте логи backend:**
   - Должны быть сообщения о сборе данных
   - Не должно быть ошибок

3. **Проверьте, что сбор данных включен:**
   - В ответе должно быть `"data_collection_enabled": true`
   - Если `false`, ученик отключил сбор данных

4. **Проверьте user_id:**
   - Убедитесь, что используете правильный `user_id`
   - Проверьте через `--all` список всех учеников

## Автоматическая проверка

Можно добавить в тесты:

```python
def test_analytics_collection():
    from services.student_analytics import get_analytics_service
    
    service = get_analytics_service()
    user_id = "test_student"
    
    # Симулируем взаимодействие
    service.process_chat_message(user_id, "Не понимаю дроби")
    
    # Проверяем данные
    analytics = service.get_analytics(user_id)
    assert analytics['total_interactions'] > 0
    assert 'дроби' in analytics['academic_traits']['weak_topics']
```









