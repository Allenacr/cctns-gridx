"""
CCTNS-GridX — Behavioral Analysis Engine
Time series pattern detection, seasonal analysis, and criminal behavior profiling.
"""

import numpy as np
import sqlite3
import json
from collections import Counter, defaultdict
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class BehavioralEngine:
    """Analyzes criminal behavior patterns across time, location, and demographics."""

    def get_temporal_patterns(self, db_path: str, crime_type: str = None,
                              district_id: int = None) -> dict:
        """Analyze hourly, daily, and monthly crime distribution patterns."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT f.time_of_crime, f.date_of_crime, c.crime_type
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            WHERE f.time_of_crime IS NOT NULL
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

        hourly = [0] * 24
        daily = [0] * 7  # Mon=0, Sun=6
        monthly = [0] * 12

        for r in rows:
            try:
                hour = int(r["time_of_crime"].split(":")[0])
                hourly[hour] += 1
            except (ValueError, AttributeError, IndexError):
                pass

            try:
                dt = datetime.strptime(r["date_of_crime"], "%Y-%m-%d")
                daily[dt.weekday()] += 1
                monthly[dt.month - 1] += 1
            except (ValueError, AttributeError):
                pass

        # Peak detection
        peak_hour = int(np.argmax(hourly))
        peak_day = int(np.argmax(daily))
        peak_month = int(np.argmax(monthly))

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        return {
            "hourly_distribution": hourly,
            "daily_distribution": daily,
            "monthly_distribution": monthly,
            "peak_hour": peak_hour,
            "peak_hour_label": f"{peak_hour:02d}:00 - {(peak_hour + 1) % 24:02d}:00",
            "peak_day": day_names[peak_day],
            "peak_month": month_names[peak_month],
            "total_analyzed": len(rows),
            "night_crime_pct": round(sum(hourly[22:] + hourly[:6]) / max(sum(hourly), 1) * 100, 1),
            "weekend_crime_pct": round(sum(daily[5:]) / max(sum(daily), 1) * 100, 1),
        }

    def get_seasonal_analysis(self, db_path: str, district_id: int = None) -> dict:
        """Analyze seasonal crime patterns (Summer, Monsoon, Winter, Festival)."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT f.date_of_crime, c.crime_type, c.severity
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            WHERE f.date_of_crime IS NOT NULL
        """
        params = []
        if district_id:
            query += " AND f.district_id = ?"
            params.append(district_id)

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        def _get_season(month):
            if month in (3, 4, 5, 6):
                return "Summer"
            elif month in (7, 8, 9, 10):
                return "Monsoon"
            elif month in (11, 12, 1, 2):
                return "Winter"
            return "General"

        seasonal = defaultdict(lambda: {"total": 0, "crimes": Counter()})
        festival_months = {1: "Pongal", 4: "Tamil New Year", 8: "Krishna Jayanthi",
                           10: "Navaratri/Dussehra", 11: "Deepavali", 12: "Christmas"}

        for r in rows:
            try:
                dt = datetime.strptime(r["date_of_crime"], "%Y-%m-%d")
                season = _get_season(dt.month)
                seasonal[season]["total"] += 1
                seasonal[season]["crimes"][r["crime_type"]] += 1

                if dt.month in festival_months:
                    seasonal["Festival"]["total"] += 1
                    seasonal["Festival"]["crimes"][r["crime_type"]] += 1
            except (ValueError, AttributeError):
                pass

        result = {}
        for season, data in seasonal.items():
            top_crimes = data["crimes"].most_common(5)
            result[season] = {
                "total_crimes": data["total"],
                "top_crimes": [{"type": c[0], "count": c[1]} for c in top_crimes],
                "dominant_crime": top_crimes[0][0] if top_crimes else "N/A",
            }

        # Find most dangerous season
        if result:
            most_dangerous = max(result.items(), key=lambda x: x[1]["total_crimes"])
            safest = min(result.items(), key=lambda x: x[1]["total_crimes"])
        else:
            most_dangerous = ("N/A", {"total_crimes": 0})
            safest = ("N/A", {"total_crimes": 0})

        return {
            "seasonal_data": result,
            "most_dangerous_season": most_dangerous[0],
            "safest_season": safest[0],
            "festival_months": festival_months,
        }

    def get_demographic_patterns(self, db_path: str, crime_type: str = None) -> dict:
        """Analyze accused/victim demographics."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT f.accused_age, f.accused_gender, f.victim_age, f.victim_gender,
                   c.crime_type, d.name as district_name
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            JOIN districts d ON f.district_id = d.id
            WHERE 1=1
        """
        params = []
        if crime_type:
            query += " AND ? IN (c.crime_type, c.description)"
            params.append(crime_type)

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        accused_ages = [r["accused_age"] for r in rows if r["accused_age"]]
        victim_ages = [r["victim_age"] for r in rows if r["victim_age"]]
        accused_genders = Counter(r["accused_gender"] for r in rows if r["accused_gender"])
        victim_genders = Counter(r["victim_gender"] for r in rows if r["victim_gender"])

        # Age group distribution
        age_groups = {"<18": 0, "18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "55+": 0}
        for age in accused_ages:
            if age < 18:
                age_groups["<18"] += 1
            elif age <= 25:
                age_groups["18-25"] += 1
            elif age <= 35:
                age_groups["26-35"] += 1
            elif age <= 45:
                age_groups["36-45"] += 1
            elif age <= 55:
                age_groups["46-55"] += 1
            else:
                age_groups["55+"] += 1

        return {
            "accused": {
                "avg_age": round(np.mean(accused_ages), 1) if accused_ages else 0,
                "gender_distribution": dict(accused_genders),
                "age_groups": age_groups,
            },
            "victim": {
                "avg_age": round(np.mean(victim_ages), 1) if victim_ages else 0,
                "gender_distribution": dict(victim_genders),
            },
            "total_records": len(rows),
        }

    def get_crime_type_trends(self, db_path: str, district_id: int = None) -> dict:
        """Get crime type distribution and year-over-year trends."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT c.crime_type, f.date_of_crime, c.severity
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            WHERE f.date_of_crime IS NOT NULL
        """
        params = []
        if district_id:
            query += " AND f.district_id = ?"
            params.append(district_id)

        rows = cursor.execute(query, params).fetchall()
        conn.close()

        type_counts = Counter()
        yearly_trends = defaultdict(lambda: Counter())

        for r in rows:
            type_counts[r["crime_type"]] += 1
            try:
                year = datetime.strptime(r["date_of_crime"], "%Y-%m-%d").year
                yearly_trends[year][r["crime_type"]] += 1
            except (ValueError, AttributeError):
                pass

        # Year-over-year change
        years = sorted(yearly_trends.keys())
        yoy_changes = {}
        if len(years) >= 2:
            for ct in type_counts:
                prev = yearly_trends[years[-2]].get(ct, 0)
                curr = yearly_trends[years[-1]].get(ct, 0)
                if prev > 0:
                    change = round((curr - prev) / prev * 100, 1)
                else:
                    change = 100.0 if curr > 0 else 0.0
                yoy_changes[ct] = change

        return {
            "crime_type_distribution": dict(type_counts.most_common()),
            "yearly_trends": {str(y): dict(c) for y, c in yearly_trends.items()},
            "yoy_changes": yoy_changes,
            "total_crimes": sum(type_counts.values()),
        }

    def get_repeat_offender_analysis(self, db_path: str) -> dict:
        """Analyze patterns of repeat offending."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute("""
            SELECT accused_name, COUNT(*) as crime_count,
                   GROUP_CONCAT(DISTINCT c.crime_type) as crime_types,
                   GROUP_CONCAT(DISTINCT d.name) as districts,
                   MIN(f.date_of_crime) as first_crime,
                   MAX(f.date_of_crime) as last_crime
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            JOIN districts d ON f.district_id = d.id
            WHERE f.accused_name IS NOT NULL
            GROUP BY f.accused_name
            HAVING COUNT(*) > 1
            ORDER BY crime_count DESC
            LIMIT 50
        """).fetchall()
        conn.close()

        repeat_offenders = []
        for r in rows:
            repeat_offenders.append({
                "name": r["accused_name"],
                "crime_count": r["crime_count"],
                "crime_types": r["crime_types"].split(",") if r["crime_types"] else [],
                "districts": r["districts"].split(",") if r["districts"] else [],
                "first_crime": r["first_crime"],
                "last_crime": r["last_crime"],
            })

        return {
            "repeat_offenders": repeat_offenders,
            "total_repeat_offenders": len(repeat_offenders),
            "avg_crimes_per_offender": round(
                np.mean([r["crime_count"] for r in repeat_offenders]), 1
            ) if repeat_offenders else 0,
        }


# Singleton
behavioral_engine = BehavioralEngine()
