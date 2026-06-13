import random

from app.schemas.dashboard_schema import MemeResponse


STATIC_MEMES = [
    {
        "title": "Crypto Meme",
        "image_url": "/memes/hodl.svg",
        "caption": "Portfolio down 2%, conviction presentation up 200 slides.",
        "source": "local-static",
        "item_key": "meme-hodl",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/to-the-moon.svg",
        "caption": "Refreshing the chart until gravity negotiates.",
        "source": "local-static",
        "item_key": "meme-to-the-moon",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/gas-fees.svg",
        "caption": "Buying the dip, then tipping the network like a five-star restaurant.",
        "source": "local-static",
        "item_key": "meme-gas-fees",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/diamond-hands.svg",
        "caption": "Emotionally diversified: 90% patience, 10% dramatic chart staring.",
        "source": "local-static",
        "item_key": "meme-diamond-hands",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/market-dip.svg",
        "caption": "The chart called it a dip. My watchlist called it a personality test.",
        "source": "local-static",
        "item_key": "meme-market-dip",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/chart-drama.svg",
        "caption": "One tiny candle moved and the group chat opened an emergency room.",
        "source": "local-static",
        "item_key": "meme-chart-drama",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/seed-phrase.svg",
        "caption": "Security plan: less sticky note, more responsible adult energy.",
        "source": "local-static",
        "item_key": "meme-seed-phrase",
    },
    {
        "title": "Crypto Meme",
        "image_url": "/memes/refresh-ritual.svg",
        "caption": "Daily ritual: refresh dashboard, breathe, remember it is educational.",
        "source": "local-static",
        "item_key": "meme-refresh-ritual",
    },
]


def get_crypto_meme() -> MemeResponse:
    return MemeResponse(**random.choice(STATIC_MEMES))
