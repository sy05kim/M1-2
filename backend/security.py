"""Single-user demo access control. Not a multi-tenant auth solution."""
import hmac
import os
from fastapi import Header, HTTPException


def require_token(x_access_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("APP_ACCESS_TOKEN", "")
    if not expected:
        # Force safe configuration instead of publicly exposing billable endpoints.
        raise HTTPException(status_code=503, detail="Server APP_ACCESS_TOKEN is not configured")
    if not x_access_token or not hmac.compare_digest(x_access_token, expected):
        raise HTTPException(status_code=401, detail="Access token is missing or invalid")
