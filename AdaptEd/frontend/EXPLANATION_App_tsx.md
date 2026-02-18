# ПОСТРОЧНОЕ ОБЪЯСНЕНИЕ App.tsx - ГЛАВНЫЙ КОМПОНЕНТ

## БЛОК 1: ИМПОРТЫ (строки 1-9)

### Строка 1: `import { useState, useEffect } from 'react';`

**Что это:**
- Импортирует хуки React: `useState` и `useEffect`

**useState - для состояния:**
```javascript
// useState создает "состояние" - данные, которые могут изменяться
const [value, setValue] = useState(начальноеЗначение);
// value - текущее значение
// setValue - функция для изменения
```

**useEffect - для побочных эффектов:**
```javascript
// useEffect выполняет код после рендера
useEffect(() => {
    // Код выполнится после рендера
}, [зависимости]);
```

---

## БЛОК 2: СОСТОЯНИЯ (строки 12-16)

### Строка 12: `const [isAuthenticated, setIsAuthenticated] = useState(false);`

**Как работает useState:**
```javascript
// useState возвращает массив из 2 элементов:
const result = useState(false);
// result[0] - текущее значение
// result[1] - функция для изменения

// Деструктуризация:
const [isAuthenticated, setIsAuthenticated] = useState(false);
// isAuthenticated = false (начальное значение)
// setIsAuthenticated - функция для изменения

// Изменение:
setIsAuthenticated(true);
// Теперь isAuthenticated = true
// React автоматически перерисовывает компонент!
```

### Строка 13: `const [currentUser, setCurrentUser] = useState<any>(null);`
- Хранит текущего пользователя
- `any` - тип TypeScript (любой тип)
- Начальное значение: `null`

### Строка 14: `const [currentRole, setCurrentRole] = useState<'student' | 'teacher' | 'admin'>('student');`
- Хранит роль пользователя
- Тип: только 'student', 'teacher' или 'admin'
- Начальное значение: 'student'

### Строка 15: `const [showProfile, setShowProfile] = useState(false);`
- Показывать ли профиль пользователя
- Начальное значение: `false`

### Строка 16: `const [loading, setLoading] = useState(true);`
- Идет ли загрузка данных
- Начальное значение: `true` (показываем спиннер)

---

## БЛОК 3: useEffect (строки 18-20)

### `useEffect(() => { checkAuth(); }, []);`

**Как работает:**
```javascript
// useEffect выполняет код после рендера
useEffect(() => {
    checkAuth();  // Вызов функции проверки авторизации
}, []);  // Пустой массив = выполнится только один раз
```

**Массив зависимостей:**
- `[]` - выполнится только один раз при монтировании
- `[currentUser]` - выполнится при изменении currentUser
- Без массива - выполнится при каждом рендере (не рекомендуется!)

---

## БЛОК 4: ФУНКЦИЯ checkAuth (строки 22-40)

### Строка 22: `const checkAuth = async () => {`

**Что такое async:**
```javascript
// async - асинхронная функция
// Всегда возвращает Promise
async function checkAuth() {
    // Внутри можно использовать await
}
```

### Строка 23: `setLoading(true);`
- Показываем индикатор загрузки
- React перерисовывает компонент

### Строка 25: `const user = await authService.getCurrentUser();`

**Что такое await:**
```javascript
// await ждет, пока Promise выполнится
// Можно использовать только в async функции

const user = await authService.getCurrentUser();
// Ждет результат, затем сохраняет в user
```

**Без await:**
```javascript
const user = authService.getCurrentUser();
// user = Promise { <pending> }  ← Не то!
```

**С await:**
```javascript
const user = await authService.getCurrentUser();
// user = { id: 1, name: "John" }  ← Результат!
```

### Строки 26-31: Обработка успешного результата
```typescript
if (user) {
  setCurrentUser(user);           // Сохраняем пользователя
  setIsAuthenticated(true);       // Помечаем как авторизованного
  const userRole = user.role || localStorage.getItem('role') || 'student';
  setCurrentRole(userRole);       // Сохраняем роль
}
```

