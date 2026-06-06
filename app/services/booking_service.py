from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.models import Booking, BookingStatus, Room, TimeSlot, User, UserRole
from app.schemas.schemas import BookingCreate


class BookingService:
    def __init__(self, db: Session):
        self.db = db

    def get_availability(self, target_date: date) -> list[dict]:
        rooms = self.db.query(Room).all()
        result = []

        for room in rooms:
            slots_info = []
            for slot in room.slots:
                is_booked = (
                    self.db.query(Booking)
                    .filter(
                        Booking.slot_id == slot.id,
                        Booking.date == target_date,
                        Booking.status == BookingStatus.active,
                    )
                    .first()
                    is not None
                )
                slots_info.append(
                    {
                        "slot_id": slot.id,
                        "start_time": slot.start_time,
                        "end_time": slot.end_time,
                        "available": not is_booked,
                    }
                )

            result.append(
                {
                    "room_id": room.id,
                    "room_name": room.name,
                    "date": target_date,
                    "slots": slots_info,
                }
            )
        return result

    def create_booking(self, user: User, data: BookingCreate) -> Booking:
        # Validate slot belongs to room
        slot = (
            self.db.query(TimeSlot)
            .filter(TimeSlot.id == data.slot_id, TimeSlot.room_id == data.room_id)
            .first()
        )
        if not slot:
            raise NotFoundException("Slot not found for the specified room")

        # Check for conflicts
        conflict = (
            self.db.query(Booking)
            .filter(
                Booking.slot_id == data.slot_id,
                Booking.date == data.date,
                Booking.status == BookingStatus.active,
            )
            .first()
        )
        if conflict:
            raise ConflictException("This slot is already booked for the selected date")

        booking = Booking(
            user_id=user.id,
            room_id=data.room_id,
            slot_id=data.slot_id,
            date=data.date,
            status=BookingStatus.active,
        )
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get_user_bookings(self, user: User) -> list[Booking]:
        return (
            self.db.query(Booking)
            .filter(Booking.user_id == user.id)
            .all()
        )

    def get_booking_by_id(self, booking_id: int) -> Booking:
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise NotFoundException(f"Booking {booking_id} not found")
        return booking

    def cancel_booking(self, booking_id: int, current_user: User) -> Booking:
        booking = self.get_booking_by_id(booking_id)

        if booking.status == BookingStatus.cancelled:
            raise ConflictException("Booking is already cancelled")

        # Employees can only cancel their own bookings
        if current_user.role == UserRole.employee and booking.user_id != current_user.id:
            raise ForbiddenException("You can only cancel your own bookings")

        booking.status = BookingStatus.cancelled
        self.db.commit()
        self.db.refresh(booking)
        return booking
