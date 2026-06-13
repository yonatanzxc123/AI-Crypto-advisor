import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env", override=False)


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AI Crypto Advisor API")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_crypto_advisor.db")
    # Local fallback only. Production must provide a strong SECRET_KEY value.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "local-development-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    EXTERNAL_API_TIMEOUT_SECONDS: int = _get_int_env("EXTERNAL_API_TIMEOUT_SECONDS", 10)
    COINGECKO_SIMPLE_PRICE_URL: str = os.getenv(
        "COINGECKO_SIMPLE_PRICE_URL",
        "https://api.coingecko.com/api/v3/simple/price",
    )
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    OPENROUTER_CHAT_URL: str = os.getenv(
        "OPENROUTER_CHAT_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    BACKEND_CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
