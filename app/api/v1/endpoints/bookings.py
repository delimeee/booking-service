from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import BookingCreate, BookingRead
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/availability", response_model=list[dict])
def get_availability(
    date: date,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list:
    return BookingService(db).get_availability(date)


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BookingService(db).create_booking(current_user, data)


@router.get("", response_model=list[BookingRead])
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    return BookingService(db).get_user_bookings(current_user)


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.exceptions import ForbiddenException
    from app.models.models import UserRole

    svc = BookingService(db)
    booking = svc.get_booking_by_id(booking_id)
    if current_user.role == UserRole.employee and booking.user_id != current_user.id:
        raise ForbiddenException("Access to this booking is not allowed")
    return booking


@router.delete("/{booking_id}", response_model=BookingRead)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BookingService(db).cancel_booking(booking_id, current_user)
