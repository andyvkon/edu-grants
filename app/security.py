from fastapi import Header, HTTPException, status

ADMIN_TOKEN_DEFAULT = 'dev-admin'

def require_admin(x_admin_token: str | None = Header(None)):
    if not x_admin_token or x_admin_token != ADMIN_TOKEN_DEFAULT:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid X-Admin-Token')
