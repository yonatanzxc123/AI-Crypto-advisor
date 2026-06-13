from collections.abc import Generator
import os

os.environ["DATABASE_URL"] = "sqlite://"

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.schemas.dashboard_schema import AiInsightResponse, MemeResponse, PriceItemResponse
from app.services import ai_service, coingecko_service, meme_service


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


def onboarding_payload() -> dict:
    return {
        "assets": ["bitcoin", "ethereum"],
        "investor_type": "HODLer",
        "content_types": ["Market News", "Coin Prices", "AI Insight", "Fun"],
    }


def create_onboarded_user() -> dict[str, str]:
    headers = auth_headers_for()
    client.post("/onboarding", json=onboarding_payload(), headers=headers)
    return headers


def mock_dashboard_helpers(monkeypatch) -> None:
    def fake_prices(assets: list[str]) -> list[PriceItemResponse]:
        return [
            PriceItemResponse(
                coin_id=asset,
                symbol=asset[:4].upper(),
                price_usd=100.0,
                change_24h=1.0,
                item_key=f"price-{asset}",
            )
            for asset in assets
        ]

    monkeypatch.setattr(coingecko_service, "get_coin_prices", fake_prices)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(
        meme_service,
        "get_crypto_meme",
        lambda: MemeResponse(
            title="Crypto Meme",
            image_url="https://placehold.co/600x400/png?text=Test",
            caption="Test meme caption",
            item_key="meme-test",
        ),
    )


def test_dashboard_without_token_fails() -> None:
    response = client.get("/dashboard/today")

    assert response.status_code == 401


def test_dashboard_without_onboarding_returns_clear_error() -> None:
    response = client.get("/dashboard/today", headers=auth_headers_for())

    assert response.status_code == 400
    assert response.json()["detail"] == "Please complete onboarding before viewing the dashboard"


def test_dashboard_returns_all_sections_for_onboarded_user(monkeypatch) -> None:
    mock_dashboard_helpers(monkeypatch)
    headers = create_onboarded_user()

    response = client.get("/dashboard/today", headers=headers)

    assert response.status_code == 200
    assert set(response.json().keys()) == {
        "profile",
        "prices",
        "news",
        "ai_insight",
        "meme",
    }


def test_dashboard_response_does_not_include_password_hash(monkeypatch) -> None:
    mock_dashboard_helpers(monkeypatch)
    headers = create_onboarded_user()

    response = client.get("/dashboard/today", headers=headers)

    assert response.status_code == 200
    assert "password_hash" not in response.text


def test_dashboard_uses_selected_assets_in_profile_and_prices(monkeypatch) -> None:
    mock_dashboard_helpers(monkeypatch)
    headers = create_onboarded_user()

    response = client.get("/dashboard/today", headers=headers)
    data = response.json()

    assert data["profile"]["assets"] == ["bitcoin", "ethereum"]
    assert [price["coin_id"] for price in data["prices"]] == ["bitcoin", "ethereum"]


def test_coingecko_failure_falls_back_to_static_prices(monkeypatch) -> None:
    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("CoinGecko timed out")

    monkeypatch.setattr(coingecko_service.httpx, "get", raise_timeout)

    prices = coingecko_service.get_coin_prices(["bitcoin"])

    assert len(prices) == 1
    assert prices[0].coin_id == "bitcoin"
    assert prices[0].symbol == "BTC"
    assert prices[0].item_key == "price-bitcoin"


def test_missing_openrouter_key_uses_static_ai_fallback(monkeypatch) -> None:
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")

    insight = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
    )

    assert insight.model == "static-fallback"
    assert "HODLer" in insight.content
    assert "bitcoin" in insight.content
    assert insight.item_key == "ai-insight-today"


def test_every_dashboard_item_has_item_key(monkeypatch) -> None:
    mock_dashboard_helpers(monkeypatch)
    headers = create_onboarded_user()

    data = client.get("/dashboard/today", headers=headers).json()

    assert all(price["item_key"] for price in data["prices"])
    assert all(news_item["item_key"] for news_item in data["news"])
    assert data["ai_insight"]["item_key"]
    assert data["meme"]["item_key"]


def test_meme_response_exists_and_has_item_key(monkeypatch) -> None:
    mock_dashboard_helpers(monkeypatch)
    headers = create_onboarded_user()

    meme = client.get("/dashboard/today", headers=headers).json()["meme"]

    assert meme["title"] == "Crypto Meme"
    assert meme["image_url"]
    assert meme["caption"]
    assert meme["item_key"] == "meme-test"
