from datetime import date

from sqlalchemy.orm import Session

from app.db.models import DailyAiInsight


def get_successful_insight_for_date(
    db: Session,
    user_id: int,
    generated_for_date: date,
    preferences_hash: str,
) -> DailyAiInsight | None:
    return (
        db.query(DailyAiInsight)
        .filter(
            DailyAiInsight.user_id == user_id,
            DailyAiInsight.generated_for_date == generated_for_date,
            DailyAiInsight.preferences_hash == preferences_hash,
            DailyAiInsight.source == "openrouter",
        )
        .first()
    )


def get_latest_successful_insight_by_user(
    db: Session,
    user_id: int,
    preferences_hash: str | None = None,
) -> DailyAiInsight | None:
    insights = get_successful_insights_by_user(
        db=db,
        user_id=user_id,
        preferences_hash=preferences_hash,
        limit=1,
    )

    return insights[0] if insights else None


def get_successful_insights_by_user(
    db: Session,
    user_id: int,
    preferences_hash: str | None = None,
    limit: int = 5,
) -> list[DailyAiInsight]:
    query = (
        db.query(DailyAiInsight)
        .filter(
            DailyAiInsight.user_id == user_id,
            DailyAiInsight.source == "openrouter",
        )
    )

    if preferences_hash is not None:
        query = query.filter(DailyAiInsight.preferences_hash == preferences_hash)

    return query.order_by(DailyAiInsight.generated_for_date.desc(), DailyAiInsight.updated_at.desc()).limit(limit).all()


def create_or_update_successful_insight(
    db: Session,
    user_id: int,
    generated_for_date: date,
    preferences_hash: str,
    content: str,
    model: str,
) -> DailyAiInsight:
    insight = get_successful_insight_for_date(
        db=db,
        user_id=user_id,
        generated_for_date=generated_for_date,
        preferences_hash=preferences_hash,
    )

    if insight is None:
        insight = DailyAiInsight(
            user_id=user_id,
            generated_for_date=generated_for_date,
            preferences_hash=preferences_hash,
            content=content,
            model=model,
            source="openrouter",
        )
        db.add(insight)
    else:
        insight.content = content
        insight.model = model
        insight.source = "openrouter"

    db.commit()
    db.refresh(insight)
    return insight


def update_insight_content(db: Session, insight: DailyAiInsight, content: str) -> DailyAiInsight:
    insight.content = content
    db.commit()
    db.refresh(insight)
    return insight


def delete_insight(db: Session, insight: DailyAiInsight) -> None:
    db.delete(insight)
    db.commit()
