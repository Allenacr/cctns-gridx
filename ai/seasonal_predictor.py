"""
CCTNS-GridX — Seasonal Crime Predictor
Time series decomposition and linear regression for monthly crime forecasting.
"""

import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class SeasonalPredictor:
    """Predicts future crime trends using seasonal decomposition."""

    def _decompose_seasonal(self, monthly_counts: list) -> dict:
        """Simple seasonal decomposition (additive model).

        Decomposes into trend + seasonal + residual.
        """
        n = len(monthly_counts)
        if n < 12:
            return {"trend": monthly_counts, "seasonal": [0] * n, "residual": [0] * n}

        data = np.array(monthly_counts, dtype=float)

        # Trend: 3-month moving average
        trend = np.convolve(data, np.ones(3) / 3, mode="same")
        trend[0] = data[0]
        trend[-1] = data[-1]

        # Seasonal component: average deviation per month position
        detrended = data - trend
        period = 12
        seasonal = np.zeros(n)
        for i in range(period):
            indices = list(range(i, n, period))
            seasonal_val = np.mean([detrended[j] for j in indices])
            for j in indices:
                seasonal[j] = seasonal_val

        # Residual
        residual = data - trend - seasonal

        return {
            "trend": [round(float(x), 2) for x in trend],
            "seasonal": [round(float(x), 2) for x in seasonal],
            "residual": [round(float(x), 2) for x in residual],
        }

    def forecast_monthly(self, db_path: str, months_ahead: int = 6,
                         district_id: int = None, crime_type: str = None) -> dict:
        """Forecast crime counts for the next N months."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = """
            SELECT strftime('%Y-%m', f.date_of_crime) as month, COUNT(*) as count
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
            WHERE f.date_of_crime IS NOT NULL
        """
        params = []
        if district_id:
            query += " AND f.district_id = ?"
            params.append(district_id)
        if crime_type:
            query += " AND ? IN (c.crime_type, c.description)"
            params.append(crime_type)

        query += " GROUP BY month ORDER BY month"
        rows = cursor.execute(query, params).fetchall()
        conn.close()

        if len(rows) < 6:
            return {"error": "Insufficient historical data for forecasting"}

        months = [r[0] for r in rows]
        counts = [r[1] for r in rows]

        # Decompose
        decomposition = self._decompose_seasonal(counts)

        # Simple linear regression on trend for forecasting
        x = np.arange(len(counts))
        trend = np.array(decomposition["trend"])
        seasonal = np.array(decomposition["seasonal"])

        # Fit linear trend
        coeffs = np.polyfit(x, trend, 1)
        slope, intercept = coeffs

        # Generate future months
        forecasts = []
        last_month = datetime.strptime(months[-1], "%Y-%m")

        for i in range(1, months_ahead + 1):
            future_x = len(counts) + i - 1
            trend_val = slope * future_x + intercept
            seasonal_idx = (len(counts) + i - 1) % min(12, len(seasonal))
            seasonal_val = seasonal[seasonal_idx] if seasonal_idx < len(seasonal) else 0
            predicted = max(0, round(trend_val + seasonal_val))

            # Calculate confidence interval
            residual_std = np.std(decomposition["residual"])
            ci_lower = max(0, round(predicted - 1.96 * residual_std))
            ci_upper = round(predicted + 1.96 * residual_std)

            # Generate month label
            future_month_num = (last_month.month + i - 1) % 12 + 1
            future_year = last_month.year + (last_month.month + i - 1) // 12
            month_label = f"{future_year}-{future_month_num:02d}"

            forecasts.append({
                "month": month_label,
                "predicted_count": predicted,
                "confidence_interval": [ci_lower, ci_upper],
                "trend_component": round(float(trend_val), 2),
                "seasonal_component": round(float(seasonal_val), 2),
            })

        # Trend direction
        if slope > 0.5:
            trend_direction = "Increasing"
        elif slope < -0.5:
            trend_direction = "Decreasing"
        else:
            trend_direction = "Stable"

        return {
            "historical": {
                "months": months,
                "counts": counts,
                "decomposition": decomposition,
            },
            "forecasts": forecasts,
            "trend_direction": trend_direction,
            "trend_slope": round(float(slope), 4),
            "avg_monthly_count": round(float(np.mean(counts)), 1),
            "total_historical_crimes": sum(counts),
        }

    def get_seasonal_risk_map(self, db_path: str, target_month: int) -> dict:
        """Get district-level risk scores for a given month.

        Returns risk levels for each district based on historical data.
        """
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute("""
            SELECT d.id, d.name, d.lat, d.lng, COUNT(*) as total,
                   SUM(CASE WHEN CAST(strftime('%m', f.date_of_crime) AS INTEGER) = ? THEN 1 ELSE 0 END) as month_count
            FROM fir_records f
            JOIN districts d ON f.district_id = d.id
            WHERE f.date_of_crime IS NOT NULL
            GROUP BY d.id
        """, (target_month,)).fetchall()
        conn.close()

        results = []
        max_count = max(r["month_count"] for r in rows) if rows else 1

        for r in rows:
            risk_score = round(r["month_count"] / max(max_count, 1), 3)
            if risk_score >= 0.75:
                risk_level = "Critical"
            elif risk_score >= 0.5:
                risk_level = "High"
            elif risk_score >= 0.25:
                risk_level = "Medium"
            else:
                risk_level = "Low"

            results.append({
                "district_id": r["id"],
                "district_name": r["name"],
                "lat": r["lat"],
                "lng": r["lng"],
                "total_crimes": r["total"],
                "month_crimes": r["month_count"],
                "risk_score": risk_score,
                "risk_level": risk_level,
            })

        results.sort(key=lambda x: x["risk_score"], reverse=True)
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]

        return {
            "target_month": month_names[target_month] if 1 <= target_month <= 12 else "Unknown",
            "district_risks": results,
        }


# Singleton
seasonal_predictor = SeasonalPredictor()
