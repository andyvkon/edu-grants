@echo off
setlocal enabledelayedexpansion

set PROJECT_DIR=C:\Mine\NIW\edu-grants
pushd "%PROJECT_DIR%"

REM === venv ===
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  call ".venv\Scripts\python.exe" -m pip install --upgrade pip
)

REM === зависимости (если есть requirements.txt) ===
if exist "requirements.txt" (
  echo [setup] Installing requirements...
  call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

REM === загрузка CSV в БД (скрипт лежит в app) ===
if exist "app\load_csv_direct.py" (
  echo [data] Loading CSV...
  call ".venv\Scripts\python.exe" "app\load_csv_direct.py" || goto :error
)

REM === окружение и путь ===
set PYTHONPATH=%CD%
if "%ADMIN_API_KEY%"=="" set ADMIN_API_KEY=devkey

REM === старт API в отдельном окне и пишем лог ===
echo [api] Starting Uvicorn on http://127.0.0.1:8000
start "EDU-GRANTS API" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload >> run.log 2>&1"

echo [ok] Launched. Logs: %PROJECT_DIR%\run.log
popd
endlocal
exit /b 0

:error
echo [ERROR] Something failed above. See console output.
pause
exit /b 1
