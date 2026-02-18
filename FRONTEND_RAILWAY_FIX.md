# 🔧 Исправление белого экрана на Railway Frontend

## ❌ Проблема:

Браузер пытается загрузить `/src/main.tsx` вместо собранных файлов из `/assets/`. Это означает, что Railway раздает исходный `index.html` вместо собранного.

## ✅ Решение:

### Вариант 1: Использовать Railway Static Files (Рекомендуется)

1. **Railway Dashboard** → Frontend Service → Settings
2. **Найдите раздел "Static Files"** или "Output Directory"
3. **Включите Static Files**
4. **Укажите Output Directory**: `build`
5. **Сохраните**

Railway автоматически будет раздавать файлы из папки `build/`.

### Вариант 2: Использовать serve (через railway.json)

Конфигурация уже обновлена в `railway.json`:
```json
{
  "deploy": {
    "staticAssetsPath": "build",
    "staticServeCommand": "npx serve -s build -l $PORT"
  }
}
```

**Важно:** Убедитесь, что:
- `serve` добавлен в `package.json` (уже добавлен)
- Root Directory установлен в `AdaptEd/frontend`
- Build Command: `npm install && npm run build`

### Вариант 3: Использовать Express сервер

Если предыдущие варианты не работают, используйте `server.js`:

1. Убедитесь, что `express` в `package.json` (уже добавлен)
2. В `railway.json`:
```json
{
  "deploy": {
    "startCommand": "npm start"
  }
}
```

## 🔍 Проверка:

После деплоя проверьте:

1. **Откройте сайт**
2. **F12 → Network**
3. **Проверьте, что загружаются:**
   - `/assets/index-XXXXX.js` (не `/src/main.tsx`)
   - `/assets/index-XXXXX.css`
   - `index.html` с правильными путями

## 🆘 Если всё ещё белый экран:

1. **Проверьте логи Railway:**
   - Railway Dashboard → Frontend Service → Deployments → View Logs
   - Должно быть: `npm run build` успешно
   - Должно быть: `Server running` или `serving files`

2. **Проверьте Root Directory:**
   - Railway Dashboard → Frontend Service → Settings
   - Root Directory должен быть: `AdaptEd/frontend`

3. **Проверьте, что папка build создана:**
   - В логах должно быть: `build/index.html created`

4. **Попробуйте пересобрать:**
   - Railway Dashboard → Frontend Service → Deployments → Redeploy

## 📝 Что было исправлено:

1. ✅ Добавлен `serve` в `package.json`
2. ✅ Обновлен `railway.json` для использования `serve`
3. ✅ Улучшен `server.js` (если нужен Express)
4. ✅ Добавлен `base: '/'` в `vite.config.ts`

## 🚀 После исправлений:

1. Закоммитьте изменения:
   ```bash
   git add .
   git commit -m "Исправлена конфигурация frontend для Railway static files"
   git push
   ```

2. Railway автоматически пересоберет проект

3. Проверьте сайт через 2-3 минуты

