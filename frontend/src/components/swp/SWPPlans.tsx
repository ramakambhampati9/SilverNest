import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CalendarClock, Play, TriangleAlert } from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { InputField } from '../common/InputField';
import { swpService } from '../../services/swpService';
import { formatINR } from '../../utils/currency';
import type { SWPPlanType } from '../../types/api';

const schema = z.object({
  identifier: z.string().trim().min(1, 'Holding identifier is required'),
  withdrawal_amount: z.number().gt(0, 'Withdrawal must be greater than zero'),
  frequency: z.enum(['monthly', 'quarterly', 'annual']),
  annual_growth_pct: z.number().min(0),
  expected_return_pct: z.number().min(0),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

interface SWPPlansProps {
  planType: SWPPlanType;
  goalId?: string;
  expectedReturnPct?: number;
}

const today = new Date().toISOString().slice(0, 10);

export const SWPPlans: React.FC<SWPPlansProps> = ({ planType, goalId, expectedReturnPct = 0 }) => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const queryKey = ['swpPlans', planType, goalId];
  const { data: plans = [], isLoading } = useQuery({
    queryKey,
    queryFn: () => swpService.getPlans({ plan_type: planType, ...(goalId ? { goal_id: goalId } : {}) }),
  });
  const { register, handleSubmit, formState: { errors }, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { identifier: '', withdrawal_amount: 0, frequency: 'monthly', annual_growth_pct: 0, expected_return_pct: expectedReturnPct, start_date: today, end_date: '' },
  });
  const invalidate = () => queryClient.invalidateQueries({ queryKey });
  const createMutation = useMutation({
    mutationFn: (data: FormData) => swpService.createPlan({ ...data, plan_type: planType, goal_id: goalId, end_date: data.end_date || null }),
    onSuccess: () => { invalidate(); reset({ identifier: '', withdrawal_amount: 0, frequency: 'monthly', annual_growth_pct: 0, expected_return_pct: expectedReturnPct, start_date: today, end_date: '' }); setError(null); },
    onError: (err: Error) => setError(err.message || 'Unable to save SWP plan.'),
  });
  const executeMutation = useMutation({
    mutationFn: swpService.executePlan,
    onSuccess: () => { invalidate(); queryClient.invalidateQueries({ queryKey: ['portfolioHoldings'] }); setError(null); },
    onError: (err: Error) => setError(err.message || 'Unable to execute SWP withdrawal.'),
  });

  return <Card title="SWP Plans" className="mt-4">
    <p className="text-secondary text-sm mb-3">Set a recurring withdrawal from an existing holding. Each due withdrawal is recorded as a portfolio sell.</p>
    {error && <div className="alert alert-danger mb-3">{error}</div>}
    {isLoading ? <div className="skeleton skeleton-card" /> : plans.map((plan) => {
      const isDue = plan.status === 'active' && plan.next_withdrawal_date <= today;
      return <div className="swp-plan-row" key={plan.id}>
        <div><strong>{formatINR(plan.withdrawal_amount)} / {plan.frequency.slice(0, -2)}</strong><p className="text-secondary text-xs m-0">{plan.identifier} · Next: {plan.next_withdrawal_date}</p></div>
        <div className="text-right"><span className={`status-pill status-sm ${plan.status === 'active' ? 'status-success' : 'status-neutral'}`}>{plan.status}</span>{isDue && <Button variant="secondary" className="btn-sm mt-2" isLoading={executeMutation.isPending} onClick={() => executeMutation.mutate(plan.id)}><Play size={13} /> Execute</Button>}</div>
        {plan.sustainability_warning && <div className="swp-warning"><TriangleAlert size={14} />{plan.sustainability_warning}</div>}
      </div>;
    })}
    {!isLoading && !plans.length && <p className="text-secondary text-sm mb-3">No recurring withdrawals configured.</p>}
    <form className="swp-form" onSubmit={handleSubmit((data) => { setError(null); createMutation.mutate(data); })}>
      <div className="form-row-2"><InputField label="Holding Identifier" placeholder="Fund / asset code" error={errors.identifier?.message} {...register('identifier')} /><InputField label="Withdrawal Amount (₹)" type="number" min="0" error={errors.withdrawal_amount?.message} {...register('withdrawal_amount', { valueAsNumber: true })} /></div>
      <div className="form-row-3 mt-3"><div className="form-group"><label className="form-label" htmlFor={`swp-frequency-${planType}`}>Frequency</label><select id={`swp-frequency-${planType}`} className="form-control" {...register('frequency')}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option></select></div><InputField label="Expected Return (%)" type="number" step="0.1" error={errors.expected_return_pct?.message} {...register('expected_return_pct', { valueAsNumber: true })} /><InputField label="Withdrawal Growth (%)" type="number" step="0.1" error={errors.annual_growth_pct?.message} {...register('annual_growth_pct', { valueAsNumber: true })} /></div>
      <div className="form-row-2 mt-3"><InputField label="First Withdrawal" type="date" error={errors.start_date?.message} {...register('start_date')} /><InputField label="End Date (optional)" type="date" {...register('end_date')} /></div>
      <Button type="submit" variant="primary" className="mt-3" isLoading={createMutation.isPending}><CalendarClock size={16} /> Add SWP Plan</Button>
    </form>
  </Card>;
};
