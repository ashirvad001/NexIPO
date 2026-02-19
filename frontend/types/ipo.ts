// types/ipo.ts
export enum IPOStatus {
  UPCOMING = 'upcoming',
  OPEN = 'open',
  CLOSED = 'closed',
  LISTED = 'listed',
  WITHDRAWN = 'withdrawn',
}

export enum IPOType {
  MAINBOARD = 'mainboard',
  SME = 'sme',
}

export interface IPO {
  id: number;
  company_name: string;
  symbol: string | null;
  status: IPOStatus;
  ipo_type: IPOType;
  
  // Dates
  open_date: string | null;
  close_date: string | null;
  allotment_date: string | null;
  listing_date: string | null;
  
  // Pricing
  price_band_lower: number | null;
  price_band_upper: number | null;
  issue_price: number | null;
  listing_price: number | null;
  current_price: number | null;
  
  // Issue Size
  issue_size_rs_cr: number | null;
  shares_offered: number | null;
  fresh_issue_size: number | null;
  offer_for_sale: number | null;
  
  // Subscription
  qib_subscription: number | null;
  nii_subscription: number | null;
  retail_subscription: number | null;
  total_subscription: number | null;
  
  // GMP
  gmp_amount: number | null;
  gmp_percentage: number | null;
  estimated_listing_price: number | null;
  
  // Company Details
  industry_sector: string | null;
  lead_managers: string | null;
  registrar: string | null;
  
  // Financial Metrics
  market_cap_cr: number | null;
  pe_ratio: number | null;
  roce: number | null;
  roe: number | null;
  revenue_growth: number | null;
  profit_growth: number | null;
  
  // ML Risk Assessment
  risk_score: number | null;
  risk_category: string | null;
  ml_processed: boolean;
  ml_processed_at: string | null;
  
  // Additional
  prospectus_url: string | null;
  prospectus_file_id: string | null;
  lot_size: number | null;
  min_investment: number | null;
  description: string | null;
  
  // Metadata
  created_at: string;
  updated_at: string;
  
  // Computed
  is_active: boolean;
  listing_gain_percentage: number | null;
}

export interface IPOListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: IPO[];
}

export interface IPOFilter {
  status?: IPOStatus;
  ipo_type?: IPOType;
  industry_sector?: string;
  min_issue_size?: number;
  max_issue_size?: number;
  min_subscription?: number;
  min_risk_score?: number;
  max_risk_score?: number;
  search?: string;
}

export interface IPOQueryParams extends IPOFilter {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
