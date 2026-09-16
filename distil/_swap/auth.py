"""HTTP Basic Auth for the web panel.

Enabled via ``API_AUTH_ENABLED=true`` in ``.env``. When disabled, all
requests pass through (local development mode).

Security notes
--------------
* Uses :func:`secrets.compare_digest` for constant-time comparison to
  avoid timing attacks on the username/password.
* Credentials are read from :class:`Settings` — never hard-coded.
* When the app is behind a reverse-proxy that terminates TLS, the
  ``WWW-Authenticate`` challenge still works correctly because the
  header is a plain HTTP response header.
"""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import Settings

security = HTTPBasic(auto_error=False)

CredentialsDep = Annotated[
    HTTPBasicCredentials | None, Depends(security)
]


async def require_auth(
    request: Request,
    credentials: CredentialsDep,
) -> None:
    """Enforce HTTP Basic Auth when ``API_AUTH_ENABLED`` is true.

    When the feature is disabled (local dev), this dependency is a no-op.
    """
    settings: Settings = request.app.state.settings

    if not settings.api_auth_enabled:
        return

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    expected_user = settings.api_auth_username or ""
    expected_pass = (
        settings.api_auth_password.get_secret_value()
        if settings.api_auth_password
        else ""
    )

    user_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        expected_user.encode("utf-8"),
    )
    pass_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        expected_pass.encode("utf-8"),
    )

    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )