@echo off
setlocal

set "BACKEND_DIR=%~dp0"
for %%I in ("%BACKEND_DIR%..") do set "ROOT_DIR=%%~fI"

cd /d "%ROOT_DIR%"
set "FAILED_STEP=git pull --ff-only"
echo [1/6] Updating repository...
git pull --ff-only
if errorlevel 1 goto :fail

cd /d "%ROOT_DIR%\frontend"
set "FAILED_STEP=npm run build"
echo [2/6] Building frontend...
call npm run build
if errorlevel 1 goto :fail

cd /d "%BACKEND_DIR%"
if not exist .venv (
    set "FAILED_STEP=python -m venv .venv"
    echo [3/6] Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 goto :fail
) else (
    echo [3/6] Python virtual environment already exists.
)

set "FAILED_STEP=pip install -r requirements.txt"
echo [4/6] Installing backend dependencies...
.venv\Scripts\pip install -r requirements.txt -q
if errorlevel 1 goto :fail

set "FAILED_STEP=python prepare_database.py"
echo [5/6] Preparing database...
.venv\Scripts\python prepare_database.py
if errorlevel 1 goto :fail

set "FAILED_STEP=uvicorn main:app"
echo [6/6] Starting backend server...
.venv\Scripts\uvicorn main:app --reload --port 8000
if errorlevel 1 goto :fail

echo.
echo Backend server stopped.
pause
exit /b 0

:fail
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo [ERROR] %FAILED_STEP% failed with exit code %EXIT_CODE%.
echo Please review the error output above.
pause
exit /b %EXIT_CODE%
