import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import SummaryCards from './components/SummaryCards';
import DemoPanel from './components/DemoPanel';
import FraudTrendChart from './components/FraudTrendChart';
import TransactionTable from './components/TransactionTable';
import ExplainModal from './components/ExplainModal';
import api from './services/api';
import { AlertCircle } from 'lucide-react';

export default function App() {
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [isHealthy, setIsHealthy] = useState(false);
  const [threshold, setThreshold] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTxId, setSelectedTxId] = useState(null);
  const [errorBanner, setErrorBanner] = useState(null);

  const fetchData = useCallback(async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);

      // Check health
      try {
        const healthRes = await api.checkHealth();
        setIsHealthy(healthRes.status === 'healthy');
        setThreshold(healthRes.decision_threshold);
        setErrorBanner(null);
      } catch (hErr) {
        setIsHealthy(false);
        setErrorBanner('FastAPI backend is unreachable. Make sure the server is running on http://127.0.0.1:8000.');
        setLoading(false);
        setRefreshing(false);
        return;
      }

      // Fetch stats and transactions in parallel
      const [statsData, txData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getTransactions(50).catch(() => []),
      ]);

      if (statsData) setStats(statsData);
      if (txData) setTransactions(txData);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Poll every 10 seconds
    const interval = setInterval(() => {
      fetchData();
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTransactionScored = (newTx) => {
    // Immediately refresh stats and transaction list
    fetchData();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <Header
        isHealthy={isHealthy}
        threshold={threshold}
        onRefresh={() => fetchData(true)}
        isRefreshing={refreshing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Offline Banner */}
        {errorBanner && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/80 flex items-start gap-3 text-rose-300 text-xs">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200">Backend Communication Warning</p>
              <p className="mt-0.5 text-rose-300/90">{errorBanner}</p>
              <p className="mt-1 text-[11px] font-mono text-rose-400">
                Run command: <code>python -m uvicorn backend.main:app --reload --port 8000</code>
              </p>
            </div>
          </div>
        )}

        {/* KPI Summary Cards */}
        <SummaryCards stats={stats} loading={loading} />

        {/* Demo Simulator Panel */}
        <DemoPanel
          onTransactionScored={handleTransactionScored}
          isHealthy={isHealthy}
        />

        {/* Visualization & Activity Stream */}
        <FraudTrendChart
          transactions={transactions}
          threshold={threshold}
        />

        {/* Recent Transactions Feed */}
        <TransactionTable
          transactions={transactions}
          onSelectExplain={(id) => setSelectedTxId(id)}
          loading={loading}
        />
      </main>

      {/* SHAP Explanation Modal */}
      {selectedTxId && (
        <ExplainModal
          transactionId={selectedTxId}
          onClose={() => setSelectedTxId(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/50 py-4 px-6 text-center text-xs text-slate-500">
        Explainable Credit Card Fraud Detection MVP &bull; XGBoost TreeExplainer &bull; SQLite Persistence &bull; React Dashboard
      </footer>
    </div>
  );
}
