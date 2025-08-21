import os
from fastapi import Header, HTTPException, status

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin")  # поменяй в проде

def require_admin(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin token required")
    return True
