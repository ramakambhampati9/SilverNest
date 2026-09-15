from __future__ import annotations

import calendar
from datetime import date

from app.core.exceptions import AppError
from app.lib.finance_math import calculate_growing_annuity_pv, calculate_growing_withdrawal_depletion_periods
from app.modules.goals.repository import GoalRepository
from app.modules.portfolio.repository import PortfolioRepository
from app.modules.portfolio.schemas import TransactionIn
from app.modules.portfolio.service import PortfolioService
from app.modules.retirement.repository import RetirementRepository

from .repository import SWPRepository
from .schemas import SWPExecutionOut, SWPPlanCreate, SWPPlanOut, SWPPlanUpdate


_FREQUENCY_MONTHS = {"monthly": 1, "quarterly": 3, "annual": 12}


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year, month = value.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def _to_out(access_token: str, user_id: str, row: dict) -> SWPPlanOut:
    holding = PortfolioRepository.get_holding(access_token, user_id, row["identifier"])
    corpus = float(holding["current_value"]) if holding else 0.0
    interval_months = _FREQUENCY_MONTHS[row["frequency"]]
    periods_per_year = 12 / interval_months
    next_withdrawal_date = date.fromisoformat(str(row["next_withdrawal_date"]))
    end_date = date.fromisoformat(str(row["end_date"])) if row.get("end_date") else None
    horizon_end = end_date or _add_months(next_withdrawal_date, 1200)
    max_periods = max(1, int((horizon_end - next_withdrawal_date).days / (30.44 * interval_months)))

    # Same growing-annuity model used by retirement corpus sizing. It tells us
    # whether the current corpus covers the configured horizon; the iterative
    # calculation below provides the user-facing depletion date.
    required_corpus = calculate_growing_annuity_pv(
        first_payment=float(row["withdrawal_amount"]) * periods_per_year,
        periods=max(1, int(max_periods / periods_per_year)),
        rate_pct=float(row["expected_return_pct"]),
        growth_pct=float(row["annual_growth_pct"]),
    )
    depletion_periods = calculate_growing_withdrawal_depletion_periods(
        corpus=corpus,
        first_payment=float(row["withdrawal_amount"]),
        periods=max_periods,
        annual_return_pct=float(row["expected_return_pct"]),
        annual_growth_pct=float(row["annual_growth_pct"]),
        periods_per_year=periods_per_year,
    )
    depletion_date = _add_months(next_withdrawal_date, depletion_periods * interval_months) if depletion_periods else None
    warning = None
    if corpus <= 0:
        warning = "No current value is available for this holding; an SWP cannot be executed."
    elif depletion_date:
        warning = f"At this rate, corpus depletes by {depletion_date.strftime('%d %b %Y')}."
    elif corpus < required_corpus:
        warning = "The configured withdrawal may not sustain the selected horizon."

    return SWPPlanOut(**row, current_corpus=round(corpus, 2), estimated_depletion_date=depletion_date, sustainability_warning=warning)


class SWPService:
    @staticmethod
    def list(access_token: str, user_id: str, goal_id: str | None = None, plan_type: str | None = None) -> list[SWPPlanOut]:
        return [_to_out(access_token, user_id, row) for row in SWPRepository.list_by_user(access_token, user_id, goal_id, plan_type)]

    @staticmethod
    def create(access_token: str, user_id: str, payload: SWPPlanCreate) -> SWPPlanOut:
        if payload.plan_type == "goal" and not GoalRepository.get_by_id(access_token, user_id, payload.goal_id or ""):
            raise AppError("Goal not found.", 404)
        if payload.plan_type == "retirement" and not RetirementRepository.get_by_user_id(access_token, user_id):
            raise AppError("Create a retirement plan before adding a retirement SWP.", 422)
        if not PortfolioRepository.get_holding(access_token, user_id, payload.identifier):
            raise AppError("Create a holding for this asset before adding an SWP plan.", 422)
        row = SWPRepository.create(access_token, user_id, {
            **payload.model_dump(mode="json"),
            "next_withdrawal_date": payload.start_date.isoformat(),
        })
        return _to_out(access_token, user_id, row)

    @staticmethod
    def update(access_token: str, user_id: str, plan_id: str, payload: SWPPlanUpdate) -> SWPPlanOut:
        if not SWPRepository.get_by_id(access_token, user_id, plan_id):
            raise AppError("SWP plan not found.", 404)
        updates = payload.model_dump(exclude_none=True, mode="json")
        row = SWPRepository.update(access_token, user_id, plan_id, updates) if updates else SWPRepository.get_by_id(access_token, user_id, plan_id)
        return _to_out(access_token, user_id, row)

    @staticmethod
    def execute(access_token: str, user_id: str, plan_id: str) -> SWPExecutionOut:
        row = SWPRepository.get_by_id(access_token, user_id, plan_id)
        if not row:
            raise AppError("SWP plan not found.", 404)
        if row["status"] != "active":
            raise AppError("Only active SWP plans can be executed.", 422)
        if date.fromisoformat(str(row["next_withdrawal_date"])) > date.today():
            raise AppError("This withdrawal is not due yet.", 422)
        holding = PortfolioRepository.get_holding(access_token, user_id, row["identifier"])
        if not holding or float(holding["quantity"]) <= 0 or float(holding["current_value"]) <= 0:
            raise AppError("Holding has no executable current value for this SWP.", 422)
        price = float(holding["current_value"]) / float(holding["quantity"])
        quantity = float(row["withdrawal_amount"]) / price
        if quantity > float(holding["quantity"]):
            raise AppError("SWP withdrawal exceeds the remaining holding; pause or reduce the plan.", 422)
        transaction = PortfolioService.process_transaction(access_token, user_id, TransactionIn(
            identifier=row["identifier"], transaction_type="sell", quantity=quantity,
            price=price, amount=float(row["withdrawal_amount"]), transaction_date=date.today(),
            metadata={"swp_plan_id": row["id"], "plan_type": row["plan_type"]},
        ))
        next_date = _add_months(date.fromisoformat(str(row["next_withdrawal_date"])), _FREQUENCY_MONTHS[row["frequency"]])
        status = "completed" if row.get("end_date") and next_date > date.fromisoformat(str(row["end_date"])) else "active"
        updated = SWPRepository.update(access_token, user_id, plan_id, {"last_withdrawal_date": date.today().isoformat(), "next_withdrawal_date": next_date.isoformat(), "status": status})
        return SWPExecutionOut(plan=_to_out(access_token, user_id, updated), transaction_id=transaction.transaction.id, withdrawn_amount=float(row["withdrawal_amount"]), quantity_sold=quantity)
