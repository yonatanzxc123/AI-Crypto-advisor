from app.db.models import Feedback
from app.schemas.feedback_schema import FeedbackResponse


def map_feedback_to_response(feedback: Feedback) -> FeedbackResponse:
    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        section_type=feedback.section_type,
        item_key=feedback.item_key,
        vote=feedback.vote,
        created_at=feedback.created_at,
    )
