@echo off
echo ========================================
echo Проверка подключения к Ollama
echo ========================================
echo.

REM Проверяем, установлена ли Ollama
where ollama >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Ollama не установлена!
    echo.
    echo Установите Ollama:
    echo 1. Запустите install_ollama.bat
    echo 2. Или скачайте с https://ollama.com/download
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama установлена
echo.

REM Проверяем, запущена ли Ollama
echo Проверяем подключение к Ollama...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -UseBasicParsing; Write-Host '[OK] Ollama запущена и доступна' } catch { Write-Host '[ОШИБКА] Ollama не запущена или недоступна' }"

echo.
echo Проверяем установленные модели...
ollama list

echo.
echo ========================================
echo Тест подключения к модели
echo ========================================
echo.

set /p test_model="Введите название модели для теста (или нажмите Enter для llama3.2): "
if "%test_model%"=="" set test_model=llama3.2

echo.
echo Отправляем тестовый запрос к модели %test_model%...
echo Это может занять несколько секунд...
echo.

ollama run %test_model% "Привет! Ответь одним предложением."

if %ERRORLEVEL% == 0 (
    echo.
    echo ========================================
    echo [OK] Ollama работает правильно!
    echo ========================================
    echo.
    echo Теперь можно:
    echo 1. Создать файл .env в AdaptEd\backend\ со следующими настройками:
    echo    ASSISTANT_PROVIDER=ollama
    echo    OLLAMA_URL=http://localhost:11434
    echo    OLLAMA_MODEL=%test_model%
    echo.
    echo 2. Запустить backend: start_backend.bat
    echo 3. Запустить frontend: start_frontend.bat
    echo.
) else (
    echo.
    echo [ОШИБКА] Не удалось подключиться к модели
    echo.
    echo Возможные причины:
    echo - Модель не установлена (выполните: ollama pull %test_model%)
    echo - Ollama не запущена (выполните: ollama serve)
    echo.
)

pause



