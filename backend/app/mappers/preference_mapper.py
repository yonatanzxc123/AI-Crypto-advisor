import json

from app.db.models import Preference
from app.schemas.preference_schema import PreferenceResponse


def _json_string_to_list(value: str | None) -> list[str]:
    if not value:
        return []

    try:
        items = json.loads(value)
    except json.JSONDecodeError:
        return []

    if not isinstance(items, list):
        return []

    return [str(item) for item in items]


def map_preference_to_response(preference: Preference) -> PreferenceResponse:
    return PreferenceResponse(
        id=preference.id,
        user_id=preference.user_id,
        assets=_json_string_to_list(preference.assets_json),
        investor_type=preference.investor_type,
        content_types=_json_string_to_list(preference.content_types_json),
        updated_at=preference.updated_at,
    )
