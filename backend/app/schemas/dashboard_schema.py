from pydantic import BaseModel


class DashboardProfileResponse(BaseModel):
    name: str
    email: str
    investor_type: str
    assets: list[str]
    content_types: list[str]


class PriceItemResponse(BaseModel):
    coin_id: str
    symbol: str
    price_usd: float
    change_24h: float | None
    item_key: str


class NewsItemResponse(BaseModel):
    title: str
    source: str
    url: str
    summary: str
    related_assets: list[str]
    item_key: str


class AiInsightResponse(BaseModel):
    title: str
    content: str
    model: str
    item_key: str


class MemeResponse(BaseModel):
    title: str
    image_url: str
    caption: str
    item_key: str


class DashboardResponse(BaseModel):
    profile: DashboardProfileResponse
    prices: list[PriceItemResponse]
    news: list[NewsItemResponse]
    ai_insight: AiInsightResponse
    meme: MemeResponse
