from pathlib import Path
from typing import Optional, Literal, List, Dict, Any
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from ..db import get_db
from ..security import require_admin, ADMIN_TOKEN

ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(ROOT / "templates"))

router = APIRouter(prefix="/admin", tags=["admin"])
TABLES = ["grants","courses","scholarships","nonprofits"]

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: Optional[int] = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@router.post("/login")
def login_post(token: str = Form(...)):
    if token != ADMIN_TOKEN:
        return RedirectResponse("/admin/login?error=1", status_code=303)
    resp = RedirectResponse("/admin", status_code=303)
    # сохраним токен в cookie, чтобы формы работали без ручного заголовка
    resp.set_cookie("admin_token", token, httponly=True, samesite="lax")
    resp.set_cookie("x_admin_token", token, httponly=True, samesite="lax")
    return resp

@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db = Depends(get_db),
    _ = Depends(require_admin),
    table: str = "grants",
    include_status: Literal["published","draft","all"] = "all",
    q: Optional[str] = None,
):
    if table not in TABLES: table = "grants"
    sql = f"SELECT * FROM {table}"
    params: list = []
    if include_status != "all":
        sql += " WHERE status=?"
        params.append(include_status)
    if q:
        sql += (" AND" if "WHERE" in sql else " WHERE") + " (title LIKE ? OR description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    rows = [dict(r) for r in db.execute(sql, params).fetchall()]
    return templates.TemplateResponse("admin_list.html", {
        "request": request, "table": table, "rows": rows,
        "include_status": include_status, "q": q, "tables": TABLES
    })

@router.post("/{table}/{item_id}/publish")
def publish_item(table: str, item_id: int, db = Depends(get_db), _ = Depends(require_admin)):
    if table not in TABLES: raise HTTPException(404)
    db.execute(f"UPDATE {table} SET status='published' WHERE id=?", (item_id,))
    db.commit()
    return RedirectResponse(f"/admin?table={table}&include_status=all", status_code=303)

@router.post("/{table}/{item_id}/unpublish")
def unpublish_item(table: str, item_id: int, db = Depends(get_db), _ = Depends(require_admin)):
    if table not in TABLES: raise HTTPException(404)
    db.execute(f"UPDATE {table} SET status='draft' WHERE id=?", (item_id,))
    db.commit()
    return RedirectResponse(f"/admin?table={table}&include_status=all", status_code=303)

@router.post("/{table}/bulk")
def bulk_action(table: str, action: str = Form(...), db = Depends(get_db), _ = Depends(require_admin)):
    if table not in TABLES: raise HTTPException(404)
    if action == "publish_all_drafts":
        db.execute(f"UPDATE {table} SET status='published' WHERE status='draft'")
        db.commit()
    return RedirectResponse(f"/admin?table={table}&include_status=all", status_code=303)
