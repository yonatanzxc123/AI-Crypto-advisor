from datetime import date

import httpx

from app.core.config import settings
from app.schemas.dashboard_schema import AiInsightResponse


_DAILY_AI_CACHE: dict[tuple, AiInsightResponse] = {}


class EmptyOpenRouterResponseError(Exception):
    pass


def get_ai_insight(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
    today: date | None = None,
) -> AiInsightResponse:
    insight_date = today or date.today()
    model_name = settings.OPENROUTER_MODEL if settings.OPENROUTER_API_KEY else "static-fallback"
    cache_key = _build_cache_key(insight_date, investor_type, assets, content_types, model_name)
    cached_insight = _DAILY_AI_CACHE.get(cache_key)

    if cached_insight:
        return cached_insight

    if not settings.OPENROUTER_API_KEY:
        return _cache_insight(
            cache_key,
            _build_fallback_insight(
                investor_type=investor_type,
                assets=assets,
                content_types=content_types,
                insight_date=insight_date,
                fallback_reason="missing_api_key",
            ),
        )

    try:
        content = _fetch_openrouter_insight(investor_type, assets, content_types)
    except EmptyOpenRouterResponseError:
        return _build_fallback_insight(
            investor_type=investor_type,
            assets=assets,
            content_types=content_types,
            insight_date=insight_date,
            fallback_reason="empty_response",
        )
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return _build_fallback_insight(
            investor_type=investor_type,
            assets=assets,
            content_types=content_types,
            insight_date=insight_date,
            fallback_reason="api_request_failed",
        )

    if not content:
        return _build_fallback_insight(
            investor_type=investor_type,
            assets=assets,
            content_types=content_types,
            insight_date=insight_date,
            fallback_reason="empty_response",
        )

    return _cache_insight(
        cache_key,
        AiInsightResponse(
            title="AI Insight of the Day",
            content=content,
            model=settings.OPENROUTER_MODEL,
            source="openrouter",
            fallback_reason=None,
            generated_for_date=insight_date,
            item_key=_build_item_key(insight_date),
        ),
    )


def _fetch_openrouter_insight(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
) -> str:
    prompt = _build_prompt(investor_type, assets, content_types)
    response = httpx.post(
        settings.OPENROUTER_CHAT_URL,
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You provide short crypto education, not financial advice.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 120,
            "temperature": 0.7,
        },
        timeout=settings.EXTERNAL_API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise EmptyOpenRouterResponseError() from exc

    return _extract_openrouter_content(data)


def _extract_openrouter_content(data: object) -> str:
    if not isinstance(data, dict):
        raise EmptyOpenRouterResponseError()

    choices = data.get("choices")

    if not isinstance(choices, list) or not choices:
        raise EmptyOpenRouterResponseError()

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        raise EmptyOpenRouterResponseError()

    message = first_choice.get("message")

    if not isinstance(message, dict):
        raise EmptyOpenRouterResponseError()

    content = message.get("content")

    if not isinstance(content, str):
        raise EmptyOpenRouterResponseError()

    stripped_content = content.strip()

    if not stripped_content:
        raise EmptyOpenRouterResponseError()

    return stripped_content


def _build_prompt(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
) -> str:
    assets_text = ", ".join(assets)
    content_types_text = ", ".join(content_types)
    return (
        f"Write one short educational crypto insight for a {investor_type}. "
        f"They follow these assets: {assets_text}. "
        f"They like this content: {content_types_text}. "
        "Do not provide buy, sell, or price prediction instructions. "
        "End by reminding them this is not financial advice."
    )


def _build_fallback_insight(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
    insight_date: date,
    fallback_reason: str,
) -> AiInsightResponse:
    assets_text = ", ".join(assets) if assets else "the crypto market"
    content_types_text = ", ".join(content_types) if content_types else "balanced dashboard content"
    content = (
        f"For a {investor_type} watching {assets_text} and preferring {content_types_text}, "
        "today's useful habit is to compare price movement with broader market context "
        "before forming an opinion. "
        "This is educational only and not financial advice."
    )

    return AiInsightResponse(
        title="AI Insight of the Day",
        content=content,
        model="static-fallback",
        source="static-fallback",
        fallback_reason=fallback_reason,
        generated_for_date=insight_date,
        item_key=_build_item_key(insight_date),
    )


def _build_item_key(insight_date: date) -> str:
    return f"ai-insight-{insight_date.isoformat()}"


def _build_cache_key(
    insight_date: date,
    investor_type: str,
    assets: list[str],
    content_types: list[str],
    model_name: str,
) -> tuple:
    return (
        insight_date.isoformat(),
        investor_type.strip().lower(),
        tuple(asset.strip().lower() for asset in assets),
        tuple(content_type.strip().lower() for content_type in content_types),
        model_name,
    )


def _cache_insight(cache_key: tuple, insight: AiInsightResponse) -> AiInsightResponse:
    _DAILY_AI_CACHE[cache_key] = insight
    return insight
