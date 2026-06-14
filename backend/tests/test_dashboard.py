from collections.abc import Generator
from datetime import date, timezone
import os

os.environ["DATABASE_URL"] = "sqlite://"

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.db.models import DailyAiInsight, User
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
    ai_service._DAILY_AI_CACHE.clear()
    coingecko_service._PRICE_CACHE.clear()


def teardown_function() -> None:
    app.dependency_overrides.clear()
    ai_service._DAILY_AI_CACHE.clear()
    coingecko_service._PRICE_CACHE.clear()


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
                source="coingecko",
                last_updated_at=None,
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
            image_url="/memes/test.svg",
            caption="Test meme caption",
            source="static-json",
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


def test_coingecko_failure_with_no_cache_returns_unavailable_prices(monkeypatch) -> None:
    def raise_timeout(*args, **kwargs):
        raise httpx.TimeoutException("CoinGecko timed out")

    monkeypatch.setattr(coingecko_service.httpx, "get", raise_timeout)

    prices = coingecko_service.get_coin_prices(["bitcoin"])

    assert len(prices) == 1
    assert prices[0].coin_id == "bitcoin"
    assert prices[0].symbol == "BTC"
    assert prices[0].price_usd is None
    assert prices[0].change_24h is None
    assert prices[0].source == "unavailable"
    assert prices[0].last_updated_at is None
    assert prices[0].item_key == "price-bitcoin"


def test_coingecko_success_marks_prices_with_live_source(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "bitcoin": {
                    "usd": 70000.0,
                    "usd_24h_change": 1.5,
                    "last_updated_at": 1710000000,
                }
            }

    def fake_get(url, params, timeout):
        assert params["ids"] == "bitcoin"
        assert params["vs_currencies"] == "usd"
        assert params["include_24hr_change"] == "true"
        assert params["include_last_updated_at"] == "true"
        assert timeout == settings.EXTERNAL_API_TIMEOUT_SECONDS
        return FakeResponse()

    monkeypatch.setattr(coingecko_service.httpx, "get", fake_get)

    prices = coingecko_service.get_coin_prices(["bitcoin"])

    assert len(prices) == 1
    assert prices[0].source == "coingecko"
    assert prices[0].price_usd == 70000.0
    assert prices[0].last_updated_at is not None
    assert prices[0].last_updated_at.tzinfo == timezone.utc


def test_coingecko_failure_after_success_returns_cached_prices(monkeypatch) -> None:
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "bitcoin": {
                    "usd": 70000.0,
                    "usd_24h_change": 1.5,
                    "last_updated_at": 1710000000,
                }
            }

    def fake_get(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            return FakeResponse()

        raise httpx.TimeoutException("CoinGecko timed out")

    monkeypatch.setattr(coingecko_service.httpx, "get", fake_get)

    live_prices = coingecko_service.get_coin_prices(["bitcoin"])
    cached_prices = coingecko_service.get_coin_prices(["bitcoin"])

    assert live_prices[0].source == "coingecko"
    assert cached_prices[0].source == "coingecko-cached"
    assert cached_prices[0].price_usd == 70000.0
    assert cached_prices[0].last_updated_at is not None
    assert calls["count"] == 3


def test_missing_coin_data_uses_unavailable_row(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "bitcoin": {
                    "usd": 70000.0,
                    "usd_24h_change": 1.5,
                    "last_updated_at": 1710000000,
                }
            }

    monkeypatch.setattr(coingecko_service.httpx, "get", lambda *args, **kwargs: FakeResponse())

    prices = coingecko_service.get_coin_prices(["bitcoin", "ethereum"])

    assert [price.coin_id for price in prices] == ["bitcoin", "ethereum"]
    assert prices[0].source == "coingecko"
    assert prices[1].source == "unavailable"
    assert prices[1].price_usd is None
    assert prices[1].change_24h is None


def test_missing_openrouter_key_uses_static_ai_fallback(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("OpenRouter should not be called without an API key")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(ai_service.httpx, "post", fail_if_called)
    fixed_date = date(2026, 6, 13)

    insight = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
        today=fixed_date,
    )

    assert insight.model == "static-fallback"
    assert insight.source == "static-fallback"
    assert insight.fallback_reason == "missing_api_key"
    assert "HODLer" in insight.content
    assert "bitcoin" in insight.content
    assert "AI Insight" in insight.content
    assert insight.generated_for_date == fixed_date
    assert insight.item_key == "ai-insight-2026-06-13"


def test_openrouter_success_uses_daily_cache(monkeypatch) -> None:
    fixed_date = date(2026, 6, 13)
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Short educational insight. This is not financial advice.",
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        calls["count"] += 1
        assert url == settings.OPENROUTER_CHAT_URL
        assert headers["Authorization"] == "Bearer test-key"
        assert json["model"] == "openrouter/free"
        assert timeout == settings.EXTERNAL_API_TIMEOUT_SECONDS
        return FakeResponse()

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    first = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
        today=fixed_date,
    )
    second = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
        today=fixed_date,
    )

    assert calls["count"] == 1
    assert first.model == "openrouter/free"
    assert first.source == "openrouter"
    assert first.fallback_reason is None
    assert first.item_key == "ai-insight-2026-06-13"
    assert second == first


