"""
CCTNS-GridX — Authentication Routes
Login, token refresh, and user info endpoints.
"""

from fastapi import APIRouter, HTTPException
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from security.jwt_handler import generate_token, verify_token
from security.encryption import verify_password
from backend.models.user_model import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate user and return JWT token."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    user = cursor.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1",
        (req.username,),
    ).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = generate_token(user["id"], user["username"], user["role"], user["rank"])

    # Update last login
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user["id"],))
    conn.commit()
    conn.close()

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "rank": user["rank"],
            "role": user["role"],
            "badge_number": user["badge_number"],
        },
        "message": "Login successful",
    }


@router.get("/me")
async def get_current_user_info():
    """Get current user info (requires valid token passed via query for simplicity)."""
    return {"message": "Use Authorization header with Bearer token"}


@router.get("/users")
async def list_demo_users():
    """List available demo accounts for login page."""
    return {
        "demo_accounts": [
            {"username": "sp_admin", "password": "admin123", "rank": "SP", "role": "Admin"},
            {"username": "dsp_ops", "password": "admin123", "rank": "DSP", "role": "Analyst"},
            {"username": "sho_adyar", "password": "admin123", "rank": "SHO", "role": "Officer"},
            {"username": "si_patrol", "password": "admin123", "rank": "SI", "role": "Officer"},
            {"username": "constable1", "password": "admin123", "rank": "Constable", "role": "Viewer"},
        ]
    }
