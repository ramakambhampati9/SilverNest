from fastapi import APIRouter, Depends, status

from app.middleware.auth import get_access_token, get_current_user
from app.modules.auth.schemas import UserOut
from .schemas import InsuranceOverviewOut, InsurancePolicyCreate, InsurancePolicyOut, InsurancePolicyUpdate
from .service import InsuranceService

router = APIRouter(prefix="/insurance", tags=["insurance"])


@router.get("/policies", response_model=InsuranceOverviewOut)
def list_policies(user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return InsuranceService.list(token, user.id)


@router.post("/policies", response_model=InsurancePolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(payload: InsurancePolicyCreate, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return InsuranceService.create(token, user.id, payload)


@router.get("/policies/{policy_id}", response_model=InsurancePolicyOut)
def get_policy(policy_id: str, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return InsuranceService.get(token, user.id, policy_id)


@router.put("/policies/{policy_id}", response_model=InsurancePolicyOut)
def update_policy(policy_id: str, payload: InsurancePolicyUpdate, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    return InsuranceService.update(token, user.id, policy_id, payload)


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: str, user: UserOut = Depends(get_current_user), token: str = Depends(get_access_token)):
    InsuranceService.delete(token, user.id, policy_id)
