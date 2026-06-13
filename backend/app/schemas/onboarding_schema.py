from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_unique_values(values: list[str]) -> list[str]:
    cleaned_values = []

    for value in values:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("List values cannot be empty")

        if cleaned_value not in cleaned_values:
            cleaned_values.append(cleaned_value)

    return cleaned_values


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assets: list[str] = Field(min_length=1)
    investor_type: str = Field(min_length=1)
    content_types: list[str] = Field(min_length=1)

    @field_validator("assets", "content_types")
    @classmethod
    def validate_list_values(cls, values: list[str]) -> list[str]:
        return _clean_unique_values(values)

    @field_validator("investor_type")
    @classmethod
    def validate_investor_type(cls, value: str) -> str:
        investor_type = value.strip()

        if not investor_type:
            raise ValueError("Investor type is required")

        return investor_type