def test_dashboard_caches_successful_openrouter_insight(monkeypatch) -> None:
    calls = {"count": 0}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "## Daily Insight\n"
                                "**Bitcoin** can move quickly 🚀, but a HODLer should compare "
                                "short-term price action with liquidity, fees, and broader market context "
                                "before reacting. This is educational only and not financial advice."
                            ),
                        }
                    }
                ]
            }

    def fake_prices(assets: list[str]) -> list[PriceItemResponse]:
        return [
            PriceItemResponse(
                coin_id=asset,
                symbol=asset[:4].upper(),
                price_usd=100.0,
                change_24h=1.0,
                source="coingecko",
                last_updated_at=None,
                item_key=f"price-{asset}",
            )
            for asset in assets
        ]

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)
    monkeypatch.setattr(coingecko_service, "get_coin_prices", fake_prices)

    headers = create_onboarded_user()
    first_response = client.get("/dashboard/today", headers=headers)
    second_response = client.get("/dashboard/today", headers=headers)

    first_insight = first_response.json()["ai_insight"]
    second_insight = second_response.json()["ai_insight"]
    db = TestingSessionLocal()

    try:
        saved_insight_count = db.query(DailyAiInsight).count()
    finally:
        db.close()

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert calls["count"] == 1
    assert saved_insight_count == 1
    assert first_insight["source"] == "openrouter"
    assert second_insight["source"] == "cached-openrouter"
    assert "**" not in first_insight["content"]
    assert "🚀" not in first_insight["content"]
    assert not first_insight["content"].lower().startswith("daily insight")
    assert "not financial advice" in first_insight["content"].lower()


def test_valid_cached_openrouter_content_is_returned_without_api_call(monkeypatch) -> None:
    fixed_date = date(2026, 6, 14)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("OpenRouter should not be called when valid cache exists")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fail_if_called)

    create_onboarded_user()
    db = TestingSessionLocal()

    try:
        user_id = db.query(User).filter(User.email == "user@example.com").first().id
        preferences_hash = ai_service._build_preferences_hash(
            investor_type="HODLer",
            assets=["bitcoin"],
            content_types=["AI Insight"],
        )
        db.add(
            DailyAiInsight(
                user_id=user_id,
                generated_for_date=fixed_date,
                preferences_hash=preferences_hash,
                content=(
                    "Bitcoin can help a HODLer compare short-term market noise with broader "
                    "liquidity and network context. This is educational only and not financial advice."
                ),
                model="openrouter/free",
                source="openrouter",
            )
        )
        db.commit()

        insight = ai_service.get_ai_insight(
            investor_type="HODLer",
            assets=["bitcoin"],
            content_types=["AI Insight"],
            today=fixed_date,
            db=db,
            user_id=user_id,
        )
    finally:
        db.close()

    assert insight.source == "cached-openrouter"
    assert insight.content.startswith("Bitcoin can help")
    assert insight.fallback_reason is None


def test_prompt_like_cached_today_insight_is_deleted_and_openrouter_retried(monkeypatch) -> None:
    fixed_date = date(2026, 6, 14)
    calls = {"count": 0}

    class SuccessResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Bitcoin can help a HODLer compare a quick price move with liquidity, "
                                "fees, and broader market context before reacting. This is educational "
                                "only and not financial advice."
                            ),
                        }
                    }
                ]
            }

    def fake_post(*args, **kwargs):
        calls["count"] += 1
        return SuccessResponse()

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    create_onboarded_user()
    db = TestingSessionLocal()

    try:
        user_id = db.query(User).filter(User.email == "user@example.com").first().id
        preferences_hash = ai_service._build_preferences_hash(
            investor_type="HODLer",
            assets=["bitcoin"],
            content_types=["AI Insight"],
        )
        db.add(
            DailyAiInsight(
                user_id=user_id,
                generated_for_date=fixed_date,
                preferences_hash=preferences_hash,
                content=(
                    "We need to produce a daily educational crypto insight. Must be plain text. "
                    "Must not give buy, sell, or price prediction recommendations. Word count: 80-120 words."
                ),
                model="openrouter/free",
                source="openrouter",
            )
        )
        db.commit()

        insight = ai_service.get_ai_insight(
            investor_type="HODLer",
            assets=["bitcoin"],
            content_types=["AI Insight"],
            today=fixed_date,
            db=db,
            user_id=user_id,
        )
        saved_insights = db.query(DailyAiInsight).all()
    finally:
        db.close()

    assert calls["count"] == 1
    assert insight.source == "openrouter"
    assert "We need to produce" not in insight.content
    assert len(saved_insights) == 1
    assert "We need to produce" not in saved_insights[0].content


