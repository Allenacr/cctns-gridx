"""
CCTNS-GridX — Analytics Routes
Crime predictions, forecasting, and trend analysis endpoints.
"""

from fastapi import APIRouter, Query
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from ai.crime_model import crime_model
from ai.seasonal_predictor import seasonal_predictor
from ai.behavioral_engine import behavioral_engine

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Predictions"])


@router.get("/predict")
async def predict_crime(
    latitude: float = Query(..., ge=7.0, le=14.0),
    longitude: float = Query(..., ge=76.0, le=81.0),
    hour: int = Query(12, ge=0, le=23),
    day_of_week: int = Query(0, ge=0, le=6),
    month: int = Query(6, ge=1, le=12),
    district_id: int = Query(1),
):
    """Predict crime type probability for given location and time."""
    result = crime_model.predict(latitude, longitude, hour, day_of_week, month, district_id)
    return result


@router.get("/forecast")
async def forecast_crimes(
    months_ahead: int = Query(6, ge=1, le=12),
    district_id: int = None,
    crime_type: str = None,
):
    """Forecast monthly crime counts."""
    result = seasonal_predictor.forecast_monthly(
        config.DATABASE_PATH, months_ahead, district_id, crime_type,
    )
    return result


@router.get("/seasonal-risk")
async def seasonal_risk_map(month: int = Query(..., ge=1, le=12)):
    """Get district risk levels for a specific month."""
    return seasonal_predictor.get_seasonal_risk_map(config.DATABASE_PATH, month)


@router.get("/temporal-patterns")
async def temporal_patterns(crime_type: str = None, district_id: int = None):
    """Get hourly, daily, monthly crime distribution patterns."""
    return behavioral_engine.get_temporal_patterns(config.DATABASE_PATH, crime_type, district_id)


@router.get("/seasonal-analysis")
async def seasonal_analysis(district_id: int = None):
    """Get seasonal crime analysis."""
    return behavioral_engine.get_seasonal_analysis(config.DATABASE_PATH, district_id)


@router.get("/demographics")
async def demographics(crime_type: str = None):
    """Get accused/victim demographic patterns."""
    return behavioral_engine.get_demographic_patterns(config.DATABASE_PATH, crime_type)


@router.get("/crime-trends")
async def crime_trends(district_id: int = None):
    """Get crime type distribution and year-over-year trends."""
    return behavioral_engine.get_crime_type_trends(config.DATABASE_PATH, district_id)


@router.get("/repeat-offenders")
async def repeat_offenders():
    """Get repeat offender analysis."""
    return behavioral_engine.get_repeat_offender_analysis(config.DATABASE_PATH)


@router.get("/feature-importance")
async def feature_importance():
    """Get ML model feature importance rankings."""
    return {"features": crime_model.get_feature_importance()}
