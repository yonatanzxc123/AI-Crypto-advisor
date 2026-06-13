from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


ALLOWED_SECTION_TYPES = {"price", "news", "ai_insight", "meme"}
ALLOWED_VOTES = {"up", "down"}


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_type: str
    item_key: str
    vote: str

    @field_validator("section_type")
    @classmethod
    def validate_section_type(cls, value: str) -> str:
        section_type = value.strip().lower()

        if section_type not in ALLOWED_SECTION_TYPES:
            raise ValueError("Invalid section type")

        return section_type

    @field_validator("item_key")
    @classmethod
    def validate_item_key(cls, value: str) -> str:
        item_key = value.strip()

        if not item_key:
            raise ValueError("Item key is required")

        return item_key

    @field_validator("vote")
    @classmethod
    def validate_vote(cls, value: str) -> str:
        vote = value.strip().lower()

        if vote not in ALLOWED_VOTES:
            raise ValueError("Invalid vote")

        return vote


class FeedbackMessageResponse(BaseModel):
    message: str


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    section_type: str
    item_key: str
    vote: str
    created_at: datetime
