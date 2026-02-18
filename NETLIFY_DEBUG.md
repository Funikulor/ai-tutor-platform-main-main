# Отладка Netlify Functions

## Проверка работы функций

### 1. Тестовая функция
Проверьте простую функцию:
```
https://web-tutor-ai.netlify.app/.netlify/functions/test
```

Должно вернуть:
```json
{
  "message": "Netlify Function работает!",
  "event": {...}
}
```

### 2. API функция
Проверьте API функцию:
```
https://web-tutor-ai.netlify.app/.netlify/functions/api/
```

Или через прокси:
```
https://web-tutor-ai.netlify.app/api/
```

### 3. Проверка логов

В Netlify Dashboard:
1. Site settings → Functions → View logs
2. Ищите ошибки инициализации
3. Проверьте, что все зависимости установлены

### 4. Переменные окружения

Убедитесь, что установлены в Netlify:
- `DATABASE_URL` - строка подключения к Neon
- `OPENAI_API_KEY` - ваш ключ OpenAI
- `ASSISTANT_PROVIDER` = `openai`
- `OPENAI_MODEL` = `gpt-4o-mini`

### 5. Структура файлов

Функции должны быть в:
```
netlify/
  functions/
    api/
      handler.py
      requirements.txt
    test/
      handler.py
```

### 6. Возможные проблемы

#### Функция не найдена (404)
- Проверьте, что `[functions] directory = "netlify/functions"` в `netlify.toml`
- Убедитесь, что файлы закоммичены в Git

#### Ошибка инициализации (500)
- Проверьте логи функции
- Убедитесь, что все зависимости в `requirements.txt`
- Проверьте, что `DATABASE_URL` установлен

#### Ошибка подключения к БД
- Neon может "засыпать" - первое подключение может занять 1-2 секунды
- Проверьте строку подключения
- Убедитесь, что используете pooler URL

