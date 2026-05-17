"""
utils/validators.py — Input validation helpers for Kerala Blood Connect Bot
All functions return (is_valid: bool, error_msg: str | None).
"""

import re
from config import BLOOD_GROUPS, KERALA_DISTRICTS


def validate_name(name: str) -> tuple[bool, str | None]:
    """
    Name must be 2–60 characters, letters and spaces only.
    Accepts both Malayalam Unicode names and English names.
    """
    name = name.strip()
    if len(name) < 2:
        return False, "❌ Name is too short. Please enter at least 2 characters."
    if len(name) > 60:
        return False, "❌ Name is too long. Please keep it under 60 characters."
    # Allow Unicode letters (covers Malayalam) and spaces
    if not re.fullmatch(r"[\w\u0D00-\u0D7F\s'-]+", name, re.UNICODE):
        return False, "❌ Name contains invalid characters."
    return True, None


def validate_phone(phone: str) -> tuple[bool, str | None]:
    """
    Accept Indian mobile numbers.
    Formats: 9876543210 / +919876543210 / 919876543210
    Normalises to 10-digit local form.
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    # Strip country code
    if phone.startswith("+91"):
        phone = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    if not re.fullmatch(r"[6-9]\d{9}", phone):
        return False, (
            "❌ Invalid phone number.\n"
            "Please enter a valid 10-digit Indian mobile number.\n"
            "Example: 9876543210"
        )
    return True, None


def normalise_phone(phone: str) -> str:
    """Strip formatting and return bare 10-digit number."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+91"):
        phone = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    return phone


def validate_blood_group(bg: str) -> tuple[bool, str | None]:
    if bg not in BLOOD_GROUPS:
        return False, f"❌ Invalid blood group. Choose from: {', '.join(BLOOD_GROUPS)}"
    return True, None


def validate_district(district: str) -> tuple[bool, str | None]:
    if district not in KERALA_DISTRICTS:
        return False, "❌ Invalid district. Please choose from the list."
    return True, None


def validate_date(date_str: str) -> tuple[bool, str | None]:
    """
    Accept date in DD/MM/YYYY or YYYY-MM-DD format.
    Returns normalised YYYY-MM-DD string on success.
    """
    date_str = date_str.strip()
    # Try DD/MM/YYYY
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
            return True, f"{year:04d}-{month:02d}-{day:02d}"
        return False, "❌ Invalid date. Use DD/MM/YYYY format."
    # Try YYYY-MM-DD
    m2 = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_str)
    if m2:
        year, month, day = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2100:
            return True, f"{year:04d}-{month:02d}-{day:02d}"
    return False, "❌ Invalid date format.\nUse DD/MM/YYYY  e.g. 25/12/2023"


def validate_area(area: str) -> tuple[bool, str | None]:
    area = area.strip()
    if len(area) < 2:
        return False, "❌ Area name is too short."
    if len(area) > 100:
        return False, "❌ Area name is too long."
    return True, None


def escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters to prevent parse errors."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)
