from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pathlib import Path
from app import db
from app.routes import router as api_router

# Путь к папке web
WEB_PATH = Path(__file__).resolve().parents[1] / 'web'

def mount_static_and_routes(app: FastAPI):
    """Инициализирует БД, роуты и статику"""
    # 1. Инициализация БД. HelpMap never auto-seeds fake/demo resources.
    db.init_db()
    
    # 2. Подключаем API роутер с префиксом /api
    app.include_router(api_router, prefix="/api")
    
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