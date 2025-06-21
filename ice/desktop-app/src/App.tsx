import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { Monitor, Terminal, MessageSquare, Activity } from 'lucide-react';

// Components
import ProjectDashboard from './components/ProjectDashboard/ProjectDashboard';
import CommandCenter from './components/CommandCenter/CommandCenter';
import LiveWorkspace from './components/LiveWorkspace/LiveWorkspace';
import SystemMonitor from './components/SystemMonitor/SystemMonitor';
import { WebSocketTester } from './components/WebSocketTester';

// Services and Hooks
import { useWebSocket } from './hooks/useWebSocket';
import { useTheme } from './hooks/useTheme';

// Types
import { ViewType } from './types';

function App() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [isConnected, setIsConnected] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { 
    connectionStatus, 
    sendMessage, 
    agentThoughts,
    fileChanges,
    commandOutputs,
    memoryUpdates,
    terminalOutputs,
    websocket
  } = useWebSocket('ws://localhost:8766/ws');

  useEffect(() => {
    setIsConnected(connectionStatus === 'connected');
  }, [connectionStatus]);

  const views = [
    { id: 'dashboard' as ViewType, label: 'Mission Control', icon: Monitor, component: ProjectDashboard },
    { id: 'command' as ViewType, label: 'Command Center', icon: MessageSquare, component: CommandCenter },
    { id: 'workspace' as ViewType, label: 'Live Workspace', icon: Terminal, component: LiveWorkspace },
    { id: 'monitor' as ViewType, label: 'System Monitor', icon: Activity, component: SystemMonitor },
    { id: 'tester' as ViewType, label: 'WebSocket Tester', icon: Activity, component: WebSocketTester },
  ];

  const currentViewComponent = views.find(view => view.id === currentView)?.component || ProjectDashboard;
  const CurrentViewComponent = currentViewComponent;

  // Prepare props for each component
  const handleAttachContext = (type: string, content: string) => {
    sendMessage({
      type: 'attach_context',
      attachment: { type, content }
    });
  };

  const handleFileSelect = (path: string) => {
    sendMessage({
      type: 'file_select',
      path
    });
  };

  const getComponentProps = () => {
    const baseProps = {
      connectionStatus,
      sendMessage,
      websocket
    };

    switch (currentView) {
      case 'dashboard':
        return {
          ...baseProps,
          agentThoughts,
          fileChanges,
          commandOutputs
        };
      case 'command':
        return {
          ...baseProps,
          agentThoughts,
          onAttachContext: handleAttachContext
        };
      case 'workspace':
        return {
          ...baseProps,
          websocket,
          fileChanges,
          terminalOutputs,
          onFileSelect: handleFileSelect
        };
      case 'monitor':
        return {
          ...baseProps,
          memoryUpdates,
          agentThoughts
        };
      default:
        return baseProps;
    }
  };

  return (
    <div className={`h-screen flex flex-col ${theme === 'dark' ? 'dark' : ''}`}>
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">L</span>
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                LANS ICE
              </h1>
            </div>
            
            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-success-500 animate-pulse' : 'bg-error-500'
              }`} />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            {theme === 'dark' ? '🌞' : '🌙'}
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-4">
          <div className="flex space-x-1">
            {views.map((view) => {
              const Icon = view.icon;
              return (
                <button
                  key={view.id}
                  onClick={() => setCurrentView(view.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    currentView === view.id
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon size={16} />
                  <span className="text-sm font-medium">{view.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            <CurrentViewComponent 
              {...getComponentProps()}
            />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
