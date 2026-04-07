"""
CCTNS-GridX — Patrol Routes API
Patrol route generation, unit tracking, and route management.
"""

from fastapi import APIRouter, Query
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from ai.route_optimizer import route_optimizer

router = APIRouter(prefix="/api/patrol", tags=["Patrol Management"])


@router.get("/routes")
async def list_patrol_routes(
    district_id: int = None,
    season: str = None,
    route_type: str = None,
):
    """List existing patrol routes."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT pr.*, d.name as district_name, ps.name as station_name
        FROM patrol_routes pr
        JOIN districts d ON pr.district_id = d.id
        JOIN police_stations ps ON pr.police_station_id = ps.id
        WHERE pr.is_active = 1
    """
    params = []
    if district_id:
        query += " AND pr.district_id = ?"
        params.append(district_id)
    if season:
        query += " AND pr.season = ?"
        params.append(season)
    if route_type:
        query += " AND pr.route_type = ?"
        params.append(route_type)

    query += " ORDER BY pr.priority ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    routes = []
    for r in rows:
        route = dict(r)
        route["waypoints"] = json.loads(route["waypoints"])
        routes.append(route)

    return {"routes": routes, "total": len(routes)}


@router.get("/generate")
async def generate_route(
    district_id: int = Query(...),
    season: str = Query("General"),
    route_type: str = Query("Regular"),
    max_waypoints: int = Query(8, ge=3, le=15),
):
    """Generate an AI-optimized patrol route for a district."""
    result = route_optimizer.generate_patrol_route(
        config.DATABASE_PATH, district_id, season, route_type, max_waypoints,
    )
    return result


@router.get("/zones")
async def get_patrol_zones(
    district_id: int = None,
    n_zones: int = Query(5, ge=2, le=10),
):
    """Get K-Means patrol zone clusters."""
    return route_optimizer.get_zone_clusters(config.DATABASE_PATH, district_id, n_zones)


@router.get("/units")
async def list_patrol_units(district_id: int = None):
    """List patrol units with current positions."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT pu.*, ps.name as station_name, d.name as district_name
        FROM patrol_units pu
        JOIN police_stations ps ON pu.police_station_id = ps.id
        JOIN districts d ON ps.district_id = d.id
        WHERE 1=1
    """
    params = []
    if district_id:
        query += " AND d.id = ?"
        params.append(district_id)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return {"units": [dict(r) for r in rows], "total": len(rows)}


@router.get("/stats")
async def patrol_stats():
    """Get patrol statistics."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    total_routes = conn.execute("SELECT COUNT(*) as c FROM patrol_routes WHERE is_active = 1").fetchone()["c"]
    total_units = conn.execute("SELECT COUNT(*) as c FROM patrol_units").fetchone()["c"]
    active_units = conn.execute("SELECT COUNT(*) as c FROM patrol_units WHERE status = 'Active'").fetchone()["c"]
    by_season = conn.execute(
        "SELECT season, COUNT(*) as count FROM patrol_routes WHERE is_active = 1 GROUP BY season"
    ).fetchall()
    by_type = conn.execute(
        "SELECT route_type, COUNT(*) as count FROM patrol_routes WHERE is_active = 1 GROUP BY route_type"
    ).fetchall()

    conn.close()

    return {
        "total_routes": total_routes,
        "total_units": total_units,
        "active_units": active_units,
        "idle_units": total_units - active_units,
        "by_season": {r["season"]: r["count"] for r in by_season},
        "by_type": {r["route_type"]: r["count"] for r in by_type},
    }
