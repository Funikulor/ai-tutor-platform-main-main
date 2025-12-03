@echo off
echo ========================================
echo Установка Ollama для локальной нейросети
echo ========================================
echo.

REM Проверяем, установлена ли уже Ollama
where ollama >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Ollama уже установлена!
    echo.
    goto :check_model
)

echo Ollama не найдена. Начинаем установку...
echo.
echo Скачиваем Ollama для Windows...
echo.

REM Скачиваем установщик Ollama
powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/windows' -OutFile '%TEMP%\ollama-installer.exe'"

if not exist "%TEMP%\ollama-installer.exe" (
    echo Ошибка: Не удалось скачать установщик.
    echo.
    echo Пожалуйста, установите Ollama вручную:
    echo 1. Откройте https://ollama.com/download
    echo 2. Скачайте установщик для Windows
    echo 3. Запустите установщик
    echo.
    pause
    exit /b 1
)

echo Установщик скачан. Запускаем установку...
echo ВНИМАНИЕ: Следуйте инструкциям установщика!
echo.
start /wait "" "%TEMP%\ollama-installer.exe"

REM Удаляем установщик
del "%TEMP%\ollama-installer.exe"

:check_model
echo.
echo Проверяем установленные модели...
ollama list

echo.
echo ========================================
echo Установка модели для чата
echo ========================================
echo.
echo Рекомендуемые модели:
echo 1. llama3.2 (быстрая, ~2GB) - рекомендуется
echo 2. qwen2.5:1.5b (хорошо для русского, ~2GB)
echo 3. mistral (качественная, ~4GB)
echo.

set /p model_choice="Выберите модель (1/2/3) или введите название модели: "

if "%model_choice%"=="1" (
    set model_name=llama3.2
) else if "%model_choice%"=="2" (
    set model_name=qwen2.5:1.5b
) else if "%model_choice%"=="3" (
    set model_name=mistral
) else (
    set model_name=%model_choice%
)

echo.
echo Скачиваем модель %model_name%...
echo Это может занять несколько минут в зависимости от размера модели...
echo.

ollama pull %model_name%

if %ERRORLEVEL% == 0 (
    echo.
    echo ========================================
    echo Установка завершена успешно!
    echo ========================================
    echo.
    echo Модель %model_name% установлена.
    echo.
    echo Теперь нужно:
    echo 1. Убедиться, что Ollama запущена (должна запускаться автоматически)
    echo 2. Создать файл .env в папке AdaptEd\backend\ со следующим содержимым:
    echo.
    echo ASSISTANT_PROVIDER=ollama
    echo OLLAMA_URL=http://localhost:11434
    echo OLLAMA_MODEL=%model_name%
    echo.
    echo 3. Запустить backend
    echo.
) else (
    echo.
    echo Ошибка при установке модели.
    echo Попробуйте установить модель вручную:
    echo ollama pull %model_name%
    echo.
)

pause



