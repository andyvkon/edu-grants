# app/routers/content.py
from typing import Literal, Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from app.db import get_db
from app.security import require_admin

def make_content_router(table_name: str) -> APIRouter:
    r = APIRouter(prefix=f"/{table_name}", tags=[table_name])

    @r.get("/", response_model=List[Dict[str, Any]])
    def list_items(
        include_status: Optional[Literal["published","draft","all"]] = Query("published"),
        db = Depends(get_db),
    ):
        if include_status == "all":
            rows = db.execute(f"SELECT * FROM {table_name}").fetchall()
        else:
            rows = db.execute(
                f"SELECT * FROM {table_name} WHERE status=?",
                (include_status,),
            ).fetchall()
        return [dict(row) for row in rows]

    @r.get("/{item_id}", response_model=Dict[str, Any])
    def get_item(
        item_id: int,
        db = Depends(get_db),
        include_status: Optional[Literal["published","draft","all"]] = Query("published"),
    ):
        if include_status == "all":
            row = db.execute(f"SELECT * FROM {table_name} WHERE id=?", (item_id,)).fetchone()
        else:
            row = db.execute(
                f"SELECT * FROM {table_name} WHERE id=? AND status=?",
                (item_id, include_status),
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return dict(row)

    @r.patch("/{item_id}/publish")
    def publish_item(item_id: int, db = Depends(get_db), _=Depends(require_admin)):
        db.execute(f"UPDATE {table_name} SET status='published' WHERE id=?", (item_id,))
        db.commit()
        return {"ok": True, "id": item_id, "status": "published"}

    @r.patch("/{item_id}/unpublish")
    def unpublish_item(item_id: int, db = Depends(get_db), _=Depends(require_admin)):
        db.execute(f"UPDATE {table_name} SET status='draft' WHERE id=?", (item_id,))
        db.commit()
        return {"ok": True, "id": item_id, "status": "draft"}

    return r
