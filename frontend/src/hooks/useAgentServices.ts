/**
 * React Query hooks for commercialization agent endpoints.
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/services/api';
import { API_ENDPOINTS, QUERY_KEYS } from '@/utils/constants';
import type {
  SubscriptionStatus,
  FeatureCheck,
  PricePredictionResponse,
  BestTimeResponse,
  TrendingDestination,
  TravelDNA,
  Recommendation,
  DebateResult,
  DebateOption,
  AffiliatePartner,
  AffiliateLink,
  AffiliateReport,
  PriceWatch,
  AutonomousBookingResult,
} from '@/types/agents';

// ── Subscription ──

export const useSubscription = () =>
  useQuery<SubscriptionStatus>({
    queryKey: ['subscription'],
    queryFn: async () => {
      const { data } = await api.get(API_ENDPOINTS.AGENT.SUBSCRIPTION);
      return data;
    },
  });

export const useCheckFeature = () =>
  useMutation<FeatureCheck, Error, string>({
    mutationFn: async (feature) => {
      const { data } = await api.post('/api/agents/check-feature', { feature });
      return data;
    },
  });

// ── Predictions ──

export const usePredictPrices = () =>
  useMutation<PricePredictionResponse, Error, { origin: string; destination: string; target_date: string; days_ahead?: number }>({
    mutationFn: async (params) => {
      const { data } = await api.post(API_ENDPOINTS.AGENT.PREDICT_PRICES, params);
      return data;
    },
  });

export const useBestTime = (destination: string | null) =>
  useQuery<BestTimeResponse>({
    queryKey: ['best-time', destination],
    queryFn: async () => {
      const { data } = await api.get(`${API_ENDPOINTS.AGENT.BEST_TIME}?destination=${encodeURIComponent(destination!)}`);
      return data;
    },
    enabled: !!destination,
  });

export const useTrends = () =>
  useQuery<{ trending_destinations: TrendingDestination[] }>({
    queryKey: ['trends'],
    queryFn: async () => {
      const { data } = await api.get(`${API_ENDPOINTS.AGENT.TRENDS}?limit=10`);
      return data;
    },
    enabled: false, // Manual trigger only
  });

// ── Personalization ──

export const useTravelDNA = () =>
  useQuery<{ success: boolean; travel_dna: TravelDNA }>({
    queryKey: ['travel-dna'],
    queryFn: async () => {
      const { data } = await api.get(API_ENDPOINTS.AGENT.TRAVEL_DNA);
      return data;
    },
  });

export const useRecommendations = (limit = 5) =>
  useQuery<{ success: boolean; travel_dna: TravelDNA; recommendations: Recommendation[] }>({
    queryKey: ['recommendations', limit],
    queryFn: async () => {
      const { data } = await api.get(`${API_ENDPOINTS.AGENT.RECOMMENDATIONS}?limit=${limit}`);
      return data;
    },
  });

// ── Debate ──

export const useDebate = () =>
  useMutation<DebateResult, Error, { options: DebateOption[]; context?: Record<string, unknown>; use_llm?: boolean }>({
    mutationFn: async (params) => {
      const { data } = await api.post('/api/agents/debate', params);
      return data;
    },
  });

// ── Affiliate ──

export const useAffiliatePartners = (clickType?: string) =>
  useQuery<{ success: boolean; partners: AffiliatePartner[] }>({
    queryKey: ['affiliate-partners', clickType],
    queryFn: async () => {
      const url = clickType
        ? `${API_ENDPOINTS.AGENT.AFFILIATE_LINK}/../partners?type=${clickType}`
        : '/api/agents/affiliate/partners';
      const { data } = await api.get(url);
      return data;
    },
  });

export const useGenerateAffiliateLink = () =>
  useMutation<AffiliateLink, Error, { partner: string; click_type: string; destination?: string }>({
    mutationFn: async (params) => {
      const { data } = await api.post(API_ENDPOINTS.AGENT.AFFILIATE_LINK, params);
      return data;
    },
  });

export const useAffiliateReport = (days = 30) =>
  useQuery<AffiliateReport>({
    queryKey: ['affiliate-report', days],
    queryFn: async () => {
      const { data } = await api.get(`${API_ENDPOINTS.AGENT.AFFILIATE_REPORT}?days=${days}`);
      return data;
    },
  });

// ── Price Watch ──

export const usePriceWatches = () =>
  useQuery<{ success: boolean; watches: PriceWatch[] }>({
    queryKey: ['price-watches'],
    queryFn: async () => {
      const { data } = await api.get(API_ENDPOINTS.AGENT.PRICE_WATCH_LIST);
      return data;
    },
  });

export const useCreatePriceWatch = () =>
  useMutation<Record<string, unknown>, Error, { watch_type: string; search_params: Record<string, unknown>; target_price?: number }>({
    mutationFn: async (params) => {
      const { data } = await api.post(API_ENDPOINTS.AGENT.PRICE_WATCH_CREATE, params);
      return data;
    },
  });

// ── Autonomous Booking ──

export const useAutonomousBook = () =>
  useMutation<AutonomousBookingResult, Error, {
    destination: string;
    start_date: string;
    end_date: string;
    origin?: string;
    budget?: number;
    travelers?: number;
    preferences?: Record<string, unknown>;
  }>({
    mutationFn: async (params) => {
      const { data } = await api.post(API_ENDPOINTS.AGENT.AUTONOMOUS_BOOK, params);
      return data;
    },
  });

export const useConfirmBooking = () =>
  useMutation<Record<string, unknown>, Error, { task_id: string }>({
    mutationFn: async (params) => {
      const { data } = await api.post('/api/agents/confirm-booking', params);
      return data;
    },
  });
