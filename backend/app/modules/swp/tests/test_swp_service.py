from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from app.core.exceptions import AppError
from app.lib.finance_math import calculate_growing_withdrawal_depletion_periods
from app.modules.swp.schemas import SWPPlanCreate
from app.modules.swp.service import SWPService


PLAN_ROW = {
    "id": "swp-1", "user_id": "user-1", "goal_id": "goal-1", "plan_type": "goal",
    "identifier": "fund-1", "withdrawal_amount": 1000, "frequency": "monthly",
    "annual_growth_pct": 0, "expected_return_pct": 0, "start_date": "2026-01-01",
    "next_withdrawal_date": "2026-01-01", "end_date": None, "last_withdrawal_date": None,
    "status": "active", "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
}


def test_growing_withdrawal_reports_depletion_period():
    assert calculate_growing_withdrawal_depletion_periods(3000, 1000, 12, 0, 0) == 3
    assert calculate_growing_withdrawal_depletion_periods(3000, 100, 12, 12, 0) is None


def test_goal_plan_requires_owned_goal_and_holding():
    payload = SWPPlanCreate(plan_type="goal", goal_id="goal-1", identifier="fund-1", withdrawal_amount=1000, start_date=date(2026, 1, 1))
    with patch("app.modules.swp.service.GoalRepository.get_by_id", return_value={"id": "goal-1"}), \
         patch("app.modules.swp.service.PortfolioRepository.get_holding", return_value={"current_value": 50000}), \
         patch("app.modules.swp.service.SWPRepository.create", return_value=PLAN_ROW):
        result = SWPService.create("token", "user-1", payload)
    assert result.current_corpus == 50000
    assert result.estimated_depletion_date is not None


def test_goal_plan_rejects_missing_goal():
    payload = SWPPlanCreate(plan_type="goal", goal_id="missing", identifier="fund-1", withdrawal_amount=1000, start_date=date(2026, 1, 1))
    with patch("app.modules.swp.service.GoalRepository.get_by_id", return_value=None):
        with pytest.raises(AppError, match="Goal not found"):
            SWPService.create("token", "user-1", payload)
