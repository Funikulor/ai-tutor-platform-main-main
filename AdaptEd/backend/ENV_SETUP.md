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

### 2. Настройки Ollama

```env
ASSISTANT_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Важно:** 
- `OLLAMA_URL` должен указывать на адрес, где запущен Ollama сервер
- `OLLAMA_MODEL` должна быть установлена в вашей системе Ollama

## Проверка работы Ollama

### 1. Проверьте, что Ollama запущен:
```bash
ollama list
```

### 2. Проверьте, что модель установлена:
```bash
ollama list
```
Должна быть видна ваша модель (например, `llama3.2`)

### 3. Если модель не установлена, установите её:
```bash
ollama pull llama3.2
```

### 4. Проверьте доступность API:
```bash
curl http://localhost:11434/api/tags
```

### 5. Протестируйте модель:
```bash
ollama run llama3.2 "Привет!"
```

## Пример полного .env файла

```env
# База данных
DATABASE_URL=sqlite:///./adapted.db

# Ollama настройки
ASSISTANT_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Решение проблем

### Ollama не работает:
1. Убедитесь, что Ollama запущен: `ollama serve` или проверьте службу Windows
2. Проверьте, что модель установлена: `ollama list`
3. Проверьте URL в .env - должен быть `http://localhost:11434`
4. Проверьте имя модели - должно совпадать с установленной моделью

### База данных не работает:
1. Проверьте формат DATABASE_URL
2. Для SQLite убедитесь, что файл `adapted.db` существует или будет создан
3. Для PostgreSQL/MySQL убедитесь, что сервер запущен и доступен

