from collections.abc import Generator
import os

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Feedback, User
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


def valid_feedback_payload(vote: str = "up") -> dict:
    return {
        "section_type": "ai_insight",
        "item_key": "ai-insight-today",
        "vote": vote,
    }


def get_user_id_by_email(email: str) -> int:
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user.id
    finally:
        db.close()


def get_all_feedback() -> list[Feedback]:
    db = TestingSessionLocal()
    try:
        return db.query(Feedback).order_by(Feedback.id).all()
    finally:
        db.close()


def test_post_feedback_without_token_fails() -> None:
    response = client.post("/feedback", json=valid_feedback_payload())

    assert response.status_code == 401


def test_authenticated_user_can_submit_upvote() -> None:
    response = client.post(
        "/feedback",
        json=valid_feedback_payload(vote="up"),
        headers=auth_headers_for(),
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Feedback saved successfully"}


def test_authenticated_user_can_submit_downvote() -> None:
    response = client.post(
        "/feedback",
        json=valid_feedback_payload(vote="down"),
        headers=auth_headers_for(),
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Feedback saved successfully"}


def test_invalid_vote_value_fails() -> None:
    response = client.post(
        "/feedback",
        json=valid_feedback_payload(vote="sideways"),
        headers=auth_headers_for(),
    )

    assert response.status_code == 422


def test_invalid_section_type_fails() -> None:
    payload = valid_feedback_payload()
    payload["section_type"] = "profile"

    response = client.post("/feedback", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_empty_item_key_fails() -> None:
    payload = valid_feedback_payload()
    payload["item_key"] = "   "

    response = client.post("/feedback", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_request_body_with_user_id_is_rejected() -> None:
    payload = valid_feedback_payload()
    payload["user_id"] = 999

    response = client.post("/feedback", json=payload, headers=auth_headers_for())

    assert response.status_code == 422


def test_feedback_is_stored_with_authenticated_user_id() -> None:
    headers = auth_headers_for(email="owner@example.com")
    user_id = get_user_id_by_email("owner@example.com")

    client.post("/feedback", json=valid_feedback_payload(), headers=headers)
    feedback_items = get_all_feedback()

    assert len(feedback_items) == 1
    assert feedback_items[0].user_id == user_id
    assert feedback_items[0].section_type == "ai_insight"
    assert feedback_items[0].item_key == "ai-insight-today"
    assert feedback_items[0].vote == "up"


def test_multiple_feedback_rows_for_same_item_are_allowed() -> None:
    headers = auth_headers_for()

    client.post("/feedback", json=valid_feedback_payload(vote="up"), headers=headers)
    client.post("/feedback", json=valid_feedback_payload(vote="down"), headers=headers)

    feedback_items = get_all_feedback()

    assert len(feedback_items) == 2
    assert [feedback.vote for feedback in feedback_items] == ["up", "down"]


def test_response_does_not_expose_password_hash_or_secrets() -> None:
    response = client.post(
        "/feedback",
        json=valid_feedback_payload(),
        headers=auth_headers_for(),
    )
    response_text = response.text

    assert response.status_code == 200
    assert "password_hash" not in response_text
    assert "SECRET_KEY" not in response_text
    assert "DATABASE_URL" not in response_text
