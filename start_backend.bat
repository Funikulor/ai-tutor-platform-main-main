@echo off
setlocal

echo Starting AdaptEd Backend Server (venv)...
cd /d "%~dp0AdaptEd\backend"

if not exist .venv (
  echo Creating virtual environment...
  py -m venv .venv
)

call .\.venv\Scripts\activate
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt

python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

endlocal
pause