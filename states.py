"""
states.py — Finite State Machine state groups for aiogram 3
Each StatesGroup represents one multi-step conversation flow.
"""

from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    """Step-by-step donor registration."""
    waiting_name = State()
    waiting_phone = State()
    waiting_blood_group = State()
    waiting_district = State()
    waiting_area = State()
    waiting_last_donation = State()


class SearchStates(StatesGroup):
    """Two-step donor search: blood group → district."""
    waiting_blood_group = State()
    waiting_district = State()
    viewing_results = State()


class EmergencyStates(StatesGroup):
    """Multi-step emergency blood request submission."""
    waiting_patient_name = State()
    waiting_blood_group = State()
    waiting_district = State()
    waiting_hospital = State()
    waiting_contact = State()
    waiting_urgency = State()


class ProfileUpdateStates(StatesGroup):
    """Allow user to update individual profile fields."""
    choose_field = State()
    waiting_new_name = State()
    waiting_new_phone = State()
    waiting_new_area = State()
    waiting_new_last_donation = State()


class AdminStates(StatesGroup):
    """Admin broadcast & remove-user flows."""
    waiting_broadcast_message = State()
    waiting_remove_user_id = State()
