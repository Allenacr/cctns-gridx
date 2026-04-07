"""
CCTNS-GridX — Map Data Routes
Hotspot data, zone mapping, crime points, and heatmap data endpoints.
"""

from fastapi import APIRouter, Query
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from ai.hotspot_detector import hotspot_detector

router = APIRouter(prefix="/api/maps", tags=["Maps & Hotspots"])


@router.get("/hotspots")
async def get_hotspots(
    crime_type: str = None,
    district_id: int = None,
    date_from: str = None,
    date_to: str = None,
):
    """Get crime hotspot clusters detected by DBSCAN."""
    return hotspot_detector.detect_hotspots(
        config.DATABASE_PATH, crime_type, district_id, date_from, date_to,
    )


@router.get("/heatmap")
async def get_heatmap(
    crime_type: str = None,
    district_id: int = None,
    grid_size: int = Query(40, ge=10, le=100),
):
    """Get KDE-based heatmap intensity data for Leaflet."""
    points = hotspot_detector.generate_heatmap_data(
        config.DATABASE_PATH, crime_type, district_id, grid_size,
    )
    return {"points": points, "total": len(points)}


@router.get("/crime-points")
async def get_crime_points(
    crime_type: str = None,
    district_id: int = None,
    limit: int = Query(2000, ge=100, le=5000),
):
    """Get raw crime coordinate points for map markers."""
    points = hotspot_detector.get_crime_points(
        config.DATABASE_PATH, crime_type, district_id, limit,
    )
    return {"points": points, "total": len(points)}


@router.get("/zones")
async def get_zone_mapping():
    """Get multi-colored zone mapping -- crime counts per district with dominant crime type."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    # Get total crimes per district
    district_rows = conn.execute("""
        SELECT d.id, d.name, d.lat, d.lng, d.population, d.area_sq_km, d.zone,
               COUNT(f.id) as total_crimes
        FROM districts d
        LEFT JOIN fir_records f ON d.id = f.district_id
        GROUP BY d.id
        ORDER BY total_crimes DESC
    """).fetchall()

    # Get dominant crime type per district
    crime_by_district = {}
    rows2 = conn.execute("""
        SELECT f.district_id, c.crime_type, COUNT(*) as cnt
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        GROUP BY f.district_id, c.crime_type
        ORDER BY f.district_id, cnt DESC
    """).fetchall()
    conn.close()

    for r in rows2:
        did = r["district_id"]
        if did not in crime_by_district:
            crime_by_district[did] = r["crime_type"]

    CRIME_COLORS = {
        "Property Crime": "#e74c3c",
        "Violent Crime": "#ff1744",
        "Crime Against Women": "#e91e63",
        "Economic Crime": "#f39c12",
        "Public Order": "#3498db",
        "Narcotics": "#9b59b6",
        "Excise": "#1abc9c",
        "Kidnapping": "#e67e22",
        "Communal": "#ff6d00",
        "Arms": "#78909c",
        "Vice Crime": "#8e44ad",
        "Mining": "#2ecc71",
        "Animal Protection": "#16a085",
        "Atrocity": "#d35400",
        "Anti-National": "#546e7a",
    }

    # Use percentile-based risk levels for better distribution
    crime_counts = sorted([r["total_crimes"] for r in district_rows], reverse=True)
    p25 = crime_counts[len(crime_counts) // 4] if crime_counts else 1
    p50 = crime_counts[len(crime_counts) // 2] if crime_counts else 1
    p75 = crime_counts[3 * len(crime_counts) // 4] if crime_counts else 1

    zones = []
    for r in district_rows:
        dominant = crime_by_district.get(r["id"], "N/A")
        tc = r["total_crimes"]

        if tc >= p25:
            risk = "Critical"
        elif tc >= p50:
            risk = "High"
        elif tc >= p75:
            risk = "Medium"
        else:
            risk = "Low"

        max_crimes = crime_counts[0] if crime_counts else 1
        zones.append({
            "district_id": r["id"],
            "name": r["name"],
            "lat": r["lat"],
            "lng": r["lng"],
            "population": r["population"],
            "area_sq_km": r["area_sq_km"],
            "total_crimes": tc,
            "crime_density": round(tc / max(r["area_sq_km"], 1), 3),
            "dominant_crime": dominant,
            "color": CRIME_COLORS.get(dominant, "#95a5a6"),
            "risk_level": risk,
            "risk_score": round(tc / max(max_crimes, 1), 3),
            "zone": r["zone"],
        })

    return {"zones": zones}


@router.get("/station-mapping")
async def get_station_mapping():
    """Get police station area-wise mapping with crime counts."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT ps.id, ps.name, ps.lat, ps.lng, ps.station_type, ps.sho_name,
               d.name as district_name,
               COUNT(f.id) as total_crimes,
               SUM(CASE WHEN f.status = 'Registered' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN f.status = 'Under Investigation' THEN 1 ELSE 0 END) as investigating,
               SUM(CASE WHEN f.status = 'Closed' THEN 1 ELSE 0 END) as closed
        FROM police_stations ps
        JOIN districts d ON ps.district_id = d.id
        LEFT JOIN fir_records f ON f.police_station_id = ps.id
        GROUP BY ps.id
        ORDER BY total_crimes DESC
    """).fetchall()
    conn.close()

    return {"stations": [dict(r) for r in rows]}


@router.get("/crime-types")
async def get_crime_type_list():
    """Get list of all crime types and specific crime descriptions for filter dropdowns."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cat_rows = conn.execute("SELECT DISTINCT crime_type FROM crime_categories").fetchall()
    desc_rows = conn.execute("SELECT DISTINCT description FROM crime_categories").fetchall()
    conn.close()
    
    types = sorted([r[0] for r in cat_rows] + [r[0] for r in desc_rows])
    return {"crime_types": types}
