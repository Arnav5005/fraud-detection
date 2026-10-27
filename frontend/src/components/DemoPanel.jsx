import React, { useState } from 'react';
import { Play, Sparkles, AlertCircle, Check, Send } from 'lucide-react';
import api from '../services/api';

// Realistic sample payloads derived from actual credit card benchmark characteristics
const SAMPLE_LEGITIMATE = {
  Time: 14200.0,
  Amount: 42.50,
  V1: 1.15, V2: -0.25, V3: 0.65, V4: -0.12, V5: -0.35, V6: 0.45, V7: -0.22,
  V8: 0.18, V9: 0.35, V10: -0.15, V11: 0.20, V12: 0.05, V13: -0.32, V14: 0.12,
  V15: 0.45, V16: -0.08, V17: 0.15, V18: -0.25, V19: 0.12, V20: -0.05,
  V21: 0.02, V22: 0.12, V23: -0.05, V24: 0.08, V25: 0.25, V26: -0.15,
  V27: 0.02, V28: 0.01
};

// Fraud pattern with extreme V14, V10, V12 negative deviations characteristic of fraud
const SAMPLE_FRAUD = {
  Time: 42000.0,
  Amount: 840.00,
  V1: -3.85, V2: 3.10, V3: -4.50, V4: 4.80, V5: -2.90, V6: -1.80, V7: -4.20,
  V8: 2.10, V9: -2.80, V10: -6.50, V11: 4.20, V12: -7.10, V13: 0.25, V14: -8.90,
  V15: -0.80, V16: -5.40, V17: -8.10, V18: -3.20, V19: 1.85, V20: 0.85,
  V21: 0.95, V22: -0.25, V23: -0.18, V24: -0.42, V25: 0.35, V26: 0.42,
  V27: 0.88, V28: 0.35
};

export default function DemoPanel({ onTransactionScored, isHealthy }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runPrediction = async (payload, typeLabel) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await api.predict(payload);
      setResult({ ...response, type: typeLabel });
      if (onTransactionScored) onTransactionScored(response);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Prediction request failed.');
    } finally {
      setLoading(false);
    }
  };

  const runBatchSimulation = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      // Submit 5 transactions with varying noise
      for (let i = 1; i <= 5; i++) {
        const isFraud = i === 3; // 1 fraud in the batch
        const base = isFraud ? { ...SAMPLE_FRAUD } : { ...SAMPLE_LEGITIMATE };
        base.Time += i * 360;
        base.Amount = parseFloat((base.Amount + (Math.random() * 20 - 10)).toFixed(2));
        if (base.Amount < 1) base.Amount = 5.0;

        const res = await api.predict(base);
        if (onTransactionScored) onTransactionScored(res);
        setResult({ ...res, type: `Batch ${i}/5 (${isFraud ? 'High Risk' : 'Normal'})` });
        await new Promise((r) => setTimeout(r, 400));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Batch simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pb-4 border-b border-slate-700/50">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Live Inference & Demo Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Submit benchmark transaction vectors to test real-time FastAPI scoring and SHAP attribution
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          onClick={() => runPrediction(SAMPLE_LEGITIMATE, 'Normal Transaction')}
          disabled={loading || !isHealthy}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition disabled:opacity-40"
        >
          <Check className="w-4 h-4" />
          Test Legitimate ($42.50)
        </button>

        <button
          onClick={() => runPrediction(SAMPLE_FRAUD, 'High-Risk Fraud')}
          disabled={loading || !isHealthy}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-semibold transition disabled:opacity-40"
        >
          <AlertCircle className="w-4 h-4" />
          Test Fraud ($840.00)
        </button>

        <button
          onClick={runBatchSimulation}
          disabled={loading || !isHealthy}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition disabled:opacity-40"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          Simulate 5-Tx Stream
        </button>
      </div>

      {/* Result or Error Banner */}
      {loading && (
        <div className="mt-4 p-3 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300 flex items-center gap-2">
          <div className="animate-spin w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
          <span>Dispatching payload to FastAPI inference engine...</span>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300">
          <strong>Request Failed:</strong> {error}
        </div>
      )}

      {result && !loading && (
        <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 text-xs animate-in fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2 mb-2">
            <span className="font-semibold text-slate-200">
              Response for: <span className="text-indigo-400">{result.type}</span>
            </span>
            <span className="font-mono text-slate-400 text-[11px]">
              Persisted as ID #{result.transaction_id}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div>
              <span className="text-slate-500 text-[11px] block">Verdict</span>
              <span
                className={`font-bold uppercase text-xs ${
                  result.verdict === 'fraud' ? 'text-rose-400' : 'text-emerald-400'
                }`}
              >
                {result.verdict}
              </span>
            </div>
            <div>
              <span className="text-slate-500 text-[11px] block">Fraud Probability</span>
              <span className="font-mono font-bold text-slate-200 text-xs">
                {(result.fraud_probability * 100).toFixed(2)}%
              </span>
            </div>
            <div className="col-span-2">
              <span className="text-slate-500 text-[11px] block">SHAP Top Drivers</span>
              <div className="flex gap-1.5 mt-0.5">
                {result.top_reasons?.map((r, i) => (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[10px] text-slate-300"
                  >
                    {r}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
