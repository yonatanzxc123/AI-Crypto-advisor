from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.schemas.dashboard_schema import PriceItemResponse


KNOWN_COIN_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "dogecoin": "DOGE",
    "cardano": "ADA",
}

_PRICE_CACHE: dict[tuple[str, ...], list[PriceItemResponse]] = {}


def get_coin_prices(assets: list[str]) -> list[PriceItemResponse]:
    coin_ids = _normalize_assets(assets)

    if not coin_ids:
        return []

    cache_key = tuple(coin_ids)

    try:
        prices = _fetch_prices_with_retry(coin_ids)
        _cache_successful_prices(cache_key, prices)
        return prices
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        cached_prices = _get_cached_prices(cache_key)

        if cached_prices:
            return cached_prices

    return [_build_unavailable_price(coin_id) for coin_id in coin_ids]


def _fetch_prices_with_retry(coin_ids: list[str]) -> list[PriceItemResponse]:
    last_error: Exception | None = None

    for _ in range(2):
        try:
            return _fetch_prices_from_coingecko(coin_ids)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            last_error = exc

    if last_error:
        raise last_error

    raise ValueError("CoinGecko price fetch failed")


def _fetch_prices_from_coingecko(coin_ids: list[str]) -> list[PriceItemResponse]:
    response = httpx.get(
        settings.COINGECKO_SIMPLE_PRICE_URL,
        params={
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_last_updated_at": "true",
        },
        timeout=settings.EXTERNAL_API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    return [
        _build_live_price(coin_id, data[coin_id])
        if coin_id in data and "usd" in data[coin_id]
        else _build_unavailable_price(coin_id)
        for coin_id in coin_ids
    ]


def _build_live_price(coin_id: str, coin_data: dict) -> PriceItemResponse:
    return PriceItemResponse(
        coin_id=coin_id,
        symbol=_get_symbol(coin_id),
        price_usd=float(coin_data["usd"]),
        change_24h=_get_change_24h(coin_data),
        source="coingecko",
        last_updated_at=_get_last_updated_at(coin_data),
        item_key=f"price-{coin_id}",
    )


def _build_unavailable_price(coin_id: str) -> PriceItemResponse:
    return PriceItemResponse(
        coin_id=coin_id,
        symbol=_get_symbol(coin_id),
        price_usd=None,
        change_24h=None,
        source="unavailable",
        last_updated_at=None,
        item_key=f"price-{coin_id}",
    )


def _cache_successful_prices(cache_key: tuple[str, ...], prices: list[PriceItemResponse]) -> None:
    if any(price.source == "coingecko" for price in prices):
        _PRICE_CACHE[cache_key] = prices


def _get_cached_prices(cache_key: tuple[str, ...]) -> list[PriceItemResponse]:
    cached_prices = _PRICE_CACHE.get(cache_key)

    if not cached_prices:
        return []

    return [_copy_price_for_cached_response(price) for price in cached_prices]


def _copy_price_for_cached_response(price: PriceItemResponse) -> PriceItemResponse:
    source = "coingecko-cached" if price.source == "coingecko" else price.source

    return PriceItemResponse(
        coin_id=price.coin_id,
        symbol=price.symbol,
        price_usd=price.price_usd,
        change_24h=price.change_24h,
        source=source,
        last_updated_at=price.last_updated_at,
        item_key=price.item_key,
    )


def _get_change_24h(coin_data: dict) -> float | None:
    change = coin_data.get("usd_24h_change")

    if change is None:
        return None

    return float(change)


def _get_last_updated_at(coin_data: dict) -> datetime | None:
    timestamp = coin_data.get("last_updated_at")

    if timestamp is None:
        return None

    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)


def _get_symbol(coin_id: str) -> str:
    return KNOWN_COIN_SYMBOLS.get(coin_id, coin_id[:4].upper())


def _normalize_assets(assets: list[str]) -> list[str]:
    return [asset.strip().lower() for asset in assets if asset.strip()]
