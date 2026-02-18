# Настройка .env файла

## Расположение файла
Файл `.env` должен находиться в папке `AdaptEd/backend/`

## Обязательные настройки

### 1. База данных (DATABASE_URL)

#### Для SQLite (локальная база):
```env
DATABASE_URL=sqlite:///./adapted.db
```

#### Для Browsec SQL или PostgreSQL:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

#### Для MySQL:
```env
DATABASE_URL=mysql://username:password@localhost:3306/database_name
```

### 2. Настройки OpenAI

```env
ASSISTANT_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

**Важно:** 
- `OPENAI_API_KEY` - ваш API ключ от OpenAI (получить можно на https://platform.openai.com/api-keys)
- `OPENAI_MODEL` - модель OpenAI для использования

**Рекомендации по выбору модели (для бесплатного тарифа с $5/месяц):**
- **gpt-4o-mini** (рекомендуется) - лучший баланс цены и качества:
  - 60,000 токенов в минуту (TPM)
  - 3 запроса в минуту (RPM)
  - 200 запросов в день (RPD)
  - 200,000 токенов в день (TPD)
- **gpt-3.5-turbo** - самый дешевый вариант:
  - 40,000 TPM, 3 RPM, 200 RPD, 200,000 TPD
- **gpt-4o** - более качественные ответы, но дороже:
  - 10,000 TPM, 3 RPM, 200 RPD, 90,000 TPD

## Получение API ключа OpenAI

1. Перейдите на https://platform.openai.com/api-keys
2. Войдите в свой аккаунт или создайте новый
3. Нажмите "Create new secret key"
4. Скопируйте ключ и добавьте его в `.env` файл

## Проверка работы OpenAI

### 1. Убедитесь, что API ключ установлен:
Проверьте, что в `.env` файле есть строка `OPENAI_API_KEY=sk-...`

### 2. Проверьте баланс аккаунта:
Перейдите на https://platform.openai.com/account/usage и убедитесь, что у вас есть доступные средства

### 3. Протестируйте подключение:
Запустите backend и проверьте логи - должно быть сообщение `[OpenAI] Успешно получен ответ`

## Пример полного .env файла

```env
# База данных
DATABASE_URL=sqlite:///./adapted.db

# OpenAI настройки (рекомендуется gpt-4o-mini для бесплатного тарифа)

```

## Решение проблем

### OpenAI не работает:
1. Убедитесь, что `OPENAI_API_KEY` установлен в `.env` файле
2. Проверьте, что API ключ действителен на https://platform.openai.com/api-keys
3. Проверьте баланс аккаунта на https://platform.openai.com/account/usage
4. Убедитесь, что модель указана правильно (рекомендуется: `gpt-4o-mini` для бесплатного тарифа)
5. Проверьте интернет-соединение - OpenAI требует подключения к интернету
6. При превышении rate limits система автоматически повторит запрос с задержкой (3 попытки)

### База данных не работает:
1. Проверьте формат DATABASE_URL
2. Для SQLite убедитесь, что файл `adapted.db` существует или будет создан
3. Для PostgreSQL/MySQL убедитесь, что сервер запущен и доступен

