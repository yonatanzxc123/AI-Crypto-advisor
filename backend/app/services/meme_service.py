from datetime import date
import json
from pathlib import Path

from app.schemas.dashboard_schema import MemeResponse


MEMES_FILE = Path(__file__).resolve().parents[1] / "data" / "memes.json"
REQUIRED_MEME_FIELDS = {"title", "image_url", "caption", "source", "item_key"}

FALLBACK_MEMES = [
    {
        "title": "Crypto Meme",
        "image_url": "/memes/hodl.svg",
        "caption": "Portfolio down 2%, conviction presentation up 200 slides.",
        "source": "static-json",
        "item_key": "meme-hodl",
    }
]


def get_crypto_meme(today: date | None = None) -> MemeResponse:
    memes = _load_static_memes()
    selected_date = today or date.today()
    selected_index = selected_date.toordinal() % len(memes)
    return MemeResponse(**memes[selected_index])


def _load_static_memes() -> list[dict]:
    # Static JSON is used instead of Reddit scraping for predictable local and deployed demos.
    try:
        with MEMES_FILE.open(encoding="utf-8") as memes_file:
            data = json.load(memes_file)
    except (OSError, json.JSONDecodeError):
        return FALLBACK_MEMES

    if not isinstance(data, list):
        return FALLBACK_MEMES

    valid_memes = [meme for meme in data if _is_valid_meme(meme)]
    return valid_memes or FALLBACK_MEMES


def _is_valid_meme(meme: object) -> bool:
    if not isinstance(meme, dict):
        return False

    return all(isinstance(meme.get(field), str) and meme[field].strip() for field in REQUIRED_MEME_FIELDS)
