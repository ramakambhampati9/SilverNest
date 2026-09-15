CREATE TABLE IF NOT EXISTS public.rebalancing_targets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  goal_id UUID REFERENCES public.goals(id) ON DELETE CASCADE,
  asset_class TEXT NOT NULL,
  target_pct NUMERIC NOT NULL CHECK (target_pct >= 0 AND target_pct <= 100),
  drift_threshold_pct NUMERIC NOT NULL DEFAULT 5 CHECK (drift_threshold_pct > 0 AND drift_threshold_pct <= 100),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS rebalancing_targets_scope_class_unique
  ON public.rebalancing_targets(user_id, COALESCE(goal_id, '00000000-0000-0000-0000-000000000000'::uuid), asset_class);
ALTER TABLE public.rebalancing_targets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own rebalancing targets" ON public.rebalancing_targets FOR ALL TO authenticated USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
DROP TRIGGER IF EXISTS rebalancing_targets_set_updated_at ON public.rebalancing_targets;
CREATE TRIGGER rebalancing_targets_set_updated_at BEFORE UPDATE ON public.rebalancing_targets FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.networth_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  net_worth NUMERIC NOT NULL,
  recorded_on DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  CONSTRAINT networth_snapshots_user_day_unique UNIQUE (user_id, recorded_on)
);
ALTER TABLE public.networth_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can read own net worth snapshots" ON public.networth_snapshots FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS networth_snapshots_user_date_idx ON public.networth_snapshots(user_id, recorded_on DESC);
