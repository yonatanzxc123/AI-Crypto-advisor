from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    onboarding_completed: bool
    created_at: datetime
