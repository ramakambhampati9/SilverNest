from fastapi import APIRouter, Depends
from app.middleware.auth import get_access_token, get_current_user
from app.modules.auth.schemas import UserOut
from .schemas import RebalancingOverviewOut, RebalancingTargetSetIn
from .service import RebalancingService

router = APIRouter(prefix="/rebalancing", tags=["rebalancing"])

@router.get("/allocations", response_model=RebalancingOverviewOut)
def get_allocations(goal_id: str | None = None, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return RebalancingService.get(token, user.id, goal_id)

@router.put("/allocations", response_model=RebalancingOverviewOut)
def set_allocations(payload: RebalancingTargetSetIn, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return RebalancingService.set_targets(token, user.id, payload)
