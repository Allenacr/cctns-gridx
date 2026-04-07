"""
CCTNS-GridX Configuration
Central configuration for the Crime Predictive Model & Hotspot Mapping Platform
Tamil Nadu Police — Government of Tamil Nadu
"""

import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Database ───────────────────────────────────────────────
DATABASE_PATH = os.path.join(BASE_DIR, "database", "cctns_gridx.db")

# ─── Server ─────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 8000
DEBUG = True

# ─── Security ───────────────────────────────────────────────
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24
BCRYPT_ROUNDS = 12
AES_KEY = os.environ.get("AES_KEY", secrets.token_hex(16))  # 256-bit

# ─── CORS ───────────────────────────────────────────────────
CORS_ORIGINS = ["*"]

# ─── AI Model Params ────────────────────────────────────────
DBSCAN_EPS = 0.005          # ~0.5 km radius for hotspot clustering
DBSCAN_MIN_SAMPLES = 5      # Minimum crimes for a hotspot
KDE_BANDWIDTH = 0.01        # Kernel density estimation bandwidth
RF_N_ESTIMATORS = 100       # Random Forest trees
ISOLATION_CONTAMINATION = 0.1  # Anomaly detection threshold

# ─── Tamil Nadu Bounds ──────────────────────────────────────
TN_LAT_MIN = 8.0
TN_LAT_MAX = 13.5
TN_LNG_MIN = 76.0
TN_LNG_MAX = 80.5
TN_CENTER_LAT = 10.85
TN_CENTER_LNG = 78.65

# ─── Roles ──────────────────────────────────────────────────
ROLES = {
    "SP": "Superintendent of Police",
    "DSP": "Deputy Superintendent of Police",
    "SHO": "Station House Officer",
    "SI": "Sub Inspector",
    "CONSTABLE": "Constable",
}

# ─── Logging ────────────────────────────────────────────────
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(BASE_DIR, "cctns_gridx.log")
