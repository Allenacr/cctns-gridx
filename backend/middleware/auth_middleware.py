"""
CCTNS-GridX — Auth Middleware
JWT token verification for FastAPI dependency injection.
"""

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from security.jwt_handler import verify_token, check_permission


security = HTTPBearer()


async def get_current_user(request: Request) -> dict:
    """Extract and verify JWT token from request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    try:
        payload = verify_token(token)
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_role(required_role: str):
    """Dependency factory that checks user role level."""
    async def _check(request: Request):
        user = await get_current_user(request)
        if not check_permission(user.get("role", "viewer"), required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_role}",
            )
        return user
    return _check
