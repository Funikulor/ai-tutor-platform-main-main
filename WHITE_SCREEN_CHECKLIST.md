# ✅ Чеклист: Исправление белого экрана

## 🔍 Шаг 1: Проверьте консоль браузера

1. Откройте сайт
2. Нажмите **F12** (DevTools)
3. Перейдите на вкладку **Console**
4. **Скопируйте все ошибки** (красным цветом)

### Частые ошибки:

- `Failed to load resource` - файлы не найдены
- `Uncaught Error` - ошибка JavaScript
- `CORS error` - проблема с API

## 🔍 Шаг 2: Проверьте Network tab

1. F12 → **Network**
2. Обновите страницу (F5)
3. Проверьте:
   - Загружается ли `index.html`? (статус 200)
   - Загружаются ли `.js` файлы? (статус 200)
   - Загружаются ли `.css` файлы? (статус 200)
   - Если есть 404 - проблема с путями

## 🔍 Шаг 3: Проверьте логи Railway

Railway Dashboard → Frontend Service → Deployments → View Logs

**Должно быть:**
```
✓ npm install успешно
✓ npm run build успешно
✓ Server running on port XXXX
```

**Если ошибки:**
- Скопируйте их
- Проверьте, что все зависимости установлены

## 🔍 Шаг 4: Проверьте настройки Railway

Railway Dashboard → Frontend Service → Settings:

- **Root Directory**: `AdaptEd/frontend` ✅
- **Build Command**: `npm install && npm run build` ✅
- **Start Command**: `npm start` ✅ (или оставьте пустым для static)

## 🔍 Шаг 5: Проверьте переменные окружения

Railway Dashboard → Frontend Service → Variables:

```
VITE_API_URL=https://ваш-backend-url.up.railway.app
NODE_VERSION=20
```

**Важно:** Замените `https://ваш-backend-url.up.railway.app` на реальный URL вашего backend!

## 🔍 Шаг 6: Проверьте файлы

После сборки должны быть созданы:
- `AdaptEd/frontend/build/index.html`
- `AdaptEd/frontend/build/assets/` (с .js и .css файлами)

## 🆘 Быстрое решение:

1. **Пересоберите проект:**
   - Railway Dashboard → Frontend Service → Deployments → Redeploy

2. **Проверьте, что backend работает:**
   - Откройте URL backend в браузере
   - Должно вернуться: `{"message": "Welcome to the AdaptEd API!"}`

3. **Проверьте VITE_API_URL:**
   - Должен указывать на ваш backend
   - Без `/api` в конце (если не нужно)

4. **Проверьте консоль браузера:**
   - Если есть ошибки - скопируйте их
   - Часто проблема в неправильном API URL

## 📝 Что было исправлено:

1. ✅ Добавлен `base: '/'` в `vite.config.ts`
2. ✅ Создан `server.js` для правильной раздачи статических файлов
3. ✅ Обновлен `railway.json` для использования `npm start`
4. ✅ Добавлен `express` в `package.json`

## 🚀 После исправлений:

1. Закоммитьте изменения:
   ```bash
   git add .
   git commit -m "Исправлена конфигурация frontend для Railway"
   git push
   ```

2. Railway автоматически пересоберет проект

3. Проверьте сайт через 2-3 минуты

