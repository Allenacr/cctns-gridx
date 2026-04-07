"""
CCTNS-GridX -- FIR Routes
CRUD operations for FIR records with CCTNS integration.
"""

from fastapi import APIRouter, HTTPException, Query
import sqlite3
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from backend.models.fir_model import FIRCreate, FIRUpdate

router = APIRouter(prefix="/api/fir", tags=["FIR Management"])


# ========================================================================
# STATIC ROUTES FIRST (must be before /{fir_id} to avoid path conflicts)
# ========================================================================

@router.get("/stats")
async def fir_stats():
    """Get FIR statistics for dashboard."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) as c FROM fir_records").fetchone()["c"]
    by_status = conn.execute(
        "SELECT status, COUNT(*) as count FROM fir_records GROUP BY status"
    ).fetchall()
    by_type = conn.execute("""
        SELECT c.crime_type, COUNT(*) as count
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        GROUP BY c.crime_type ORDER BY count DESC
    """).fetchall()
    by_district = conn.execute("""
        SELECT d.name, COUNT(*) as count
        FROM fir_records f
        JOIN districts d ON f.district_id = d.id
        GROUP BY d.id ORDER BY count DESC LIMIT 10
    """).fetchall()
    recent = conn.execute("""
        SELECT f.fir_number, f.date_reported, f.status, c.crime_type,
               d.name as district_name, ps.name as station_name,
               c.section, c.act_name
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        JOIN districts d ON f.district_id = d.id
        JOIN police_stations ps ON f.police_station_id = ps.id
        ORDER BY f.created_at DESC LIMIT 10
    """).fetchall()
    monthly = conn.execute("""
        SELECT strftime('%Y-%m', date_of_crime) as month, COUNT(*) as count
        FROM fir_records
        WHERE date_of_crime IS NOT NULL
        GROUP BY month ORDER BY month
    """).fetchall()

    conn.close()

    return {
        "total_firs": total,
        "by_status": {r["status"]: r["count"] for r in by_status},
        "by_crime_type": [{"type": r["crime_type"], "count": r["count"]} for r in by_type],
        "top_districts": [{"name": r["name"], "count": r["count"]} for r in by_district],
        "recent_firs": [dict(r) for r in recent],
        "monthly_trend": [{"month": r["month"], "count": r["count"]} for r in monthly],
    }


@router.get("/categories/all")
async def get_crime_categories():
    """Get all crime categories grouped by act."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM crime_categories ORDER BY act_name, section"
    ).fetchall()
    conn.close()
    return {"categories": [dict(r) for r in rows]}


