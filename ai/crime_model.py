"""
CCTNS-GridX — Crime Prediction Model
Random Forest Classifier for crime type prediction based on
location, time, demographics, and seasonal features.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import sqlite3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class CrimePredictionModel:
    """Random Forest based crime type predictor."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=config.RF_N_ESTIMATORS,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        )
        self.label_encoder = LabelEncoder()
        self.is_trained = False

    def _extract_features(self, records):
        """Extract features from FIR records for ML model.

        Features:
        - latitude, longitude
        - hour_of_day (0-23)
        - day_of_week (0-6)
        - month (1-12)
        - is_weekend (0/1)
        - is_night (0/1)  [22:00-06:00]
        - district_id
        - severity
        """
        features = []
        for r in records:
            lat = r["latitude"]
            lng = r["longitude"]
            hour = int(r.get("time_of_crime", "12:00").split(":")[0]) if r.get("time_of_crime") else 12
            date_str = r.get("date_of_crime", "2024-06-15")
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dow = dt.weekday()
                month = dt.month
            except (ValueError, TypeError):
                dow = 0
                month = 6

            is_weekend = 1 if dow >= 5 else 0
            is_night = 1 if hour >= 22 or hour <= 6 else 0
            district = r.get("district_id", 1)

            features.append([lat, lng, hour, dow, month, is_weekend, is_night, district])

        return np.array(features)

    def train(self, db_path: str):
        """Train the model on existing FIR data."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        rows = cursor.execute("""
            SELECT f.latitude, f.longitude, f.time_of_crime, f.date_of_crime,
                   f.district_id, c.crime_type, c.severity
            FROM fir_records f
            JOIN crime_categories c ON f.crime_category_id = c.id
        """).fetchall()
        conn.close()

        if len(rows) < 10:
            print("  [!] Not enough data to train crime prediction model")
            return

        records = [dict(r) for r in rows]
        X = self._extract_features(records)
        y = [r["crime_type"] for r in records]

        self.label_encoder.fit(y)
        y_encoded = self.label_encoder.transform(y)

        self.model.fit(X, y_encoded)
        self.is_trained = True

        accuracy = self.model.score(X, y_encoded)
        print(f"  [OK] Crime prediction model trained - accuracy: {accuracy:.2%}")

    def predict(self, latitude: float, longitude: float, hour: int, day_of_week: int,
                month: int, district_id: int) -> dict:
        """Predict crime type probabilities for given parameters."""
        if not self.is_trained:
            return {"error": "Model not trained"}

        is_weekend = 1 if day_of_week >= 5 else 0
        is_night = 1 if hour >= 22 or hour <= 6 else 0

        features = np.array([[latitude, longitude, hour, day_of_week, month,
                              is_weekend, is_night, district_id]])

        probabilities = self.model.predict_proba(features)[0]
        classes = self.label_encoder.classes_

        results = []
        for cls, prob in zip(classes, probabilities):
            results.append({"crime_type": cls, "probability": round(float(prob), 4)})

        results.sort(key=lambda x: x["probability"], reverse=True)

        return {
            "prediction": results[0]["crime_type"],
            "confidence": results[0]["probability"],
            "all_probabilities": results[:5],
            "features_used": {
                "latitude": latitude,
                "longitude": longitude,
                "hour": hour,
                "day_of_week": day_of_week,
                "month": month,
                "is_weekend": bool(is_weekend),
                "is_night": bool(is_night),
                "district_id": district_id,
            },
        }

    def get_feature_importance(self) -> list:
        """Get feature importance ranking."""
        if not self.is_trained:
            return []

        feature_names = [
            "latitude", "longitude", "hour", "day_of_week",
            "month", "is_weekend", "is_night", "district_id",
        ]
        importances = self.model.feature_importances_
        result = []
        for name, imp in zip(feature_names, importances):
            result.append({"feature": name, "importance": round(float(imp), 4)})
        result.sort(key=lambda x: x["importance"], reverse=True)
        return result


# Singleton instance
crime_model = CrimePredictionModel()
