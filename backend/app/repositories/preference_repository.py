from sqlalchemy.orm import Session

from app.db.models import Preference


def get_preference_by_user_id(db: Session, user_id: int) -> Preference | None:
    return db.query(Preference).filter(Preference.user_id == user_id).first()


def create_preference(
    db: Session,
    user_id: int,
    assets_json: str,
    investor_type: str,
    content_types_json: str,
) -> Preference:
    preference = Preference(
        user_id=user_id,
        assets_json=assets_json,
        investor_type=investor_type,
        content_types_json=content_types_json,
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def update_preference(
    db: Session,
    preference: Preference,
    assets_json: str | None = None,
    investor_type: str | None = None,
    content_types_json: str | None = None,
) -> Preference:
    if assets_json is not None:
        preference.assets_json = assets_json

    if investor_type is not None:
        preference.investor_type = investor_type

    if content_types_json is not None:
        preference.content_types_json = content_types_json

    db.commit()
    db.refresh(preference)
    return preference
