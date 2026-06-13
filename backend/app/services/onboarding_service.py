import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.mappers.preference_mapper import map_preference_to_response
from app.repositories import preference_repository, user_repository
from app.schemas.onboarding_schema import OnboardingRequest
from app.schemas.preference_schema import PreferenceResponse


def get_my_preferences(db: Session, current_user: User) -> PreferenceResponse:
    preference = preference_repository.get_preference_by_user_id(db, current_user.id)

    if preference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding preferences not found",
        )

    return map_preference_to_response(preference)


def save_my_preferences(
    db: Session,
    current_user: User,
    onboarding_data: OnboardingRequest,
) -> PreferenceResponse:
    assets_json = json.dumps(onboarding_data.assets)
    content_types_json = json.dumps(onboarding_data.content_types)

    existing_preference = preference_repository.get_preference_by_user_id(db, current_user.id)

    if existing_preference is None:
        preference = preference_repository.create_preference(
            db=db,
            user_id=current_user.id,
            assets_json=assets_json,
            investor_type=onboarding_data.investor_type,
            content_types_json=content_types_json,
        )
    else:
        preference = preference_repository.update_preference(
            db=db,
            preference=existing_preference,
            assets_json=assets_json,
            investor_type=onboarding_data.investor_type,
            content_types_json=content_types_json,
        )

    user_repository.update_user_onboarding_status(db, current_user.id, completed=True)
    return map_preference_to_response(preference)
