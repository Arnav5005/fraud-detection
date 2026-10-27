import React from 'react';
import { HelpCircle, AlertTriangle, CheckCircle2, Search } from 'lucide-react';

export default function TransactionTable({ transactions, onSelectExplain, loading }) {
  if (loading && (!transactions || transactions.length === 0)) {
    return (
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-8 text-center text-slate-400">
        <div className="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-3"></div>
        <p className="text-sm">Loading transactions...</p>
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-8 text-center text-slate-400">
        <Search className="w-8 h-8 text-slate-500 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-300">No Transactions Recorded</p>
        <p className="text-xs text-slate-500 mt-1">
          Use the Simulator above to generate test transactions and populate the feed.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl overflow-hidden backdrop-blur-sm">
      <div className="px-5 py-4 border-b border-slate-700/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">Recent Scored Transactions</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit log of model predictions, verdicts, and leading explanation attributions
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Showing {transactions.length} record{transactions.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">TX ID</th>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4 text-right">Amount</th>
              <th className="py-3 px-4 text-center">Hour</th>
              <th className="py-3 px-4">Fraud Probability</th>
              <th className="py-3 px-4">Verdict</th>
              <th className="py-3 px-4">Top SHAP Reasons</th>
              <th className="py-3 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {transactions.map((tx) => {
              const isFraud = tx.verdict === 'fraud';
              const probPercent = (tx.fraud_probability * 100).toFixed(1);

              return (
                <tr
                  key={tx.id}
                  className={`hover:bg-slate-750/30 transition-colors ${
                    isFraud ? 'bg-rose-950/10' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-mono font-medium text-slate-300">
                    #{tx.id}
                  </td>
                  <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                    {tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-medium text-slate-200">
                    ${tx.amount_raw.toFixed(2)}
                  </td>
                  <td className="py-3 px-4 text-center font-mono text-slate-400">
                    {tx.hour.toFixed(1)}h
                  </td>
                  <td className="py-3 px-4 min-w-[140px]">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-700/50 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            isFraud ? 'bg-rose-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(2, tx.fraud_probability * 100))}%` }}
                        ></div>
                      </div>
                      <span
                        className={`font-mono text-xs font-semibold ${
                          isFraud ? 'text-rose-400' : 'text-slate-300'
                        }`}
                      >
                        {probPercent}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold uppercase ${
                        isFraud
                          ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {isFraud ? (
                        <AlertTriangle className="w-3 h-3 text-rose-400" />
                      ) : (
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      )}
                      {tx.verdict}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1 max-w-[200px]">
                      {tx.top_reasons && tx.top_reasons.length > 0 ? (
                        tx.top_reasons.map((reason, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[10px]"
                          >
                            {reason}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-500 text-[11px]">None</span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => onSelectExplain(tx.id)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition"
                    >
                      <HelpCircle className="w-3 h-3" />
                      Explain
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
