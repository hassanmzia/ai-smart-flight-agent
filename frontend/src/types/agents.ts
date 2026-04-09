// ─────────────────────────────────────────────────
// Subscription & Plan Types
// ─────────────────────────────────────────────────

export interface SubscriptionStatus {
  plan: 'free' | 'pro' | 'business';
  status: 'active' | 'cancelled' | 'past_due' | 'trialing';
  usage: {
    ai_plans: { used: number; limit: number };
    price_alerts: { used: number; limit: number };
  };
  features: {
    voice_enabled: boolean;
    auto_builder_enabled: boolean;
    collaborators_limit: number;
  };
  period: {
    start: string | null;
    end: string | null;
  };
  stripe_customer_id: string | null;
}

export interface FeatureCheck {
  allowed: boolean;
  used?: number;
  limit?: number;
  feature: string;
  plan: string;
  upgrade_message?: string | null;
}

// ─────────────────────────────────────────────────
// Predictions Types
// ─────────────────────────────────────────────────

export interface PriceForecastItem {
  days_from_now: number;
  estimated_price: number;
  range: [number, number];
}

export interface PricePrediction {
  current_estimate: number | null;
  trend: 'rising' | 'falling' | 'stable' | 'unknown';
  confidence: number;
  forecast?: PriceForecastItem[];
  recommendation: 'buy_now' | 'wait' | 'monitor';
  reasoning: string;
  best_booking_window?: string;
}

export interface PricePredictionResponse {
  success: boolean;
  route: string;
  target_date: string;
  prediction: PricePrediction;
  historical_data: Array<Record<string, unknown>>;
}

export interface BestTimeMonth {
  month: string;
  score: number;
  weather: string;
  crowds: 'low' | 'moderate' | 'high';
  prices: 'low' | 'moderate' | 'high';
  events?: string[];
}

export interface BestTimeResponse {
  success: boolean;
  destination: string;
  best_months?: BestTimeMonth[];
  peak_season?: { months: string[]; reason: string };
  shoulder_season?: { months: string[]; reason: string };
  off_season?: { months: string[]; reason: string };
  overall_recommendation: string;
  budget_tip?: string;
  weather_tip?: string;
}

export interface TrendingDestination {
  destination: string;
  search_count: number;
  rank: number;
}

// ─────────────────────────────────────────────────
// Personalization Types
// ─────────────────────────────────────────────────

export interface TravelDNA {
  destinations: {
    favorite_destinations: string[];
    total_destinations: number;
    repeat_visitor?: boolean;
  };
  budget: {
    range: string;
    average_spend?: number;
    total_spend?: number;
    booking_count?: number;
  };
  style: {
    style: string;
    avg_trip_duration: number;
    top_interests?: string[];
  };
  timing: {
    preferred_booking_months: string[];
    avg_advance_days: number;
    is_last_minute?: boolean;
  };
  preferences: Record<string, unknown>;
}

export interface Recommendation {
  title: string;
  destination: string;
  reason: string;
  match_score: number;
  based_on: string;
}

// ─────────────────────────────────────────────────
// Debate Types
// ─────────────────────────────────────────────────

export interface DebateOption {
  name: string;
  price?: number | string;
  rating?: number;
  reviews_count?: number;
  location?: string;
  amenities?: string[];
  stops?: number;
  duration_hours?: number;
}

export interface DebateAgentResult {
  agent: string;
  perspective: string;
  recommendation: string | null;
  top_score: number;
  reasoning: string;
  all_scores: Array<{
    option: string;
    score: number;
    argument: string;
  }>;
}

export interface DebateResult {
  success: boolean;
  debate: DebateAgentResult[];
  final_recommendation: {
    winner: string | null;
    total_score: number;
    score_breakdown: Record<string, { raw_score: number; weighted_score: number; argument: string }>;
    all_rankings: Array<{ name: string; score: number }>;
    consensus: boolean;
    llm_verdict?: string;
  };
  options_evaluated: number;
}

// ─────────────────────────────────────────────────
// Affiliate Types
// ─────────────────────────────────────────────────

export interface AffiliatePartner {
  id: string;
  name: string;
  types: string[];
  commission_rate: string;
}

export interface AffiliateLink {
  success: boolean;
  tracking_id?: string;
  affiliate_url?: string;
  partner?: string;
  click_id?: number;
  error?: string;
}

export interface AffiliateReport {
  success: boolean;
  period_days: number;
  total_clicks: number;
  total_conversions: number;
  conversion_rate: string;
  total_revenue: number;
  by_partner: Array<{
    partner: string;
    clicks: number;
    conversions_count: number;
    revenue: number | null;
  }>;
}

// ─────────────────────────────────────────────────
// Price Watch Types
// ─────────────────────────────────────────────────

export interface PriceWatch {
  id: number;
  watch_type: 'flight' | 'hotel';
  search_params: Record<string, unknown>;
  target_price: number | null;
  current_price: number | null;
  lowest_price: number | null;
  price_history: Array<{ date: string; price: number }>;
  created_at: string;
  updated_at: string;
}

// ─────────────────────────────────────────────────
// Autonomous Booking Types
// ─────────────────────────────────────────────────

export interface AutonomousBookingResult {
  success: boolean;
  task_id?: string;
  package?: {
    flight: Record<string, unknown>;
    hotel: Record<string, unknown>;
    alternatives: Record<string, unknown>[];
  };
  summary?: string;
  total_cost?: number;
  error?: string;
}

// ─────────────────────────────────────────────────
// Conversation Types
// ─────────────────────────────────────────────────

export interface AgentConversation {
  id: string;
  title: string;
  status: 'active' | 'archived' | 'deleted';
  conversation_type: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface AgentMessage {
  id: string;
  conversation: string;
  content: string;
  sender_type: 'user' | 'agent' | 'system';
  message_type: string;
  metadata: Record<string, unknown>;
  intent: string;
  response_time_ms: number | null;
  tokens_used: number;
  created_at: string;
}
