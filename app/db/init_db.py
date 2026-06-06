from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.models import Room, TimeSlot, User, UserRole


def init_db(db: Session) -> None:
    """Seed the database with initial data if empty."""
    if db.query(User).first():
        return  # Already seeded

    # Create default admin
    admin = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        role=UserRole.admin,
    )
    db.add(admin)

    # Create default employee
    employee = User(
        username="employee1",
        hashed_password=hash_password("employee123"),
        role=UserRole.employee,
    )
    db.add(employee)

    # Create rooms with slots
    rooms_data = [
        {
            "name": "Conference Room A",
            "description": "Large conference room, capacity 10",
            "capacity": 10,
            "slots": [
                ("09:00", "11:00"),
                ("11:00", "13:00"),
                ("13:00", "15:00"),
                ("15:00", "17:00"),
            ],
        },
        {
            "name": "Meeting Room B",
            "description": "Small meeting room, capacity 4",
            "capacity": 4,
            "slots": [
                ("09:00", "10:30"),
                ("10:30", "12:00"),
                ("13:00", "14:30"),
                ("14:30", "16:00"),
                ("16:00", "17:30"),
            ],
        },
        {
            "name": "Board Room C",
            "description": "Executive boardroom, capacity 20",
            "capacity": 20,
            "slots": [
                ("09:00", "12:00"),
                ("13:00", "16:00"),
                ("16:00", "18:00"),
            ],
        },
    ]

    for room_data in rooms_data:
        room = Room(
            name=room_data["name"],
            description=room_data["description"],
            capacity=room_data["capacity"],
        )
        db.add(room)
        db.flush()  # get room.id

        for start, end in room_data["slots"]:
            slot = TimeSlot(room_id=room.id, start_time=start, end_time=end)
            db.add(slot)

    db.commit()
