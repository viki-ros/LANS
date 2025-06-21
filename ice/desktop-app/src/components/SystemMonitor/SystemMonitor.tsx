interface SystemMonitorProps {
  websocket: WebSocket | null;
  connectionStatus?: string;
  sendMessage?: (message: any) => void;
}

function SystemMonitor({ }: SystemMonitorProps) {
  return (
    <div className="h-full p-6 overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Agent & System Monitor
        </h1>
        <div className="card p-6">
          <p className="text-gray-600 dark:text-gray-400">
            System Monitor implementation coming soon...
          </p>
        </div>
      </div>
    </div>
  );
}

export default SystemMonitor;
