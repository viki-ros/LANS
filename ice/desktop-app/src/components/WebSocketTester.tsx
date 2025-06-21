import { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export function WebSocketTester() {
  const {
    connectionStatus,
    sendMessage,
    lastMessage,
    reconnect,
    agentThoughts,
    fileChanges,
    commandOutputs,
    memoryUpdates,
    terminalOutputs
  } = useWebSocket('ws://localhost:8765/ws');

  const [testResults, setTestResults] = useState<Record<string, string>>({});

  const runTest = (testName: string, testFn: () => void) => {
    try {
      testFn();
      setTestResults(prev => ({ ...prev, [testName]: 'PASS' }));
    } catch (error) {
      setTestResults(prev => ({ ...prev, [testName]: `FAIL: ${error}` }));
    }
  };

  const testConnectionStatus = () => {
    if (connectionStatus !== 'connected') {
      throw new Error(`Expected 'connected', got '${connectionStatus}'`);
    }
  };

  const testSendPing = () => {
    sendMessage({ type: 'ping', timestamp: new Date().toISOString() });
  };

  const testSendCommand = () => {
    sendMessage({
      type: 'command_request',
      command: 'echo "Hello from LANS ICE test"',
      context: [],
      mode: 'assistant'
    });
  };

  const testFileOperation = () => {
    sendMessage({
      type: 'file_request',
      action: 'list',
      path: '/home/viki/LANS'
    });
  };

  return (
    <div className="p-6 bg-gray-900 text-green-400 font-mono">
      <h2 className="text-xl font-bold mb-4">🧪 LANS ICE WebSocket Tester</h2>
      
      {/* Connection Status */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Connection Status</h3>
        <div className={`inline-block px-3 py-1 rounded ${
          connectionStatus === 'connected' ? 'bg-green-800' : 
          connectionStatus === 'connecting' ? 'bg-yellow-800' : 'bg-red-800'
        }`}>
          {connectionStatus.toUpperCase()}
        </div>
        {connectionStatus !== 'connected' && (
          <button
            onClick={reconnect}
            className="ml-4 px-4 py-2 bg-blue-800 hover:bg-blue-700 rounded"
          >
            Reconnect
          </button>
        )}
      </div>

      {/* Test Controls */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Manual Tests</h3>
        <div className="space-x-4">
          <button
            onClick={() => runTest('connection', testConnectionStatus)}
            className="px-4 py-2 bg-green-800 hover:bg-green-700 rounded"
          >
            Test Connection
          </button>
          <button
            onClick={() => runTest('ping', testSendPing)}
            className="px-4 py-2 bg-blue-800 hover:bg-blue-700 rounded"
          >
            Send Ping
          </button>
          <button
            onClick={() => runTest('command', testSendCommand)}
            className="px-4 py-2 bg-purple-800 hover:bg-purple-700 rounded"
          >
            Test Command
          </button>
          <button
            onClick={() => runTest('file_ops', testFileOperation)}
            className="px-4 py-2 bg-orange-800 hover:bg-orange-700 rounded"
          >
            Test File Ops
          </button>
        </div>
      </div>

      {/* Test Results */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Test Results</h3>
        <div className="space-y-2">
          {Object.entries(testResults).map(([test, result]) => (
            <div key={test} className="flex justify-between">
              <span>{test}:</span>
              <span className={result.startsWith('PASS') ? 'text-green-400' : 'text-red-400'}>
                {result}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Live Data Streams */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Last Message */}
        <div className="bg-gray-800 p-4 rounded">
          <h4 className="font-semibold mb-2">Last Message</h4>
          <pre className="text-xs overflow-auto max-h-32">
            {lastMessage ? JSON.stringify(lastMessage, null, 2) : 'No messages yet'}
          </pre>
        </div>

        {/* Agent Thoughts */}
        <div className="bg-gray-800 p-4 rounded">
          <h4 className="font-semibold mb-2">Agent Thoughts ({agentThoughts.length})</h4>
          <div className="text-xs space-y-1 max-h-32 overflow-auto">
            {agentThoughts.slice(-5).map((thought, i) => (
              <div key={i} className="border-l-2 border-blue-500 pl-2">
                {thought.content || JSON.stringify(thought)}
              </div>
            ))}
          </div>
        </div>

        {/* File Changes */}
        <div className="bg-gray-800 p-4 rounded">
          <h4 className="font-semibold mb-2">File Changes ({fileChanges.length})</h4>
          <div className="text-xs space-y-1 max-h-32 overflow-auto">
            {fileChanges.slice(-5).map((change, i) => (
              <div key={i} className="border-l-2 border-yellow-500 pl-2">
                {change.path} - {change.change_type}
              </div>
            ))}
          </div>
        </div>

        {/* Command Outputs */}
        <div className="bg-gray-800 p-4 rounded">
          <h4 className="font-semibold mb-2">Commands ({commandOutputs.length})</h4>
          <div className="text-xs space-y-1 max-h-32 overflow-auto">
            {commandOutputs.slice(-5).map((cmd, i) => (
              <div key={i} className="border-l-2 border-green-500 pl-2">
                {cmd.command} - {cmd.type}
              </div>
            ))}
          </div>
        </div>

        {/* Memory Updates */}
        <div className="bg-gray-800 p-4 rounded">
          <h4 className="font-semibold mb-2">Memory ({memoryUpdates.length})</h4>
          <div className="text-xs space-y-1 max-h-32 overflow-auto">
            {memoryUpdates.slice(-3).map((mem, i) => (
              <div key={i} className="border-l-2 border-purple-500 pl-2">
                {mem.memory_type} - {mem.size}
              </div>
            ))}
          </div>
        </div>

        {/* Terminal Outputs */}
        <div className="bg-gray-800 p-4 rounded">
          <h4 className="font-semibold mb-2">Terminal ({terminalOutputs.length})</h4>
          <div className="text-xs space-y-1 max-h-32 overflow-auto">
            {terminalOutputs.slice(-5).map((term, i) => (
              <div key={i} className="border-l-2 border-cyan-500 pl-2">
                {term.session_id ? `${term.session_id}: ${term.data}` : JSON.stringify(term)}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
