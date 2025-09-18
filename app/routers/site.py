from typing import Literal
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from pathlib import Path
from ..db import get_db

router = APIRouter(prefix="/site", tags=["site"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
TABLES = ["grants","courses","scholarships","nonprofits"]

@router.get("/{table}", response_class=HTMLResponse)
def site_table(table: Literal["grants","courses","scholarships","nonprofits"], db = Depends(get_db)):
    rows = [dict(r) for r in db.execute(f"SELECT * FROM {table} WHERE status='published'").fetchall()]
    return templates.TemplateResponse("site_table.html", {"request": {}, "table": table, "rows": rows})

@router.get("/{table}.json")
def site_table_json(table: Literal["grants","courses","scholarships","nonprofits"], db = Depends(get_db)):
    return [dict(r) for r in db.execute(f"SELECT * FROM {table} WHERE status='published'").fetchall()]
