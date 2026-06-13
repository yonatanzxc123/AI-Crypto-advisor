import random

from app.schemas.dashboard_schema import MemeResponse


STATIC_MEMES = [
    {
        "title": "Crypto Meme",
        "image_url": "https://placehold.co/600x400/png?text=HODL",
        "caption": "When the market dips and your plan still says HODL.",
        "item_key": "meme-hodl",
    },
    {
        "title": "Crypto Meme",
        "image_url": "https://placehold.co/600x400/png?text=To+The+Moon",
        "caption": "Checking charts every five minutes counts as cardio.",
        "item_key": "meme-to-the-moon",
    },
    {
        "title": "Crypto Meme",
        "image_url": "https://placehold.co/600x400/png?text=Gas+Fees",
        "caption": "That moment when the network fee has its own investment thesis.",
        "item_key": "meme-gas-fees",
    },
]


def get_crypto_meme() -> MemeResponse:
    return MemeResponse(**random.choice(STATIC_MEMES))
