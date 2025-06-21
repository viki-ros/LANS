// Common types for LANS ICE Desktop Application

export type ViewType = 'dashboard' | 'command' | 'workspace' | 'monitor' | 'tester';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

export interface WebSocketConnection {
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  isConnected: boolean;
}

export interface ProjectInfo {
  id: string;
  name: string;
  path: string;
  active: boolean;
}

export interface FileInfo {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

export interface AgentStatus {
  status: 'idle' | 'thinking' | 'executing' | 'error';
  current_task?: string;
  memory_usage?: string;
  uptime?: string;
}

export interface MemoryState {
  working_memory: {
    current_task?: string;
    task_stack: string[];
    timestamp: string;
  };
  context_buffer: {
    items: ContextItem[];
    total_items: number;
    total_size_kb: number;
  };
  knowledge_base: any;
  system_memory: {
    process_memory_mb: number;
    system_memory_percent: number;
    timestamp: string;
  };
  total_estimated_size_mb: number;
}

export interface ContextItem {
  id: string;
  type: 'file' | 'url' | 'text';
  content: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

export interface TerminalSession {
  session_id: string;
  is_active: boolean;
  working_directory: string;
  shell: string;
  process_alive: boolean;
  history_length: number;
}

export interface SystemMetrics {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_usage_percent: number;
  disk_free_gb: number;
  active_processes: number;
  timestamp: string;
}

export interface CommandRequest {
  command: string;
  context?: string[];
  mode?: 'assistant' | 'expert' | 'autonomous';
}

export interface AgentThought {
  content: string;
  context?: string[];
  confidence?: number;
  timestamp: string;
}

export interface FileChange {
  path: string;
  change_type: 'created' | 'modified' | 'deleted' | 'moved';
  diff?: string;
  old_path?: string;
  timestamp: string;
}

export interface ProjectHealth {
  tests_passed: number;
  tests_total: number;
  coverage_percent: number;
  build_status: 'success' | 'failure' | 'unknown';
  linting_status: 'success' | 'failure' | 'unknown';
  dependency_updates: number;
}

export interface ActivityItem {
  id: string;
  type: 'command' | 'file_change' | 'test' | 'build' | 'error';
  description: string;
  timestamp: string;
  status: 'success' | 'failure' | 'pending';
  details?: any;
}
