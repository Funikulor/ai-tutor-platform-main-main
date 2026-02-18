# ⚡ Быстрое исправление ошибки 405

## 🔍 Проверьте:

### 1. VITE_API_URL установлен?

Railway Dashboard → Frontend Service → Variables:
```
VITE_API_URL=https://ваш-backend-url.up.railway.app
```

**Важно:**
- Без `/api` в конце
- Без `/` в конце
- С `https://` в начале

### 2. Backend работает?

Откройте в браузере:
```
https://ваш-backend-url.up.railway.app/
```

Должно вернуться: `{"message": "Welcome to the AdaptEd API!"}`

### 3. Проверьте консоль браузера

1. Откройте сайт
2. **F12** → **Console**
3. Попробуйте войти
4. В консоли будет показано:
   - Какой URL используется
   - Какой метод (POST)
   - Какая ошибка

### 4. Проверьте Network tab

1. **F12** → **Network**
2. Попробуйте войти
3. Найдите запрос к `/auth/login`
4. Проверьте:
   - **Request URL**: должен быть `https://ваш-backend-url.up.railway.app/auth/login`
   - **Request Method**: должен быть **POST**
   - **Status Code**: если 405, проверьте URL

## 🆘 Если всё ещё 405:

Скопируйте из консоли браузера:
- Какой URL используется для запроса
- Какой метод (POST/GET)
- Полный текст ошибки

И отправьте мне - помогу разобраться!

