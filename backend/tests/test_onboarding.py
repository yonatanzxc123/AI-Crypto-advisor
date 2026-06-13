from collections.abc import Generator
import os

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Preference, User
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


def valid_onboarding_payload() -> dict:
    return {
        "assets": ["bitcoin", "ethereum"],
        "investor_type": "HODLer",
        "content_types": ["Market News", "Coin Prices", "AI Insight", "Fun"],
    }


def auth_headers_for(email: str = "user@example.com") -> dict[str, str]:
    client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "User Name",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_post_onboarding_without_token_fails() -> None:
    response = client.post("/onboarding", json=valid_onboarding_payload())

    assert response.status_code == 401


def test_get_onboarding_without_token_fails() -> None:
    response = client.get("/onboarding/me")

    assert response.status_code == 401


def test_authenticated_user_can_create_onboarding_preferences() -> None:
    response = client.post(
        "/onboarding",
        json=valid_onboarding_payload(),
        headers=auth_headers_for(),
    )

    assert response.status_code == 200
    assert response.json()["assets"] == ["bitcoin", "ethereum"]
    assert response.json()["investor_type"] == "HODLer"
    assert response.json()["content_types"] == [
        "Market News",
        "Coin Prices",
        "AI Insight",
        "Fun",
    ]


def test_authenticated_user_can_fetch_onboarding_preferences() -> None:
    headers = auth_headers_for()
    client.post("/onboarding", json=valid_onboarding_payload(), headers=headers)

    response = client.get("/onboarding/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["assets"] == ["bitcoin", "ethereum"]


def test_get_onboarding_returns_404_when_preferences_are_missing() -> None:
    response = client.get("/onboarding/me", headers=auth_headers_for())

    assert response.status_code == 404
    assert response.json()["detail"] == "Onboarding preferences not found"


def test_creating_onboarding_marks_user_as_completed() -> None:
    headers = auth_headers_for()
    client.post("/onboarding", json=valid_onboarding_payload(), headers=headers)

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["onboarding_completed"] is True


def test_posting_onboarding_twice_updates_existing_preferences() -> None:
    headers = auth_headers_for()
    client.post("/onboarding", json=valid_onboarding_payload(), headers=headers)

    updated_payload = {
        "assets": ["solana"],
        "investor_type": "Day Trader",
        "content_types": ["Charts"],
    }
    response = client.post("/onboarding", json=updated_payload, headers=headers)

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "user@example.com").first()
        preference_count = db.query(Preference).filter(Preference.user_id == user.id).count()
    finally:
        db.close()

    assert response.status_code == 200
    assert response.json()["assets"] == ["solana"]
    assert response.json()["investor_type"] == "Day Trader"
    assert preference_count == 1


def test_empty_assets_list_fails() -> None:
    payload = valid_onboarding_payload()
    payload["assets"] = []

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_empty_content_types_list_fails() -> None:
    payload = valid_onboarding_payload()
    payload["content_types"] = []

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_empty_investor_type_fails() -> None:
    payload = valid_onboarding_payload()
    payload["investor_type"] = "   "

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_empty_string_inside_assets_fails() -> None:
    payload = valid_onboarding_payload()
    payload["assets"] = ["bitcoin", " "]

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_empty_string_inside_content_types_fails() -> None:
    payload = valid_onboarding_payload()
    payload["content_types"] = ["Market News", ""]

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_duplicate_values_are_removed() -> None:
    payload = {
        "assets": ["bitcoin", "ethereum", "bitcoin"],
        "investor_type": "HODLer",
        "content_types": ["Fun", "Market News", "Fun"],
    }

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 200
    assert response.json()["assets"] == ["bitcoin", "ethereum"]
    assert response.json()["content_types"] == ["Fun", "Market News"]


def test_user_cannot_control_user_id_from_request_body() -> None:
    payload = valid_onboarding_payload()
    payload["user_id"] = 999

    response = client.post("/onboarding", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_users_can_only_access_their_own_preferences() -> None:
    user_a_headers = auth_headers_for(email="a@example.com")
    user_b_headers = auth_headers_for(email="b@example.com")

    user_a_payload = valid_onboarding_payload()
    user_b_payload = {
        "assets": ["solana"],
        "investor_type": "NFT Collector",
        "content_types": ["Fun"],
    }

    client.post("/onboarding", json=user_a_payload, headers=user_a_headers)
    client.post("/onboarding", json=user_b_payload, headers=user_b_headers)

    user_a_response = client.get("/onboarding/me", headers=user_a_headers)
    user_b_response = client.get("/onboarding/me", headers=user_b_headers)

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200
    assert user_a_response.json()["assets"] == ["bitcoin", "ethereum"]
    assert user_b_response.json()["assets"] == ["solana"]
