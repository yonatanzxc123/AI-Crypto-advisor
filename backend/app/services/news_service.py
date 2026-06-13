from app.schemas.dashboard_schema import NewsItemResponse


STATIC_NEWS = [
    {
        "title": "Bitcoin market update",
        "source": "Static Fallback",
        "url": "https://example.com/bitcoin-market-update",
        "summary": "Bitcoin remains a key reference point for broad crypto market sentiment.",
        "related_assets": ["bitcoin"],
        "item_key": "news-bitcoin-market-update",
    },
    {
        "title": "Ethereum ecosystem activity",
        "source": "Static Fallback",
        "url": "https://example.com/ethereum-ecosystem-activity",
        "summary": "Ethereum activity often reflects developer interest in DeFi and smart contracts.",
        "related_assets": ["ethereum"],
        "item_key": "news-ethereum-ecosystem-activity",
    },
    {
        "title": "Solana network momentum",
        "source": "Static Fallback",
        "url": "https://example.com/solana-network-momentum",
        "summary": "Solana continues to attract attention from users watching fast-moving ecosystems.",
        "related_assets": ["solana"],
        "item_key": "news-solana-network-momentum",
    },
    {
        "title": "Crypto market risk reminder",
        "source": "Static Fallback",
        "url": "https://example.com/crypto-market-risk-reminder",
        "summary": "Crypto markets can move quickly, so education and risk awareness matter.",
        "related_assets": ["bitcoin", "ethereum", "solana", "dogecoin", "cardano"],
        "item_key": "news-crypto-market-risk-reminder",
    },
]


def get_market_news(assets: list[str]) -> list[NewsItemResponse]:
    selected_assets = {asset.strip().lower() for asset in assets}
    matching_news = [
        news_item
        for news_item in STATIC_NEWS
        if selected_assets.intersection(news_item["related_assets"])
    ]

    if not matching_news:
        matching_news = STATIC_NEWS[-1:]

    return [NewsItemResponse(**news_item) for news_item in matching_news[:3]]
