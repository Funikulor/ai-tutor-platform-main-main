# 🤖 Настройка PROXYAPI для чат-бота

## ✅ Добавлена поддержка PROXYAPI!

Теперь ваш чат-бот может использовать PROXYAPI - сервис с агентами для доступа к различным AI моделям.

## 📝 Настройка:

### 1. У вас уже есть API ключ PROXYAPI

Отлично! Теперь нужно его настроить.

### 2. Установите переменные окружения

**Локально (`.env` файл):**
```env
ASSISTANT_PROVIDER=proxyapi
PROXYAPI_KEY=ваш-api-ключ-здесь
PROXYAPI_URL=https://api.proxyapi.ru/openai/v1/chat/completions
PROXYAPI_MODEL=gpt-4o-mini
```

**На Railway:**
1. Railway Dashboard → Backend Service → **Variables**
2. Добавьте переменные:
   - `ASSISTANT_PROVIDER` = `proxyapi`
   - `PROXYAPI_KEY` = `ваш-api-ключ`
   - `PROXYAPI_URL` = `https://api.proxyapi.ru/openai/v1/chat/completions` (или ваш URL)
   - `PROXYAPI_MODEL` = `gpt-4o-mini` (или другая модель)

### 3. Доступные модели PROXYAPI:

Зависит от вашего тарифа PROXYAPI. Обычно доступны:
- `gpt-4o-mini` - быстрая и дешевая
- `gpt-4o` - более мощная
- `gpt-3.5-turbo` - стандартная
- И другие модели, доступные в вашем тарифе

### 4. Пересоберите Backend

После установки переменных:

1. **Railway Dashboard** → Backend Service → **Deployments** → **Redeploy**
2. Или локально: перезапустите backend

### 5. Проверьте логи

В логах должно быть:
```
[AssistantService] Провайдер: proxyapi
[AssistantService] PROXYAPI URL: https://api.proxyapi.ru/openai/v1/chat/completions
[AssistantService] PROXYAPI модель: gpt-4o-mini
[AssistantService] PROXYAPI ключ: установлен
```

## 🔄 Переключение между провайдерами:

### Использовать PROXYAPI:
```env
ASSISTANT_PROVIDER=proxyapi
PROXYAPI_KEY=ваш-ключ
PROXYAPI_URL=https://api.proxyapi.ru/openai/v1/chat/completions
PROXYAPI_MODEL=gpt-4o-mini
```

### Использовать OpenAI:
```env
ASSISTANT_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## ✅ Преимущества PROXYAPI:

1. **Единый API** - доступ к различным моделям через один интерфейс
2. **Гибкость** - можно переключаться между моделями
3. **Надежность** - стабильный API
4. **Совместимость** - работает с OpenAI форматом

## 🔧 Автоматический Fallback:

Если выбранный провайдер недоступен, система автоматически попробует другой:

- Если `proxyapi` недоступен → попробует `openai`
- Если `openai` недоступен → попробует `proxyapi`
- Если оба недоступны → попробует Hugging Face API
- Если все недоступны → локальная модель

## 📝 Пример использования API:

```typescript
// Отправка сообщения в чат-бот с PROXYAPI
const response = await fetch('https://ваш-backend-url.up.railway.app/assistant/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: 'Объясни теорему Пифагора' }
    ],
    mode: 'general',
    user_id: 'user-123'
  })
});

const data = await response.json();
console.log(data.message); // Ответ от PROXYAPI
```

## ⚠️ Важно:

1. **API ключ должен быть установлен** до запуска backend
2. **PROXYAPI_URL** должен быть правильным (проверьте документацию PROXYAPI)
3. **Пересоберите backend** после изменения переменных
4. **Проверьте баланс** на вашем аккаунте PROXYAPI

## 🔗 Полезные ссылки:

- PROXYAPI: https://proxyapi.ru/
- Документация: проверьте документацию вашего тарифа PROXYAPI

