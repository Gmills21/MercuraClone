/**
 * Shared types for OpenMercura
 * Used by both Web App and Chrome Extension
 */

// Customer Types
export interface Customer {
  id: string;
  name: string;
  email: string;
  company?: string;
  phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

// Product Types
export interface Product {
  id: string;
  sku: string;
  name: string;
  description?: string;
  price: number;
  cost?: number;
  category?: string;
  competitor_sku?: string;
  created_at: string;
  updated_at: string;
}

// Quote Types
export interface Quote {
  id: string;
  customer_id: string;
  customer_name?: string;
  status: 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired';
  items: QuoteItem[];
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  notes?: string;
  token: string;
  created_at: string;
  updated_at: string;
  expires_at?: string;
}

export interface QuoteItem {
  id: string;
  product_id: string;
  product_name?: string;
  sku?: string;
  description?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  competitor_sku?: string;
}

// Extraction Types
export interface LineItem {
  item_name: string;
  sku?: string;
  description?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface ExtractionResult {
  success: boolean;
  line_items: LineItem[];
  confidence_score: number;
  document_type?: string;
  document_number?: string;
  date?: string;
  vendor?: string;
  total_amount?: number;
  currency?: string;
  error?: string;
}

// Competitor Analysis Types
export interface CompetitorData {
  url: string;
  name: string;
  title?: string;
  description?: string;
  keywords?: string[];
  pricing?: string;
  features?: string[];
  last_updated: string;
  error?: string;
}

export interface CompetitorComparison {
  competitor: CompetitorData;
  ourProduct?: Product;
  priceComparison?: {
    competitorPrice: number;
    ourPrice: number;
    difference: number;
    percentDiff: number;
  };
}

// RAG Types
export interface Document {
  id: string;
  content: string;
  metadata: {
    source: string;
    type: string;
    created_at: string;
    [key: string]: any;
  };
  embedding?: number[];
}

export interface SearchResult {
  document: Document;
  score: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: SearchResult[];
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Chrome Extension Types
export interface PageContent {
  url: string;
  title: string;
  content: string;
  extractedAt: string;
}

export interface ExtractionJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  type: 'text' | 'pdf' | 'image';
  result?: ExtractionResult;
  error?: string;
  created_at: string;
}
