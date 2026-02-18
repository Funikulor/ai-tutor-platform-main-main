# 🔍 Как найти URL Backend на Railway

## 📋 Способ 1: Через Railway Dashboard (Самый простой)

1. **Войдите на Railway**: https://railway.app
2. **Откройте ваш проект**
3. **Найдите сервис "Backend"** (или как вы его назвали)
4. **Нажмите на сервис**
5. **Перейдите на вкладку "Settings"** (или "Settings" в меню слева)
6. **Найдите раздел "Networking"** или "Domains"
7. **Там будет URL** вида: `https://ваш-проект-production.up.railway.app`

Или:

1. **Нажмите на сервис Backend**
2. **В правом верхнем углу** будет кнопка **"Generate Domain"** или уже будет показан URL
3. **Скопируйте URL**

## 📋 Способ 2: Через вкладку "Deployments"

1. **Railway Dashboard** → Ваш проект → Backend сервис
2. **Вкладка "Deployments"**
3. **Нажмите на последний деплой**
4. **В логах** будет показан URL или домен

## 📋 Способ 3: Через вкладку "Settings" → "Networking"

1. **Backend сервис** → **Settings**
2. **Networking** или **Domains**
3. **Там будет Public Domain** или **Custom Domain**
4. **Скопируйте URL**

## 📋 Способ 4: Если URL не виден

1. **Backend сервис** → **Settings**
2. **Найдите кнопку "Generate Domain"** или **"Create Public Domain"**
3. **Нажмите на неё**
4. **Railway создаст публичный URL**

## ✅ Пример URL:

URL будет выглядеть примерно так:
```
https://adapted-backend-production.up.railway.app
```

или

```
https://your-project-name-production.up.railway.app
```

## 🔧 После того, как нашли URL:

1. **Скопируйте URL backend**
2. **Railway Dashboard** → **Frontend сервис** → **Variables**
3. **Добавьте или обновите:**
   ```
   VITE_API_URL=https://ваш-backend-url.up.railway.app
   ```
4. **Сохраните**
5. **Railway автоматически пересоберет frontend**

## ⚠️ Важно:

- URL должен быть **без `/api`** в конце (если не нужно)
- URL должен начинаться с **`https://`**
- После изменения переменных Railway пересоберет проект автоматически

## 🆘 Если не можете найти URL:

1. Проверьте, что backend сервис **задеплоен** (зеленый статус)
2. Проверьте, что backend **запущен** (не в состоянии "sleeping")
3. Если backend "sleeping" - сделайте запрос к нему, он проснется

## 📝 Проверка работы Backend:

После того, как нашли URL, откройте его в браузере:
```
https://ваш-backend-url.up.railway.app/
```

Должно вернуться:
```json
{"message": "Welcome to the AdaptEd API!"}
```

Если это работает - URL правильный! Используйте его в `VITE_API_URL`.

