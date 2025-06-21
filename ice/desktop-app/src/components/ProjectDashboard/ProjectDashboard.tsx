import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Folder, 
  Target, 
  Brain, 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  Zap
} from 'lucide-react';

import { ProjectInfo, AgentStatus } from '../../types';

interface ProjectDashboardProps {
  websocket: WebSocket | null;
  connectionStatus?: string;
  sendMessage?: (message: any) => void;
}

function ProjectDashboard({ }: ProjectDashboardProps) {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({ status: 'idle' });

  // Fetch initial data
  useEffect(() => {
    fetchProjects();
    fetchSystemStatus();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await fetch('http://localhost:8765/projects');
      const data = await response.json();
      setProjects(data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8765/health');
      const data = await response.json();
      // Update agent status based on health data
      setAgentStatus({
        status: data.status === 'healthy' ? 'idle' : 'error',
        memory_usage: '15.2MB',
        uptime: '2h 34m'
      });
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'thinking':
      case 'executing':
        return 'text-primary-600 dark:text-primary-400';
      case 'idle':
        return 'text-success-600 dark:text-success-400';
      case 'error':
        return 'text-error-600 dark:text-error-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'thinking':
        return <Brain className="w-4 h-4 animate-pulse" />;
      case 'executing':
        return <Zap className="w-4 h-4 animate-bounce" />;
      case 'idle':
        return <CheckCircle className="w-4 h-4" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="h-full p-6 overflow-y-auto bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Mission Control
          </h1>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </div>

        {/* Top Row - Projects and Current Mission */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Active Projects */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex items-center space-x-2 mb-4">
              <Folder className="w-5 h-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Active Projects
              </h2>
            </div>
            
            <div className="space-y-3">
              {projects.map((project) => (
                <div 
                  key={project.id}
                  className={`p-3 rounded-lg border-2 transition-colors cursor-pointer ${
                    project.active 
                      ? 'border-primary-200 bg-primary-50 dark:border-primary-800 dark:bg-primary-900/20' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                  onClick={() => {/* TODO: Handle project selection */}}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-gray-900 dark:text-white">
                          {project.name}
                        </span>
                        {project.active && (
                          <div className="status-active" />
                        )}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {project.path}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Current Mission */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center space-x-2 mb-4">
              <Target className="w-5 h-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Current Mission
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Implementing OAuth2 Integration
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    <span className="text-gray-600 dark:text-gray-300">Research OAuth2 libraries</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-success-500" />
                    <span className="text-gray-600 dark:text-gray-300">Design auth flow</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-primary-500 rounded-full animate-spin border-t-transparent" />
                    <span className="text-gray-900 dark:text-white font-medium">Implement token validation</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Middle Row - Agent Status and Project Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Agent Status */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="flex items-center space-x-2 mb-4">
              <Brain className="w-5 h-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Agent Status
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Status:</span>
                <div className={`flex items-center space-x-2 ${getStatusColor(agentStatus.status)}`}>
                  {getStatusIcon(agentStatus.status)}
                  <span className="font-medium capitalize">{agentStatus.status}</span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Memory:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {agentStatus.memory_usage || '0MB'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Uptime:</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {agentStatus.uptime || '0m'}
                </span>
              </div>
              
              {agentStatus.current_task && (
                <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
                  <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Current Task:</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {agentStatus.current_task}
                  </div>
                </div>
              )}
            </div>
          </motion.div>

          {/* Project Health */}
          <motion.div 
            className="card p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <div className="flex items-center space-x-2 mb-4">
              <Activity className="w-5 h-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Project Health
              </h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Tests:</span>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-success-500" />
                  <span className="font-medium text-gray-900 dark:text-white">
                    85% (17/20)
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Build:</span>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-success-500" />
                  <span className="font-medium text-success-600 dark:text-success-400">
                    Passing
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Coverage:</span>
                <span className="font-medium text-gray-900 dark:text-white">92%</span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Linting:</span>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-success-500" />
                  <span className="font-medium text-success-600 dark:text-success-400">
                    Clean
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Dependencies:</span>
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-warning-500" />
                  <span className="font-medium text-warning-600 dark:text-warning-400">
                    3 updates available
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Recent Activity */}
        <motion.div 
          className="card p-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center space-x-2 mb-4">
            <Clock className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Activity
            </h2>
          </div>
          
          <div className="space-y-3">
            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center space-x-3 p-3">
                <CheckCircle className="w-4 h-4 text-success-500" />
                <span>14:32 ✓ Implemented user authentication endpoint</span>
              </div>
              <div className="flex items-center space-x-3 p-3">
                <CheckCircle className="w-4 h-4 text-success-500" />
                <span>14:28 📝 Updated API documentation</span>
              </div>
              <div className="flex items-center space-x-3 p-3">
                <CheckCircle className="w-4 h-4 text-success-500" />
                <span>14:25 🔧 Fixed CORS configuration issue</span>
              </div>
              <div className="flex items-center space-x-3 p-3">
                <CheckCircle className="w-4 h-4 text-success-500" />
                <span>14:20 📦 Added express-rate-limit dependency</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

export default ProjectDashboard;
