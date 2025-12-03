@echo off
echo Starting AdaptEd React Frontend...

REM Проверяем, установлены ли зависимости
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo.
echo Starting Vite development server...
echo Frontend will be available at: http://localhost:3000
echo.
call npm run dev
pause


