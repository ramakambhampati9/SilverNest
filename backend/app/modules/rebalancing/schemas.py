from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class RebalancingTargetIn(BaseModel):
    asset_class: str = Field(min_length=1, max_length=80)
    target_pct: float = Field(ge=0, le=100)
    drift_threshold_pct: float = Field(default=5, gt=0, le=100)


class RebalancingTargetSetIn(BaseModel):
    goal_id: Optional[str] = None
    targets: list[RebalancingTargetIn] = Field(min_length=1)

    @model_validator(mode="after")
    def targets_total_one_hundred(self) -> "RebalancingTargetSetIn":
        if abs(sum(target.target_pct for target in self.targets) - 100) > 0.01:
            raise ValueError("Target allocations must add up to 100%")
        if len({target.asset_class.lower() for target in self.targets}) != len(self.targets):
            raise ValueError("Each asset class can appear only once")
        return self


class AllocationComparisonOut(BaseModel):
    asset_class: str
    target_pct: float
    current_pct: float
    current_value: float
    drift_pct: float
    drift_threshold_pct: float
    suggested_trade: Optional[str] = None
    suggested_amount: float = 0


class RebalancingOverviewOut(BaseModel):
    goal_id: Optional[str] = None
    portfolio_value: float
    allocations: list[AllocationComparisonOut]
    has_drift_alert: bool
    updated_at: Optional[datetime] = None
