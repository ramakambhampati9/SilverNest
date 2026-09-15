from pydantic import BaseModel
from typing import Optional


class SIPReminderItem(BaseModel):
    """Minimal data shape returned per SIP-enabled goal for n8n notifications.
    Intentionally narrow — do NOT add financial/feasibility fields here."""
    user_id: str
    email: Optional[str]
    goal_id: str
    goal_name: str
    monthly_contribution: float
    sip_day: int


class SIPRemindersResponse(BaseModel):
    reminders: list[SIPReminderItem]


class GoalProgressReminderItem(BaseModel):
    user_id: str
    email: Optional[str]
    goal_id: str
    goal_name: str
    target_amount: float
    current_amount: float
    progress_percentage: float
    reached_milestones: list[int]


class GoalProgressRemindersResponse(BaseModel):
    reminders: list[GoalProgressReminderItem]


class InsuranceRenewalReminderItem(BaseModel):
    user_id: str
    email: Optional[str]
    policy_id: str
    provider_name: str
    policy_type: str
    renewal_date: str
    premium_amount: float
    premium_frequency: str


class InsuranceRenewalRemindersResponse(BaseModel):
    reminders: list[InsuranceRenewalReminderItem]


class InAppNotificationItem(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    link: str


class InAppNotificationFeed(BaseModel):
    notifications: list[InAppNotificationItem]
