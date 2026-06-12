import os

os.environ["DATABASE_URL"] = "sqlite://"

from app.db.models import Feedback, Preference, User


def test_user_model_construction() -> None:
    user = User(
        email="satoshi@example.com",
        name="Satoshi",
        password_hash="hashed-password",
        onboarding_completed=False,
    )

    assert user.email == "satoshi@example.com"
    assert user.name == "Satoshi"
    assert user.password_hash == "hashed-password"
    assert user.onboarding_completed is False


def test_preference_model_construction() -> None:
    preference = Preference(
        user_id=1,
        assets_json='["bitcoin", "ethereum"]',
        investor_type="HODLer",
        content_types_json='["Market News", "Fun"]',
    )

    assert preference.user_id == 1
    assert preference.assets_json == '["bitcoin", "ethereum"]'
    assert preference.investor_type == "HODLer"
    assert preference.content_types_json == '["Market News", "Fun"]'


def test_feedback_model_construction() -> None:
    feedback = Feedback(
        user_id=1,
        section_type="market_news",
        item_key="bitcoin-news-1",
        vote="up",
    )

    assert feedback.user_id == 1
    assert feedback.section_type == "market_news"
    assert feedback.item_key == "bitcoin-news-1"
    assert feedback.vote == "up"
