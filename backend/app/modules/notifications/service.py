from .repository import NotificationRepository
from .schemas import (
    SIPReminderItem,
    SIPRemindersResponse,
    GoalProgressReminderItem,
    GoalProgressRemindersResponse,
    InsuranceRenewalReminderItem,
    InsuranceRenewalRemindersResponse,
    InAppNotificationFeed,
    InAppNotificationItem,
)
from datetime import date
from app.modules.goals.service import GoalService
from app.modules.insurance.repository import InsuranceRepository
from app.modules.rebalancing.service import RebalancingService


class NotificationService:
    @staticmethod
    def get_sip_reminders() -> SIPRemindersResponse:
        """Collect all SIP-enabled goals and resolve each goal's user email.
        Returns a narrow payload intended solely for n8n SIP reminder delivery.
        No financial calculations are performed here.
        """
        goals = NotificationRepository.list_sip_goals()

        # Build a per-user email cache to avoid redundant Auth API calls
        email_cache: dict[str, str | None] = {}

        reminders: list[SIPReminderItem] = []
        for goal in goals:
            user_id = goal["user_id"]
            if user_id not in email_cache:
                email_cache[user_id] = NotificationRepository.get_user_email(user_id)

            reminders.append(SIPReminderItem(
                user_id=user_id,
                email=email_cache[user_id],
                goal_id=goal["id"],
                goal_name=goal["name"],
                monthly_contribution=goal["monthly_contribution"],
                sip_day=goal["sip_day"],
            ))

        return SIPRemindersResponse(reminders=reminders)

    @staticmethod
    def get_goal_progress_reminders() -> GoalProgressRemindersResponse:
        """Calculate progress for active goals and return those that reached a milestone."""
        goals = NotificationRepository.list_active_goals_for_progress()
        email_cache: dict[str, str | None] = {}
        reminders: list[GoalProgressReminderItem] = []

        defined_milestones = [25, 50, 75, 100]

        for goal in goals:
            target_amount = goal["target_amount"]
            current_amount = goal.get("lumpsum_amount") or 0.0
            
            if target_amount <= 0:
                continue
                
            progress_ratio = current_amount / target_amount
            progress_percentage = round(progress_ratio * 100, 2)
            
            # Find reached milestones
            reached = [m for m in defined_milestones if progress_percentage >= m]
            
            if not reached:
                continue

            user_id = goal["user_id"]
            if user_id not in email_cache:
                email_cache[user_id] = NotificationRepository.get_user_email(user_id)

            reminders.append(GoalProgressReminderItem(
                user_id=user_id,
                email=email_cache[user_id],
                goal_id=goal["id"],
                goal_name=goal["name"],
                target_amount=target_amount,
                current_amount=current_amount,
                progress_percentage=progress_percentage,
                reached_milestones=reached,
            ))

        return GoalProgressRemindersResponse(reminders=reminders)

    @staticmethod
    def get_insurance_renewal_reminders(days_ahead: int = 30) -> InsuranceRenewalRemindersResponse:
        policies = NotificationRepository.list_insurance_renewals(days_ahead)
        email_cache: dict[str, str | None] = {}
        reminders: list[InsuranceRenewalReminderItem] = []
        for policy in policies:
            user_id = policy["user_id"]
            if user_id not in email_cache:
                email_cache[user_id] = NotificationRepository.get_user_email(user_id)
            reminders.append(InsuranceRenewalReminderItem(
                user_id=user_id, email=email_cache[user_id], policy_id=policy["id"],
                provider_name=policy["provider_name"], policy_type=policy["policy_type"],
                renewal_date=str(policy["renewal_date"]), premium_amount=policy["premium_amount"],
                premium_frequency=policy["premium_frequency"],
            ))
        return InsuranceRenewalRemindersResponse(reminders=reminders)

    @staticmethod
    def get_in_app_feed(access_token: str, user_id: str) -> InAppNotificationFeed:
        items: list[InAppNotificationItem] = []
        today = date.today()
        for goal in GoalService.list_goals(access_token, user_id):
            if goal.sip_day == today.day:
                items.append(InAppNotificationItem(id=f"sip-{goal.id}-{today}", title="SIP due today", message=f"{goal.name}: ₹{goal.monthly_contribution:,.0f} contribution is due today.", severity="info", link=f"/goals/{goal.id}"))
            if goal.feasibility_status in ("at_risk", "unlikely"):
                items.append(InAppNotificationItem(id=f"goal-risk-{goal.id}", title="Goal feasibility downgraded", message=f"{goal.name} is currently {goal.feasibility_status.replace('_', ' ')}.", severity="warning", link=f"/goals/{goal.id}"))
        for policy in InsuranceRepository.list_by_user(access_token, user_id):
            renewal = date.fromisoformat(str(policy["renewal_date"]))
            if policy["status"] == "active" and 0 <= (renewal - today).days <= 30:
                items.append(InAppNotificationItem(id=f"renewal-{policy['id']}", title="Insurance renewal approaching", message=f"{policy['provider_name']} renews on {renewal.isoformat()}.", severity="warning", link="/insurance"))
        rebalance = RebalancingService.get(access_token, user_id)
        for allocation in rebalance.allocations:
            if allocation.suggested_trade:
                items.append(InAppNotificationItem(id=f"rebalance-{allocation.asset_class}", title="Rebalancing drift detected", message=allocation.suggested_trade, severity="warning", link="/rebalancing"))
        return InAppNotificationFeed(notifications=items[:3])
