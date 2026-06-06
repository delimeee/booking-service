import datetime
import pytest


class TestAuth:
    def test_register_and_login(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "pass1234"},
        )
        assert r.status_code == 201
        assert r.json()["username"] == "newuser"

        r = client.post(
            "/api/v1/auth/login",
            data={"username": "newuser", "password": "pass1234"},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert r.status_code == 401

    def test_get_me(self, client, admin_headers):
        r = client.get("/api/v1/auth/me", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["username"] == "admin"
        assert r.json()["role"] == "admin"

    def test_duplicate_username_raises_409(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"username": "uniqueuser", "password": "pw"},
        )
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "uniqueuser", "password": "pw2"},
        )
        assert r.status_code == 409

    def test_unauthenticated_access_returns_401(self, client):
        r = client.get("/api/v1/rooms")
        assert r.status_code == 401


class TestRooms:
    def test_admin_can_create_room(self, client, admin_headers):
        r = client.post(
            "/api/v1/rooms",
            json={"name": "Room X", "capacity": 8},
            headers=admin_headers,
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Room X"

    def test_employee_cannot_create_room(self, client, employee_headers):
        r = client.post(
            "/api/v1/rooms",
            json={"name": "Forbidden Room"},
            headers=employee_headers,
        )
        assert r.status_code == 403

    def test_list_rooms(self, client, employee_headers):
        r = client.get("/api/v1/rooms", headers=employee_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        # Seeded rooms should be present
        assert len(r.json()) >= 3

    def test_get_room_by_id(self, client, admin_headers, employee_headers):
        rooms = client.get("/api/v1/rooms", headers=employee_headers).json()
        room_id = rooms[0]["id"]
        r = client.get(f"/api/v1/rooms/{room_id}", headers=employee_headers)
        assert r.status_code == 200
        assert r.json()["id"] == room_id

    def test_get_nonexistent_room(self, client, employee_headers):
        r = client.get("/api/v1/rooms/99999", headers=employee_headers)
        assert r.status_code == 404

    def test_admin_can_add_slot(self, client, admin_headers):
        r = client.post(
            "/api/v1/rooms",
            json={"name": "SlotRoom"},
            headers=admin_headers,
        )
        room_id = r.json()["id"]
        r = client.post(
            f"/api/v1/rooms/{room_id}/slots",
            json={"start_time": "08:00", "end_time": "10:00"},
            headers=admin_headers,
        )
        assert r.status_code == 201
        assert r.json()["start_time"] == "08:00"


class TestBookings:
    def _get_first_room_and_slot(self, client, headers):
        rooms = client.get("/api/v1/rooms", headers=headers).json()
        room = next(r for r in rooms if r["slots"])
        slot = room["slots"][0]
        return room["id"], slot["id"]

    def test_create_booking(self, client, employee_headers):
        room_id, slot_id = self._get_first_room_and_slot(client, employee_headers)
        r = client.post(
            "/api/v1/bookings",
            json={"room_id": room_id, "slot_id": slot_id, "date": "2035-06-15"},
            headers=employee_headers,
        )
        assert r.status_code == 201
        assert r.json()["status"] == "active"

    def test_double_booking_returns_409(self, client, employee_headers):
        room_id, slot_id = self._get_first_room_and_slot(client, employee_headers)
        payload = {"room_id": room_id, "slot_id": slot_id, "date": "2035-07-20"}
        client.post("/api/v1/bookings", json=payload, headers=employee_headers)
        r = client.post("/api/v1/bookings", json=payload, headers=employee_headers)
        assert r.status_code == 409

    def test_list_my_bookings(self, client, employee_headers):
        r = client.get("/api/v1/bookings", headers=employee_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_employee_cancel_own_booking(self, client, employee_headers):
        room_id, slot_id = self._get_first_room_and_slot(client, employee_headers)
        booking = client.post(
            "/api/v1/bookings",
            json={"room_id": room_id, "slot_id": slot_id, "date": "2035-08-10"},
            headers=employee_headers,
        ).json()
        r = client.delete(f"/api/v1/bookings/{booking['id']}", headers=employee_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    def test_employee_cannot_cancel_others_booking(
        self, client, admin_headers, employee_headers
    ):
        room_id, slot_id = self._get_first_room_and_slot(client, admin_headers)
        booking = client.post(
            "/api/v1/bookings",
            json={"room_id": room_id, "slot_id": slot_id, "date": "2035-09-01"},
            headers=admin_headers,
        ).json()
        r = client.delete(f"/api/v1/bookings/{booking['id']}", headers=employee_headers)
        assert r.status_code == 403

    def test_admin_can_cancel_any_booking(self, client, admin_headers, employee_headers):
        room_id, slot_id = self._get_first_room_and_slot(client, employee_headers)
        booking = client.post(
            "/api/v1/bookings",
            json={"room_id": room_id, "slot_id": slot_id, "date": "2035-10-05"},
            headers=employee_headers,
        ).json()
        r = client.delete(f"/api/v1/bookings/{booking['id']}", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    def test_availability(self, client, employee_headers):
        r = client.get(
            "/api/v1/bookings/availability",
            params={"date": "2035-11-01"},
            headers=employee_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for room in data:
            assert "room_id" in room
            assert "slots" in room
            for slot in room["slots"]:
                assert "available" in slot

    def test_employee_cannot_see_others_booking(
        self, client, admin_headers, employee_headers
    ):
        room_id, slot_id = self._get_first_room_and_slot(client, admin_headers)
        booking = client.post(
            "/api/v1/bookings",
            json={"room_id": room_id, "slot_id": slot_id, "date": "2035-12-01"},
            headers=admin_headers,
        ).json()
        r = client.get(f"/api/v1/bookings/{booking['id']}", headers=employee_headers)
        assert r.status_code == 403
