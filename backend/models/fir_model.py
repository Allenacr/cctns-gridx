"""
CCTNS-GridX — FIR Data Model
Pydantic models for FIR record validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FIRCreate(BaseModel):
    """Schema for creating a new FIR record."""
    police_station_id: int
    district_id: int
    crime_category_id: int
    date_of_crime: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time_of_crime: Optional[str] = None
    latitude: float = Field(..., ge=7.0, le=14.0)
    longitude: float = Field(..., ge=76.0, le=81.0)
    location_address: Optional[str] = None
    location_landmark: Optional[str] = None
    complainant_name: str = Field(..., min_length=2)
    complainant_age: Optional[int] = Field(None, ge=1, le=120)
    complainant_gender: Optional[str] = None
    complainant_contact: Optional[str] = None
    accused_name: Optional[str] = None
    accused_age: Optional[int] = Field(None, ge=1, le=120)
    accused_gender: Optional[str] = None
    accused_description: Optional[str] = None
    victim_name: Optional[str] = None
    victim_age: Optional[int] = Field(None, ge=1, le=120)
    victim_gender: Optional[str] = None
    description: str = Field(..., min_length=10)
    modus_operandi: Optional[str] = None
    property_stolen: Optional[str] = None
    property_value: Optional[float] = 0
    weapon_used: Optional[str] = None


class FIRUpdate(BaseModel):
    """Schema for updating FIR status."""
    status: Optional[str] = None
    investigating_officer: Optional[str] = None
    description: Optional[str] = None
    accused_name: Optional[str] = None
    accused_description: Optional[str] = None


class FIRResponse(BaseModel):
    """Schema for FIR API response."""
    id: int
    fir_number: str
    police_station_id: int
    district_id: int
    crime_category_id: int
    date_reported: str
    date_of_crime: str
    time_of_crime: Optional[str]
    latitude: float
    longitude: float
    location_address: Optional[str]
    complainant_name: str
    accused_name: Optional[str]
    victim_name: Optional[str]
    description: str
    status: str
    investigating_officer: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
