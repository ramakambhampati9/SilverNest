from app.core.supabase import supabase_as_user

TABLE = "insurance_policies"


class InsuranceRepository:
    @staticmethod
    def list_by_user(access_token: str, user_id: str) -> list[dict]:
        result = (supabase_as_user(access_token).table(TABLE).select("*")
                  .eq("user_id", user_id).order("renewal_date").execute())
        return result.data or []

    @staticmethod
    def get_by_id(access_token: str, user_id: str, policy_id: str) -> dict | None:
        result = (supabase_as_user(access_token).table(TABLE).select("*")
                  .eq("user_id", user_id).eq("id", policy_id).maybe_single().execute())
        return result.data if result else None

    @staticmethod
    def create(access_token: str, user_id: str, payload: dict) -> dict:
        result = supabase_as_user(access_token).table(TABLE).insert({**payload, "user_id": user_id}).execute()
        return result.data[0]

    @staticmethod
    def update(access_token: str, user_id: str, policy_id: str, payload: dict) -> dict:
        result = (supabase_as_user(access_token).table(TABLE).update(payload)
                  .eq("user_id", user_id).eq("id", policy_id).execute())
        return result.data[0]

    @staticmethod
    def delete(access_token: str, user_id: str, policy_id: str) -> None:
        (supabase_as_user(access_token).table(TABLE).delete()
         .eq("user_id", user_id).eq("id", policy_id).execute())
