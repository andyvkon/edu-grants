from typing import Optional, Literal, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from ..db import get_db
from ..security import require_admin

router = APIRouter(prefix="/v2/grants", tags=["v2"])

@router.get("/", response_model=List[Dict[str, Any]])
def list_grants(
    include_status: Literal["published","draft","all"] = Query("published"),
    q: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    db = Depends(get_db),
):
    sql = "SELECT * FROM grants WHERE 1=1"
    params: list = []

    if include_status != "all":
        sql += " AND status = ?"
        params.append(include_status)

    if q:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    if tags:
        sql += " AND tags LIKE ?"
        params.append(f"%{tags}%")

    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]

@router.get("/{item_id}", response_model=Dict[str, Any])
def get_grant(
    item_id: int,
    include_status: Literal["published","draft","all"] = Query("published"),
    db = Depends(get_db),
):
    if include_status == "all":
        row = db.execute("SELECT * FROM grants WHERE id=?", (item_id,)).fetchone()
    else:
        row = db.execute(
            "SELECT * FROM grants WHERE id=? AND status=?",
            (item_id, include_status),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return dict(row)

@router.patch("/{item_id}/publish")
def publish_grant(item_id: int, db = Depends(get_db), _=Depends(require_admin)):
    db.execute("UPDATE grants SET status='published' WHERE id=?", (item_id,))
    db.commit()
    return {"ok": True, "id": item_id, "status": "published"}

@router.patch("/{item_id}/unpublish")
def unpublish_grant(item_id: int, db = Depends(get_db), _=Depends(require_admin)):
    db.execute("UPDATE grants SET status='draft' WHERE id=?", (item_id,))
    db.commit()
    return {"ok": True, "id": item_id, "status": "draft"}
