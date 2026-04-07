"""
CCTNS-GridX — User Model
Pydantic models for authentication.
"""

from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=5)


class LoginResponse(BaseModel):
    token: str
    user: dict
    message: str = "Login successful"


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    rank: str
    role: str
    badge_number: Optional[str]
    district_id: Optional[int]
