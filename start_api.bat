@echo off
setlocal

REM HelpMap local development launcher
cd /d %~dp0

REM Activate virtual environment
call .venv\Scripts\activate

REM Require ADMIN_TOKEN for local development
if "%ADMIN_TOKEN%"=="" (
    echo [ERROR] ADMIN_TOKEN environment variable is not set.
    echo.
    echo Example for the current terminal:
    echo set ADMIN_TOKEN=your-local-development-token
    echo.
    echo Then run start_api.bat again.
    pause
    exit /b 1
)

REM Start HelpMap API
echo [INFO] Starting HelpMap API...
uvicorn main:app --reload --port 8000

pause
