import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pathlib import Path
from app import db
from app.routes import router as api_router

# Путь к папке web
WEB_PATH = Path(__file__).resolve().parents[1] / 'web'

def seed_if_empty():
    """Заполняет базу данных, если она пуста"""
    conn = db.get_conn()
    cur = conn.cursor()
    
    # Проверяем количество записей
    cnt = cur.execute('SELECT COUNT(*) FROM grants').fetchone()[0]
    
    if cnt == 0:
        print("DEBUG: База пуста, наполняем новыми данными...")
        
        hours_regular = json.dumps({
            "Mon": "08:00-20:00", "Tue": "08:00-20:00", "Wed": "08:00-20:00",
            "Thu": "08:00-20:00", "Fri": "08:00-17:00", "Sat": "Closed", "Sun": "Closed"
        })

        grants_data = [
            ('WIC Program Center', 'Food assistance for women and children', 'published', 40.7128, -74.0060, 'WIC', hours_regular, 'https://example.com/wic'),
            ('Immigration Legal Hub', 'Free legal aid for refugees and immigrants', 'published', 40.7306, -73.9352, 'Legal', hours_regular, 'https://example.com/legal'),
            ('Shelter "Safe Haven"', 'Emergency housing and support', 'published', 40.7580, -73.9855, 'Shelter', hours_regular, 'https://example.com/shelter')
        ]

        cur.executemany('''
            INSERT INTO grants (title, summary, status, lat, lng, category, working_hours, url) 
            VALUES (?,?,?,?,?,?,?,?)
        ''', grants_data)
        conn.commit()
        print("DEBUG: Данные успешно добавлены!")
    
    conn.close()

def mount_static_and_routes(app: FastAPI):
    """Инициализирует БД, роуты и статику"""
    # 1. Инициализация и наполнение БД
    db.init_db()
    seed_if_empty()
    
    # 2. Подключаем API роутер
    app.include_router(api_router)
    
    # 3. Монтируем статику (папку web)
    if WEB_PATH.exists():
        app.mount("/web", StaticFiles(directory=str(WEB_PATH), html=True), name="web")

    # 4. Редирект с главной на карту
    @app.get("/")
    async def root():
        if WEB_PATH.exists():
            return RedirectResponse(url="/web/helpmap/index.html")
        return JSONResponse({"status": "error", "details": f"Folder web not found at {WEB_PATH}"})

    # 5. Отладка пути
    @app.get('/__debug/web')
    async def debug_web():
        return {
            'exists': WEB_PATH.exists(),
            'path': str(WEB_PATH),
            'files': [p.name for p in WEB_PATH.glob('*')] if WEB_PATH.exists() else []
        }