from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    section_type: str
    item_key: str
    vote: Literal["up", "down"]


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    section_type: str
    item_key: str
    vote: str
    created_at: datetime
