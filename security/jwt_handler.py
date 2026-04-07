"""
CCTNS-GridX — JWT Authentication Handler
Handles token generation, validation, and role-based access control
"""

import jwt
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def generate_token(user_id: int, username: str, role: str, rank: str) -> str:
    """Generate a JWT token for authenticated user."""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "rank": rank,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=config.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Returns payload or raises exception."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def get_user_from_token(token: str) -> dict:
    """Extract user info from token."""
    payload = verify_token(token)
    return {
        "user_id": payload.get("user_id"),
        "username": payload.get("username"),
        "role": payload.get("role"),
        "rank": payload.get("rank"),
    }


# Role hierarchy for RBAC
ROLE_HIERARCHY = {
    "admin": 4,
    "analyst": 3,
    "officer": 2,
    "viewer": 1,
}


def check_permission(user_role: str, required_role: str) -> bool:
    """Check if user role meets the required role level."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level
