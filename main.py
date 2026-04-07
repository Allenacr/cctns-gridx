"""
CCTNS-GridX - Master Controller
Initializes database, trains AI models, and starts the FastAPI server.
"""

import os
import sys
import webbrowser
import threading
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure project root is in path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import config


def print_banner():
    banner = r"""
  ____   ____ _____ _   _ ____         ____      _     ___  __
 / ___| / ___|_   _| \ | / ___|       / ___|_ __(_) __| \ \/ /
| |    | |     | | |  \| \___ \ _____| |  _| '__| |/ _` |\  /
| |___ | |___  | | | |\  |___) |_____| |_| | |  | | (_| |/  \
 \____| \____| |_| |_| \_|____/       \____|_|  |_|\__,_/_/\_\

    Crime Predictive Model & Hotspot Mapping Platform
    Tamil Nadu Police - Government of Tamil Nadu
    """
    print(banner)


def init_database():
    """Initialize and seed the database if needed."""
    print("[*] Database Initialization")
    db_exists = os.path.exists(config.DATABASE_PATH)

    if not db_exists:
        os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
        from database.seed_data import seed_database
        seed_database(config.DATABASE_PATH)
    else:
        print(f"  [OK] Database already exists at {config.DATABASE_PATH}")
        import sqlite3
        conn = sqlite3.connect(config.DATABASE_PATH)
        count = conn.execute("SELECT COUNT(*) FROM fir_records").fetchone()[0]
        conn.close()
        if count == 0:
            print("  [!] Database is empty, re-seeding...")
            from database.seed_data import seed_database
            seed_database(config.DATABASE_PATH)
        else:
            print(f"  [OK] Database has {count} FIR records")


def train_models():
    """Train AI prediction models."""
    print("\n[*] AI Model Training")
    try:
        from ai.crime_model import crime_model
        crime_model.train(config.DATABASE_PATH)
    except Exception as e:
        print(f"  [!] Crime model training warning: {e}")

    print("  [OK] AI models ready")


def open_browser():
    """Open browser after a short delay."""
    time.sleep(2)
    url = f"http://{config.HOST}:{config.PORT}"
    print(f"\n[*] Opening browser at {url}")
    webbrowser.open(url)


def main():
    """Main entry point."""
    print_banner()

    # Step 1: Initialize database
    init_database()

    # Step 2: Train AI models
    train_models()

    # Step 3: Open browser in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Step 4: Start FastAPI server
    print(f"\n[*] Starting Server")
    print(f"  Server:   http://{config.HOST}:{config.PORT}")
    print(f"  API Docs: http://{config.HOST}:{config.PORT}/api/docs")
    print(f"  ReDoc:    http://{config.HOST}:{config.PORT}/api/redoc")
    print(f"\n  Press Ctrl+C to stop the server\n")

    import uvicorn
    from backend.app import create_app

    app = create_app()
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
