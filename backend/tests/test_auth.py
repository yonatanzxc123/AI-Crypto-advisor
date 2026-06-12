from collections.abc import Generator
import os

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import User
from app.main import app


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function() -> None:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db


def teardown_function() -> None:
    app.dependency_overrides.clear()


client = TestClient(app)


def register_test_user(email: str = "user@example.com") -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "User Name",
            "password": "password123",
        },
    )
    return response.json()


def login_test_user(email: str = "user@example.com", password: str = "password123") -> dict:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    return response.json()


def test_register_successfully_creates_user() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "name": "User Name",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert response.json()["name"] == "User Name"
    assert response.json()["onboarding_completed"] is False


def test_register_with_invalid_email_fails() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "name": "User Name",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_with_short_password_fails() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "name": "User Name",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_register_with_empty_name_fails() -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "name": "   ",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_duplicate_email_registration_returns_error() -> None:
    register_test_user()

    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "name": "Another Name",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_duplicate_email_with_different_casing_returns_error() -> None:
    register_test_user(email="User@Example.com")

    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "name": "Another Name",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_login_successfully_returns_access_token() -> None:
    register_test_user()

    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_works_with_normalized_email_casing() -> None:
    register_test_user(email="User@Example.com")

    response = client.post(
        "/auth/login",
        json={
            "email": "USER@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_wrong_password_fails() -> None:
    register_test_user()

    response = client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_register_stores_hashed_password() -> None:
    register_test_user()

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "user@example.com").first()
    finally:
        db.close()

    assert user is not None
    assert user.password_hash != "password123"
    assert user.password_hash.startswith("$2")


def test_auth_me_with_valid_token_returns_current_user() -> None:
    register_test_user()
    login_data = login_test_user()

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_auth_me_without_token_fails() -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_user_response_never_includes_password_hash() -> None:
    registered_user = register_test_user()
    login_data = login_test_user()
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )

    assert "password_hash" not in registered_user
    assert "password_hash" not in me_response.json()
