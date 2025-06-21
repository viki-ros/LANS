import React, { useEffect, useRef, useState } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import 'xterm/css/xterm.css';

interface TerminalProps {
  onMessage?: (message: any) => void;
  websocket?: WebSocket | null;
  className?: string;
}

export const Terminal: React.FC<TerminalProps> = ({ 
  onMessage, 
  websocket, 
  className = '' 
}) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!terminalRef.current) return;

    // Create terminal instance
    const terminal = new XTerm({
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#d4d4d4',
        selectionBackground: '#264f78',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      },
      fontSize: 14,
      fontFamily: 'Consolas, "Courier New", monospace',
      cursorBlink: true,
      scrollback: 10000,
      tabStopWidth: 4
    });

    // Create addons
    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    terminal.loadAddon(fitAddon);
    terminal.loadAddon(webLinksAddon);

    // Open terminal
    terminal.open(terminalRef.current);
    fitAddon.fit();

    // Store references
    xtermRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Welcome message
    terminal.writeln('\x1b[32mLANS ICE Terminal\x1b[0m');
    terminal.writeln('Connecting to agent host...');

    // Handle terminal input
    terminal.onData((data) => {
      if (websocket && sessionId && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'terminal_input',
          session_id: sessionId,
          data: data
        }));
      }
    });

    // Handle resize
    const handleResize = () => {
      fitAddon.fit();
      if (websocket && sessionId && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'terminal_resize',
          session_id: sessionId,
          cols: terminal.cols,
          rows: terminal.rows
        }));
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      terminal.dispose();
    };
  }, []);

  // Handle WebSocket connection and messages
  useEffect(() => {
    if (!websocket || !xtermRef.current) return;

    if (websocket.readyState === WebSocket.OPEN && !sessionId) {
      // Create terminal session
      websocket.send(JSON.stringify({
        type: 'create_terminal'
      }));
    }

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'terminal_created':
            setSessionId(message.session_id);
            setIsConnected(true);
            xtermRef.current?.writeln(`\x1b[32m✅ Agent Command Session Created: ${message.session_id.slice(0, 8)}...\x1b[0m`);
            xtermRef.current?.writeln(`\x1b[36m📁 Working Directory: ${message.working_directory}\x1b[0m`);
            xtermRef.current?.writeln('Type commands to interact with the agent...\r\n');
            break;

          case 'command_start':
            if (message.session_id === sessionId) {
              xtermRef.current?.writeln(`\x1b[33m🚀 Executing: ${message.command}\x1b[0m`);
            }
            break;

          case 'terminal_output':
            if (message.session_id === sessionId) {
              // Color code different streams
              const color = message.stream === 'stderr' ? '\x1b[31m' : '\x1b[37m'; // Red for stderr, white for stdout
              xtermRef.current?.write(`${color}${message.data}\x1b[0m`);
            }
            break;

          case 'command_complete':
            if (message.session_id === sessionId) {
              const statusColor = message.success ? '\x1b[32m' : '\x1b[31m'; // Green for success, red for failure
              const statusIcon = message.success ? '✅' : '❌';
              xtermRef.current?.writeln(`${statusColor}${statusIcon} Command completed (exit code: ${message.exit_code})\x1b[0m`);
            }
            break;

          case 'command_error':
            if (message.session_id === sessionId) {
              xtermRef.current?.writeln(`\x1b[31m❌ Command Error: ${message.error}\x1b[0m`);
            }
            break;

          case 'terminal_error':
            if (message.session_id === sessionId) {
              xtermRef.current?.writeln(`\x1b[31m⚠️  Error: ${message.error}\x1b[0m`);
            }
            break;

          case 'agent_thought':
            // Display agent thoughts in a different color
            xtermRef.current?.writeln(`\x1b[36m🤖 [Agent] ${message.content}\x1b[0m`);
            break;

          case 'agent_action':
            xtermRef.current?.writeln(`\x1b[33m⚡ [Action] ${message.action}: ${message.description}\x1b[0m`);
            break;
        }

        // Pass message to parent component
        if (onMessage) {
          onMessage(message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    websocket.addEventListener('message', handleMessage);

    return () => {
      websocket.removeEventListener('message', handleMessage);
    };
  }, [websocket, sessionId, onMessage]);

  // Fit terminal on connection
  useEffect(() => {
    if (isConnected && fitAddonRef.current) {
      setTimeout(() => {
        fitAddonRef.current?.fit();
      }, 100);
    }
  }, [isConnected]);

  return (
    <div className={`terminal-container ${className}`}>
      <div className="terminal-header bg-gray-800 text-white px-4 py-2 text-sm">
        <div className="flex items-center justify-between">
          <span>Terminal {sessionId ? `(${sessionId.slice(0, 8)})` : '(disconnected)'}</span>
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xs">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>
      <div 
        ref={terminalRef} 
        className="terminal-content"
        style={{ 
          height: '100%', 
          backgroundColor: '#1e1e1e',
          padding: '8px'
        }}
      />
    </div>
  );
};
