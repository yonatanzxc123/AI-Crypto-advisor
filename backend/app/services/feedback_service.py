from sqlalchemy.orm import Session

from app.db.models import User
from app.repositories import feedback_repository
from app.schemas.feedback_schema import FeedbackCreate, FeedbackMessageResponse


def save_feedback(
    db: Session,
    current_user: User,
    feedback_data: FeedbackCreate,
) -> FeedbackMessageResponse:
    feedback_repository.create_feedback(
        db=db,
        user_id=current_user.id,
        section_type=feedback_data.section_type,
        item_key=feedback_data.item_key,
        vote=feedback_data.vote,
    )

    return FeedbackMessageResponse(message="Feedback saved successfully")