def test_openrouter_null_content_returns_empty_response_fallback(monkeypatch) -> None:
    fixed_date = date(2026, 6, 13)

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": None}}]}

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", lambda *args, **kwargs: FakeResponse())

    insight = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
        today=fixed_date,
    )

    assert insight.model == "static-fallback"
    assert insight.source == "static-fallback"
    assert insight.fallback_reason == "empty_response"
    assert insight.item_key == "ai-insight-2026-06-13"


def test_openrouter_empty_choices_returns_empty_response_fallback(monkeypatch) -> None:
    fixed_date = date(2026, 6, 13)

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": []}

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", lambda *args, **kwargs: FakeResponse())

    insight = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
        today=fixed_date,
    )

    assert insight.model == "static-fallback"
    assert insight.source == "static-fallback"
    assert insight.fallback_reason == "empty_response"
    assert insight.item_key == "ai-insight-2026-06-13"


def test_openrouter_failure_returns_static_fallback(monkeypatch) -> None:
    fixed_date = date(2026, 6, 13)

    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("OpenRouter timed out")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    insight = ai_service.get_ai_insight(
        investor_type="Beginner",
        assets=["ethereum"],
        content_types=["AI Insight"],
        today=fixed_date,
    )

    assert insight.model == "static-fallback"
    assert insight.source == "static-fallback"
    assert insight.fallback_reason == "api_request_failed"
    assert "Beginner" in insight.content
    assert "ethereum" in insight.content
    assert insight.item_key == "ai-insight-2026-06-13"


def test_openrouter_failure_returns_previous_successful_insight(monkeypatch) -> None:
    class SuccessResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Ethereum activity can help a Beginner connect market movement with "
                                "network usage and developer momentum. This is educational only and not "
                                "financial advice."
                            ),
                        }
                    }
                ]
            }

    def success_post(*args, **kwargs):
        return SuccessResponse()

    def failing_post(*args, **kwargs):
        raise httpx.TimeoutException("OpenRouter timed out")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", success_post)

    create_onboarded_user()
    db = TestingSessionLocal()

    try:
        user_id = db.query(User).filter(User.email == "user@example.com").first().id
        previous = ai_service.get_ai_insight(
            investor_type="Beginner",
            assets=["ethereum"],
            content_types=["AI Insight"],
            today=date(2026, 6, 13),
            db=db,
            user_id=user_id,
        )

        monkeypatch.setattr(ai_service.httpx, "post", failing_post)
        current = ai_service.get_ai_insight(
            investor_type="Beginner",
            assets=["ethereum"],
            content_types=["AI Insight"],
            today=date(2026, 6, 14),
            db=db,
            user_id=user_id,
        )
    finally:
        db.close()

    assert previous.source == "openrouter"
    assert current.source == "cached-openrouter"
    assert current.fallback_reason == "using_previous_success"
    assert current.content == previous.content


def test_dashboard_uses_ai_fallback_when_openrouter_response_is_empty(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"choices": [{"message": {"content": None}}]}

    def fake_prices(assets: list[str]) -> list[PriceItemResponse]:
        return [
            PriceItemResponse(
                coin_id=asset,
                symbol=asset[:4].upper(),
                price_usd=100.0,
                change_24h=1.0,
                source="coingecko",
                last_updated_at=None,
                item_key=f"price-{asset}",
            )
            for asset in assets
        ]

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", lambda *args, **kwargs: FakeResponse())
    monkeypatch.setattr(coingecko_service, "get_coin_prices", fake_prices)

    headers = create_onboarded_user()
    response = client.get("/dashboard/today", headers=headers)

    assert response.status_code == 200
    assert response.json()["ai_insight"]["source"] == "static-fallback"
    assert response.json()["ai_insight"]["fallback_reason"] == "empty_response"


