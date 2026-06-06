from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.models import BookingStatus, UserRole


# ── Auth ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.employee


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRole
    is_active: bool


# ── TimeSlot ──────────────────────────────────────────────────────────────────

class TimeSlotCreate(BaseModel):
    start_time: str   # "HH:MM"
    end_time: str

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be in HH:MM format")
        h, m = parts
        if not (h.isdigit() and m.isdigit() and 0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("Invalid time value")
        return v


class TimeSlotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_time: str
    end_time: str


# ── Room ──────────────────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    name: str
    description: str | None = None
    capacity: int = 1


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    capacity: int
    slots: list[TimeSlotRead] = []


class RoomAvailability(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
    room_name: str
    date: date
    slots: list[dict]   # {slot_id, start_time, end_time, available: bool}


# ── Booking ───────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    room_id: int
    slot_id: int
    date: date


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    slot_id: int
    date: date
    status: BookingStatus
    user: UserRead
