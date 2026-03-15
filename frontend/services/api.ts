// services/api.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication token (managed via apiService.setAuthToken)
let authToken: string | null = null;

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
  // Authentication token management
  authToken,

  setAuthToken(token: string | null) {
    authToken = token;
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete apiClient.defaults.headers.common['Authorization'];
    }
  },

  // Auth endpoints
  async signup(data: {
    email: string;
    username: string;
    password: string;
    confirm_password: string;
    full_name?: string;
  }) {
    const response = await apiClient.post('/auth/signup', data);
    return response.data;
  },

  async login(identifier: string, password: string) {
    const response = await apiClient.post('/auth/login/json', { identifier, password });
    return response.data;
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  async updateProfile(data: {
    full_name?: string;
    phone?: string;
    company?: string;
    designation?: string;
    bio?: string;
  }) {
    const response = await apiClient.put('/auth/me', data);
    return response.data;
  },

  async changePassword(data: {
    current_password: string;
    new_password: string;
    confirm_new_password: string;
  }) {
    await apiClient.post('/auth/change-password', data);
  },

  async logout() {
    await apiClient.post('/auth/logout');
  },

  async deleteAccount() {
    await apiClient.delete('/auth/me');
  },

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

  async getIPOAnalysis(id: number) {
    const response = await apiClient.get(`/ipos/${id}/analysis`);
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

  async bulkImportIPOs(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/ipos/bulk-import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
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

  // Volatility endpoints - Phase 3
  async predictVolatility(ipoId: number, daysAhead: number = 7): Promise<any> {
    const response = await apiClient.post(
      `/volatility/predict/${ipoId}`,
      null,
      { params: { days_ahead: daysAhead } }
    );
    return response.data;
  },

  async getCurrentGeopoliticalEvents(): Promise<any> {
    const response = await apiClient.get('/volatility/geopolitical-events');
    return response.data;
  },

  async getHighVolatilityIPOs(): Promise<any> {
    const response = await apiClient.get('/volatility/high-volatility-alert');
    return response.data;
  },

  // Prospectus endpoints
  async getProspectusSections(ipoId: number) {
    const response = await apiClient.get(`/files/prospectus/${ipoId}/sections`);
    return response.data;
  },

  async getProspectus(ipoId: number, includeContent = true) {
    const response = await apiClient.get(`/files/prospectus/${ipoId}`, {
      params: { include_content: includeContent },
    });
    return response.data;
  },

  async deleteProspectus(ipoId: number) {
    const response = await apiClient.delete(`/files/prospectus/${ipoId}`);
    return response.data;
  },

  // RHP Downloads
  async searchRHP(companyName: string) {
    const response = await apiClient.get(`/files/rhp/search/${encodeURIComponent(companyName)}`);
    return response.data;
  },

  async downloadRHP(ipoId: number) {
    const response = await apiClient.post(`/files/rhp/download/${ipoId}`);
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
