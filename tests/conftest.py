"""
Test configuration.

We use a SQLite file database for integration tests so that the app's
lifespan engine and the override_get_db engine share the same DB.
The file is removed after each test function.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
import app.db.session as db_session_module

TEST_DB_FILE = "/tmp/test_booking.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"


def _make_engine():
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


@pytest.fixture(scope="function")
def app(monkeypatch):
    # Remove stale DB file
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)

    test_engine = _make_engine()
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Patch session module so lifespan uses the same engine
    monkeypatch.setattr(db_session_module, "engine", test_engine)
    monkeypatch.setattr(db_session_module, "SessionLocal", test_session_local)

    def override_get_db():
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    from app.main import create_app
    application = create_app()
    application.dependency_overrides[get_db] = override_get_db

    yield application

    test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


@pytest.fixture(scope="function")
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def employee_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "employee1", "password": "employee123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def employee_headers(employee_token):
    return {"Authorization": f"Bearer {employee_token}"}
