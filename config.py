"""
config.py — Environment configuration for Kerala Blood Connect Bot
Loads all settings from .env file using python-dotenv
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str
    MONGO_URI: str
    ADMIN_IDS: list[int]
    DB_NAME: str = "kerala_blood_bot"
    USERS_COLLECTION: str = "users"
    EMERGENCY_COLLECTION: str = "emergency_requests"
    BROADCAST_DELAY: float = 0.05          # seconds between each message in broadcast
    EMERGENCY_EXPIRY_HOURS: int = 48       # auto-delete emergency requests after N hours
    DONATION_COOLDOWN_DAYS: int = 90       # 3-month reminder threshold
    MAX_DONORS_PER_PAGE: int = 5           # pagination: donors shown per page
    RATE_LIMIT_SECONDS: int = 2            # seconds between allowed user actions


def _load_admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_ID", "")
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


config = Config(
    BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
    MONGO_URI=os.getenv("MONGO_URI", ""),
    ADMIN_IDS=_load_admin_ids(),
)

# ── Kerala districts ──────────────────────────────────────────────────────────
KERALA_DISTRICTS = [
    "Thiruvananthapuram",
    "Kollam",
    "Pathanamthitta",
    "Alappuzha",
    "Kottayam",
    "Idukki",
    "Ernakulam",
    "Thrissur",
    "Palakkad",
    "Malappuram",
    "Kozhikode",
    "Wayanad",
    "Kannur",
    "Kasaragod",
]

# ── Blood groups ──────────────────────────────────────────────────────────────
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# ── Urgency levels for emergency requests ────────────────────────────────────
URGENCY_LEVELS = ["🔴 Critical", "🟠 Urgent", "🟡 Moderate"]
