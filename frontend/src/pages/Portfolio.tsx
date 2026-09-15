import React, { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { BarChart3, CheckCircle2, CircleDollarSign, TrendingDown, TrendingUp } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { InputField } from '../components/common/InputField';
import { portfolioService } from '../services/portfolioService';
import { formatINR } from '../utils/currency';

const transactionSchema = z.object({
  identifier: z.string().trim().min(1, 'Asset identifier is required').max(50),
  transaction_type: z.enum(['buy', 'sell', 'sip', 'redeem']),
  quantity: z.number().gt(0, 'Quantity must be greater than zero'),
  price: z.number().min(0, 'Price cannot be negative'),
  transaction_date: z.string().min(1, 'Transaction date is required'),
});

type TransactionFormData = z.infer<typeof transactionSchema>;

const today = new Date().toISOString().slice(0, 10);

export const Portfolio: React.FC = () => {
  const queryClient = useQueryClient();
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const { data: holdings = [], isLoading, error } = useQuery({
    queryKey: ['portfolioHoldings'],
    queryFn: () => portfolioService.getHoldings(),
  });
  const { register, handleSubmit, formState: { errors }, watch, reset } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema),
    defaultValues: { identifier: '', transaction_type: 'buy', quantity: 1, price: 0, transaction_date: today },
  });

  const quantity = watch('quantity') || 0;
  const price = watch('price') || 0;
  const transactionType = watch('transaction_type');
  const amount = quantity * price;
  const summary = useMemo(() => {
    const totalInvested = holdings.reduce((total, holding) => total + holding.invested_amount, 0);
    const currentValue = holdings.reduce((total, holding) => total + holding.current_value, 0);
    const gainLoss = currentValue - totalInvested;
    const assetClasses = holdings.reduce<Record<string, number>>((totals, holding) => {
      totals[holding.asset_class] = (totals[holding.asset_class] || 0) + holding.current_value;
      return totals;
    }, {});
    return { totalInvested, currentValue, gainLoss, gainLossPercent: totalInvested ? (gainLoss / totalInvested) * 100 : 0, assetClasses };
  }, [holdings]);

  const transactionMutation = useMutation({
    mutationFn: (data: TransactionFormData) => portfolioService.createTransaction({ ...data, amount: data.quantity * data.price }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolioHoldings'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      reset({ identifier: '', transaction_type: 'buy', quantity: 1, price: 0, transaction_date: today });
      setServerError(null);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    },
    onError: (err: Error) => setServerError(err.message || 'Failed to add transaction.'),
  });

  if (isLoading) return <div className="skeleton-loading-container"><div className="skeleton skeleton-banner" /><div className="skeleton skeleton-card mt-3" /></div>;
  if (error) return <div className="error-state-box card p-4"><h3>Failed to load portfolio</h3><p className="text-secondary">{error.message || 'Please try again later.'}</p></div>;

  const isGain = summary.gainLoss >= 0;
  const allocationEntries = Object.entries(summary.assetClasses).sort(([, a], [, b]) => b - a);
  return (
    <div className="portfolio-page">
      <div className="page-header-row mb-4"><div><h2>Portfolio</h2><p className="text-secondary">Track your investments, current value, and transactions in one place.</p></div></div>

      <div className="portfolio-summary-grid">
        <Card title="Total Invested" className="portfolio-metric-card"><CircleDollarSign className="metric-icon text-accent" /><strong>{formatINR(summary.totalInvested)}</strong></Card>
        <Card title="Current Value" className="portfolio-metric-card"><BarChart3 className="metric-icon text-primary" /><strong>{formatINR(summary.currentValue)}</strong></Card>
        <Card title="Gain / Loss" className="portfolio-metric-card"><span className={isGain ? 'text-success' : 'text-danger'}>{isGain ? <TrendingUp className="metric-icon" /> : <TrendingDown className="metric-icon" />}</span><strong className={isGain ? 'text-success' : 'text-danger'}>{isGain ? '+' : ''}{summary.gainLossPercent.toFixed(2)}%</strong><span className="text-secondary text-sm">{isGain ? '+' : ''}{formatINR(summary.gainLoss)}</span></Card>
      </div>

      <div className="portfolio-layout mt-4">
        <Card title="Add Transaction">
          {success && <div className="alert alert-success d-flex align-items-center mb-3"><CheckCircle2 size={16} className="me-2" />Transaction recorded and holding updated.</div>}
          {serverError && <div className="alert alert-danger mb-3">{serverError}</div>}
          <form onSubmit={handleSubmit((data) => { setServerError(null); transactionMutation.mutate(data); })}>
            <InputField label="Asset Identifier" placeholder="e.g. mutual fund scheme code" error={errors.identifier?.message} disabled={transactionMutation.isPending} {...register('identifier')} />
            <div className="form-group mt-3"><label className="form-label" htmlFor="transaction_type">Transaction Type</label><select id="transaction_type" className="form-control" disabled={transactionMutation.isPending} {...register('transaction_type')}><option value="buy">Buy</option><option value="sell">Sell</option><option value="sip">SIP</option><option value="redeem">Redeem</option></select></div>
            <div className="form-row-2 mt-3"><InputField label="Quantity" type="number" min="0" step="any" error={errors.quantity?.message} disabled={transactionMutation.isPending} {...register('quantity', { valueAsNumber: true })} /><InputField label="Price per Unit (₹)" type="number" min="0" step="any" error={errors.price?.message} disabled={transactionMutation.isPending} {...register('price', { valueAsNumber: true })} /></div>
            <div className="form-row-2 mt-3"><InputField label="Transaction Date" type="date" error={errors.transaction_date?.message} disabled={transactionMutation.isPending} {...register('transaction_date')} /><div className="form-group"><label className="form-label">Calculated Amount</label><div className="form-control portfolio-readonly-value">{formatINR(amount)}</div></div></div>
            <p className="form-helper-text mt-2">Logging a {transactionType} calls the portfolio transaction flow and updates the current holding.</p>
            <Button type="submit" variant="primary" className="w-100 mt-3" isLoading={transactionMutation.isPending}>Add Transaction</Button>
          </form>
        </Card>

        <Card title="Asset Allocation">
          {allocationEntries.length ? <div className="allocation-list">{allocationEntries.map(([assetClass, value]) => { const percent = summary.currentValue ? (value / summary.currentValue) * 100 : 0; return <div key={assetClass} className="allocation-item"><div className="d-flex justify-content-between text-sm mb-1"><span>{assetClass}</span><span>{percent.toFixed(1)}% · {formatINR(value)}</span></div><div className="progress-bar-track"><div className="progress-bar-fill bg-accent" style={{ width: `${percent}%` }} /></div></div>; })}</div> : <div className="table-empty-state"><BarChart3 size={36} className="text-secondary mb-2" /><h3>No allocation yet</h3><p className="text-secondary">Add a transaction to see your asset-class breakdown.</p></div>}
        </Card>
      </div>

      <div className="mt-4"><Card title="Holdings"><div className="table-responsive">{holdings.length ? <table className="table table-clean"><thead><tr><th>Holding</th><th>Asset Class</th><th>Quantity</th><th>Invested</th><th>Current Value</th><th>Gain / Loss</th></tr></thead><tbody>{holdings.map((holding) => { const gain = holding.current_value - holding.invested_amount; return <tr key={holding.id}><td><div className="font-semibold">{holding.asset_name}</div><span className="text-secondary text-xs">{holding.identifier}</span></td><td>{holding.asset_class}</td><td>{holding.quantity.toLocaleString('en-IN', { maximumFractionDigits: 4 })}</td><td>{formatINR(holding.invested_amount)}</td><td>{formatINR(holding.current_value)}</td><td className={gain >= 0 ? 'text-success font-semibold' : 'text-danger font-semibold'}>{gain >= 0 ? '+' : ''}{formatINR(gain)}</td></tr>; })}</tbody></table> : <div className="table-empty-state"><CircleDollarSign size={36} className="text-secondary mb-2" /><h3>No holdings yet</h3><p className="text-secondary">Use the transaction form to start tracking your portfolio.</p></div>}</div></Card></div>
    </div>
  );
};
