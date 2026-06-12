from sqlalchemy.orm import Session

from app.db.models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, name: str, password_hash: str) -> User:
    user = User(email=email, name=name, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_onboarding_status(db: Session, user_id: int, completed: bool) -> User | None:
    user = get_user_by_id(db, user_id)

    if user is None:
        return None

    user.onboarding_completed = completed
    db.commit()
    db.refresh(user)
    return user
