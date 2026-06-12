from sqlalchemy.orm import Session

from app.db.models import Feedback


def create_feedback(
    db: Session,
    user_id: int,
    section_type: str,
    item_key: str,
    vote: str,
) -> Feedback:
    feedback = Feedback(
        user_id=user_id,
        section_type=section_type,
        item_key=item_key,
        vote=vote,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_user_id(db: Session, user_id: int) -> list[Feedback]:
    return (
        db.query(Feedback)
        .filter(Feedback.user_id == user_id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
