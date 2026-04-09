import { useEffect, useCallback, useRef } from 'react';
import websocketService from '@/services/websocketService';
import { useAuth } from './useAuth';
import useNotificationStore from '@/store/notificationStore';
import type { Notification } from '@/types';

/**
 * Hook to manage WebSocket connection
 */
export const useWebSocket = () => {
  const { isAuthenticated } = useAuth();
  const { addNotification } = useNotificationStore();
  const isConnectedRef = useRef(false);

  useEffect(() => {
    if (isAuthenticated && !isConnectedRef.current) {
      // Connect to WebSocket
      websocketService.connect();
      isConnectedRef.current = true;

      // Handle notifications
      const handleNotification = (notification: Notification) => {
        addNotification(notification);
      };

      websocketService.on('notification', handleNotification);

      // Cleanup
      return () => {
        websocketService.off('notification', handleNotification);
      };
    }

    // Disconnect when user logs out
    if (!isAuthenticated && isConnectedRef.current) {
      websocketService.disconnect();
      isConnectedRef.current = false;
    }
  }, [isAuthenticated, addNotification]);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    websocketService.on(event, callback);

    return () => {
      websocketService.off(event, callback);
    };
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    websocketService.send(data);
  }, []);

  return {
    isConnected: websocketService.isConnected(),
    subscribe,
    send,
  };
};

/**
 * Hook to subscribe to specific WebSocket events
 */
export const useWebSocketEvent = <T = any>(
  event: string,
  callback: (data: T) => void
) => {
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe(event, callback);
    return unsubscribe;
  }, [event, callback, subscribe]);
};
