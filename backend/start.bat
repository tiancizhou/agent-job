@echo off
setlocal

set "BACKEND_DIR=%~dp0"
for %%I in ("%BACKEND_DIR%..") do set "ROOT_DIR=%%~fI"

cd /d "%ROOT_DIR%"
git pull --ff-only
if errorlevel 1 exit /b 1

cd /d "%ROOT_DIR%\frontend"
call npm run build
if errorlevel 1 exit /b 1

cd /d "%BACKEND_DIR%"
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 exit /b 1
)

.venv\Scripts\pip install -r requirements.txt -q
if errorlevel 1 exit /b 1

.venv\Scripts\python prepare_database.py
if errorlevel 1 exit /b 1

.venv\Scripts\uvicorn main:app --reload --port 8000
