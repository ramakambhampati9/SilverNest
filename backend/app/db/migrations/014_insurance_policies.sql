CREATE TABLE IF NOT EXISTS public.insurance_policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  policy_type TEXT NOT NULL CHECK (policy_type IN ('term', 'health', 'other')),
  provider_name TEXT NOT NULL,
  policy_number TEXT,
  sum_assured NUMERIC NOT NULL DEFAULT 0 CHECK (sum_assured >= 0),
  premium_amount NUMERIC NOT NULL DEFAULT 0 CHECK (premium_amount >= 0),
  premium_frequency TEXT NOT NULL DEFAULT 'annual' CHECK (premium_frequency IN ('monthly', 'quarterly', 'annual')),
  renewal_date DATE NOT NULL,
  coverage_end_date DATE,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'lapsed', 'cancelled')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  CHECK (coverage_end_date IS NULL OR coverage_end_date >= renewal_date)
);

ALTER TABLE public.insurance_policies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own insurance policies"
  ON public.insurance_policies FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS insurance_policies_user_renewal_idx
  ON public.insurance_policies(user_id, renewal_date);

DROP TRIGGER IF EXISTS insurance_policies_set_updated_at ON public.insurance_policies;
CREATE TRIGGER insurance_policies_set_updated_at
  BEFORE UPDATE ON public.insurance_policies
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
