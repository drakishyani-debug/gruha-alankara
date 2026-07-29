"""
config.py
---------
Central configuration for the Gruha Alankara Flask application.

ASSUMPTION: The original spec mentioned PostgreSQL in the architecture
diagram, but the "Pre-requisites" and "Milestone 2" sections explicitly
say SQLite for local development with no cloud infrastructure. We follow
the explicit written instructions (SQLite) since the app is designed to
run entirely locally.
"""

import os
from datetime import timedelta

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key used for session signing / CSRF-style protections.
    # In production, set the GRUHA_SECRET_KEY environment variable instead
    # of relying on the fallback value below.
    SECRET_KEY = os.environ.get("GRUHA_SECRET_KEY", "dev-secret-key-change-me")

    # SQLite database (single file, zero external services required)
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "designs.db")

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size

    # Session behaviour
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Supported languages for the multilingual voice "buddy" agent.
    # Codes follow BCP-47 so they map directly to the browser
    # SpeechRecognition / speechSynthesis APIs on the frontend.
    SUPPORTED_LANGUAGES = {
        "en": {"label": "English", "speech_code": "en-IN"},
        "hi": {"label": "Hindi", "speech_code": "hi-IN"},
        "te": {"label": "Telugu", "speech_code": "te-IN"},
    }

    # Default currency for budgeting tools
    CURRENCY_SYMBOL = "₹"
