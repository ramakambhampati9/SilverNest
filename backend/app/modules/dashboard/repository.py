from datetime import date
from app.core.supabase import supabase_admin, supabase_as_user


class DashboardRepository:
    @staticmethod
    def list_snapshots(access_token: str, user_id: str, limit: int = 30) -> list[dict]:
        result = (supabase_as_user(access_token).table("networth_snapshots").select("recorded_on, net_worth")
                  .eq("user_id", user_id).order("recorded_on", desc=True).limit(limit).execute())
        return list(reversed(result.data or []))

    @staticmethod
    def create_daily_snapshots() -> int:
        profiles = supabase_admin.table("financial_profile").select("user_id, existing_savings, existing_investments").execute().data or []
        count = 0
        for profile in profiles:
            holdings = (supabase_admin.table("user_portfolio_holdings").select("current_value")
                        .eq("user_id", profile["user_id"]).execute().data or [])
            portfolio_value = sum(float(holding["current_value"]) for holding in holdings)
            investments = portfolio_value if holdings else float(profile.get("existing_investments") or 0)
            supabase_admin.table("networth_snapshots").upsert({"user_id": profile["user_id"], "net_worth": float(profile.get("existing_savings") or 0) + investments, "recorded_on": date.today().isoformat()}, on_conflict="user_id,recorded_on").execute()
            count += 1
        return count