def test_repeated_dashboard_call_after_failure_retries_openrouter(monkeypatch) -> None:
    calls = {"count": 0}

    class SuccessResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Bitcoin can help a HODLer practice comparing market movement with "
                                "network context before reacting to short-term noise. This is "
                                "educational only and not financial advice."
                            ),
                        }
                    }
                ]
            }

    def fake_prices(assets: list[str]) -> list[PriceItemResponse]:
        return [
            PriceItemResponse(
                coin_id=asset,
                symbol=asset[:4].upper(),
                price_usd=100.0,
                change_24h=1.0,
                source="coingecko",
                last_updated_at=None,
                item_key=f"price-{asset}",
            )
            for asset in assets
        ]

    def fake_post(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] <= 2:
            raise httpx.TimeoutException("OpenRouter timed out")

        return SuccessResponse()

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)
    monkeypatch.setattr(coingecko_service, "get_coin_prices", fake_prices)

    headers = create_onboarded_user()
    first_response = client.get("/dashboard/today", headers=headers)
    second_response = client.get("/dashboard/today", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["ai_insight"]["source"] == "static-fallback"
    assert first_response.json()["ai_insight"]["fallback_reason"] == "api_request_failed"
    assert second_response.json()["ai_insight"]["source"] == "openrouter"
    assert second_response.json()["ai_insight"]["fallback_reason"] is None
    assert calls["count"] == 3


def test_static_ai_fallback_is_not_saved_as_successful_cache(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("OpenRouter timed out")

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    create_onboarded_user()
    db = TestingSessionLocal()

    try:
        user_id = db.query(User).filter(User.email == "user@example.com").first().id
        insight = ai_service.get_ai_insight(
            investor_type="HODLer",
            assets=["bitcoin"],
            content_types=["AI Insight"],
            today=date(2026, 6, 13),
            db=db,
            user_id=user_id,
        )
        saved_insight_count = db.query(DailyAiInsight).count()
    finally:
        db.close()

    assert insight.source == "static-fallback"
    assert saved_insight_count == 0


def test_prompt_echo_openrouter_response_is_treated_as_empty(monkeypatch) -> None:
    fixed_date = date(2026, 6, 13)

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "We need to produce a daily educational crypto insight for a beginner. "
                                "Must be plain text, no markdown, headings, bullets, emojis, or "
                                "decorative symbols. Word count: 80-120 words."
                            ),
                        }
                    }
                ]
            }

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_service.httpx, "post", lambda *args, **kwargs: FakeResponse())

    create_onboarded_user()
    db = TestingSessionLocal()

    try:
        user_id = db.query(User).filter(User.email == "user@example.com").first().id
        insight = ai_service.get_ai_insight(
            investor_type="Beginner",
            assets=["bitcoin"],
            content_types=["AI Insight"],
            today=fixed_date,
            db=db,
            user_id=user_id,
        )
        saved_insight_count = db.query(DailyAiInsight).count()
    finally:
        db.close()

    assert insight.source == "static-fallback"
    assert insight.fallback_reason == "empty_response"
    assert "We need to produce" not in insight.content
    assert saved_insight_count == 0


def test_ai_response_does_not_expose_api_key_or_secret(monkeypatch) -> None:
    secret_value = "test-secret-value"
    api_key = "test-openrouter-key"

    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("OpenRouter failed")

    monkeypatch.setattr(settings, "SECRET_KEY", secret_value)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", api_key)
    monkeypatch.setattr(ai_service.httpx, "post", fake_post)

    insight = ai_service.get_ai_insight(
        investor_type="HODLer",
        assets=["bitcoin"],
        content_types=["AI Insight"],
        today=date(2026, 6, 13),
    )
    response_text = insight.model_dump_json()

    assert api_key not in response_text
    assert secret_value not in response_text


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
    assert meme["source"] == "static-json"
    assert meme["item_key"] == "meme-test"


def test_static_meme_uses_local_asset_path() -> None:
    meme = meme_service.get_crypto_meme()

    assert meme.image_url.startswith("/memes/")
    assert meme.image_url.endswith(".svg")
    assert meme.source == "static-json"
    assert meme.item_key.startswith("meme-")


def test_meme_service_loads_static_json_list() -> None:
    memes = meme_service._load_static_memes()

    assert len(memes) >= 8
    assert all(meme["source"] == "static-json" for meme in memes)


def test_dashboard_meme_response_uses_static_json(monkeypatch) -> None:
    def fake_prices(assets: list[str]) -> list[PriceItemResponse]:
        return [
            PriceItemResponse(
                coin_id=asset,
                symbol=asset[:4].upper(),
                price_usd=100.0,
                change_24h=1.0,
                source="coingecko",
                last_updated_at=None,
                item_key=f"price-{asset}",
            )
            for asset in assets
        ]

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "")
    monkeypatch.setattr(coingecko_service, "get_coin_prices", fake_prices)

    headers = create_onboarded_user()
    response = client.get("/dashboard/today", headers=headers)

    assert response.status_code == 200
    assert response.json()["meme"]["source"] == "static-json"
