import os


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "AI Crypto Advisor API")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_crypto_advisor.db")
    BACKEND_CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()

