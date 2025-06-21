import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketMessage } from '../types';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  reconnect: () => void;
  websocket: WebSocket | null;
  // Event-specific data
  agentThoughts: WebSocketMessage[];
  fileChanges: WebSocketMessage[];
  commandOutputs: WebSocketMessage[];
  memoryUpdates: WebSocketMessage[];
  terminalOutputs: WebSocketMessage[];
}

export function useWebSocket(url: string, reconnectInterval = 3000): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  // Event-specific state
  const [agentThoughts, setAgentThoughts] = useState<WebSocketMessage[]>([]);
  const [fileChanges, setFileChanges] = useState<WebSocketMessage[]>([]);
  const [commandOutputs, setCommandOutputs] = useState<WebSocketMessage[]>([]);
  const [memoryUpdates, setMemoryUpdates] = useState<WebSocketMessage[]>([]);
  const [terminalOutputs, setTerminalOutputs] = useState<WebSocketMessage[]>([]);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  const shouldReconnect = useRef(true);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    setLastMessage(message);
    
    // Route messages to appropriate state arrays
    switch (message.type) {
      case 'agent_thought':
        setAgentThoughts(prev => [...prev.slice(-50), message]); // Keep last 50
        break;
        
      case 'file_changed':
      case 'file_created':
      case 'file_deleted':
      case 'file_moved':
        setFileChanges(prev => [...prev.slice(-100), message]); // Keep last 100
        break;
        
      case 'command_start':
      case 'command_output':
      case 'command_complete':
      case 'command_error':
        setCommandOutputs(prev => [...prev.slice(-50), message]); // Keep last 50
        break;
        
      case 'memory_updated':
        setMemoryUpdates(prev => [...prev.slice(-10), message]); // Keep last 10
        break;
        
      case 'terminal_output':
      case 'terminal_created':
      case 'terminal_destroyed':
        setTerminalOutputs(prev => [...prev.slice(-200), message]); // Keep last 200
        break;
        
      default:
        console.log('Received message:', message);
    }
  }, []);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setConnectionStatus('connected');
        console.log('WebSocket connected');
        
        // Send ping to verify connection
        sendMessage({ type: 'ping' });
      };

      ws.current.onclose = (event) => {
        setConnectionStatus('disconnected');
        console.log('WebSocket disconnected:', event.code, event.reason);
        
        // Auto-reconnect if not manually closed
        if (shouldReconnect.current && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.current.onerror = (error) => {
        setConnectionStatus('error');
        console.error('WebSocket error:', error);
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

    } catch (error) {
      setConnectionStatus('error');
      console.error('Error creating WebSocket connection:', error);
    }
  }, [url, reconnectInterval, handleMessage]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (ws.current) {
      ws.current.close();
    }
    
    connect();
  }, [connect]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    return () => {
      shouldReconnect.current = false;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  return {
    connectionStatus,
    sendMessage,
    lastMessage,
    reconnect,
    websocket: ws.current,
    agentThoughts,
    fileChanges,
    commandOutputs,
    memoryUpdates,
    terminalOutputs,
  };
}
