from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import RoomCreate, RoomRead, TimeSlotCreate, TimeSlotRead
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
def list_rooms(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list:
    return RoomService(db).list_rooms()


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    data: RoomCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return RoomService(db).create(data)


@router.get("/{room_id}", response_model=RoomRead)
def get_room(
    room_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return RoomService(db).get_by_id(room_id)


@router.post("/{room_id}/slots", response_model=TimeSlotRead, status_code=status.HTTP_201_CREATED)
def add_slot(
    room_id: int,
    data: TimeSlotCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return RoomService(db).add_slot(room_id, data)
