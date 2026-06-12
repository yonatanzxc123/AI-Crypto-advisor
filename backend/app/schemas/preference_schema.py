from datetime import datetime

from pydantic import BaseModel


class PreferenceCreate(BaseModel):
    assets: list[str]
    investor_type: str
    content_types: list[str]


class PreferenceUpdate(BaseModel):
    assets: list[str] | None = None
    investor_type: str | None = None
    content_types: list[str] | None = None


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    assets: list[str]
    investor_type: str
    content_types: list[str]
    updated_at: datetime
