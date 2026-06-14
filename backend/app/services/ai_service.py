from datetime import date
import hashlib
import json
import re
import unicodedata

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories import daily_ai_insight_repository
from app.schemas.dashboard_schema import AiInsightResponse


OPENROUTER_ATTEMPTS = 2
MIN_AI_WORDS = 8
MAX_AI_CHARS = 700
DISCLAIMER = "This is educational only and not financial advice."
PROMPT_ECHO_PHRASES = (
    "we need to produce",
    "we need to ensure",
    "must be plain text",
    "must mention at least one selected asset",
    "must not give buy",
    "must not give",
    "word count",
    "write 80 to 120",
    "selected assets",
    "system prompt",
    "user prompt",
    "instructions",
    "no markdown",
    "no headings",
    "no bullets",
    "no emojis",
    "let's aim",
)

_DAILY_AI_CACHE: dict[tuple, AiInsightResponse] = {}


class EmptyOpenRouterResponseError(Exception):
    pass


def get_ai_insight(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
    today: date | None = None,
    db: Session | None = None,
    user_id: int | None = None,
) -> AiInsightResponse:
    insight_date = today or date.today()
    preferences_hash = _build_preferences_hash(investor_type, assets, content_types)

    if db is not None and user_id is not None:
        cached_insight = daily_ai_insight_repository.get_successful_insight_for_date(
            db=db,
            user_id=user_id,
            generated_for_date=insight_date,
            preferences_hash=preferences_hash,
        )

        if cached_insight is not None:
            valid_cached_insight = _get_valid_cached_insight(db, cached_insight)

            if valid_cached_insight is not None:
                return _map_cached_insight(valid_cached_insight, source="cached-openrouter")

    memory_cache_key = _build_memory_cache_key(
        insight_date,
        investor_type,
        assets,
        content_types,
        settings.OPENROUTER_MODEL if settings.OPENROUTER_API_KEY else "static-fallback",
    )

    if db is None or user_id is None:
        cached_memory_insight = _DAILY_AI_CACHE.get(memory_cache_key)

        if cached_memory_insight is not None:
            return cached_memory_insight

    if not settings.OPENROUTER_API_KEY:
        return _cache_memory_insight_if_needed(
            memory_cache_key,
            db,
            user_id,
            _build_fallback_insight(
                investor_type=investor_type,
                assets=assets,
                content_types=content_types,
                insight_date=insight_date,
                fallback_reason="missing_api_key",
            ),
        )

    try:
        content = _fetch_clean_openrouter_insight_with_retry(investor_type, assets, content_types)
    except EmptyOpenRouterResponseError:
        return _get_previous_success_or_fallback(
            db=db,
            user_id=user_id,
            preferences_hash=preferences_hash,
            investor_type=investor_type,
            assets=assets,
            content_types=content_types,
            insight_date=insight_date,
            fallback_reason="empty_response",
        )
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return _get_previous_success_or_fallback(
            db=db,
            user_id=user_id,
            preferences_hash=preferences_hash,
            investor_type=investor_type,
            assets=assets,
            content_types=content_types,
            insight_date=insight_date,
            fallback_reason="api_request_failed",
        )

    if db is not None and user_id is not None:
        saved_insight = daily_ai_insight_repository.create_or_update_successful_insight(
            db=db,
            user_id=user_id,
            generated_for_date=insight_date,
            preferences_hash=preferences_hash,
            content=content,
            model=settings.OPENROUTER_MODEL,
        )
        return _map_cached_insight(saved_insight, source="openrouter")

    return _cache_memory_insight_if_needed(
        memory_cache_key,
        db,
        user_id,
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


def _fetch_clean_openrouter_insight_with_retry(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
) -> str:
    last_empty_error: EmptyOpenRouterResponseError | None = None
    last_request_error: Exception | None = None

    for _ in range(OPENROUTER_ATTEMPTS):
        try:
            raw_content = _fetch_openrouter_insight(investor_type, assets, content_types)
            return _clean_ai_content(raw_content)
        except EmptyOpenRouterResponseError as exc:
            last_empty_error = exc
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            last_request_error = exc

    if last_empty_error is not None:
        raise last_empty_error

    if last_request_error is not None:
        raise last_request_error

    raise EmptyOpenRouterResponseError()


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
                    "content": (
                        "You write concise plain text for a crypto education dashboard. "
                        "Do not use Markdown, headings, bullets, emojis, or investment instructions."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 220,
            "temperature": 0.5,
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

    return content


def _build_prompt(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
) -> str:
    assets_text = ", ".join(assets)
    content_types_text = ", ".join(content_types)
    return (
        f"Write one daily educational crypto insight for a {investor_type}. "
        f"Use these selected assets: {assets_text}. "
        f"Use these preferred content types as context: {content_types_text}. "
        "Write 80 to 120 words in plain text only. "
        "Mention at least one selected asset when possible. "
        "Do not use Markdown, headings, bullets, emojis, or decorative symbols. "
        "Do not give buy, sell, or price prediction recommendations. "
        f"End with this exact sentence: {DISCLAIMER}"
    )


def _clean_ai_content(raw_content: str | None) -> str:
    if not isinstance(raw_content, str):
        raise EmptyOpenRouterResponseError()

    text = raw_content.strip()
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*.*(?:\n|$)", "", text)
    text = re.sub(r"(?i)^\s*(daily\s+)?insight\s*:\s*", "", text)
    text = re.sub(r"(?m)^\s*[-*\u2022]\s+", "", text)
    text = re.sub(r"[*_`~]+", "", text)
    text = _remove_decorative_symbols(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = _fix_spacing_before_punctuation(text)

    if _looks_like_prompt_echo(text):
        raise EmptyOpenRouterResponseError()

    if _word_count(text) < MIN_AI_WORDS:
        raise EmptyOpenRouterResponseError()

    if DISCLAIMER.lower() not in text.lower():
        text = _trim_to_complete_sentence(text, MAX_AI_CHARS - len(DISCLAIMER) - 2)
        text = f"{text.rstrip(' .!?')}. {DISCLAIMER}"

    text = _trim_to_complete_sentence(text, MAX_AI_CHARS)

    if _word_count(text) < MIN_AI_WORDS:
        raise EmptyOpenRouterResponseError()

    return text


def _looks_like_prompt_echo(text: str) -> bool:
    lowered_text = text.lower()
    return any(phrase in lowered_text for phrase in PROMPT_ECHO_PHRASES)


def _remove_decorative_symbols(text: str) -> str:
    cleaned_chars = []

    for character in text:
        category = unicodedata.category(character)

        if category in {"So", "Sk"} or category.startswith("C"):
            continue

        cleaned_chars.append(character)

    return "".join(cleaned_chars)


def _fix_spacing_before_punctuation(text: str) -> str:
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def _trim_to_complete_sentence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars].strip()
    last_sentence_end = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))

    if last_sentence_end >= 120:
        return truncated[: last_sentence_end + 1]

    return truncated.rsplit(" ", 1)[0].rstrip(",;:") + "."


