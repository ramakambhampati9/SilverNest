-- Recurring systematic withdrawal plans.  A plan only stores its schedule;
-- each execution is recorded in portfolio_transactions through PortfolioService.
CREATE TABLE IF NOT EXISTS public.swp_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  goal_id UUID REFERENCES public.goals(id) ON DELETE SET NULL,
  plan_type TEXT NOT NULL CHECK (plan_type IN ('goal', 'retirement')),
  identifier TEXT NOT NULL,
  withdrawal_amount NUMERIC NOT NULL CHECK (withdrawal_amount > 0),
  frequency TEXT NOT NULL DEFAULT 'monthly' CHECK (frequency IN ('monthly', 'quarterly', 'annual')),
  annual_growth_pct NUMERIC NOT NULL DEFAULT 0 CHECK (annual_growth_pct >= 0),
  expected_return_pct NUMERIC NOT NULL DEFAULT 0 CHECK (expected_return_pct >= 0),
  start_date DATE NOT NULL,
  next_withdrawal_date DATE NOT NULL,
  end_date DATE,
  last_withdrawal_date DATE,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  CHECK (end_date IS NULL OR end_date >= start_date),
  CHECK ((plan_type = 'goal' AND goal_id IS NOT NULL) OR (plan_type = 'retirement' AND goal_id IS NULL))
);

ALTER TABLE public.swp_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own SWP plans"
  ON public.swp_plans FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS swp_plans_user_next_withdrawal_idx
  ON public.swp_plans(user_id, next_withdrawal_date);

DROP TRIGGER IF EXISTS swp_plans_set_updated_at ON public.swp_plans;
CREATE TRIGGER swp_plans_set_updated_at
  BEFORE UPDATE ON public.swp_plans
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
