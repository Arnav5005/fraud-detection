import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

export const api = {
  checkHealth: async () => {
    const res = await client.get('/health');
    return res.data;
  },

  getStats: async () => {
    const res = await client.get('/stats');
    return res.data;
  },

  getTransactions: async (limit = 50) => {
    const res = await client.get(`/transactions?limit=${limit}`);
    return res.data;
  },

  predict: async (payload) => {
    const res = await client.post('/predict', payload);
    return res.data;
  },

  explain: async (transactionId) => {
    const res = await client.get(`/explain/${transactionId}`);
    return res.data;
  },
};

export default api;
