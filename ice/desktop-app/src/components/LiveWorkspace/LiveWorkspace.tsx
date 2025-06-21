import { useState } from 'react';
import { Terminal } from '../Terminal';
import { CodeEditor } from '../CodeEditor';
import { Split, Terminal as TerminalIcon, Code, Monitor } from 'lucide-react';

interface LiveWorkspaceProps {
  websocket: WebSocket | null;
  fileChanges?: any[];
  terminalOutputs?: any[];
  onFileSelect?: (path: string) => void;
  connectionStatus?: string;
  sendMessage?: (message: any) => void;
}

function LiveWorkspace({ 
  websocket, 
  fileChanges = [], 
  terminalOutputs = []
}: LiveWorkspaceProps) {
  const [layout, setLayout] = useState<'horizontal' | 'vertical' | 'editor-only' | 'terminal-only'>('horizontal');
  const [showMonitor, setShowMonitor] = useState(false);

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">
            Live Workspace
          </h1>
          
          {/* Layout Controls */}
          <div className="flex items-center space-x-2">
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setLayout('horizontal')}
                className={`p-2 rounded ${layout === 'horizontal' 
                  ? 'bg-white dark:bg-gray-600 shadow' 
                  : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Horizontal Split"
              >
                <Split size={16} className="rotate-90" />
              </button>
              <button
                onClick={() => setLayout('vertical')}
                className={`p-2 rounded ${layout === 'vertical' 
                  ? 'bg-white dark:bg-gray-600 shadow' 
                  : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Vertical Split"
              >
                <Split size={16} />
              </button>
              <button
                onClick={() => setLayout('editor-only')}
                className={`p-2 rounded ${layout === 'editor-only' 
                  ? 'bg-white dark:bg-gray-600 shadow' 
                  : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Editor Only"
              >
                <Code size={16} />
              </button>
              <button
                onClick={() => setLayout('terminal-only')}
                className={`p-2 rounded ${layout === 'terminal-only' 
                  ? 'bg-white dark:bg-gray-600 shadow' 
                  : 'hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Terminal Only"
              >
                <TerminalIcon size={16} />
              </button>
            </div>
            
            <button
              onClick={() => setShowMonitor(!showMonitor)}
              className={`p-2 rounded ${showMonitor 
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' 
                : 'hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              title="Toggle Activity Monitor"
            >
              <Monitor size={16} />
            </button>
          </div>
        </div>
        
        {/* Activity Monitor */}
        {showMonitor && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
              <div className="text-sm font-medium text-green-800 dark:text-green-200">
                File Changes
              </div>
              <div className="text-lg font-bold text-green-900 dark:text-green-100">
                {fileChanges.length}
              </div>
            </div>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
              <div className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Terminal Sessions
              </div>
              <div className="text-lg font-bold text-blue-900 dark:text-blue-100">
                {terminalOutputs.length}
              </div>
            </div>
            
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3">
              <div className="text-sm font-medium text-purple-800 dark:text-purple-200">
                Connection Status
              </div>
              <div className="text-lg font-bold text-purple-900 dark:text-purple-100">
                {websocket ? 'Connected' : 'Disconnected'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {layout === 'horizontal' && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 border-b border-gray-200 dark:border-gray-700">
              <CodeEditor websocket={websocket} className="h-full" />
            </div>
            <div className="h-64">
              <Terminal websocket={websocket} className="h-full" />
            </div>
          </div>
        )}

        {layout === 'vertical' && (
          <div className="flex-1 flex">
            <div className="flex-1 border-r border-gray-200 dark:border-gray-700">
              <CodeEditor websocket={websocket} className="h-full" />
            </div>
            <div className="w-1/2">
              <Terminal websocket={websocket} className="h-full" />
            </div>
          </div>
        )}

        {layout === 'editor-only' && (
          <div className="flex-1">
            <CodeEditor websocket={websocket} className="h-full" />
          </div>
        )}

        {layout === 'terminal-only' && (
          <div className="flex-1">
            <Terminal websocket={websocket} className="h-full" />
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveWorkspace;
