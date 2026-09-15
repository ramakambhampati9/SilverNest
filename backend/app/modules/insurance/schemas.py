from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

PolicyType = Literal["term", "health", "other"]
PremiumFrequency = Literal["monthly", "quarterly", "annual"]
PolicyStatus = Literal["active", "lapsed", "cancelled"]


class InsurancePolicyCreate(BaseModel):
    policy_type: PolicyType
    provider_name: str = Field(min_length=1, max_length=120)
    policy_number: Optional[str] = Field(default=None, max_length=100)
    sum_assured: float = Field(default=0, ge=0)
    premium_amount: float = Field(default=0, ge=0)
    premium_frequency: PremiumFrequency = "annual"
    renewal_date: date
    coverage_end_date: Optional[date] = None
    status: PolicyStatus = "active"

    @model_validator(mode="after")
    def validate_dates(self) -> "InsurancePolicyCreate":
        if self.coverage_end_date and self.coverage_end_date < self.renewal_date:
            raise ValueError("coverage_end_date cannot be before renewal_date")
        return self


class InsurancePolicyUpdate(BaseModel):
    policy_type: Optional[PolicyType] = None
    provider_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    policy_number: Optional[str] = Field(default=None, max_length=100)
    sum_assured: Optional[float] = Field(default=None, ge=0)
    premium_amount: Optional[float] = Field(default=None, ge=0)
    premium_frequency: Optional[PremiumFrequency] = None
    renewal_date: Optional[date] = None
    coverage_end_date: Optional[date] = None
    status: Optional[PolicyStatus] = None


class CoverageAdequacyOut(BaseModel):
    annual_income: float
    active_term_cover: float
    recommended_term_cover: float
    is_adequate: bool
    warning: Optional[str] = None


class InsurancePolicyOut(BaseModel):
    id: str
    user_id: str
    policy_type: PolicyType
    provider_name: str
    policy_number: Optional[str] = None
    sum_assured: float
    premium_amount: float
    premium_frequency: PremiumFrequency
    renewal_date: date
    coverage_end_date: Optional[date] = None
    status: PolicyStatus
    created_at: datetime
    updated_at: datetime


class InsuranceOverviewOut(BaseModel):
    policies: list[InsurancePolicyOut]
    coverage_adequacy: CoverageAdequacyOut
