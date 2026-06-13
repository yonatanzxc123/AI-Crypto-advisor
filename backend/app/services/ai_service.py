import httpx

from app.core.config import settings
from app.schemas.dashboard_schema import AiInsightResponse


def get_ai_insight(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
) -> AiInsightResponse:
    if not settings.OPENROUTER_API_KEY:
        return _build_fallback_insight(investor_type, assets)

    try:
        content = _fetch_openrouter_insight(investor_type, assets, content_types)
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return _build_fallback_insight(investor_type, assets)

    if not content:
        return _build_fallback_insight(investor_type, assets)

    return AiInsightResponse(
        title="AI Insight of the Day",
        content=content,
        model=settings.OPENROUTER_MODEL,
        item_key="ai-insight-today",
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
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


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


def _build_fallback_insight(investor_type: str, assets: list[str]) -> AiInsightResponse:
    assets_text = ", ".join(assets) if assets else "the crypto market"
    content = (
        f"For a {investor_type} watching {assets_text}, today's useful habit is to compare "
        "price movement with broader market context before forming an opinion. "
        "This is educational only and not financial advice."
    )

    return AiInsightResponse(
        title="AI Insight of the Day",
        content=content,
        model="static-fallback",
        item_key="ai-insight-today",
    )
