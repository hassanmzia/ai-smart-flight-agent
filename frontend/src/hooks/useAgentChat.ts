import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/services/api';
import { API_ENDPOINTS, QUERY_KEYS } from '@/utils/constants';
import useAuthStore from '@/store/authStore';
import type { ChatMessage } from '@/types';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ExtractedParams {
  origin?: string;
  destination?: string;
  departure_date?: string;
  return_date?: string;
  passengers?: number;
  budget?: number;
  cuisine?: string;
  [key: string]: any;
}

interface ChatResponse {
  success: boolean;
  reply: string;
  extracted_params?: ExtractedParams;
  params_complete?: boolean;
  ready_to_plan?: boolean;
  planning_result?: any;
  error?: string;
}

/**
 * Fully conversational AI travel assistant hook.
 *
 * Maintains conversation history, extracted parameters, and can
 * answer questions about the user's trips, bookings, recommendations,
 * and future travel plans.
 */
export const useAgentChat = (_sessionId?: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [extractedParams, setExtractedParams] = useState<ExtractedParams>({});
  const [paramsComplete, setParamsComplete] = useState(false);
  const conversationRef = useRef<ConversationMessage[]>([]);
  const extractedParamsRef = useRef<ExtractedParams>({});
  const { user, isAuthenticated } = useAuthStore();

  // Keep refs in sync
  useEffect(() => {
    extractedParamsRef.current = extractedParams;
  }, [extractedParams]);

  // Fetch user's bookings to give the assistant context
  const { data: bookingsData } = useQuery({
    queryKey: QUERY_KEYS.BOOKINGS,
    queryFn: async () => {
      try {
        const res = await api.get(API_ENDPOINTS.BOOKINGS.LIST);
        return res.data?.results || res.data || [];
      } catch { return []; }
    },
    enabled: isAuthenticated,
    staleTime: 60_000,
  });

  // Fetch user's itineraries for context
  const { data: itinerariesData } = useQuery({
    queryKey: QUERY_KEYS.ITINERARIES,
    queryFn: async () => {
      try {
        const res = await api.get(API_ENDPOINTS.ITINERARY.LIST);
        return res.data?.results || res.data || [];
      } catch { return []; }
    },
    enabled: isAuthenticated,
    staleTime: 60_000,
  });

  /**
   * Build a user-context summary for the backend so the LLM
   * can answer questions about the user's existing trips.
   */
  const buildUserContext = useCallback(() => {
    const parts: string[] = [];

    if (user) {
      parts.push(`User: ${user.first_name || user.name || 'Traveler'} (${user.email || ''})`);
    }

    if (bookingsData && Array.isArray(bookingsData) && bookingsData.length > 0) {
      const summary = bookingsData.slice(0, 10).map((b: any) => {
        const items = b.items && Array.isArray(b.items)
          ? b.items.map((item: any) => {
              const dateStr = item.start_date ? ` on ${item.start_date}` : '';
              return `${item.item_type}: ${item.item_name}${dateStr}`;
            }).join(', ')
          : 'no items';
        return `  - Booking #${b.booking_number}: ${items} | status: ${b.status}, total: $${b.total_amount}`;
      }).join('\n');
      parts.push(`\nUser's bookings (${bookingsData.length}):\n${summary}`);
    }

    if (itinerariesData && Array.isArray(itinerariesData) && itinerariesData.length > 0) {
      const summary = itinerariesData.slice(0, 10).map((it: any) => {
        const origin = it.origin_city || 'unknown';
        const budget = it.estimated_budget ? `$${it.estimated_budget}` : 'not set';
        return `  - "${it.title}": ${origin} -> ${it.destination} (${it.start_date} to ${it.end_date}, ${it.number_of_travelers || 1} travelers, status: ${it.status}, budget: ${budget})`;
      }).join('\n');
      parts.push(`\nUser's trip plans/itineraries (${itinerariesData.length}):\n${summary}`);
    }

    return parts.length > 0 ? parts.join('\n') : '';
  }, [user, bookingsData, itinerariesData]);

  /**
   * Send a message to the AI assistant. Supports:
   *  - General travel questions
   *  - Questions about the user's bookings/itineraries
   *  - Trip planning with parameter extraction
   *  - Recommendation queries
   */
  const sendMessage = useCallback(async (message: string) => {
    setError(null);
    setIsLoading(true);

    // Immediately add the user message to the UI
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    // Track in conversation history
    conversationRef.current = [
      ...conversationRef.current,
      { role: 'user', content: message },
    ];

    try {
      const userContext = buildUserContext();

      const payload: Record<string, any> = {
        message,
        conversation: conversationRef.current.slice(-20), // last 20 messages
        extracted_params: extractedParamsRef.current,
        confirmed: false,
        user_context: userContext,
      };

      const response = await api.post<ChatResponse>(
        API_ENDPOINTS.AGENT.CHAT,
        payload,
        { timeout: 60000 }, // 60s timeout for LLM calls
      );

      const data = response.data;

      if (data.success && data.reply) {
        const assistantMsg: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data.reply,
          timestamp: new Date().toISOString(),
          metadata: data.planning_result ? {
            flightResults: data.planning_result?.recommendation?.top_5_flights,
            hotelResults: data.planning_result?.recommendation?.top_5_hotels,
            suggestions: data.extracted_params
              ? Object.entries(data.extracted_params)
                  .filter(([, v]) => v)
                  .map(([k, v]) => `${k}: ${v}`)
              : undefined,
          } : undefined,
        };

        setMessages(prev => [...prev, assistantMsg]);
        conversationRef.current = [
          ...conversationRef.current,
          { role: 'assistant', content: data.reply },
        ];

        // Update extracted params
        if (data.extracted_params) {
          setExtractedParams(data.extracted_params);
        }
        if (data.params_complete !== undefined) {
          setParamsComplete(data.params_complete);
        }
      } else {
        // Handle error or no-reply
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: data.error || 'Sorry, I had trouble processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMsg]);
        conversationRef.current = [
          ...conversationRef.current,
          { role: 'assistant', content: errorMsg.content },
        ];
      }
    } catch (err: any) {
      const errorMessage = err?.message || err?.response?.data?.error || 'Connection error. Please try again.';
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `I'm having trouble connecting right now. ${errorMessage}`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
      conversationRef.current = [
        ...conversationRef.current,
        { role: 'assistant', content: errorMsg.content },
      ];
      setError(err instanceof Error ? err : new Error(errorMessage));
    } finally {
      setIsLoading(false);
    }
  }, [buildUserContext]);

  /**
   * Confirm the extracted parameters and trigger trip planning
   */
  const confirmPlan = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const confirmMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: 'Yes, plan my trip!',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, confirmMsg]);

    try {
      const response = await api.post<ChatResponse>(
        API_ENDPOINTS.AGENT.CHAT,
        {
          message: 'Confirm and plan my trip',
          conversation: conversationRef.current.slice(-20),
          extracted_params: extractedParamsRef.current,
          confirmed: true,
        },
        { timeout: 180000 }, // 3 min timeout for full trip planning
      );

      const data = response.data;

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.reply || 'Your trip has been planned! Check the results.',
        timestamp: new Date().toISOString(),
        metadata: data.planning_result ? {
          flightResults: data.planning_result?.recommendation?.top_5_flights,
          hotelResults: data.planning_result?.recommendation?.top_5_hotels,
        } : undefined,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, there was an error planning your trip. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
      setError(err instanceof Error ? err : new Error('Planning failed'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    conversationRef.current = [];
    setExtractedParams({});
    setParamsComplete(false);
  }, []);

  return {
    messages,
    sendMessage,
    confirmPlan,
    clearMessages,
    isLoading,
    error,
    extractedParams,
    paramsComplete,
  };
};

/**
 * Hook to get agent suggestions
 */
export const useAgentSuggestions = (goals: string[], budget?: number) => {
  return useQuery({
    queryKey: ['agent-suggestions', goals, budget],
    queryFn: async () => {
      const res = await api.post(`${API_ENDPOINTS.AGENT.CHAT}/suggestions`, { goals, budget });
      return res.data;
    },
    enabled: goals.length > 0,
  });
};

/**
 * Hook to get quick actions
 */
export const useQuickActions = () => {
  return useQuery({
    queryKey: ['quick-actions'],
    queryFn: async () => {
      const res = await api.get(`${API_ENDPOINTS.AGENT.CHAT}/quick-actions`);
      return res.data;
    },
  });
};
