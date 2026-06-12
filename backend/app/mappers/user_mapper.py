from app.db.models import User
from app.schemas.user_schema import UserResponse


def map_user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        onboarding_completed=user.onboarding_completed,
        created_at=user.created_at,
    )
