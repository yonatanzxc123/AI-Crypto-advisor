from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.onboarding_schema import OnboardingRequest
from app.schemas.preference_schema import PreferenceResponse
from app.services import onboarding_service


router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/me", response_model=PreferenceResponse)
def get_my_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreferenceResponse:
    return onboarding_service.get_my_preferences(db, current_user)


@router.post("", response_model=PreferenceResponse)
def save_my_onboarding(
    onboarding_data: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreferenceResponse:
    return onboarding_service.save_my_preferences(db, current_user, onboarding_data)
