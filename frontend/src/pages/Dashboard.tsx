import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ArrowRight, Bell, BriefcaseBusiness, ShieldCheck, Target } from 'lucide-react';
import { dashboardService } from '../services/dashboardService';
import { insuranceService } from '../services/insuranceService';
import { notificationService } from '../services/notificationService';
import { formatINR } from '../utils/currency';

const Sparkline: React.FC<{ values: number[] }> = ({ values }) => {
  if (values.length < 2) return <div className="sparkline-empty">Snapshots will appear after the daily refresh.</div>;
  const min = Math.min(...values), max = Math.max(...values), spread = max - min || 1;
  const points = values.map((v, i) => `${(i / (values.length - 1)) * 100},${42 - ((v - min) / spread) * 36}`).join(' ');
  return <svg className="networth-sparkline" viewBox="0 0 100 48" preserveAspectRatio="none"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="2" vectorEffect="non-scaling-stroke" /></svg>;
};

export const Dashboard: React.FC = () => {
  const dashboard = useQuery({ queryKey: ['dashboard'], queryFn: () => dashboardService.getSummary() });
  const insurance = useQuery({ queryKey: ['insurancePolicies'], queryFn: () => insuranceService.getPolicies() });
  const feed = useQuery({ queryKey: ['notificationFeed'], queryFn: () => notificationService.getFeed() });
  if (dashboard.isLoading) return <div className="skeleton-loading-container"><div className="skeleton skeleton-banner" /><div className="skeleton-grid-3"><div className="skeleton skeleton-card" /><div className="skeleton skeleton-card" /><div className="skeleton skeleton-card" /></div></div>;
  if (dashboard.error || !dashboard.data) return <div className="error-state-box card p-4"><AlertTriangle className="text-danger mb-2" size={40} /><h3>Failed to load dashboard</h3><p className="text-secondary">Please retry shortly.</p></div>;
  const data = dashboard.data;
  const adequacy = insurance.data?.coverage_adequacy;
  const coverPct = Math.round(Math.min(100, (adequacy?.active_term_cover || 0) / Math.max(1, adequacy?.recommended_term_cover || 1) * 100));
  const goalPercent = data.goals.total ? Math.round(data.goals.feasible / data.goals.total * 100) : 0;
  return <div className="dashboard-page-container ia-dashboard">
    <Link to="/portfolio" className="networth-hero"><div><span className="text-secondary text-sm">Net worth</span><h1>{formatINR(data.net_worth)}</h1><span className="text-secondary text-xs">Portfolio and savings · View portfolio <ArrowRight size={13} /></span></div><Sparkline values={data.networth_history.map(p => p.net_worth)} /></Link>
    <div className="dashboard-grid-3 mt-4">
      <Link to="/insurance" className="ring-card card"><div className="ring" style={{ background: `conic-gradient(var(--success-color, #198754) ${coverPct}%, var(--border-color) 0)` }}><span>{adequacy?.is_adequate ? 'OK' : `${coverPct}%`}</span></div><div><ShieldCheck className="text-success" size={20} /><h3>Security</h3><p>{adequacy ? `${formatINR(adequacy.active_term_cover)} term cover` : 'Set up insurance'}</p></div></Link>
      <Link to="/goals" className="ring-card card"><div className="ring" style={{ background: `conic-gradient(var(--accent-color) ${goalPercent}%, var(--border-color) 0)` }}><span>{goalPercent}%</span></div><div><Target className="text-accent" size={20} /><h3>Goals</h3><p>{data.goals.feasible} of {data.goals.total} plans feasible</p></div></Link>
      <Link to="/rebalancing" className="ring-card card"><div className="ring ring-icon"><BriefcaseBusiness size={24} /></div><div><BriefcaseBusiness className="text-accent" size={20} /><h3>Portfolio</h3><p>Review allocation drift</p></div></Link>
    </div>
    <section className="dashboard-section-panel mt-4"><div className="dashboard-feed-header"><div><Bell size={19} className="text-accent" /><h3>Alerts</h3></div><Link to="/profile" className="card-action-link">Settings <ArrowRight size={14} /></Link></div>{feed.isLoading ? <div className="skeleton skeleton-card" /> : feed.data?.notifications.length ? <div className="alert-feed">{feed.data.notifications.map(item => <Link key={item.id} to={item.link} className={`alert-feed-item alert-${item.severity}`}><div><strong>{item.title}</strong><p>{item.message}</p></div><ArrowRight size={16} /></Link>)}</div> : <div className="table-empty-state"><Bell size={30} className="text-secondary mb-2" /><p className="text-secondary">No active alerts. Your plan is quiet for now.</p></div>}</section>
  </div>;
};
