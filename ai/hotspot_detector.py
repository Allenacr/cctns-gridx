"""
CCTNS-GridX — Hotspot Detection Engine
DBSCAN spatial clustering + Kernel Density Estimation for crime hotspot mapping.
"""

import numpy as np
from sklearn.cluster import DBSCAN
from scipy.stats import gaussian_kde
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class HotspotDetector:
    """Detects crime hotspots using DBSCAN and KDE."""

    def __init__(self):
        self.eps = config.DBSCAN_EPS
        self.min_samples = config.DBSCAN_MIN_SAMPLES
        self.bandwidth = config.KDE_BANDWIDTH

    def detect_hotspots(self, db_path: str, crime_type: str = None,
                        district_id: int = None, date_from: str = None,
                        date_to: str = None) -> dict:
        """Detect crime hotspots using DBSCAN clustering.

        Args:
            db_path: Path to SQLite database
            crime_type: Filter by crime type (optional)
            district_id: Filter by district (optional)
            date_from: Start date filter YYYY-MM-DD (optional)
            date_to: End date filter YYYY-MM-DD (optional)

        Returns:
            dict with clusters, centers, and stats
        """
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT f.latitude, f.longitude, f.id, f.date_of_crime, f.time_of_crime,
                   c.crime_type, c.severity, c.act_name, c.section, d.name as district_name
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            JOIN districts d ON f.district_id = d.id
            WHERE 1=1
        """
        params = []

        if crime_type:
            query += " AND ? IN (c.crime_type, c.description)"
            params.append(crime_type)
        if district_id:
            query += " AND f.district_id = ?"
            params.append(district_id)
        if date_from:
            query += " AND f.date_of_crime >= ?"
            params.append(date_from)
        if date_to:
            query += " AND f.date_of_crime <= ?"
            params.append(date_to)

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        if len(rows) < self.min_samples:
            return {"clusters": [], "total_crimes": len(rows), "message": "Not enough data for clustering"}

        records = [dict(r) for r in rows]
        coords = np.array([[r["latitude"], r["longitude"]] for r in records])

        # Run DBSCAN
        # Convert eps (in degrees) to radians for haversine metric
        eps_rad = np.radians(self.eps)
        clustering = DBSCAN(eps=eps_rad, min_samples=self.min_samples, metric="haversine")
        # Convert to radians for haversine
        coords_rad = np.radians(coords)
        labels = clustering.fit_predict(coords_rad)

        # Build cluster info
        clusters = []
        unique_labels = set(labels)
        unique_labels.discard(-1)  # Remove noise label

        for label in sorted(unique_labels):
            mask = labels == label
            cluster_coords = coords[mask]
            cluster_records = [records[i] for i in range(len(records)) if mask[i]]

            center_lat = float(np.mean(cluster_coords[:, 0]))
            center_lng = float(np.mean(cluster_coords[:, 1]))
            count = int(np.sum(mask))

            # Determine dominant crime type in cluster
            crime_types_in_cluster = [r["crime_type"] for r in cluster_records]
            from collections import Counter
            type_counts = Counter(crime_types_in_cluster)
            dominant_type = type_counts.most_common(1)[0][0]

            avg_severity = float(np.mean([r["severity"] for r in cluster_records]))

            # Calculate radius (max distance from center)
            distances = np.sqrt(
                (cluster_coords[:, 0] - center_lat) ** 2 +
                (cluster_coords[:, 1] - center_lng) ** 2
            )
            radius_deg = float(np.max(distances))  # degrees
            radius_km = radius_deg * 111.0  # approximate

            # Intensity (normalized 0-1)
            intensity = min(1.0, count / 50.0)

            clusters.append({
                "cluster_id": int(label),
                "center": {"lat": round(center_lat, 6), "lng": round(center_lng, 6)},
                "crime_count": count,
                "radius_km": round(radius_km, 2),
                "intensity": round(intensity, 3),
                "dominant_crime_type": dominant_type,
                "crime_type_breakdown": dict(type_counts),
                "avg_severity": round(avg_severity, 2),
                "districts": list(set(r["district_name"] for r in cluster_records)),
            })

        # Sort by intensity
        clusters.sort(key=lambda x: x["intensity"], reverse=True)

        noise_count = int(np.sum(labels == -1))

        return {
            "clusters": clusters,
            "total_crimes": len(records),
            "total_clusters": len(clusters),
            "noise_points": noise_count,
            "filters": {
                "crime_type": crime_type,
                "district_id": district_id,
                "date_from": date_from,
                "date_to": date_to,
            },
        }

    def generate_heatmap_data(self, db_path: str, crime_type: str = None,
                              district_id: int = None, grid_size: int = 50) -> list:
        """Generate KDE-based heatmap intensity grid.

        Returns list of {lat, lng, intensity} points for Leaflet heatmap.
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = """
            SELECT f.latitude, f.longitude
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            WHERE 1=1
        """
        params = []
        if crime_type:
            query += " AND ? IN (c.crime_type, c.description)"
            params.append(crime_type)
        if district_id:
            query += " AND f.district_id = ?"
            params.append(district_id)

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        if len(rows) < 5:
            return []

        lats = np.array([r[0] for r in rows])
        lngs = np.array([r[1] for r in rows])

        # Build KDE
        try:
            kde = gaussian_kde(np.vstack([lats, lngs]), bw_method=self.bandwidth)
        except np.linalg.LinAlgError:
            return []

        # Generate grid
        lat_grid = np.linspace(lats.min() - 0.05, lats.max() + 0.05, grid_size)
        lng_grid = np.linspace(lngs.min() - 0.05, lngs.max() + 0.05, grid_size)

        heatmap_points = []
        for lat in lat_grid:
            for lng in lng_grid:
                density_val = kde(np.array([[lat], [lng]]))
                density = float(np.asarray(density_val).flatten()[0])
                if density > 0.001:
                    heatmap_points.append({
                        "lat": round(float(lat), 6),
                        "lng": round(float(lng), 6),
                        "intensity": round(density, 6),
                    })

        # Normalize intensities 0–1
        if heatmap_points:
            max_intensity = max(p["intensity"] for p in heatmap_points)
            if max_intensity > 0:
                for p in heatmap_points:
                    p["intensity"] = round(p["intensity"] / max_intensity, 4)

        return heatmap_points

    def get_crime_points(self, db_path: str, crime_type: str = None,
                         district_id: int = None, limit: int = 5000) -> list:
        """Get raw crime coordinate points for map overlay."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT f.latitude, f.longitude, f.fir_number, f.date_of_crime,
                   f.time_of_crime, c.crime_type, c.section, c.act_name,
                   c.severity, d.name as district_name, ps.name as station_name
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            JOIN districts d ON f.district_id = d.id
            JOIN police_stations ps ON f.police_station_id = ps.id
            WHERE 1=1
        """
        params = []
        if crime_type:
            query += " AND ? IN (c.crime_type, c.description)"
            params.append(crime_type)
        if district_id:
            query += " AND f.district_id = ?"
            params.append(district_id)

        query += f" ORDER BY f.date_of_crime DESC LIMIT {limit}"

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        return [dict(r) for r in rows]


# Singleton
hotspot_detector = HotspotDetector()
