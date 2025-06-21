import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  websocket?: WebSocket | null;
  className?: string;
}

interface FileContent {
  path: string;
  content: string;
  language: string;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ 
  websocket, 
  className = '' 
}) => {
  const [files, setFiles] = useState<FileContent[]>([]);
  const [activeFile, setActiveFile] = useState<FileContent | null>(null);
  const [fileList, setFileList] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load file list on component mount
  useEffect(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      loadFileList();
    }
  }, [websocket]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!websocket) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'file_list':
            setFileList(message.files || []);
            break;

          case 'file_content':
            const newFile: FileContent = {
              path: message.path,
              content: message.content,
              language: getLanguageFromPath(message.path)
            };
            
            setFiles(prev => {
              const existingIndex = prev.findIndex(f => f.path === message.path);
              if (existingIndex >= 0) {
                const updated = [...prev];
                updated[existingIndex] = newFile;
                return updated;
              } else {
                return [...prev, newFile];
              }
            });
            
            setActiveFile(newFile);
            setIsLoading(false);
            break;

          case 'file_changed':
            // Reload file if it's currently open
            if (activeFile && activeFile.path === message.path) {
              loadFile(message.path);
            }
            // Update file list
            loadFileList();
            break;

          case 'file_saved':
            console.log('File saved:', message.path);
            break;

          case 'error':
            console.error('File operation error:', message.message);
            setIsLoading(false);
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    websocket.addEventListener('message', handleMessage);

    return () => {
      websocket.removeEventListener('message', handleMessage);
    };
  }, [websocket, activeFile]);

  const loadFileList = () => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'list_files',
        path: '/home/viki/LANS'  // Default to LANS directory
      }));
    }
  };

  const loadFile = (path: string) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      setIsLoading(true);
      websocket.send(JSON.stringify({
        type: 'read_file',
        path: path
      }));
    }
  };

  const saveFile = (path: string, content: string) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'write_file',
        path: path,
        content: content
      }));
    }
  };

  const handleFileSelect = (path: string) => {
    const existingFile = files.find(f => f.path === path);
    if (existingFile) {
      setActiveFile(existingFile);
    } else {
      loadFile(path);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    if (activeFile && value !== undefined) {
      const updatedFile = { ...activeFile, content: value };
      setActiveFile(updatedFile);
      
      // Update files array
      setFiles(prev => {
        const index = prev.findIndex(f => f.path === activeFile.path);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = updatedFile;
          return updated;
        }
        return prev;
      });
    }
  };

  const handleSave = () => {
    if (activeFile) {
      saveFile(activeFile.path, activeFile.content);
    }
  };

  const getLanguageFromPath = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py': return 'python';
      case 'ts': return 'typescript';
      case 'tsx': return 'typescript';
      case 'js': return 'javascript';
      case 'jsx': return 'javascript';
      case 'json': return 'json';
      case 'md': return 'markdown';
      case 'yml':
      case 'yaml': return 'yaml';
      case 'toml': return 'toml';
      case 'txt': return 'plaintext';
      case 'sh': return 'shell';
      case 'css': return 'css';
      case 'html': return 'html';
      default: return 'plaintext';
    }
  };

  return (
    <div className={`code-editor-container ${className}`}>
      <div className="flex h-full">
        {/* File Explorer */}
        <div className="w-64 bg-gray-900 text-white border-r border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="font-medium text-sm">Files</h3>
            <button 
              onClick={loadFileList}
              className="mt-2 px-3 py-1 bg-blue-600 text-xs rounded hover:bg-blue-700"
            >
              Refresh
            </button>
          </div>
          <div className="overflow-y-auto h-full">
            {fileList.map((file, index) => (
              <div
                key={index}
                onClick={() => handleFileSelect(file)}
                className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-800 ${
                  activeFile?.path === file ? 'bg-gray-800 border-r-2 border-blue-500' : ''
                }`}
              >
                <div className="truncate" title={file}>
                  {file.split('/').pop()}
                </div>
                <div className="text-xs text-gray-400 truncate">
                  {file}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 flex flex-col">
          {activeFile && (
            <div className="bg-gray-800 text-white px-4 py-2 border-b border-gray-700 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">
                  {activeFile.path.split('/').pop()}
                </span>
                <span className="text-xs text-gray-400">
                  {activeFile.path}
                </span>
              </div>
              <button
                onClick={handleSave}
                className="px-3 py-1 bg-green-600 text-xs rounded hover:bg-green-700"
              >
                Save
              </button>
            </div>
          )}
          
          <div className="flex-1">
            {isLoading ? (
              <div className="flex items-center justify-center h-full bg-gray-900 text-white">
                <div className="text-center">
                  <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p>Loading file...</p>
                </div>
              </div>
            ) : activeFile ? (
              <Editor
                height="100%"
                defaultLanguage={activeFile.language}
                language={activeFile.language}
                value={activeFile.content}
                onChange={handleEditorChange}
                theme="vs-dark"
                options={{
                  minimap: { enabled: true },
                  fontSize: 14,
                  wordWrap: 'on',
                  automaticLayout: true,
                  scrollBeyondLastLine: false,
                  renderWhitespace: 'boundary',
                  rulers: [80, 120],
                  bracketPairColorization: { enabled: true },
                  smoothScrolling: true,
                  cursorBlinking: 'smooth',
                  contextmenu: true,
                  multiCursorModifier: 'ctrlCmd',
                  formatOnPaste: true,
                  formatOnType: true
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full bg-gray-900 text-white">
                <div className="text-center">
                  <p className="text-gray-400 mb-4">No file selected</p>
                  <p className="text-sm text-gray-500">
                    Select a file from the explorer to start editing
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
