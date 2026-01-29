from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Depends
from app.db import get_conn
from app.security import require_admin

router = APIRouter()

# --- 1. ПОЛУЧЕНИЕ ДАННЫХ ДЛЯ КАРТЫ ---
@router.get('/v2/grants/')
def list_grants(q: Optional[str] = None, include_status: str = Query('published')):
    allowed = {'draft', 'published'}
    statuses = [s.strip() for s in include_status.split(',') if s.strip() in allowed]
    if not statuses:
        statuses = ['published']
        
    placeholders = ','.join('?' * len(statuses))
    sql = f'''
        SELECT id, title, summary, status, lat, lng, category, working_hours, url, address 
        FROM grants 
        WHERE status IN ({placeholders})
    '''
    params = list(statuses)
    
    if q:
        sql += ' AND (title LIKE ? OR summary LIKE ?)'
        like = f'%{q}%'
        params.extend([like, like])
    
    sql += ' ORDER BY id DESC'
    
    conn = get_conn()
    cursor = conn.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# --- 2. СОЗДАНИЕ НОВОЙ ТОЧКИ (ДЛЯ АДМИНКИ) ---
@router.post('/v2/grants/')
def create_grant(data: dict, _ = Depends(require_admin)): # Добавил защиту админом
    required = ['title', 'summary', 'category', 'lat', 'lng']
    if not all(k in data for k in required):
        raise HTTPException(status_code=400, detail=f"Missing fields: {required}")
        
    conn = get_conn(); cur = conn.cursor()
    # СОВЕТ: Для теста можешь поменять 'draft' на 'published', 
    # чтобы точка сразу летела на карту без модерации
    cur.execute(
        '''INSERT INTO grants (title, summary, status, lat, lng, category, working_hours, url, address) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (data['title'], data['summary'], data.get('status', 'draft'), data['lat'], data['lng'],
         data['category'], data.get('working_hours'), data.get('url'), data.get('address'))
    )
    new_id = cur.lastrowid
    conn.commit(); conn.close()
    return {'ok': True, 'id': new_id}

# --- 3. УПРАВЛЕНИЕ СТАТУСОМ (ДЛЯ МОДЕРАЦИИ) ---
@router.patch('/v2/grants/{id}/publish')
def publish_grant(id: int, _ = Depends(require_admin)):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('UPDATE grants SET status = "published" WHERE id = ?', (id,))
    conn.commit(); conn.close()
    return {'ok': True}

@router.patch('/v2/grants/{id}/unpublish')
def unpublish_grant(id: int, _ = Depends(require_admin)):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('UPDATE grants SET status = "draft" WHERE id = ?', (id,))
    conn.commit(); conn.close()
    return {'ok': True}