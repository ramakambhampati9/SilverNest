from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


SWPFrequency = Literal["monthly", "quarterly", "annual"]
SWPPlanType = Literal["goal", "retirement"]
SWPStatus = Literal["active", "paused", "completed"]


class SWPPlanCreate(BaseModel):
    plan_type: SWPPlanType
    identifier: str = Field(min_length=1, max_length=50)
    withdrawal_amount: float = Field(gt=0)
    frequency: SWPFrequency = "monthly"
    annual_growth_pct: float = Field(default=0, ge=0)
    expected_return_pct: float = Field(default=0, ge=0)
    start_date: date
    end_date: Optional[date] = None
    goal_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_source_and_dates(self) -> "SWPPlanCreate":
        if self.plan_type == "goal" and not self.goal_id:
            raise ValueError("goal_id is required for a goal SWP plan")
        if self.plan_type == "retirement" and self.goal_id:
            raise ValueError("goal_id is only allowed for a goal SWP plan")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class SWPPlanUpdate(BaseModel):
    withdrawal_amount: Optional[float] = Field(default=None, gt=0)
    frequency: Optional[SWPFrequency] = None
    annual_growth_pct: Optional[float] = Field(default=None, ge=0)
    expected_return_pct: Optional[float] = Field(default=None, ge=0)
    end_date: Optional[date] = None
    status: Optional[SWPStatus] = None


class SWPPlanOut(BaseModel):
    id: str
    user_id: str
    goal_id: Optional[str] = None
    plan_type: SWPPlanType
    identifier: str
    withdrawal_amount: float
    frequency: SWPFrequency
    annual_growth_pct: float
    expected_return_pct: float
    start_date: date
    next_withdrawal_date: date
    end_date: Optional[date] = None
    last_withdrawal_date: Optional[date] = None
    status: SWPStatus
    current_corpus: float
    estimated_depletion_date: Optional[date] = None
    sustainability_warning: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SWPExecutionOut(BaseModel):
    plan: SWPPlanOut
    transaction_id: str
    withdrawn_amount: float
    quantity_sold: float
