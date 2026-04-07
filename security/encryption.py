"""
CCTNS-GridX — Encryption Module
AES-256 encryption for sensitive FIR data & bcrypt password hashing
"""

import bcrypt
import base64
import os
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _get_fernet():
    """Derive a Fernet key from the AES_KEY config."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"cctns_gridx_salt_v1",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(config.AES_KEY.encode()))
    return Fernet(key)


def encrypt_data(plaintext: str) -> str:
    """Encrypt sensitive data using Fernet (AES-128-CBC under the hood)."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_data(ciphertext: str) -> str:
    """Decrypt encrypted data."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=config.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_fir_number(district_code: str, station_id: int, year: int, sequence: int) -> str:
    """Generate a standardized FIR number.
    Format: TN/[DISTRICT_CODE]/[STATION_ID]/[YEAR]/[SEQUENCE]
    """
    return f"TN/{district_code}/{station_id:03d}/{year}/{sequence:04d}"
