import { WS_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/helpers';

class WebSocketService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private url: string = '';

  /**
   * Connect to WebSocket server
   */
  connect(path = '/ws/notifications/'): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    const token = getAuthToken();
    if (!token) {
      console.warn('No auth token found, skipping WebSocket connection');
      return;
    }

    // Build WebSocket URL: wss://host/ws/notifications/?token=...
    const base = WS_BASE_URL.replace(/^http/, 'ws');
    this.url = `${base}${path}?token=${encodeURIComponent(token)}`;

    this.createConnection();
  }

  private createConnection(): void {
    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected', null);
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.emit('disconnected', { reason: event.reason, code: event.code });
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { message: 'WebSocket connection error' });
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const type = data.type || 'message';
          this.emit(type, data);
        } catch {
          console.warn('Non-JSON WebSocket message:', event.data);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('error', { message: 'Failed to connect to server' });
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      console.log(`WebSocket reconnecting (attempt ${this.reconnectAttempts})...`);
      this.createConnection();
    }, delay);
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // prevent reconnect
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.listeners.clear();
    }
  }

  /**
   * Send message through WebSocket
   */
  send(data: Record<string, unknown>): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, message not sent');
    }
  }

  /**
   * Add event listener
   */
  on(event: string, callback: (data: any) => void): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  /**
   * Remove event listener
   */
  off(event: string, callback: (data: any) => void): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.delete(callback);
      if (listeners.size === 0) {
        this.listeners.delete(event);
      }
    }
  }

  /**
   * Emit event to all listeners
   */
  private emit(event: string, data: any): void {
    const listeners = this.listeners.get(event);
    if (listeners) {
      listeners.forEach(callback => callback(data));
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
const websocketService = new WebSocketService();
export default websocketService;
