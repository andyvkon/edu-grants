from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pathlib import Path
from app import db
from app.routes import router as api_router

WEB_PATH = Path(__file__).resolve().parents[1] / 'web'

def mount_static_and_routes(app: FastAPI):
    db.init_db(); seed_if_empty()
    if WEB_PATH.exists():
        app.mount('/web', StaticFiles(directory=str(WEB_PATH), html=True), name='web')
    app.include_router(api_router)

    @app.get('/')
    async def root():
        if WEB_PATH.exists():
            return RedirectResponse(url='/web/')
        return JSONResponse({'message':'Web folder not found'})

    @app.get('/__debug/web')
    async def debug_web():
        return {'exists':WEB_PATH.exists(),'files':[p.name for p in WEB_PATH.glob('*')]}

def seed_if_empty():
    conn=db.get_conn(); cur=conn.cursor()
    cnt=cur.execute('SELECT COUNT(*) FROM grants').fetchone()[0]
    if cnt==0:
        cur.executemany('INSERT INTO grants (title,summary,status) VALUES (?,?,?)',[
            ('Программа поддержки НКО','Финансирование проектов в сфере образования','published'),
            ('Стипендии 2025','Именные стипендии для студентов STEM','published'),
            ('Господдержка ИТ','Софинансирование внедрения цифровых решений','draft')
        ])
        conn.commit()
    conn.close()
