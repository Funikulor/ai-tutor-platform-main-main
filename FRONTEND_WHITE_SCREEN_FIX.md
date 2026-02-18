# 🔧 Исправление белого экрана на Frontend

## Возможные причины:

1. **Ошибки JavaScript в консоли браузера**
2. **Неправильные пути к статическим файлам**
3. **Ошибки при сборке**
4. **Проблемы с serve командой**

## ✅ Решение:

### 1. Проверьте консоль браузера

Откройте DevTools (F12) → Console и посмотрите ошибки:
- Если есть ошибки - скопируйте их
- Часто это проблемы с путями к файлам или импортами

### 2. Проверьте логи сборки в Railway

Railway Dashboard → Frontend Service → Deployments → View Logs
- Должна быть успешная сборка: `npm run build`
- Должен быть создан файл `build/index.html`

### 3. Проверьте настройки Railway

В Railway Dashboard → Frontend Service → Settings:

**Root Directory**: `AdaptEd/frontend`
**Build Command**: `npm install && npm run build`
**Start Command**: (оставьте пустым для static site)
**Output Directory**: `build`

Или используйте **Static Files**:
- Railway → Frontend Service → Settings → Static Files
- **Output Directory**: `build`

### 4. Обновите railway.json для frontend

Убедитесь, что `AdaptEd/frontend/railway.json` содержит:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm install && npm run build"
  },
  "deploy": {
    "staticAssetsPath": "build",
    "staticServeCommand": "npx serve -s build -l $PORT"
  }
}
```

### 5. Альтернатива: Используйте nginx или другой сервер

Если `serve` не работает, можно использовать другой подход:

**Вариант 1: Использовать Railway Static Files**
- В Railway Dashboard → Frontend Service
- Settings → Static Files → Enable
- Output Directory: `build`

**Вариант 2: Создать простой Node.js сервер**

Создайте `AdaptEd/frontend/server.js`:
```javascript
const express = require('express');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname, 'build')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
```

И обновите `package.json`:
```json
{
  "scripts": {
    "start": "node server.js"
  }
}
```

### 6. Проверьте переменные окружения

В Railway Dashboard → Frontend Service → Variables:
```
VITE_API_URL=https://ваш-backend-url.up.railway.app
NODE_VERSION=20
```

### 7. Проверьте index.html

Убедитесь, что `AdaptEd/frontend/index.html` содержит:
```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

## 🔍 Диагностика:

1. **Откройте Network tab** (F12 → Network)
   - Проверьте, загружаются ли файлы `.js` и `.css`
   - Если 404 - проблема с путями

2. **Проверьте Sources tab** (F12 → Sources)
   - Должны быть видны файлы из `build/`

3. **Проверьте URL**
   - Должен быть правильный URL без лишних путей
   - Например: `https://your-app.up.railway.app/` (не `/build/`)

## 🆘 Если ничего не помогает:

1. Проверьте, что `build/index.html` существует после сборки
2. Проверьте, что все пути в `index.html` правильные (относительные)
3. Попробуйте пересобрать: Railway → Redeploy
4. Проверьте логи Railway на наличие ошибок

