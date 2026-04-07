"""
CCTNS-GridX — Patrol Route Optimizer
Greedy TSP-based patrol route optimization + K-Means zone clustering
"""

import numpy as np
from sklearn.cluster import KMeans
import sqlite3
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class RouteOptimizer:
    """Optimizes patrol routes based on crime hotspots and zone clustering."""

    def _haversine_km(self, lat1, lng1, lat2, lng2):
        """Calculate haversine distance in kilometers."""
        R = 6371.0
        lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    def _greedy_tsp(self, points):
        """Solve TSP greedily — nearest neighbor heuristic.

        Args:
            points: list of (lat, lng, name) tuples

        Returns:
            Ordered list of points forming the route
        """
        if len(points) <= 2:
            return points

        remaining = list(range(len(points)))
        route = [remaining.pop(0)]

        while remaining:
            last = route[-1]
            nearest = min(
                remaining,
                key=lambda i: self._haversine_km(
                    points[last][0], points[last][1],
                    points[i][0], points[i][1],
                ),
            )
            route.append(nearest)
            remaining.remove(nearest)

        # Return to start (circular route)
        route.append(route[0])

        return [points[i] for i in route]

    def _clamp_to_tn_land(self, lat, lng, district_lat=None, district_lng=None):
        """Clamp coordinates to stay within Tamil Nadu's land area.
        
        Keeps points away from the sea (east coast) and neighbouring states.
        Uses the district center as an anchor — waypoints are pulled back
        toward the district center if they stray too far.
        """
        # Hard boundaries for TN land area
        lat = max(8.07, min(13.4, lat))   # TN latitude range
        lng = max(76.25, min(80.3, lng))  # TN longitude range (keep away from sea)

        # The east coast curves — sea boundary is roughly:
        #   South TN (lat 8-9): lng must be < 79.5
        #   Central TN (lat 9-11): lng must be < 79.8
        #   North TN (lat 11-13): lng must be < 80.3
        #   Chennai area (lat 13+): lng must be < 80.3
        if lat < 9.0:
            lng = min(lng, 79.2)
        elif lat < 10.0:
            lng = min(lng, 79.5)
        elif lat < 11.0:
            lng = min(lng, 79.8)
        elif lat < 12.5:
            lng = min(lng, 80.1)
        else:
            lng = min(lng, 80.3)

        # Keep waypoints close to their district center (max ~0.15 degrees ≈ 15km)
        if district_lat is not None and district_lng is not None:
            max_drift = 0.15
            if abs(lat - district_lat) > max_drift:
                lat = district_lat + max_drift * (1 if lat > district_lat else -1)
            if abs(lng - district_lng) > max_drift:
                lng = district_lng + max_drift * (1 if lng > district_lng else -1)

        return round(lat, 6), round(lng, 6)

    def generate_patrol_route(self, db_path: str, district_id: int,
                              season: str = "General",
                              route_type: str = "Regular",
                              max_waypoints: int = 8) -> dict:
        """Generate an optimized patrol route for a district.

        Uses crime hotspots as waypoints and optimizes with greedy TSP.
        """
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get crime locations for district
        month_map = {
            "Summer": (3, 4, 5, 6),
            "Monsoon": (7, 8, 9, 10),
            "Winter": (11, 12, 1, 2),
            "Festival": (1, 4, 8, 10, 11, 12),
        }

        query = """
            SELECT f.latitude, f.longitude, c.crime_type, c.severity,
                   ps.name as station_name, ps.lat as station_lat, ps.lng as station_lng
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            JOIN police_stations ps ON f.police_station_id = ps.id
            WHERE f.district_id = ?
        """
        params = [district_id]

        if season in month_map:
            placeholders = ",".join("?" * len(month_map[season]))
            query += f" AND CAST(strftime('%m', f.date_of_crime) AS INTEGER) IN ({placeholders})"
            params.extend(month_map[season])

        if route_type == "Women Safety":
            query += " AND c.crime_type = 'Crime Against Women'"
        elif route_type == "Night":
            query += " AND (CAST(substr(f.time_of_crime, 1, 2) AS INTEGER) >= 20 OR CAST(substr(f.time_of_crime, 1, 2) AS INTEGER) <= 5)"

        rows = cursor.execute(query, params).fetchall()

        # Get police station as starting point
        station = cursor.execute(
            "SELECT name, lat, lng FROM police_stations WHERE district_id = ? LIMIT 1",
            (district_id,),
        ).fetchone()

        # Get district info
        district = cursor.execute("SELECT name, lat, lng FROM districts WHERE id = ?", (district_id,)).fetchone()
        conn.close()

        if not rows or not station:
            return {"error": "No data available for route generation"}

        d_lat, d_lng = district["lat"], district["lng"]
        records = [dict(r) for r in rows]
        coords = np.array([[r["latitude"], r["longitude"]] for r in records])

        # Use K-Means to find hotspot centers as waypoints
        n_clusters = min(max_waypoints, len(coords))
        if n_clusters < 2:
            n_clusters = 2

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(coords)
        centers = kmeans.cluster_centers_

        # Add station as first waypoint (clamped)
        s_lat, s_lng = self._clamp_to_tn_land(station["lat"], station["lng"], d_lat, d_lng)
        waypoints_raw = [(s_lat, s_lng, f"{station['name']} (Start)")]

        for i, center in enumerate(centers):
            # Clamp waypoint to TN land
            wp_lat, wp_lng = self._clamp_to_tn_land(float(center[0]), float(center[1]), d_lat, d_lng)
            # Find nearest crime type for labeling
            distances = np.sqrt(np.sum((coords - center) ** 2, axis=1))
            nearest_idx = np.argmin(distances)
            label = f"Hotspot Zone {i + 1} ({records[nearest_idx]['crime_type']})"
            waypoints_raw.append((wp_lat, wp_lng, label))

        # Optimize route with TSP
        optimized = self._greedy_tsp(waypoints_raw)

        # Calculate total distance
        total_dist = 0
        for i in range(len(optimized) - 1):
            total_dist += self._haversine_km(
                optimized[i][0], optimized[i][1],
                optimized[i + 1][0], optimized[i + 1][1],
            )

        waypoints = [
            {"lat": round(p[0], 6), "lng": round(p[1], 6), "name": p[2]}
            for p in optimized
        ]

        # Estimated time (assuming 30 km/h average)
        est_time_mins = round(total_dist / 30 * 60)

        return {
            "route_name": f"{district['name']} {season} {route_type} Patrol",
            "district": district["name"],
            "season": season,
            "route_type": route_type,
            "waypoints": waypoints,
            "total_distance_km": round(total_dist, 2),
            "estimated_time_mins": est_time_mins,
            "waypoint_count": len(waypoints),
            "based_on_crimes": len(records),
        }

    def get_zone_clusters(self, db_path: str, district_id: int = None,
                          n_zones: int = 5) -> dict:
        """Cluster the patrol area into n zones using K-Means."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = "SELECT latitude, longitude FROM fir_records WHERE 1=1"
        params = []
        if district_id:
            query += " AND district_id = ?"
            params.append(district_id)

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        if len(rows) < n_zones:
            return {"zones": [], "message": "Insufficient data"}

        coords = np.array(rows)
        kmeans = KMeans(n_clusters=n_zones, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)

        zones = []
        for i in range(n_zones):
            mask = labels == i
            zone_coords = coords[mask]
            center = kmeans.cluster_centers_[i]

            zones.append({
                "zone_id": i + 1,
                "center": {"lat": round(float(center[0]), 6), "lng": round(float(center[1]), 6)},
                "crime_count": int(np.sum(mask)),
                "radius_km": round(float(np.max(np.sqrt(np.sum((zone_coords - center) ** 2, axis=1)))) * 111, 2),
            })

        zones.sort(key=lambda x: x["crime_count"], reverse=True)
        return {"zones": zones, "total_zones": n_zones}


# Singleton
route_optimizer = RouteOptimizer()
