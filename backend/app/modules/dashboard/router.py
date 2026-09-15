from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user, get_access_token
from app.modules.auth.schemas import UserOut
from .schemas import DashboardOut
from .service import DashboardService
from app.modules.notifications.router import _require_notification_key

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    user: UserOut = Depends(get_current_user),
    token: str = Depends(get_access_token),
):
    return DashboardService.get_summary(token, user.id)


@router.post("/networth-snapshots")
def snapshot_net_worth(_: None = Depends(_require_notification_key)):
    return {"snapshots_created": DashboardService.snapshot_all()}
