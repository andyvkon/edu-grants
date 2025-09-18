@echo off
REM ==== запуск проекта Edu-Grants ====
cd /d %~dp0

REM активируем виртуальное окружение
call .venv\Scripts\activate

REM пробуем подгрузить CSV, если есть
if exist csv\grants.csv (
    echo [INFO] Загружаем csv\grants.csv ...
    python app\load_csv_direct.py
) else (
    echo [WARN] Файл csv\grants.csv не найден. Пропускаем импорт.
)

REM запускаем сервер
uvicorn main:app --reload --port 8000

pause
