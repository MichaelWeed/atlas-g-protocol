import { io, type Socket } from 'socket.io-client';

interface AuditEntry {
  timestamp: string;
  action: string;
  status: 'PASS' | 'WARN' | 'BLOCK' | 'PENDING';
  details: string;
}

interface ChatResponse {
  content: string;
  blocked: boolean;
  facts_verified?: number;
  claims_filtered?: number;
  contact_requested?: boolean;
}

const SOCKET_URL = import.meta.env.VITE_API_URL || '';

class AtlasSocket {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<(data: unknown) => void>> = new Map();

  connect(): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(SOCKET_URL, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ Socket connection error:', error.message);
      console.error('Socket URL:', SOCKET_URL);
      console.error('Transport:', this.socket?.io.engine.transport.name);
    });

    this.socket.on('connect', () => {
      console.log('✅ Socket connected successfully to:', SOCKET_URL);
      console.log('Final Transport:', this.socket?.io.engine.transport.name);
    });

    // Re-attach listeners
    this.listeners.forEach((callbacks, event) => {
      callbacks.forEach((callback) => {
        this.socket?.on(event, callback as (...args: unknown[]) => void);
      });
    });

    return this.socket;
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }

  on(event: string, callback: (data: unknown) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    this.socket?.on(event, callback as (...args: unknown[]) => void);

    // Return unsubscribe function
    return () => {
      this.listeners.get(event)?.delete(callback);
      this.socket?.off(event, callback as (...args: unknown[]) => void);
    };
  }

  emit(event: string, data: unknown): void {
    this.socket?.emit(event, data);
  }

  sendMessage(message: string, sessionId?: string): void {
    this.emit('chat', { message, session_id: sessionId });
  }

  get isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

// Singleton instance
export const atlasSocket = new AtlasSocket();

export type { AuditEntry, ChatResponse };
