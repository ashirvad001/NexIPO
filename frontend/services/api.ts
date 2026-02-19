// services/api.ts
import axios, { AxiosInstance, AxiosError } from 'axios';
import { IPO, IPOListResponse, IPOQueryParams } from '@/types/ipo';

class APIService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Get all IPOs with filters and pagination
  async getIPOs(params?: IPOQueryParams): Promise<IPOListResponse> {
    const response = await this.client.get<IPOListResponse>('/ipos/', { params });
    return response.data;
  }

  // Get single IPO by ID
  async getIPOById(id: number): Promise<IPO> {
    const response = await this.client.get<IPO>(`/ipos/${id}`);
    return response.data;
  }

  // Get IPO by symbol
  async getIPOBySymbol(symbol: string): Promise<IPO> {
    const response = await this.client.get<IPO>(`/ipos/symbol/${symbol}`);
    return response.data;
  }

  // Get active IPOs
  async getActiveIPOs(): Promise<IPO[]> {
    const response = await this.client.get<IPO[]>('/ipos/active');
    return response.data;
  }

  // Get upcoming IPOs
  async getUpcomingIPOs(limit: number = 10): Promise<IPO[]> {
    const response = await this.client.get<IPO[]>('/ipos/upcoming', {
      params: { limit },
    });
    return response.data;
  }

  // Create IPO
  async createIPO(data: Partial<IPO>): Promise<IPO> {
    const response = await this.client.post<IPO>('/ipos/', data);
    return response.data;
  }

  // Update IPO
  async updateIPO(id: number, data: Partial<IPO>): Promise<IPO> {
    const response = await this.client.put<IPO>(`/ipos/${id}`, data);
    return response.data;
  }

  // Delete IPO
  async deleteIPO(id: number): Promise<void> {
    await this.client.delete(`/ipos/${id}`);
  }

  // Upload prospectus PDF
  async uploadProspectus(ipoId: number, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await this.client.post(
      `/files/upload/prospectus/${ipoId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  // Get prospectus data
  async getProspectus(ipoId: number, includeFullText: boolean = false): Promise<any> {
    const response = await this.client.get(`/files/prospectus/${ipoId}`, {
      params: { include_full_text: includeFullText },
    });
    return response.data;
  }

  // Get prospectus sections
  async getProspectusSections(ipoId: number): Promise<any> {
    const response = await this.client.get(`/files/prospectus/${ipoId}/sections`);
    return response.data;
  }

  // Get specific prospectus section
  async getProspectusSection(ipoId: number, sectionName: string): Promise<any> {
    const response = await this.client.get(
      `/files/prospectus/${ipoId}/section/${sectionName}`
    );
    return response.data;
  }

  // Delete prospectus
  async deleteProspectus(ipoId: number): Promise<void> {
    await this.client.delete(`/files/prospectus/${ipoId}`);
  }

  // Get file metadata
  async getFileMetadata(fileId: string): Promise<any> {
    const response = await this.client.get(`/files/metadata/${fileId}`);
    return response.data;
  }
}

// Export singleton instance
export const apiService = new APIService();
