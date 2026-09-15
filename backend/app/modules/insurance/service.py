from app.core.exceptions import AppError
from app.modules.profile.repository import ProfileRepository

from .repository import InsuranceRepository
from .schemas import CoverageAdequacyOut, InsuranceOverviewOut, InsurancePolicyCreate, InsurancePolicyOut, InsurancePolicyUpdate


def _coverage_adequacy(access_token: str, user_id: str, policies: list[dict]) -> CoverageAdequacyOut:
    profile = ProfileRepository.get_by_user_id(access_token, user_id)
    annual_income = float(profile["monthly_income"]) * 12 if profile else 0.0
    active_term_cover = sum(float(policy["sum_assured"]) for policy in policies if policy["policy_type"] == "term" and policy["status"] == "active")
    recommended = annual_income * 10
    warning = None
    if annual_income > 0 and active_term_cover < recommended:
        warning = f"Active term cover is below 10× annual income. Consider at least ₹{recommended:,.0f} of total term cover."
    elif annual_income == 0:
        warning = "Add your financial profile to assess term-cover adequacy against income."
    return CoverageAdequacyOut(annual_income=annual_income, active_term_cover=active_term_cover, recommended_term_cover=recommended, is_adequate=annual_income > 0 and active_term_cover >= recommended, warning=warning)


class InsuranceService:
    @staticmethod
    def list(access_token: str, user_id: str) -> InsuranceOverviewOut:
        policies = InsuranceRepository.list_by_user(access_token, user_id)
        return InsuranceOverviewOut(policies=[InsurancePolicyOut(**policy) for policy in policies], coverage_adequacy=_coverage_adequacy(access_token, user_id, policies))

    @staticmethod
    def create(access_token: str, user_id: str, payload: InsurancePolicyCreate) -> InsurancePolicyOut:
        row = InsuranceRepository.create(access_token, user_id, payload.model_dump(mode="json"))
        return InsurancePolicyOut(**row)

    @staticmethod
    def get(access_token: str, user_id: str, policy_id: str) -> InsurancePolicyOut:
        row = InsuranceRepository.get_by_id(access_token, user_id, policy_id)
        if not row:
            raise AppError("Insurance policy not found.", 404)
        return InsurancePolicyOut(**row)

    @staticmethod
    def update(access_token: str, user_id: str, policy_id: str, payload: InsurancePolicyUpdate) -> InsurancePolicyOut:
        existing = InsuranceRepository.get_by_id(access_token, user_id, policy_id)
        if not existing:
            raise AppError("Insurance policy not found.", 404)
        updates = payload.model_dump(exclude_unset=True, mode="json")
        merged = {**existing, **updates}
        if merged.get("coverage_end_date") and merged["coverage_end_date"] < merged["renewal_date"]:
            raise AppError("coverage_end_date cannot be before renewal_date", 422)
        return InsurancePolicyOut(**(InsuranceRepository.update(access_token, user_id, policy_id, updates) if updates else existing))

    @staticmethod
    def delete(access_token: str, user_id: str, policy_id: str) -> None:
        if not InsuranceRepository.get_by_id(access_token, user_id, policy_id):
            raise AppError("Insurance policy not found.", 404)
        InsuranceRepository.delete(access_token, user_id, policy_id)
