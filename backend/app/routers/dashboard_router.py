from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.dashboard_schema import DashboardResponse
from app.services import dashboard_service


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/today", response_model=DashboardResponse)
def get_today_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    return dashboard_service.get_today_dashboard(db, current_user)
