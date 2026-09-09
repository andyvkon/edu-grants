import os

from fastapi import Header, HTTPException, status


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not ADMIN_TOKEN:
    raise RuntimeError(
        "ADMIN_TOKEN environment variable is required. "
        "Set it before starting the HelpMap API."
    )


def require_admin(x_admin_token: str = Header(default="")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid admin token required",
        )

    return True
