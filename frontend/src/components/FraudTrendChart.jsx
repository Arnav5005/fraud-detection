import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { TrendingUp } from 'lucide-react';

export default function FraudTrendChart({ transactions, threshold }) {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 flex flex-col items-center justify-center min-h-[260px] text-center">
        <TrendingUp className="w-8 h-8 text-slate-500 mb-2" />
        <p className="text-sm font-medium text-slate-300">No Transaction Data Available</p>
        <p className="text-xs text-slate-500 mt-1 max-w-xs">
          Score transactions via the Demo Simulator or API to visualize real-time probability streams.
        </p>
      </div>
    );
  }

  // Format the most recent 25 transactions reversed so older -> newer left to right
  const chartData = [...transactions]
    .slice(0, 25)
    .reverse()
    .map((tx) => ({
      id: `#${tx.id}`,
      probability: Number((tx.fraud_probability * 100).toFixed(2)),
      amount: tx.amount_raw,
      verdict: tx.verdict,
      hour: tx.hour.toFixed(1),
    }));

  const thresholdPercent = threshold ? threshold * 100 : 89.0;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const isFraud = data.verdict === 'fraud';
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1">
          <p className="font-semibold text-slate-200">Transaction {data.id}</p>
          <p className="text-slate-400">Amount: <span className="text-slate-200 font-mono">${data.amount.toFixed(2)}</span></p>
          <p className="text-slate-400">Hour: <span className="text-slate-200 font-mono">{data.hour}h</span></p>
          <p className="text-slate-400">
            Probability:{' '}
            <span className={`font-mono font-bold ${isFraud ? 'text-rose-400' : 'text-emerald-400'}`}>
              {data.probability}%
            </span>
          </p>
          <div className="pt-1">
            <span
              className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                isFraud
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}
            >
              {data.verdict}
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-700/50 gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-400" />
            Fraud Risk Probability Stream (Recent Activity)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Model confidence scores relative to decision boundary ({thresholdPercent.toFixed(1)}%)
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
            <span>Fraud Threshold</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
            <span>Probability Score</span>
          </div>
        </div>
      </div>

      <div className="h-64 mt-4 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="probGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
            <XAxis dataKey="id" stroke="#64748b" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10 }} unit="%" />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={thresholdPercent}
              stroke="#ef4444"
              strokeDasharray="4 4"
              label={{
                value: `Threshold (${thresholdPercent.toFixed(1)}%)`,
                fill: '#f87171',
                fontSize: 10,
                position: 'top',
              }}
            />
            <Area
              type="monotone"
              dataKey="probability"
              stroke="#818cf8"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#probGradient)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
