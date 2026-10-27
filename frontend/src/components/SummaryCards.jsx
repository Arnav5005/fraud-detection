import React from 'react';
import { Layers, ShieldAlert, ShieldCheck, Percent } from 'lucide-react';

export default function SummaryCards({ stats, loading }) {
  const cards = [
    {
      title: 'Total Scored',
      value: stats ? stats.total_transactions.toLocaleString() : '0',
      subtitle: 'Persisted transactions',
      icon: Layers,
      color: 'text-slate-200',
      bg: 'bg-slate-800/40 border-slate-700/60',
      iconBg: 'bg-slate-700/40 text-slate-300',
    },
    {
      title: 'Flagged Fraud',
      value: stats ? stats.fraud_count.toLocaleString() : '0',
      subtitle: 'Exceeding decision threshold',
      icon: ShieldAlert,
      color: 'text-rose-400',
      bg: 'bg-rose-950/20 border-rose-800/40',
      iconBg: 'bg-rose-900/30 text-rose-400',
    },
    {
      title: 'Legitimate Approved',
      value: stats ? stats.legit_count.toLocaleString() : '0',
      subtitle: 'Normal transaction activity',
      icon: ShieldCheck,
      color: 'text-emerald-400',
      bg: 'bg-emerald-950/20 border-emerald-800/40',
      iconBg: 'bg-emerald-900/30 text-emerald-400',
    },
    {
      title: 'Fraud Detection Rate',
      value: stats ? `${(stats.fraud_rate * 100).toFixed(2)}%` : '0.00%',
      subtitle: 'Flagged / total transactions',
      icon: Percent,
      color: 'text-amber-400',
      bg: 'bg-amber-950/20 border-amber-800/40',
      iconBg: 'bg-amber-900/30 text-amber-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className={`p-5 rounded-xl border backdrop-blur-sm transition-all duration-200 ${c.bg}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                {c.title}
              </span>
              <div className={`p-2 rounded-lg ${c.iconBg}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <div className={`text-2xl font-bold tracking-tight ${c.color}`}>
                {loading ? (
                  <div className="h-7 w-20 bg-slate-700/50 animate-pulse rounded"></div>
                ) : (
                  c.value
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1">{c.subtitle}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
