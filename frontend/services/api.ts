// services/api.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

async function requestWithRetry<T>(fn: () => Promise<T>, retries = 2, delayMs = 300) {
  let lastErr: any;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i < retries) await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw lastErr;
}

export const apiService = {
  // IPO endpoints
  async getIPOs(params?: any) {
    const response = await apiClient.get('/ipos/', { params });
    return response.data;
  },

  async getIPO(id: number) {
    const response = await apiClient.get(`/ipos/${id}`);
    return response.data;
  },

  // Backwards-compatible alias used by some pages/components
  async getIPOById(id: number) {
    const response = await apiClient.get(`/ipos/${id}`);
    return response.data;
  },

  async createIPO(data: any) {
    const response = await apiClient.post('/ipos/', data);
    return response.data;
  },

  async updateIPO(id: number, data: any) {
    const response = await apiClient.put(`/ipos/${id}`, data);
    return response.data;
  },

  async deleteIPO(id: number) {
    await apiClient.delete(`/ipos/${id}`);
  },

  // ML endpoints - Phase 5
  async predictRisk(ipoId: number) {
    const response = await apiClient.post(`/ml/predict/${ipoId}`);
    return response.data;
  },

  async getPrediction(ipoId: number) {
    const response = await apiClient.get(`/ml/prediction/${ipoId}`);
    return response.data;
  },

  async deletePrediction(ipoId: number) {
    const response = await apiClient.delete(`/ml/prediction/${ipoId}`);
    return response.data;
  },

  async predictBatch(ipoIds: number[]) {
    const response = await apiClient.post('/ml/predict/batch', { ipo_ids: ipoIds });
    return response.data;
  },

  async getModelInfo() {
    const response = await apiClient.get('/ml/model/info');
    return response.data;
  },

  async getModelPerformance() {
    const response = await apiClient.get('/ml/model/performance');
    return response.data;
  },

  async getMLStatistics() {
    const response = await apiClient.get('/ml/statistics');
    return response.data;
  },

  async getModelStatus() {
    const response = await apiClient.get('/ml/model-status');
    return response.data;
  },
  
  // Get active IPOs with retry
  async getActiveIPOs() {
    return requestWithRetry(async () => {
      const r = await apiClient.get('/ipos/active');
      return r.data;
    });
  },

  // Get upcoming IPOs with retry
  async getUpcomingIPOs(limit = 10) {
    return requestWithRetry(async () => {
      const r = await apiClient.get('/ipos/upcoming', { params: { limit } });
      return r.data;
    });
  },
};

export default apiService;
