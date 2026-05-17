"""
database.py — Async MongoDB operations via Motor for Kerala Blood Connect Bot
All DB queries are centralised here to keep handlers clean.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT

from config import config

logger = logging.getLogger(__name__)


class Database:
    """Wrapper around Motor async MongoDB client."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    # ── Connection ────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        logger.info("Connecting to MongoDB…")
        self.client = AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        await self._ensure_indexes()
        logger.info("MongoDB connected ✅")

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected.")

    async def _ensure_indexes(self) -> None:
        """Create indexes for fast lookups."""
        users = self.db[config.USERS_COLLECTION]
        await users.create_index("telegram_id", unique=True)
        await users.create_index([("district", ASCENDING), ("blood_group", ASCENDING)])
        await users.create_index("available")

        emergency = self.db[config.EMERGENCY_COLLECTION]
        await emergency.create_index("created_at")
        await emergency.create_index([("blood_group", ASCENDING), ("district", ASCENDING)])

    # ── User helpers ──────────────────────────────────────────────────────────

    @property
    def users(self):
        return self.db[config.USERS_COLLECTION]

    @property
    def emergency(self):
        return self.db[config.EMERGENCY_COLLECTION]

    # ─────────────────────────────────────────────────────────────────────────
    # USER CRUD
    # ─────────────────────────────────────────────────────────────────────────

    async def get_user(self, telegram_id: int) -> Optional[dict]:
        return await self.users.find_one({"telegram_id": telegram_id})

    async def user_exists(self, telegram_id: int) -> bool:
        doc = await self.users.find_one({"telegram_id": telegram_id}, {"_id": 1})
        return doc is not None

    async def register_user(self, data: dict) -> None:
        """Insert or replace user document."""
        data["registered_date"] = datetime.now(timezone.utc)
        data["available"] = True
        await self.users.update_one(
            {"telegram_id": data["telegram_id"]},
            {"$set": data},
            upsert=True,
        )

    async def update_user(self, telegram_id: int, fields: dict) -> None:
        await self.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": fields},
        )

    async def toggle_availability(self, telegram_id: int) -> bool:
        """Flip available flag and return the NEW value."""
        user = await self.get_user(telegram_id)
        new_val = not user.get("available", True)
        await self.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"available": new_val}},
        )
        return new_val

    async def set_last_donation(self, telegram_id: int, date_str: str) -> None:
        await self.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"last_donation": date_str}},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # DONOR SEARCH
    # ─────────────────────────────────────────────────────────────────────────

    async def find_donors(
        self,
        blood_group: str,
        district: str,
        skip: int = 0,
        limit: int = 5,
    ) -> list[dict]:
        """Return paginated list of available donors."""
        cursor = (
            self.users.find(
                {
                    "blood_group": blood_group,
                    "district": district,
                    "available": True,
                },
                {
                    "full_name": 1,
                    "blood_group": 1,
                    "district": 1,
                    "area": 1,
                    "phone": 1,
                    "last_donation": 1,
                    "username": 1,
                },
            )
            .sort("registered_date", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def count_donors(self, blood_group: str, district: str) -> int:
        return await self.users.count_documents(
            {"blood_group": blood_group, "district": district, "available": True}
        )

    # ─────────────────────────────────────────────────────────────────────────
    # EMERGENCY REQUESTS
    # ─────────────────────────────────────────────────────────────────────────

    async def save_emergency(self, data: dict) -> str:
        data["created_at"] = datetime.now(timezone.utc)
        data["active"] = True
        result = await self.emergency.insert_one(data)
        return str(result.inserted_id)

    async def get_active_emergencies(self) -> list[dict]:
        cursor = self.emergency.find(
            {"active": True},
        ).sort("created_at", DESCENDING)
        return await cursor.to_list(length=50)

    async def delete_old_emergencies(self) -> int:
        """Auto-delete requests older than EMERGENCY_EXPIRY_HOURS."""
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=config.EMERGENCY_EXPIRY_HOURS
        )
        result = await self.emergency.delete_many({"created_at": {"$lt": cutoff}})
        return result.deleted_count

    # ─────────────────────────────────────────────────────────────────────────
    # ADMIN STATS
    # ─────────────────────────────────────────────────────────────────────────

    async def total_users(self) -> int:
        return await self.users.count_documents({})

    async def total_available_donors(self) -> int:
        return await self.users.count_documents({"available": True})

    async def district_stats(self) -> list[dict]:
        pipeline = [
            {"$group": {"_id": "$district", "total": {"$sum": 1},
                        "available": {"$sum": {"$cond": ["$available", 1, 0]}}}},
            {"$sort": {"total": DESCENDING}},
        ]
        return await self.users.aggregate(pipeline).to_list(length=20)

    async def blood_group_stats(self) -> list[dict]:
        pipeline = [
            {"$group": {"_id": "$blood_group", "total": {"$sum": 1}}},
            {"$sort": {"total": DESCENDING}},
        ]
        return await self.users.aggregate(pipeline).to_list(length=10)

    async def all_users_ids(self) -> list[int]:
        cursor = self.users.find({}, {"telegram_id": 1})
        docs = await cursor.to_list(length=100_000)
        return [d["telegram_id"] for d in docs]

    async def donors_due_for_reminder(self) -> list[dict]:
        """Users whose last donation was ≥ 90 days ago."""
        cutoff_str = (
            datetime.now(timezone.utc) - timedelta(days=config.DONATION_COOLDOWN_DAYS)
        ).strftime("%Y-%m-%d")
        cursor = self.users.find(
            {"last_donation": {"$lte": cutoff_str}, "available": False}
        )
        return await cursor.to_list(length=10_000)

    async def remove_user(self, telegram_id: int) -> bool:
        result = await self.users.delete_one({"telegram_id": telegram_id})
        return result.deleted_count > 0

    async def export_donors(self) -> list[dict]:
        cursor = self.users.find(
            {"available": True},
            {"_id": 0, "full_name": 1, "phone": 1, "blood_group": 1,
             "district": 1, "area": 1, "last_donation": 1},
        ).sort("district", ASCENDING)
        return await cursor.to_list(length=10_000)


# Singleton instance used throughout the project
db = Database()
