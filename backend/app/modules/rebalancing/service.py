from app.core.exceptions import AppError
from app.modules.goals.repository import GoalRepository
from app.modules.portfolio.repository import PortfolioRepository
from .repository import RebalancingRepository
from .schemas import AllocationComparisonOut, RebalancingOverviewOut, RebalancingTargetSetIn


def _current_values(access_token: str, user_id: str, goal_id: str | None) -> dict[str, float]:
    if not goal_id:
        values: dict[str, float] = {}
        for holding in PortfolioRepository.list_holdings(access_token, user_id):
            values[holding["asset_class"]] = values.get(holding["asset_class"], 0) + float(holding["current_value"])
        return values
    values: dict[str, float] = {}
    for row in RebalancingRepository.list_goal_holding_allocations(access_token, user_id, goal_id):
        holding = row["user_portfolio_holdings"]
        asset_class = holding["asset_class"]
        values[asset_class] = values.get(asset_class, 0) + float(holding["current_value"]) * float(row["allocation_percentage"]) / 100
    return values


class RebalancingService:
    @staticmethod
    def get(access_token: str, user_id: str, goal_id: str | None = None) -> RebalancingOverviewOut:
        if goal_id and not GoalRepository.get_by_id(access_token, user_id, goal_id):
            raise AppError("Goal not found.", 404)
        targets = RebalancingRepository.list_targets(access_token, user_id, goal_id)
        current = _current_values(access_token, user_id, goal_id)
        portfolio_value = sum(current.values())
        rows: list[AllocationComparisonOut] = []
        for target in targets:
            asset_class = target["asset_class"]
            current_value = current.get(asset_class, 0)
            current_pct = current_value / portfolio_value * 100 if portfolio_value else 0
            drift = current_pct - float(target["target_pct"])
            suggested_amount = abs(drift) / 100 * portfolio_value
            suggestion = None
            if abs(drift) >= float(target["drift_threshold_pct"]):
                action = "Decrease" if drift > 0 else "Increase"
                suggestion = f"{action} {asset_class} by ₹{suggested_amount:,.0f}"
            rows.append(AllocationComparisonOut(asset_class=asset_class, target_pct=float(target["target_pct"]), current_pct=round(current_pct, 2), current_value=round(current_value, 2), drift_pct=round(drift, 2), drift_threshold_pct=float(target["drift_threshold_pct"]), suggested_trade=suggestion, suggested_amount=round(suggested_amount, 2)))
        return RebalancingOverviewOut(goal_id=goal_id, portfolio_value=round(portfolio_value, 2), allocations=rows, has_drift_alert=any(row.suggested_trade for row in rows), updated_at=max((target.get("updated_at") for target in targets), default=None))

    @staticmethod
    def set_targets(access_token: str, user_id: str, payload: RebalancingTargetSetIn) -> RebalancingOverviewOut:
        if payload.goal_id and not GoalRepository.get_by_id(access_token, user_id, payload.goal_id):
            raise AppError("Goal not found.", 404)
        RebalancingRepository.replace_targets(access_token, user_id, payload.goal_id, [target.model_dump() for target in payload.targets])
        return RebalancingService.get(access_token, user_id, payload.goal_id)
