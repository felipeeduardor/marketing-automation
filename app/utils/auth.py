"""Access control for the internal API (CRM, dashboard, metrics).

This is a single-operator sales tool, so access is a shared bearer token (ADMIN_API_TOKEN)
used by the Streamlit dashboard. Public endpoints (VSL page, tracking pixel, webhooks)
do not use this dependency.
"""

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer = HTTPBearer(auto_error=False)


async def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
    expected = get_settings().ADMIN_API_TOKEN
    if not expected:
        # Fail closed: without a configured token the internal API stays locked.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_TOKEN não configurado no servidor",
        )
    if credentials is None or not secrets.compare_digest(credentials.credentials.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
