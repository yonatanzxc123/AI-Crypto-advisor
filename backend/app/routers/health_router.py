from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def get_health_status() -> dict[str, str]:
    return {"status": "ok"}

