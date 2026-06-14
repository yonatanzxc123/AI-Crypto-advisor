from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.mappers.preference_mapper import map_preference_to_response
from app.repositories import preference_repository
from app.schemas.dashboard_schema import DashboardProfileResponse, DashboardResponse
from app.services import ai_service, coingecko_service, meme_service, news_service


def get_today_dashboard(db: Session, current_user: User) -> DashboardResponse:
    preference = preference_repository.get_preference_by_user_id(db, current_user.id)

    if preference is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete onboarding before viewing the dashboard",
        )

    preference_response = map_preference_to_response(preference)
    profile = DashboardProfileResponse(
        name=current_user.name,
        email=current_user.email,
        investor_type=preference_response.investor_type,
        assets=preference_response.assets,
        content_types=preference_response.content_types,
    )

    # Dashboard source contract: CoinGecko prices, static MVP news, optional OpenRouter AI, local meme assets.
    return DashboardResponse(
        profile=profile,
        prices=coingecko_service.get_coin_prices(preference_response.assets),
        news=news_service.get_market_news(preference_response.assets),
        ai_insight=ai_service.get_ai_insight(
            investor_type=preference_response.investor_type,
            assets=preference_response.assets,
            content_types=preference_response.content_types,
            db=db,
            user_id=current_user.id,
        ),
        meme=meme_service.get_crypto_meme(),
    )
