@echo off
cd /d "%~dp0"
:loop
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
ping -n 3 127.0.0.1 >nul
goto loop
