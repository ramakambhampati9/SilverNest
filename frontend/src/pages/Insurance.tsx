import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CheckCircle2, ShieldAlert, ShieldCheck, Trash2 } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { InputField } from '../components/common/InputField';
import { insuranceService } from '../services/insuranceService';
import { formatINR } from '../utils/currency';

const policySchema = z.object({
  policy_type: z.enum(['term', 'health', 'other']),
  provider_name: z.string().trim().min(1, 'Provider name is required'),
  policy_number: z.string().optional(),
  sum_assured: z.number().min(0, 'Cannot be negative'),
  premium_amount: z.number().min(0, 'Cannot be negative'),
  premium_frequency: z.enum(['monthly', 'quarterly', 'annual']),
  renewal_date: z.string().min(1, 'Renewal date is required'),
  coverage_end_date: z.string().optional(),
});
type PolicyFormData = z.infer<typeof policySchema>;
const today = new Date().toISOString().slice(0, 10);

export const Insurance: React.FC = () => {
  const queryClient = useQueryClient();
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const { data, isLoading, error } = useQuery({ queryKey: ['insurancePolicies'], queryFn: () => insuranceService.getPolicies() });
  const { register, handleSubmit, formState: { errors }, reset } = useForm<PolicyFormData>({
    resolver: zodResolver(policySchema),
    defaultValues: { policy_type: 'term', provider_name: '', policy_number: '', sum_assured: 0, premium_amount: 0, premium_frequency: 'annual', renewal_date: today, coverage_end_date: '' },
  });
  const createMutation = useMutation({
    mutationFn: (form: PolicyFormData) => insuranceService.createPolicy({ ...form, policy_number: form.policy_number || null, coverage_end_date: form.coverage_end_date || null, status: 'active' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['insurancePolicies'] }); reset(); setServerError(null); setSuccess(true); setTimeout(() => setSuccess(false), 3000); },
    onError: (err: Error) => setServerError(err.message || 'Unable to save policy.'),
  });
  const deleteMutation = useMutation({
    mutationFn: insuranceService.deletePolicy,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['insurancePolicies'] }),
    onError: (err: Error) => setServerError(err.message || 'Unable to remove policy.'),
  });

  if (isLoading) return <div className="skeleton-loading-container"><div className="skeleton skeleton-banner" /><div className="skeleton skeleton-card mt-3" /></div>;
  if (error || !data) return <div className="error-state-box card p-4"><ShieldAlert size={40} className="text-danger mb-2" /><h3>Failed to load insurance policies</h3><p className="text-secondary">{error?.message || 'Please try again later.'}</p></div>;
  const { policies, coverage_adequacy: adequacy } = data;

  return <div className="insurance-page">
    <div className="page-header-row mb-4"><div><h2>Financial Security</h2><p className="text-secondary">Keep insurance coverage and renewal dates in one place.</p></div></div>
    <div className="emergency-grid">
      <div className="emergency-form-panel"><Card title="Add Insurance Policy">
        {success && <div className="alert alert-success d-flex align-items-center mb-3"><CheckCircle2 size={16} className="me-2" />Policy saved successfully.</div>}
        {serverError && <div className="alert alert-danger mb-3">{serverError}</div>}
        <form onSubmit={handleSubmit((form) => { setServerError(null); createMutation.mutate(form); })}>
          <div className="form-row-2"><div className="form-group"><label className="form-label" htmlFor="policy_type">Policy Type</label><select id="policy_type" className="form-control" {...register('policy_type')}><option value="term">Term Life</option><option value="health">Health</option><option value="other">Other</option></select></div><InputField label="Provider Name" error={errors.provider_name?.message} {...register('provider_name')} /></div>
          <div className="form-row-2 mt-3"><InputField label="Policy Number (optional)" {...register('policy_number')} /><InputField label="Sum Assured / Cover (₹)" type="number" min="0" error={errors.sum_assured?.message} {...register('sum_assured', { valueAsNumber: true })} /></div>
          <div className="form-row-2 mt-3"><InputField label="Premium Amount (₹)" type="number" min="0" error={errors.premium_amount?.message} {...register('premium_amount', { valueAsNumber: true })} /><div className="form-group"><label className="form-label" htmlFor="premium_frequency">Premium Frequency</label><select id="premium_frequency" className="form-control" {...register('premium_frequency')}><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option></select></div></div>
          <div className="form-row-2 mt-3"><InputField label="Renewal Date" type="date" error={errors.renewal_date?.message} {...register('renewal_date')} /><InputField label="Coverage End Date (optional)" type="date" {...register('coverage_end_date')} /></div>
          <Button type="submit" variant="primary" className="w-100 mt-4" isLoading={createMutation.isPending}>Save Policy</Button>
        </form>
      </Card></div>
      <div className="emergency-summary-panel"><Card title="Term Cover Check" className="bg-surface-dark-subtle border-none">
        <div className="metric-row-inline mb-4"><div><span className="text-secondary text-sm">Active Term Cover</span><h4 className="font-semibold text-primary mt-1">{formatINR(adequacy.active_term_cover)}</h4></div><ShieldCheck size={32} className={adequacy.is_adequate ? 'text-success' : 'text-warning'} /></div>
        <div className="detail-rows"><div className="detail-row"><span className="text-secondary">Annual Income</span><span className="font-semibold">{formatINR(adequacy.annual_income)}</span></div><div className="detail-row"><span className="text-secondary">Suggested Cover (10×)</span><span className="font-semibold text-accent">{formatINR(adequacy.recommended_term_cover)}</span></div></div>
        {adequacy.warning ? <div className="alert alert-warning mt-4 mb-0 text-sm"><ShieldAlert size={16} className="me-2" />{adequacy.warning}</div> : <div className="alert alert-success mt-4 mb-0 text-sm"><CheckCircle2 size={16} className="me-2" />Term cover meets the 10× annual-income guideline.</div>}
      </Card></div>
    </div>
    <div className="mt-4"><Card title="Your Policies"><div className="table-responsive">{policies.length ? <table className="table table-clean"><thead><tr><th>Provider / Policy</th><th>Type</th><th>Cover</th><th>Premium</th><th>Renewal</th><th /></tr></thead><tbody>{policies.map((policy) => <tr key={policy.id}><td><div className="font-semibold">{policy.provider_name}</div><span className="text-secondary text-xs">{policy.policy_number || 'No policy number'}</span></td><td className="text-capitalize">{policy.policy_type}</td><td>{formatINR(policy.sum_assured)}</td><td>{formatINR(policy.premium_amount)} / {policy.premium_frequency}</td><td>{policy.renewal_date}</td><td className="text-right"><Button variant="ghost" className="btn-sm text-danger" aria-label={`Delete ${policy.provider_name}`} isLoading={deleteMutation.isPending} onClick={() => deleteMutation.mutate(policy.id)}><Trash2 size={15} /></Button></td></tr>)}</tbody></table> : <div className="table-empty-state"><ShieldCheck size={36} className="text-secondary mb-2" /><h3>No insurance policies saved</h3><p className="text-secondary">Add policies to monitor coverage and renewals.</p></div>}</div></Card></div>
  </div>;
};
