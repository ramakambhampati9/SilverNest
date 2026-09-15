from app.core.supabase import supabase_as_user

TABLE = "swp_plans"


class SWPRepository:
    @staticmethod
    def create(access_token: str, user_id: str, payload: dict) -> dict:
        result = supabase_as_user(access_token).table(TABLE).insert({**payload, "user_id": user_id}).execute()
        return result.data[0]

    @staticmethod
    def get_by_id(access_token: str, user_id: str, plan_id: str) -> dict | None:
        result = (supabase_as_user(access_token).table(TABLE).select("*")
                  .eq("user_id", user_id).eq("id", plan_id).maybe_single().execute())
        return result.data if result else None

    @staticmethod
    def list_by_user(access_token: str, user_id: str, goal_id: str | None = None, plan_type: str | None = None) -> list[dict]:
        query = supabase_as_user(access_token).table(TABLE).select("*").eq("user_id", user_id)
        if goal_id:
            query = query.eq("goal_id", goal_id)
        if plan_type:
            query = query.eq("plan_type", plan_type)
        return query.order("next_withdrawal_date").execute().data or []

    @staticmethod
    def update(access_token: str, user_id: str, plan_id: str, payload: dict) -> dict:
        result = (supabase_as_user(access_token).table(TABLE).update(payload)
                  .eq("user_id", user_id).eq("id", plan_id).execute())
        return result.data[0]
