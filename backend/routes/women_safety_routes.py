"""
CCTNS-GridX — Women Safety & Accident Zone Routes
Women security analysis, highway patrol locations, and accident-prone area data.
"""

from fastapi import APIRouter, Query
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

router = APIRouter(prefix="/api/safety", tags=["Women Safety & Accidents"])


# ─── Women Safety ──────────────────────────────────────────────

@router.get("/women-zones")
async def get_women_safety_zones(
    district_id: int = None,
    risk_level: str = None,
    zone_type: str = None,
):
    """Get women safety zones with risk levels and patrol coverage."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT ws.*, d.name as district_name,
               ps.name as nearest_station_name
        FROM women_safety_zones ws
        JOIN districts d ON ws.district_id = d.id
        LEFT JOIN police_stations ps ON ws.nearest_station_id = ps.id
        WHERE 1=1
    """
    params = []
    if district_id:
        query += " AND ws.district_id = ?"
        params.append(district_id)
    if risk_level:
        query += " AND ws.risk_level = ?"
        params.append(risk_level)
    if zone_type:
        query += " AND ws.zone_type = ?"
        params.append(zone_type)

    query += " ORDER BY CASE ws.risk_level WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {"zones": [dict(r) for r in rows], "total": len(rows)}


@router.get("/women-stats")
async def women_safety_stats():
    """Get women safety statistics."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    total_zones = conn.execute("SELECT COUNT(*) as c FROM women_safety_zones").fetchone()["c"]
    by_risk = conn.execute(
        "SELECT risk_level, COUNT(*) as count FROM women_safety_zones GROUP BY risk_level"
    ).fetchall()
    by_type = conn.execute(
        "SELECT zone_type, COUNT(*) as count FROM women_safety_zones GROUP BY zone_type"
    ).fetchall()

    # Women-related crimes from FIR data
    women_crimes = conn.execute("""
        SELECT d.name, COUNT(*) as count
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        JOIN districts d ON f.district_id = d.id
        WHERE c.crime_type = 'Crime Against Women'
        GROUP BY d.id ORDER BY count DESC LIMIT 10
    """).fetchall()

    # Monthly trend of women-related crimes
    monthly = conn.execute("""
        SELECT strftime('%Y-%m', f.date_of_crime) as month, COUNT(*) as count
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        WHERE c.crime_type = 'Crime Against Women' AND f.date_of_crime IS NOT NULL
        GROUP BY month ORDER BY month
    """).fetchall()

    # Time distribution
    hourly = conn.execute("""
        SELECT CAST(substr(f.time_of_crime, 1, 2) AS INTEGER) as hour, COUNT(*) as count
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        WHERE c.crime_type = 'Crime Against Women' AND f.time_of_crime IS NOT NULL
        GROUP BY hour ORDER BY hour
    """).fetchall()

    conn.close()

    return {
        "total_safety_zones": total_zones,
        "by_risk_level": {r["risk_level"]: r["count"] for r in by_risk},
        "by_zone_type": {r["zone_type"]: r["count"] for r in by_type},
        "top_districts": [{"name": r["name"], "count": r["count"]} for r in women_crimes],
        "monthly_trend": [{"month": r["month"], "count": r["count"]} for r in monthly],
        "hourly_distribution": {r["hour"]: r["count"] for r in hourly},
    }


# ─── Accident Zones ───────────────────────────────────────────

@router.get("/accident-zones")
async def get_accident_zones(
    district_id: int = None,
    severity: str = None,
    road_type: str = None,
):
    """Get accident-prone areas with IRAD data."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT az.*, d.name as district_name
        FROM accident_zones az
        JOIN districts d ON az.district_id = d.id
        WHERE 1=1
    """
    params = []
    if district_id:
        query += " AND az.district_id = ?"
        params.append(district_id)
    if severity:
        query += " AND az.severity = ?"
        params.append(severity)
    if road_type:
        query += " AND az.road_type = ?"
        params.append(road_type)

    query += " ORDER BY az.accident_count DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {"zones": [dict(r) for r in rows], "total": len(rows)}


@router.get("/accident-stats")
async def accident_stats():
    """Get accident zone statistics."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) as c FROM accident_zones").fetchone()["c"]
    total_accidents = conn.execute("SELECT SUM(accident_count) as c FROM accident_zones").fetchone()["c"] or 0
    total_fatalities = conn.execute("SELECT SUM(fatality_count) as c FROM accident_zones").fetchone()["c"] or 0
    total_injuries = conn.execute("SELECT SUM(injury_count) as c FROM accident_zones").fetchone()["c"] or 0

    by_severity = conn.execute(
        "SELECT severity, COUNT(*) as count, SUM(accident_count) as accidents FROM accident_zones GROUP BY severity"
    ).fetchall()
    by_road = conn.execute(
        "SELECT road_type, COUNT(*) as count, SUM(accident_count) as accidents FROM accident_zones GROUP BY road_type"
    ).fetchall()
    by_cause = conn.execute(
        "SELECT primary_cause, COUNT(*) as count FROM accident_zones GROUP BY primary_cause ORDER BY count DESC"
    ).fetchall()

    conn.close()

    return {
        "total_zones": total,
        "total_accidents": total_accidents,
        "total_fatalities": total_fatalities,
        "total_injuries": total_injuries,
        "by_severity": [{"severity": r["severity"], "zones": r["count"], "accidents": r["accidents"]} for r in by_severity],
        "by_road_type": [{"type": r["road_type"], "zones": r["count"], "accidents": r["accidents"]} for r in by_road],
        "by_cause": [{"cause": r["primary_cause"], "count": r["count"]} for r in by_cause],
    }
