import { useState, useCallback, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import * as agentService from '@/services/agentService';
import type { ChatMessage, AgentContext } from '@/types';

/**
 * Hook to manage AI agent chat
 */
export const useAgentChat = (sessionId?: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [context, setContext] = useState<Partial<AgentContext>>({});

  // Fetch chat history
  const { data: historyData, isPending: isLoadingHistory } = useQuery({
    queryKey: ['chat-history', sessionId],
    queryFn: () => agentService.getChatHistory(sessionId),
    enabled: !!sessionId,
  });

  // Update messages when history loads
  useEffect(() => {
    if (historyData) {
      setMessages(historyData);
    }
  }, [historyData]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) => agentService.sendChatMessage(message, context),
  });

  const sendMessage = useCallback(
    async (message: string) => {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);

      // Send to agent
      await sendMessageMutation.mutateAsync(message);
    },
    [sendMessageMutation, context]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const updateContext = useCallback((newContext: Partial<AgentContext>) => {
    setContext((prev) => ({ ...prev, ...newContext }));
  }, []);

  return {
    messages,
    sendMessage,
    clearMessages,
    updateContext,
    isLoading: sendMessageMutation.isPending || isLoadingHistory,
    error: sendMessageMutation.error,
  };
};

/**
 * Hook to get agent suggestions
 */
export const useAgentSuggestions = (goals: string[], budget?: number) => {
  return useQuery({
    queryKey: ['agent-suggestions', goals, budget],
    queryFn: () => agentService.getAgentSuggestions(goals, budget),
    enabled: goals.length > 0,
  });
};

/**
 * Hook to get quick actions
 */
export const useQuickActions = () => {
  return useQuery({
    queryKey: ['quick-actions'],
    queryFn: agentService.getQuickActions,
  });
};
