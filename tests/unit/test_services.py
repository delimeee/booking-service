import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.session import Base
from app.models.models import Room, TimeSlot, User, UserRole
from app.schemas.schemas import BookingCreate, RoomCreate, TimeSlotCreate, UserCreate
from app.services.booking_service import BookingService
from app.services.room_service import RoomService
from app.services.user_service import UserService
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException

import datetime

TEST_URL = "sqlite:///:memory:"


@pytest.fixture
def db():
    engine = create_engine(TEST_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_user(db):
    user = User(username="admin", hashed_password=hash_password("pass"), role=UserRole.admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def employee_user(db):
    user = User(username="emp", hashed_password=hash_password("pass"), role=UserRole.employee)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def room_with_slot(db):
    room = Room(name="Test Room", capacity=4)
    db.add(room)
    db.flush()
    slot = TimeSlot(room_id=room.id, start_time="09:00", end_time="11:00")
    db.add(slot)
    db.commit()
    db.refresh(room)
    return room


# ── UserService ───────────────────────────────────────────────────────────────

class TestUserService:
    def test_create_user(self, db):
        svc = UserService(db)
        user = svc.create(UserCreate(username="alice", password="pw123"))
        assert user.id is not None
        assert user.username == "alice"
        assert user.role == UserRole.employee

    def test_authenticate_valid(self, db):
        svc = UserService(db)
        svc.create(UserCreate(username="bob", password="secret"))
        assert svc.authenticate("bob", "secret") is not None

    def test_authenticate_wrong_password(self, db):
        svc = UserService(db)
        svc.create(UserCreate(username="carol", password="correct"))
        assert svc.authenticate("carol", "wrong") is None

    def test_get_nonexistent_user(self, db):
        assert UserService(db).get_by_id(9999) is None


# ── RoomService ───────────────────────────────────────────────────────────────

class TestRoomService:
    def test_create_room(self, db):
        svc = RoomService(db)
        room = svc.create(RoomCreate(name="Alpha", capacity=6))
        assert room.id is not None

    def test_duplicate_room_raises_conflict(self, db):
        svc = RoomService(db)
        svc.create(RoomCreate(name="Beta"))
        with pytest.raises(ConflictException):
            svc.create(RoomCreate(name="Beta"))

    def test_get_nonexistent_room_raises(self, db):
        with pytest.raises(NotFoundException):
            RoomService(db).get_by_id(999)

    def test_add_slot(self, db):
        svc = RoomService(db)
        room = svc.create(RoomCreate(name="Gamma"))
        slot = svc.add_slot(room.id, TimeSlotCreate(start_time="10:00", end_time="12:00"))
        assert slot.id is not None
        assert slot.room_id == room.id

    def test_duplicate_slot_raises_conflict(self, db):
        svc = RoomService(db)
        room = svc.create(RoomCreate(name="Delta"))
        svc.add_slot(room.id, TimeSlotCreate(start_time="10:00", end_time="12:00"))
        with pytest.raises(ConflictException):
            svc.add_slot(room.id, TimeSlotCreate(start_time="10:00", end_time="12:00"))


# ── BookingService ────────────────────────────────────────────────────────────

class TestBookingService:
    def test_create_booking(self, db, employee_user, room_with_slot):
        svc = BookingService(db)
        slot = room_with_slot.slots[0]
        booking = svc.create_booking(
            employee_user,
            BookingCreate(
                room_id=room_with_slot.id,
                slot_id=slot.id,
                date=datetime.date(2030, 1, 15),
            ),
        )
        assert booking.id is not None
        assert booking.user_id == employee_user.id

    def test_double_booking_raises_conflict(self, db, employee_user, room_with_slot):
        svc = BookingService(db)
        slot = room_with_slot.slots[0]
        data = BookingCreate(
            room_id=room_with_slot.id,
            slot_id=slot.id,
            date=datetime.date(2030, 1, 15),
        )
        svc.create_booking(employee_user, data)
        with pytest.raises(ConflictException):
            svc.create_booking(employee_user, data)

    def test_employee_cannot_cancel_others_booking(
        self, db, admin_user, employee_user, room_with_slot
    ):
        svc = BookingService(db)
        slot = room_with_slot.slots[0]
        booking = svc.create_booking(
            admin_user,
            BookingCreate(
                room_id=room_with_slot.id,
                slot_id=slot.id,
                date=datetime.date(2030, 3, 10),
            ),
        )
        with pytest.raises(ForbiddenException):
            svc.cancel_booking(booking.id, employee_user)

    def test_admin_can_cancel_any_booking(self, db, admin_user, employee_user, room_with_slot):
        svc = BookingService(db)
        slot = room_with_slot.slots[0]
        booking = svc.create_booking(
            employee_user,
            BookingCreate(
                room_id=room_with_slot.id,
                slot_id=slot.id,
                date=datetime.date(2030, 4, 1),
            ),
        )
        cancelled = svc.cancel_booking(booking.id, admin_user)
        from app.models.models import BookingStatus
        assert cancelled.status == BookingStatus.cancelled

    def test_cancel_already_cancelled_raises(self, db, employee_user, room_with_slot):
        svc = BookingService(db)
        slot = room_with_slot.slots[0]
        booking = svc.create_booking(
            employee_user,
            BookingCreate(
                room_id=room_with_slot.id,
                slot_id=slot.id,
                date=datetime.date(2030, 5, 5),
            ),
        )
        svc.cancel_booking(booking.id, employee_user)
        with pytest.raises(ConflictException):
            svc.cancel_booking(booking.id, employee_user)
