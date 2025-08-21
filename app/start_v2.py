# app/start_v2.py
# Берём существующее приложение из app.main и ДОПОДКЛЮЧАЕМ наш v2-роутер.
from app.main import app
from app.routers.v2_grants import router as v2_grants_router

app.include_router(v2_grants_router)
