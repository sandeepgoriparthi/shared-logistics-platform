/**
 * API Client for Shared Logistics Platform
 * Connects to the Python FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Auth Types
export type UserRole = 'shipper' | 'carrier' | 'admin';

export interface User {
  id: string;
  email: string;
  full_name: string;
  company_name?: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  company_name?: string;
  phone?: string;
  role?: UserRole;
}

export interface LoginData {
  email: string;
  password: string;
}

// Types
export interface Location {
  address: string;
  city: string;
  state: string;
  zip_code: string;
  latitude?: number;
  longitude?: number;
}

export interface TimeWindow {
  earliest: string;
  latest: string;
}

export interface Dimensions {
  weight_lbs: number;
  linear_feet: number;
  pallet_count: number;
  piece_count: number;
  stackable: boolean;
}

export interface Shipment {
  id: string;
  reference_number: string;
  status: string;
  origin: Location;
  destination: Location;
  pickup_window: TimeWindow;
  delivery_window: TimeWindow;
  dimensions: Dimensions;
  distance_miles: number;
  quoted_price?: number;
  final_price?: number;
  savings_percent?: number;
  pooled: boolean;
  pooling_probability?: number;
  created_at: string;
  updated_at: string;
}

export interface Quote {
  id: string;
  shipment_id: string;
  base_rate: number;
  fuel_surcharge: number;
  accessorial_charges: number;
  pooling_discount: number;
  total_price: number;
  rate_per_mile: number;
  market_rate?: number;
  savings_vs_market?: number;
  pooling_probability: number;
  estimated_pooling_savings?: number;
  valid_until: string;
  status: string;
}

export interface PoolingMatch {
  id: string;
  shipment_ids: string[];
  num_shipments: number;
  geographic_score: number;
  temporal_score: number;
  capacity_score: number;
  overall_score: number;
  ml_probability: number;
  individual_cost_total: number;
  pooled_cost: number;
  total_savings: number;
  savings_percent: number;
  total_distance_miles: number;
  total_duration_hours: number;
  estimated_utilization: number;
  status: string;
  expires_at: string;
}

export interface Carrier {
  id: string;
  name: string;
  email: string;
  mc_number: string;
  dot_number: string;
  equipment_type: string;
  trailer_count: number;
  driver_count: number;
  on_time_percentage: number;
  damage_free_percentage: number;
  acceptance_rate: number;
  total_loads: number;
  total_miles: number;
  current_city?: string;
  current_state?: string;
  status: string;
  created_at: string;
}

export interface PlatformMetrics {
  total_shipments: number;
  shipments_today: number;
  shipments_this_week: number;
  shipments_this_month: number;
  pooled_shipments: number;
  pooling_rate_percent: number;
  total_savings_from_pooling: number;
  average_pooling_savings_percent: number;
  total_revenue: number;
  revenue_today: number;
  average_rate_per_mile: number;
  average_shipment_value: number;
  on_time_delivery_percent: number;
  damage_free_percent: number;
  average_transit_days: number;
  total_carriers: number;
  active_carriers: number;
  average_utilization_percent: number;
  total_miles_saved: number;
  carbon_reduced_kg: number;
}

// Helper function for API calls
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `API Error: ${response.status}`);
  }

  return response.json();
}

// API Client
export const api = {
  // Health check
  health: async () => {
    return fetchAPI<{ status: string; version: string }>('/health');
  },

  // Shipments
  shipments: {
    list: (params?: { status?: string; limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set('status', params.status);
      if (params?.limit) searchParams.set('limit', params.limit.toString());
      if (params?.offset) searchParams.set('offset', params.offset.toString());
      const query = searchParams.toString();
      return fetchAPI<Shipment[]>(`/shipments${query ? `?${query}` : ''}`);
    },

    get: (id: string) => {
      return fetchAPI<Shipment>(`/shipments/${id}`);
    },

    create: (data: {
      origin: Location;
      destination: Location;
      pickup_window: TimeWindow;
      delivery_window: TimeWindow;
      dimensions: Dimensions;
      equipment_type?: string;
      commodity_type?: string;
      requires_liftgate?: boolean;
      requires_appointment?: boolean;
    }) => {
      return fetchAPI<Shipment>('/shipments', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    book: (id: string, data: { quote_id: string; payment_method?: string }) => {
      return fetchAPI<{ shipment_id: string; booking_number: string; status: string }>(
        `/shipments/${id}/book`,
        {
          method: 'POST',
          body: JSON.stringify(data),
        }
      );
    },

    track: (id: string) => {
      return fetchAPI<{
        shipment_id: string;
        status: string;
        current_location?: Location;
        last_update: string;
        events: Array<{ timestamp: string; event: string; location?: string }>;
        estimated_pickup?: string;
        estimated_delivery?: string;
        route_id?: string;
        carrier_name?: string;
        driver_name?: string;
        driver_phone?: string;
      }>(`/shipments/${id}/tracking`);
    },

    cancel: (id: string) => {
      return fetchAPI<{ message: string; shipment_id: string }>(`/shipments/${id}`, {
        method: 'DELETE',
      });
    },
  },

  // Quotes
  quotes: {
    create: (shipmentId: string) => {
      return fetchAPI<Quote>('/quotes', {
        method: 'POST',
        body: JSON.stringify({ shipment_id: shipmentId }),
      });
    },

    get: (id: string) => {
      return fetchAPI<Quote>(`/quotes/${id}`);
    },

    accept: (id: string) => {
      return fetchAPI<{ message: string; quote_id: string; next_step: string }>(
        `/quotes/${id}/accept`,
        { method: 'POST' }
      );
    },

    list: (params?: { shipment_id?: string; status?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.shipment_id) searchParams.set('shipment_id', params.shipment_id);
      if (params?.status) searchParams.set('status', params.status);
      const query = searchParams.toString();
      return fetchAPI<Quote[]>(`/quotes${query ? `?${query}` : ''}`);
    },
  },

  // Pooling
  pooling: {
    optimize: (data?: {
      shipment_ids?: string[];
      origin_state?: string;
      dest_state?: string;
      max_shipments_per_pool?: number;
      min_savings_percent?: number;
    }) => {
      return fetchAPI<PoolingMatch[]>('/pooling/optimize', {
        method: 'POST',
        body: JSON.stringify(data || {}),
      });
    },

    listMatches: (params?: { status?: string; min_savings?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set('status', params.status);
      if (params?.min_savings) searchParams.set('min_savings', params.min_savings.toString());
      const query = searchParams.toString();
      return fetchAPI<PoolingMatch[]>(`/pooling/matches${query ? `?${query}` : ''}`);
    },

    getMatch: (id: string) => {
      return fetchAPI<PoolingMatch>(`/pooling/matches/${id}`);
    },

    execute: (id: string) => {
      return fetchAPI<{
        message: string;
        match_id: string;
        shipments_pooled: number;
        total_savings: number;
        savings_percent: number;
      }>(`/pooling/matches/${id}/execute`, {
        method: 'POST',
        body: JSON.stringify({ confirm: true }),
      });
    },

    stats: () => {
      return fetchAPI<{
        total_matches_found: number;
        matches_executed: number;
        total_savings_dollars: number;
        average_savings_percent: number;
        pooling_success_rate: number;
      }>('/pooling/stats');
    },
  },

  // Carriers
  carriers: {
    register: (data: {
      name: string;
      email: string;
      mc_number: string;
      dot_number: string;
      equipment_type?: string;
      trailer_count?: number;
    }) => {
      return fetchAPI<Carrier>('/carriers', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    list: (params?: { equipment_type?: string; state?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.equipment_type) searchParams.set('equipment_type', params.equipment_type);
      if (params?.state) searchParams.set('state', params.state);
      const query = searchParams.toString();
      return fetchAPI<Carrier[]>(`/carriers${query ? `?${query}` : ''}`);
    },

    get: (id: string) => {
      return fetchAPI<Carrier>(`/carriers/${id}`);
    },

    getMatches: (carrierId: string, params?: { min_rate?: number; max_deadhead?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.min_rate) searchParams.set('min_rate', params.min_rate.toString());
      if (params?.max_deadhead) searchParams.set('max_deadhead', params.max_deadhead.toString());
      const query = searchParams.toString();
      return fetchAPI<Array<{
        shipment_id: string;
        origin_city: string;
        origin_state: string;
        dest_city: string;
        dest_state: string;
        distance_miles: number;
        pickup_date: string;
        delivery_date: string;
        rate: number;
        rate_per_mile: number;
        linear_feet: number;
        weight_lbs: number;
        match_score: number;
      }>>(`/carriers/${carrierId}/matches${query ? `?${query}` : ''}`);
    },

    acceptLoad: (carrierId: string, shipmentId: string) => {
      return fetchAPI<{ message: string; carrier_id: string; shipment_id: string }>(
        `/carriers/${carrierId}/accept/${shipmentId}`,
        { method: 'POST' }
      );
    },

    updateAvailability: (carrierId: string, data: {
      available: boolean;
      current_latitude: number;
      current_longitude: number;
      current_city: string;
      current_state: string;
      available_from: string;
      available_until: string;
    }) => {
      return fetchAPI<{ message: string; carrier_id: string }>(
        `/carriers/${carrierId}/availability`,
        {
          method: 'PUT',
          body: JSON.stringify(data),
        }
      );
    },
  },

  // Analytics
  analytics: {
    platform: () => {
      return fetchAPI<PlatformMetrics>('/analytics/platform');
    },

    lanes: (params?: { origin_state?: string; dest_state?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.origin_state) searchParams.set('origin_state', params.origin_state);
      if (params?.dest_state) searchParams.set('dest_state', params.dest_state);
      const query = searchParams.toString();
      return fetchAPI<Array<{
        origin_state: string;
        dest_state: string;
        total_shipments: number;
        average_rate_per_mile: number;
        pooling_rate_percent: number;
        average_transit_days: number;
        demand_trend: string;
      }>>(`/analytics/lanes${query ? `?${query}` : ''}`);
    },

    forecast: (originState: string, destState: string, horizonDays?: number) => {
      const searchParams = new URLSearchParams();
      searchParams.set('origin_state', originState);
      searchParams.set('dest_state', destState);
      if (horizonDays) searchParams.set('horizon_days', horizonDays.toString());
      return fetchAPI<{
        lane: string;
        forecast_horizon_days: number;
        forecasts: Array<{
          lane: string;
          forecast_date: string;
          predicted_volume_low: number;
          predicted_volume_mid: number;
          predicted_volume_high: number;
          confidence: number;
        }>;
      }>(`/analytics/forecast?${searchParams.toString()}`);
    },

    savingsReport: () => {
      return fetchAPI<{
        period: { start: string; end: string };
        summary: {
          total_shipments: number;
          pooled_shipments: number;
          pooling_rate_percent: number;
        };
        financial: {
          total_billed: number;
          estimated_market_cost: number;
          total_savings_vs_market: number;
          savings_percent_vs_market: number;
          savings_from_pooling: number;
        };
        environmental: {
          miles_reduced: number;
          carbon_reduced_kg: number;
          trucks_removed_equivalent: number;
        };
      }>('/analytics/savings-report');
    },

    performance: () => {
      return fetchAPI<{
        delivery_performance: {
          total_delivered: number;
          currently_in_transit: number;
          on_time_rate_percent: number;
          damage_free_rate_percent: number;
          average_transit_time_hours: number;
        };
        carrier_performance: Array<{
          carrier_id: string;
          name: string;
          on_time_percent: number;
          damage_free_percent: number;
          total_loads: number;
        }>;
        pooling_efficiency: {
          average_shipments_per_pool: number;
          average_utilization_percent: number;
          pool_success_rate_percent: number;
        };
      }>('/analytics/performance');
    },
  },

  // Authentication
  auth: {
    register: (data: RegisterData) => {
      return fetchAPI<AuthToken>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    login: (data: LoginData) => {
      return fetchAPI<AuthToken>('/auth/login/json', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    logout: (token: string) => {
      return fetchAPI<{ message: string }>('/auth/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    },

    me: (token: string) => {
      return fetchAPI<User>('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    },

    updateProfile: (token: string, data: { full_name?: string; company_name?: string; phone?: string }) => {
      return fetchAPI<User>('/auth/me', {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
    },

    changePassword: (token: string, data: { current_password: string; new_password: string }) => {
      return fetchAPI<{ message: string }>('/auth/change-password', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
    },

    verify: (token: string) => {
      return fetchAPI<{ valid: boolean; user_id: string; email: string; role: string }>('/auth/verify', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    },
  },
};

export default api;