@router.get("/districts/all")
async def get_districts():
    """Get all districts."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM districts ORDER BY name").fetchall()
    conn.close()
    return {"districts": [dict(r) for r in rows]}


@router.get("/stations/all")
async def get_police_stations(district_id: int = None):
    """Get police stations, optionally filtered by district."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    if district_id:
        rows = conn.execute(
            "SELECT * FROM police_stations WHERE district_id = ? ORDER BY name",
            (district_id,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM police_stations ORDER BY name").fetchall()
    conn.close()
    return {"stations": [dict(r) for r in rows]}


# ========================================================================
# LIST + CREATE (root path)
# ========================================================================

@router.get("/")
async def list_firs(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    district_id: int = None,
    crime_type: str = None,
    status: str = None,
    date_from: str = None,
    date_to: str = None,
    search: str = None,
):
    """List FIR records with pagination and filters."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT f.*, c.act_name, c.section, c.crime_type, c.severity,
               d.name as district_name, ps.name as station_name
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        JOIN districts d ON f.district_id = d.id
        JOIN police_stations ps ON f.police_station_id = ps.id
        WHERE 1=1
    """
    count_query = """
        SELECT COUNT(*) as total
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        WHERE 1=1
    """
    params = []
    count_params = []

    if district_id:
        query += " AND f.district_id = ?"
        count_query += " AND f.district_id = ?"
        params.append(district_id)
        count_params.append(district_id)
    if crime_type:
        query += " AND ? IN (c.crime_type, c.description)"
        count_query += " AND ? IN (c.crime_type, c.description)"
        params.append(crime_type)
        count_params.append(crime_type)
    if status:
        query += " AND f.status = ?"
        count_query += " AND f.status = ?"
        params.append(status)
        count_params.append(status)
    if date_from:
        query += " AND f.date_of_crime >= ?"
        count_query += " AND f.date_of_crime >= ?"
        params.append(date_from)
        count_params.append(date_from)
    if date_to:
        query += " AND f.date_of_crime <= ?"
        count_query += " AND f.date_of_crime <= ?"
        params.append(date_to)
        count_params.append(date_to)
    if search:
        query += " AND (f.fir_number LIKE ? OR f.complainant_name LIKE ? OR f.accused_name LIKE ?)"
        count_query += " AND (f.fir_number LIKE ? OR f.complainant_name LIKE ? OR f.accused_name LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
        count_params.extend([s, s, s])

    # Count total
    total = conn.execute(count_query, count_params).fetchone()["total"]

    # Paginate
    offset = (page - 1) * limit
    query += f" ORDER BY f.date_reported DESC LIMIT {limit} OFFSET {offset}"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {
        "firs": [dict(r) for r in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        },
    }


@router.post("/")
async def create_fir(fir: FIRCreate):
    """Create a new FIR record."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    # Generate FIR number
    district = conn.execute("SELECT code FROM districts WHERE id = ?", (fir.district_id,)).fetchone()
    if not district:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid district_id")

    year = datetime.now().year
    count = conn.execute(
        "SELECT COUNT(*) as c FROM fir_records WHERE district_id = ?",
        (fir.district_id,),
    ).fetchone()["c"]
    fir_number = f"TN/{district['code']}/{fir.police_station_id:03d}/{year}/{count + 1:04d}"

    cursor = conn.execute("""
        INSERT INTO fir_records (
            fir_number, police_station_id, district_id, crime_category_id,
            date_reported, date_of_crime, time_of_crime,
            latitude, longitude, location_address, location_landmark,
            complainant_name, complainant_age, complainant_gender, complainant_contact,
            accused_name, accused_age, accused_gender, accused_description,
            victim_name, victim_age, victim_gender,
            description, modus_operandi, property_stolen, property_value, weapon_used,
            status, cctns_synced
        ) VALUES (?,?,?,?,datetime('now'),?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
    """, (
        fir_number, fir.police_station_id, fir.district_id, fir.crime_category_id,
        fir.date_of_crime, fir.time_of_crime,
        fir.latitude, fir.longitude, fir.location_address, fir.location_landmark,
        fir.complainant_name, fir.complainant_age, fir.complainant_gender, fir.complainant_contact,
        fir.accused_name, fir.accused_age, fir.accused_gender, fir.accused_description,
        fir.victim_name, fir.victim_age, fir.victim_gender,
        fir.description, fir.modus_operandi, fir.property_stolen, fir.property_value, fir.weapon_used,
        "Registered",
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {
        "id": new_id,
        "fir_number": fir_number,
        "message": "FIR registered successfully",
        "cctns_synced": False,
    }


# ========================================================================
# DYNAMIC ROUTE LAST (/{fir_id} must be after all static paths)
# ========================================================================

@router.get("/{fir_id}")
async def get_fir(fir_id: int):
    """Get a single FIR record by ID."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("""
        SELECT f.*, c.act_name, c.section, c.crime_type, c.severity, c.description as crime_description,
               d.name as district_name, ps.name as station_name
        FROM fir_records f
        JOIN crime_categories c ON f.crime_category_id = c.id
        JOIN districts d ON f.district_id = d.id
        JOIN police_stations ps ON f.police_station_id = ps.id
        WHERE f.id = ?
    """, (fir_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="FIR not found")
    return dict(row)


@router.put("/{fir_id}")
async def update_fir(fir_id: int, update: FIRUpdate):
    """Update FIR record status or details."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    sets = []
    params = []

    if update.status:
        sets.append("status = ?")
        params.append(update.status)
    if update.investigating_officer:
        sets.append("investigating_officer = ?")
        params.append(update.investigating_officer)
    if update.description:
        sets.append("description = ?")
        params.append(update.description)
    if update.accused_name:
        sets.append("accused_name = ?")
        params.append(update.accused_name)

    if not sets:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    sets.append("updated_at = datetime('now')")
    params.append(fir_id)

    conn.execute(f"UPDATE fir_records SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    conn.close()

    return {"message": "FIR updated successfully", "id": fir_id}
