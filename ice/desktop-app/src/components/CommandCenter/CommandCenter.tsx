interface CommandCenterProps {
  websocket: WebSocket | null;
  connectionStatus?: string;
  sendMessage?: (message: any) => void;
}

function CommandCenter({ }: CommandCenterProps) {
  return (
    <div className="h-full p-6 overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          Command & Cognition Center
        </h1>
        <div className="card p-6">
          <p className="text-gray-600 dark:text-gray-400">
            Command Center implementation coming soon...
          </p>
        </div>
      </div>
    </div>
  );
}

export default CommandCenter;
