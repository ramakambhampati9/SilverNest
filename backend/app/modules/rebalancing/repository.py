from app.core.supabase import supabase_as_user

TARGETS_TABLE = "rebalancing_targets"
ALLOCATIONS_TABLE = "portfolio_goal_allocations"


class RebalancingRepository:
    @staticmethod
    def list_targets(access_token: str, user_id: str, goal_id: str | None) -> list[dict]:
        query = supabase_as_user(access_token).table(TARGETS_TABLE).select("*").eq("user_id", user_id)
        query = query.eq("goal_id", goal_id) if goal_id else query.is_("goal_id", "null")
        return query.order("asset_class").execute().data or []

    @staticmethod
    def replace_targets(access_token: str, user_id: str, goal_id: str | None, targets: list[dict]) -> list[dict]:
        client = supabase_as_user(access_token)
        query = client.table(TARGETS_TABLE).delete().eq("user_id", user_id)
        query = query.eq("goal_id", goal_id) if goal_id else query.is_("goal_id", "null")
        query.execute()
        result = client.table(TARGETS_TABLE).insert([{**target, "user_id": user_id, "goal_id": goal_id} for target in targets]).execute()
        return result.data or []

    @staticmethod
    def list_goal_holding_allocations(access_token: str, user_id: str, goal_id: str) -> list[dict]:
        result = (supabase_as_user(access_token).table(ALLOCATIONS_TABLE)
                  .select("allocation_percentage, user_portfolio_holdings!inner(user_id, asset_class, current_value)")
                  .eq("goal_id", goal_id).eq("user_portfolio_holdings.user_id", user_id).execute())
        return result.data or []
