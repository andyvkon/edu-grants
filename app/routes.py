from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.db import get_conn
from app.security import require_admin

router = APIRouter()

@router.get('/v2/grants/')
def list_grants(q: Optional[str] = None, include_status: str = Query('published')):
    allowed = {'draft','published'}
    statuses = [s.strip() for s in include_status.split(',') if s.strip() in allowed]
    if not statuses:
        statuses = ['published']
    placeholders = ','.join('?'*len(statuses))
    sql = f'SELECT id,title,summary,status FROM grants WHERE status IN ({placeholders})'
    params = statuses
    if q:
        sql += ' AND (title LIKE ? OR summary LIKE ?)'
        like = f'%{q}%'
        params += [like, like]
    sql += ' ORDER BY id DESC'
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows

@router.patch('/v2/grants/{grant_id}/publish')
def publish(grant_id: int, _: None = require_admin):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('UPDATE grants SET status="published" WHERE id=?',(grant_id,))
    if cur.rowcount==0:
        conn.close(); raise HTTPException(404,'Grant not found')
    conn.commit(); conn.close()
    return {'ok':True,'id':grant_id,'status':'published'}

@router.patch('/v2/grants/{grant_id}/unpublish')
def unpublish(grant_id: int, _: None = require_admin):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('UPDATE grants SET status="draft" WHERE id=?',(grant_id,))
    if cur.rowcount==0:
        conn.close(); raise HTTPException(404,'Grant not found')
    conn.commit(); conn.close()
    return {'ok':True,'id':grant_id,'status':'draft'}