def _word_count(text: str) -> int:
    return len([word for word in text.split(" ") if word])


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
        f"{DISCLAIMER}"
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


def _get_previous_success_or_fallback(
    db: Session | None,
    user_id: int | None,
    preferences_hash: str,
    investor_type: str,
    assets: list[str],
    content_types: list[str],
    insight_date: date,
    fallback_reason: str,
) -> AiInsightResponse:
    if db is not None and user_id is not None:
        previous_insights = daily_ai_insight_repository.get_successful_insights_by_user(
            db=db,
            user_id=user_id,
            preferences_hash=preferences_hash,
        )

        for previous_insight in previous_insights:
            valid_previous_insight = _get_valid_cached_insight(db, previous_insight)

            if valid_previous_insight is None:
                continue

            return _map_cached_insight(
                valid_previous_insight,
                source="cached-openrouter",
                fallback_reason="using_previous_success",
            )

    return _build_fallback_insight(
        investor_type=investor_type,
        assets=assets,
        content_types=content_types,
        insight_date=insight_date,
        fallback_reason=fallback_reason,
    )


def _get_valid_cached_insight(db: Session, insight):
    try:
        cleaned_content = _clean_ai_content(insight.content)
    except EmptyOpenRouterResponseError:
        daily_ai_insight_repository.delete_insight(db, insight)
        return None

    if cleaned_content != insight.content:
        return daily_ai_insight_repository.update_insight_content(db, insight, cleaned_content)

    return insight


def _map_cached_insight(
    insight,
    source: str,
    fallback_reason: str | None = None,
) -> AiInsightResponse:
    return AiInsightResponse(
        title="AI Insight of the Day",
        content=insight.content,
        model=insight.model,
        source=source,
        fallback_reason=fallback_reason,
        generated_for_date=insight.generated_for_date,
        item_key=_build_item_key(insight.generated_for_date),
    )


def _build_preferences_hash(
    investor_type: str,
    assets: list[str],
    content_types: list[str],
) -> str:
    payload = {
        "investor_type": investor_type.strip().lower(),
        "assets": sorted(asset.strip().lower() for asset in assets),
        "content_types": sorted(content_type.strip().lower() for content_type in content_types),
    }
    encoded_payload = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded_payload).hexdigest()


def _build_item_key(insight_date: date) -> str:
    return f"ai-insight-{insight_date.isoformat()}"


def _build_memory_cache_key(
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


def _cache_memory_insight_if_needed(
    cache_key: tuple,
    db: Session | None,
    user_id: int | None,
    insight: AiInsightResponse,
) -> AiInsightResponse:
    if db is None or user_id is None:
        _DAILY_AI_CACHE[cache_key] = insight

    return insight
