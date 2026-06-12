from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.mappers.user_mapper import map_user_to_response
from app.repositories import user_repository
from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.schemas.user_schema import UserCreate, UserResponse


def register_user(db: Session, user_data: UserCreate) -> UserResponse:
    existing_user = user_repository.get_user_by_email(db, user_data.email)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    password_hash = hash_password(user_data.password)
    user = user_repository.create_user(
        db=db,
        email=user_data.email,
        name=user_data.name,
        password_hash=password_hash,
    )

    return map_user_to_response(user)


def login_user(db: Session, credentials: LoginRequest) -> TokenResponse:
    user = user_repository.get_user_by_email(db, credentials.email)

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=access_token)
