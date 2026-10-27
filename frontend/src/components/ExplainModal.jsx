import React, { useEffect, useState } from 'react';
import { X, ArrowUpRight, ArrowDownRight, Info, AlertTriangle, CheckCircle2 } from 'lucide-react';
import api from '../services/api';

const FEATURE_DESCRIPTIONS = {
  V14: 'PCA component strongly correlated with unauthorized merchant categories and high-risk terminal locations.',
  V10: 'PCA component capturing unusual cardholder velocity and consecutive transaction timing anomalies.',
  V12: 'PCA component associated with geographical displacement and unexpected IP geo-hops.',
  V4: 'PCA component measuring transaction velocity bursts and rapid amount escalation.',
  V17: 'PCA component tracking unusual international transaction signatures.',
  V11: 'PCA component capturing account age versus activity burst ratio.',
  Amount: 'Standardized transaction amount (log1p transformed).',
  Hour: 'Standardized hour of day extracted from elapsed time.',
};

export default function ExplainModal({ transactionId, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function fetchExplanation() {
      try {
        setLoading(true);
        setError(null);
        const res = await api.explain(transactionId);
        if (mounted) setData(res);
      } catch (err) {
        if (mounted) setError(err.response?.data?.detail || 'Failed to fetch explanation from backend.');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchExplanation();
    return () => {
      mounted = false;
    };
  }, [transactionId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Info className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-semibold text-slate-100">
              SHAP Prediction Explainability
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6">
          {loading ? (
            <div className="py-12 text-center">
              <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-3"></div>
              <p className="text-xs text-slate-400">Computing Shapley attributions via backend...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800 text-rose-300 text-xs">
              <p className="font-semibold">Unable to load explanation</p>
              <p className="mt-1 text-rose-400">{error}</p>
            </div>
          ) : data ? (
            <div className="space-y-5">
              {/* Prediction Summary */}
              <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono text-slate-400">Transaction #{data.transaction_id}</span>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold uppercase ${
                        data.verdict === 'fraud'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {data.verdict === 'fraud' ? (
                        <AlertTriangle className="w-3.5 h-3.5" />
                      ) : (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      )}
                      {data.verdict}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[11px] text-slate-400 block">Fraud Probability</span>
                  <span className="text-xl font-bold font-mono text-slate-100">
                    {(data.fraud_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Top 3 Contributing Features */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                  Top 3 Contributing Features (Shapley Values)
                </h4>
                <div className="space-y-2.5">
                  {data.top_reasons && data.top_reasons.length > 0 ? (
                    data.top_reasons.map((feat, idx) => {
                      const isHighRisk = data.verdict === 'fraud';
                      const desc = FEATURE_DESCRIPTIONS[feat] || 'PCA transformed principal component.';

                      return (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col gap-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-mono text-xs font-bold">
                                {feat}
                              </span>
                              <span className="text-xs text-slate-300 font-medium">Rank #{idx + 1} Impact</span>
                            </div>
                            <div className="flex items-center gap-1 text-xs">
                              {isHighRisk ? (
                                <span className="flex items-center gap-0.5 text-rose-400 font-medium">
                                  <ArrowUpRight className="w-3.5 h-3.5" />
                                  Elevates Fraud Risk
                                </span>
                              ) : (
                                <span className="flex items-center gap-0.5 text-emerald-400 font-medium">
                                  <ArrowDownRight className="w-3.5 h-3.5" />
                                  Decreases Fraud Risk
                                </span>
                              )}
                            </div>
                          </div>
                          <p className="text-[11px] text-slate-400 leading-relaxed">{desc}</p>
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-xs text-slate-400">No feature reasons returned for this record.</p>
                  )}
                </div>
              </div>

              <div className="text-[11px] text-slate-500 p-3 rounded-lg bg-slate-800/20 border border-slate-800">
                <strong>Methodology:</strong> SHAP (SHapley Additive exPlanations) uses game-theoretic Shapley values computed across XGBoost decision trees to isolate each feature's marginal attribution to the final fraud probability score.
              </div>
            </div>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-900 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
