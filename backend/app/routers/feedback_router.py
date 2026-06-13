from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.feedback_schema import FeedbackCreate, FeedbackMessageResponse
from app.services import feedback_service


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackMessageResponse)
def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackMessageResponse:
    return feedback_service.save_feedback(db, current_user, feedback_data)
