from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.models import Room, TimeSlot
from app.schemas.schemas import RoomCreate, TimeSlotCreate


class RoomService:
    def __init__(self, db: Session):
        self.db = db

    def list_rooms(self) -> list[Room]:
        return self.db.query(Room).all()

    def get_by_id(self, room_id: int) -> Room:
        room = self.db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise NotFoundException(f"Room {room_id} not found")
        return room

    def create(self, data: RoomCreate) -> Room:
        if self.db.query(Room).filter(Room.name == data.name).first():
            raise ConflictException(f"Room with name '{data.name}' already exists")
        room = Room(**data.model_dump())
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def add_slot(self, room_id: int, data: TimeSlotCreate) -> TimeSlot:
        room = self.get_by_id(room_id)
        existing = (
            self.db.query(TimeSlot)
            .filter(
                TimeSlot.room_id == room_id,
                TimeSlot.start_time == data.start_time,
                TimeSlot.end_time == data.end_time,
            )
            .first()
        )
        if existing:
            raise ConflictException("This time slot already exists for the room")
        slot = TimeSlot(room_id=room.id, **data.model_dump())
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)
        return slot

    def get_slot(self, room_id: int, slot_id: int) -> TimeSlot:
        slot = (
            self.db.query(TimeSlot)
            .filter(TimeSlot.id == slot_id, TimeSlot.room_id == room_id)
            .first()
        )
        if not slot:
            raise NotFoundException(f"Slot {slot_id} not found for room {room_id}")
        return slot
