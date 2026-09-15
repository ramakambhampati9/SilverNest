from fastapi import APIRouter, Depends, status

from app.middleware.auth import get_access_token, get_current_user
from app.modules.auth.schemas import UserOut
from .schemas import SWPExecutionOut, SWPPlanCreate, SWPPlanOut, SWPPlanUpdate
from .service import SWPService

router = APIRouter(prefix="/swp", tags=["swp"])


@router.get("/plans", response_model=list[SWPPlanOut])
def list_plans(goal_id: str | None = None, plan_type: str | None = None, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return SWPService.list(token, user.id, goal_id, plan_type)


@router.post("/plans", response_model=SWPPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(payload: SWPPlanCreate, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return SWPService.create(token, user.id, payload)


@router.put("/plans/{plan_id}", response_model=SWPPlanOut)
def update_plan(plan_id: str, payload: SWPPlanUpdate, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return SWPService.update(token, user.id, plan_id, payload)


@router.post("/plans/{plan_id}/execute", response_model=SWPExecutionOut)
def execute_plan(plan_id: str, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return SWPService.execute(token, user.id, plan_id)
