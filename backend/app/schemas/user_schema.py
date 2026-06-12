from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    normalized_email = value.strip().lower()

    if not EMAIL_PATTERN.fullmatch(normalized_email):
        raise ValueError("Invalid email format")

    return normalized_email


class UserCreate(BaseModel):
    email: str
    name: str = Field(min_length=1)
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized_name = value.strip()

        if not normalized_name:
            raise ValueError("Name is required")

        return normalized_name


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    onboarding_completed: bool
    created_at: datetime
