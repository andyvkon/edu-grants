# app/boot_all.py
from app.main import app

import pkgutil, importlib
from fastapi.routing import APIRoute
from fastapi import FastAPI
import app.routers as routers_pkg

# подключаем все router из app/routers/*.py (кроме __init__)
for m in pkgutil.iter_modules(routers_pkg.__path__):
    mod = importlib.import_module(f"app.routers.{m.name}")
    router = getattr(mod, "router", None)
    if router:
        # избегаем дублей по путям
        existing = {r.path for r in app.routes if isinstance(r, APIRoute)}
        new_paths = {r.path for r in router.routes if isinstance(r, APIRoute)}
        if not (existing & new_paths):
            app.include_router(router)

# на всякий случай явно добавим v2
from app.routers.v2_grants import router as v2_grants_router
app.include_router(v2_grants_router)
