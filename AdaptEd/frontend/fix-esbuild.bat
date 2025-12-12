@echo off
echo Fixing esbuild version conflict...
cd /d "%~dp0"
echo Removing node_modules and package-lock.json...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del /f package-lock.json
echo Installing dependencies...
call npm install
echo Done! Try running npm run dev now.
pause

