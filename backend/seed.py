"""Standalone seed script. Idempotent — safe to re-run.

Run with:
    python seed.py
"""
from app import app
from extensions import db

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # ensure_seed() is invoked by create_app() at import time
        print("Seed complete.")
