import httpx

from app.core.config import settings
from app.schemas.dashboard_schema import PriceItemResponse


STATIC_PRICE_FALLBACKS = {
    "bitcoin": {"symbol": "BTC", "price_usd": 65000.0, "change_24h": 1.25},
    "ethereum": {"symbol": "ETH", "price_usd": 3500.0, "change_24h": 0.85},
    "solana": {"symbol": "SOL", "price_usd": 150.0, "change_24h": 2.1},
    "dogecoin": {"symbol": "DOGE", "price_usd": 0.15, "change_24h": -0.4},
    "cardano": {"symbol": "ADA", "price_usd": 0.45, "change_24h": 0.3},
}


def get_coin_prices(assets: list[str]) -> list[PriceItemResponse]:
    coin_ids = _normalize_assets(assets)

    if not coin_ids:
        return []

    try:
        api_prices = _fetch_prices_from_coingecko(coin_ids)
        return _merge_api_prices_with_fallbacks(coin_ids, api_prices)
    except (httpx.HTTPError, ValueError, KeyError):
        pass

    return _get_fallback_prices(coin_ids)


def _fetch_prices_from_coingecko(coin_ids: list[str]) -> list[PriceItemResponse]:
    response = httpx.get(
        settings.COINGECKO_SIMPLE_PRICE_URL,
        params={
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        timeout=settings.EXTERNAL_API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    return [
        PriceItemResponse(
            coin_id=coin_id,
            symbol=_get_symbol(coin_id),
            price_usd=float(data[coin_id]["usd"]),
            change_24h=_get_change_24h(data[coin_id]),
            item_key=f"price-{coin_id}",
        )
        for coin_id in coin_ids
        if coin_id in data and "usd" in data[coin_id]
    ]


def _get_fallback_prices(coin_ids: list[str]) -> list[PriceItemResponse]:
    return [_build_fallback_price(coin_id) for coin_id in coin_ids]


def _merge_api_prices_with_fallbacks(
    coin_ids: list[str],
    api_prices: list[PriceItemResponse],
) -> list[PriceItemResponse]:
    api_prices_by_coin_id = {price.coin_id: price for price in api_prices}

    return [
        api_prices_by_coin_id.get(coin_id) or _build_fallback_price(coin_id)
        for coin_id in coin_ids
    ]


def _build_fallback_price(coin_id: str) -> PriceItemResponse:
    fallback = STATIC_PRICE_FALLBACKS.get(
        coin_id,
        {"symbol": coin_id[:4].upper(), "price_usd": 0.0, "change_24h": None},
    )

    return PriceItemResponse(
        coin_id=coin_id,
        symbol=fallback["symbol"],
        price_usd=float(fallback["price_usd"]),
        change_24h=fallback["change_24h"],
        item_key=f"price-{coin_id}",
    )


def _get_change_24h(coin_data: dict) -> float | None:
    change = coin_data.get("usd_24h_change")

    if change is None:
        return None

    return float(change)


def _get_symbol(coin_id: str) -> str:
    fallback = STATIC_PRICE_FALLBACKS.get(coin_id)

    if fallback:
        return fallback["symbol"]

    return coin_id[:4].upper()


def _normalize_assets(assets: list[str]) -> list[str]:
    return [asset.strip().lower() for asset in assets if asset.strip()]
