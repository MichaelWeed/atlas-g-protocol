import { useState, useEffect, useCallback, useRef } from 'react';
import { atlasSocket } from '../lib/socket';
import type { AuditEntry, ChatResponse } from '../lib/socket';

interface Message {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    blocked?: boolean;
    factsVerified?: number;
    claimsFiltered?: number;
    contactRequested?: boolean;
    sessionTerminated?: boolean;
  };
}

export interface AuditThread {
  id: string;
  query: string;
  entries: AuditEntry[];
}

interface UseAtlasAgentReturn {
  messages: Message[];
  auditThreads: AuditThread[];
  isConnected: boolean;
  isProcessing: boolean;
  sendMessage: (message: string) => void;
  clearMessages: () => void;
}

export function useAtlasAgent(): UseAtlasAgentReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [auditThreads, setAuditThreads] = useState<AuditThread[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const sessionIdRef = useRef<string | undefined>(undefined);

  useEffect(() => {
    // Connect to socket
    atlasSocket.connect();

    // Set up listeners
    const unsubConnect = atlasSocket.on('connect', () => {
      setIsConnected(true);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          type: 'system',
          content: '🔒 SECURE CONNECTION ESTABLISHED',
          timestamp: new Date(),
        },
      ]);
    });

    const unsubDisconnect = atlasSocket.on('disconnect', () => {
      setIsConnected(false);
    });

    const unsubAudit = atlasSocket.on('audit', (data) => {
      setAuditThreads((prev) => {
        if (prev.length === 0) return prev;
        const lastThread = prev[prev.length - 1];
        const updatedThread = {
          ...lastThread,
          entries: [...lastThread.entries, data as AuditEntry]
        };
        return [...prev.slice(0, -1), updatedThread];
      });
    });

    const unsubResponse = atlasSocket.on('response', (data) => {
      const response = data as ChatResponse;
      setIsProcessing(false);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          type: 'agent',
          content: response.content,
          timestamp: new Date(),
          metadata: {
            blocked: response.blocked,
            factsVerified: response.facts_verified,
            claimsFiltered: response.claims_filtered,
            contactRequested: (response as any).contact_requested,
            sessionTerminated: (response as any).session_terminated,
          },
        },
      ]);
    });

    const unsubError = atlasSocket.on('error', (data) => {
      const error = data as { message: string };
      setIsProcessing(false);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          type: 'system',
          content: `⚠️ Error: ${error.message}`,
          timestamp: new Date(),
        },
      ]);
    });

    return () => {
      unsubConnect();
      unsubDisconnect();
      unsubAudit();
      unsubResponse();
      unsubError();
      atlasSocket.disconnect();
    };
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (!message.trim()) return;

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        type: 'user',
        content: message,
        timestamp: new Date(),
      },
    ]);

    // Add a new audit thread for this query
    setAuditThreads((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        query: message,
        entries: []
      }
    ]);
    setIsProcessing(true);

    // Send to backend
    atlasSocket.sendMessage(message, sessionIdRef.current);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setAuditThreads([]);
  }, []);

  return {
    messages,
    auditThreads,
    isConnected,
    isProcessing,
    sendMessage,
    clearMessages,
  };
}