**Логическое ИЛИ (||):**
```javascript
// || возвращает первое "правдивое" значение
const role = user.role || localStorage.getItem('role') || 'student';
// Если user.role есть → используем его
// Если нет → проверяем localStorage
// Если и его нет → используем 'student'
```

### Строки 35-36: Обработка ошибок
```typescript
catch (error) {
  setIsAuthenticated(false);  // Помечаем как неавторизованного
}
```

### Строки 37-39: finally
```typescript
finally {
  setLoading(false);  // Всегда убираем спиннер
}
```

---

## БЛОК 5: ДРУГИЕ ФУНКЦИИ

### handleLoginSuccess (строки 42-44)
```typescript
const handleLoginSuccess = () => {
  checkAuth();  // Перепроверяем авторизацию
};
```

### handleLogout (строки 46-52)
```typescript
const handleLogout = () => {
  authService.logout();        // Выход из системы
  setIsAuthenticated(false);   // Помечаем как неавторизованного
  setCurrentUser(null);        // Очищаем пользователя
  setCurrentRole('student');   // Сбрасываем роль
  setShowProfile(false);       // Скрываем профиль
};
```

### handleRoleSwitch (строки 54-61)
```typescript
const handleRoleSwitch = (role: 'student' | 'teacher' | 'admin') => {
  if (currentUser?.role === 'admin') {  // Только админ может
    setCurrentRole(role);               // Переключать роли
    localStorage.setItem('viewing_as_role', role);
  }
};
```

**Оператор `?.` (optional chaining):**
```javascript
// Если currentUser = null, не вызовет ошибку
currentUser?.role
// То же самое, что:
currentUser && currentUser.role
```

---

## БЛОК 6: УСЛОВНЫЙ РЕНДЕРИНГ

### Строки 64-70: Показываем загрузку
```typescript
if (loading) {
  return (
    <div>
      <div className="...animate-spin"></div>  {/* Спиннер */}
    </div>
  );
}
```

### Строки 73-75: Показываем авторизацию
```typescript
if (!isAuthenticated) {
  return <Auth onSuccess={handleLoginSuccess} />;
}
```

---

## БЛОК 7: ОСНОВНОЙ РЕНДЕР (строки 82-188)

### Строка 78-80: Определение роли
```typescript
const actualRole = currentUser?.role || 'student';
const isAdmin = actualRole === 'admin';
const viewingRole = isAdmin ? currentRole : actualRole;
```

**Тернарный оператор `? :`:**
```javascript
// Если условие true → первое значение
// Если false → второе значение
const viewingRole = isAdmin ? currentRole : actualRole;
// Если isAdmin = true → viewingRole = currentRole
// Если isAdmin = false → viewingRole = actualRole
```

### Строка 84: `<Toaster position="top-right" richColors />`
- Компонент для уведомлений (toast messages)

### Строки 86-173: Header (шапка сайта)
- Логотип и название
- Переключение ролей (только для админа)
- Информация о пользователе
- Кнопки профиля и выхода

### Строки 177-185: Основной контент
```typescript
{showProfile ? (
  <UserProfile onClose={() => setShowProfile(false)} />
) : (
  <>
    {viewingRole === 'student' && <StudentDashboard />}
    {viewingRole === 'teacher' && <TeacherDashboard />}
    {viewingRole === 'admin' && <AdminPanel />}
  </>
)}
```

**Условный рендеринг:**
```javascript
// Тернарный оператор:
{showProfile ? <UserProfile /> : <Dashboard />}

// Логическое И (&&):
{viewingRole === 'student' && <StudentDashboard />}
// Если условие true → показываем компонент
// Если false → ничего не показываем
```

---

## КЛЮЧЕВЫЕ МОМЕНТЫ:

1. **useState** - создает состояние, которое может изменяться
2. **useEffect** - выполняет код после рендера
3. **async/await** - для асинхронных операций
4. **try/catch/finally** - обработка ошибок
5. **Условный рендеринг** - показываем разный контент в зависимости от условий

**ВСЕ ЭТО - РАБОТА С REACT ХУКАМИ И СОСТОЯНИЕМ!**


