# 🚀 Деплой Frontend на Netlify

## ❌ Проблема: "Page not found"

Если вы видите ошибку "Page not found", это значит, что:
1. Загружен весь проект вместо собранного frontend
2. Или не настроена правильная директория публикации

---

## ✅ Решение: Правильный деплой на Netlify

### Вариант 1: Автоматический деплой через Git (Рекомендуется)

#### Шаг 1: Подключите репозиторий к Netlify

1. Войдите на https://app.netlify.com
2. Нажмите **"Add new site"** → **"Import an existing project"**
3. Выберите **GitHub/GitLab/Bitbucket** и подключите ваш репозиторий
4. Netlify автоматически найдет `netlify.toml` и настроит сборку

#### Шаг 2: Настройте переменные окружения

В настройках сайта (Site settings → Environment variables) добавьте:

```
VITE_API_URL=https://ваш-backend.onrender.com/api
```

**Важно:** Замените `https://ваш-backend.onrender.com` на реальный URL вашего backend на Render.

#### Шаг 3: Деплой

Netlify автоматически:
- Найдет `netlify.toml`
- Установит зависимости (`npm install`)
- Соберет проект (`npm run build`)
- Опубликует файлы из `AdaptEd/frontend/build/`

---

### Вариант 2: Ручная загрузка (если нет Git)

#### Шаг 1: Соберите frontend локально

```bash
cd C:\Users\Admin\Desktop\ai-tutor-platform-main-main\AdaptEd\frontend

# Создайте .env.production файл
echo VITE_API_URL=https://ваш-backend.onrender.com/api > .env.production

# Соберите проект
npm install
npm run build
```

#### Шаг 2: Загрузите только папку build

1. Войдите на https://app.netlify.com
2. Нажмите **"Add new site"** → **"Deploy manually"**
3. Перетащите **всю папку** `AdaptEd/frontend/build/` в окно загрузки
   - НЕ загружайте весь проект!
   - Только содержимое папки `build/`

#### Шаг 3: Настройте редиректы

После загрузки создайте файл `_redirects` в корне (или используйте настройки Netlify):

```
/*    /index.html   200
```

Или в настройках сайта:
- Site settings → Build & deploy → Post processing
- Добавьте SPA redirect: `/* /index.html 200`

---

## 📋 Настройки в netlify.toml

Файл `netlify.toml` уже создан в корне проекта:

```toml
[build]
  base = "AdaptEd/frontend"           # Где находится frontend
  command = "npm install && npm run build"  # Команда сборки
  publish = "AdaptEd/frontend/build"  # Что публиковать

[build.environment]
  NODE_VERSION = "20"                 # Версия Node.js

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200                        # Для SPA роутинга
```

---

## 🔧 Что НЕ нужно загружать на Netlify

❌ **НЕ загружайте:**
- Весь проект целиком
- Папку `src/` (исходный код)
- Папку `node_modules/`
- Папку `backend/`
- Файлы `.env` (используйте Environment Variables в Netlify)

✅ **Загружайте ТОЛЬКО:**
- Содержимое папки `AdaptEd/frontend/build/`
- Или подключите Git - Netlify соберет автоматически

---

## 🎯 Правильная структура на Netlify

После деплоя на Netlify должно быть:

```
/
├── index.html          ← Главный файл
├── assets/             ← Папка со скриптами и стилями
│   ├── index-xxxxx.js
│   └── index-xxxxx.css
└── (другие статические файлы)
```

---

## ✅ Проверка работы

1. **Откройте ваш сайт** на Netlify: `https://ваш-сайт.netlify.app`
2. **Проверьте консоль браузера** (F12):
   - Нет ли ошибок загрузки файлов
   - Правильно ли подключается к backend API
3. **Проверьте Network** (F12 → Network):
   - Файлы `index.html`, `.js`, `.css` загружаются с кодом 200

---

## 🆘 Решение проблем

### Ошибка "Page not found"

**Причина:** Неправильная директория публикации или отсутствие `index.html`

**Решение:**
1. Проверьте настройки в Netlify:
   - Site settings → Build & deploy → Build settings
   - **Publish directory:** `AdaptEd/frontend/build`
2. Убедитесь, что файл `index.html` есть в папке `build/`

### Ошибка "Failed during build"

**Причина:** Ошибки при сборке или неправильная версия Node.js

**Решение:**
1. Проверьте логи сборки в Netlify
2. Убедитесь, что `NODE_VERSION = "20"` в `netlify.toml`
3. Проверьте, что все зависимости в `package.json` корректны

### Frontend не подключается к backend

**Причина:** Неправильный `VITE_API_URL`

**Решение:**
1. Проверьте Environment Variables в Netlify
2. Убедитесь, что URL backend правильный (с `/api` в конце)
3. Пересоберите проект после изменения переменной

### CORS ошибки

**Причина:** Backend не разрешает запросы с Netlify домена

**Решение:**
В `AdaptEd/backend/app.py` убедитесь, что:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Или укажите конкретный Netlify URL
    ...
)
```

---

## 📝 Чек-лист деплоя

- [ ] Файл `netlify.toml` создан в корне проекта
- [ ] Репозиторий подключен к Netlify (или файлы загружены вручную)
- [ ] Переменная `VITE_API_URL` установлена в Environment Variables
- [ ] Build settings указывают на правильную директорию
- [ ] Backend работает и доступен по указанному URL
- [ ] Сайт открывается без ошибок

---

## 🎉 Готово!

После правильной настройки ваш сайт будет доступен по адресу:
`https://ваш-сайт.netlify.app`

**Важно:** Backend должен быть задеплоен отдельно (например, на Render), и его URL должен быть указан в `VITE_API_URL`.

