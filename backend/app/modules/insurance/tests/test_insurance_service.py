from datetime import datetime, timezone
from unittest.mock import patch

from app.modules.insurance.service import InsuranceService, _coverage_adequacy


POLICY = {
    "id": "policy-1", "user_id": "user-1", "policy_type": "term",
    "provider_name": "Example Life", "policy_number": "TERM-1", "sum_assured": 500000,
    "premium_amount": 10000, "premium_frequency": "annual", "renewal_date": "2027-01-01",
    "coverage_end_date": None, "status": "active", "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
}


def test_warns_when_active_term_cover_is_below_ten_times_income():
    with patch("app.modules.insurance.service.ProfileRepository.get_by_user_id", return_value={"monthly_income": 100000}):
        adequacy = _coverage_adequacy("token", "user-1", [POLICY])
    assert adequacy.recommended_term_cover == 12_000_000
    assert adequacy.is_adequate is False
    assert "below 10× annual income" in adequacy.warning


def test_list_returns_policies_and_coverage_summary():
    with patch("app.modules.insurance.service.InsuranceRepository.list_by_user", return_value=[{**POLICY, "sum_assured": 12_000_000}]), \
         patch("app.modules.insurance.service.ProfileRepository.get_by_user_id", return_value={"monthly_income": 100000}):
        overview = InsuranceService.list("token", "user-1")
    assert len(overview.policies) == 1
    assert overview.coverage_adequacy.is_adequate is True
