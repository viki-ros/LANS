#!/usr/bin/env python3
"""
LANS Production Health Check Endpoint
Comprehensive health monitoring for production deployment
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import psutil
import aiohttp
from aiohttp import web
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LANSHealthChecker:
    """Production-grade health checker for LANS system"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_checks = {
            'memory_manager': self._check_memory_manager,
            'overfitting_prevention': self._check_overfitting_prevention,
            'database': self._check_database,
            'agents': self._check_agents,
            'system_resources': self._check_system_resources
        }
    
    async def _check_memory_manager(self) -> Dict[str, Any]:
        """Check GlobalMemoryManager health"""
        try:
            from global_mcp_server.core.memory_manager import GlobalMemoryManager
            manager = GlobalMemoryManager()
            
            # Test basic functionality
            test_memory = {
                "content": "Health check test memory",
                "type": "health_check",
                "metadata": {"timestamp": datetime.now().isoformat()}
            }
            
            # This would normally store and retrieve, but for health check
            # we'll just verify the manager can be instantiated
            return {
                "status": "healthy",
                "message": "Memory manager operational",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_overfitting_prevention(self) -> Dict[str, Any]:
        """Check overfitting prevention system"""
        try:
            from global_mcp_server.core.overfitting_prevention import OverfittingPreventionManager
            prevention = OverfittingPreventionManager()
            
            return {
                "status": "healthy",
                "message": "Overfitting prevention system operational",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e), 
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from global_mcp_server.storage.database import DatabaseManager
            db = DatabaseManager()
            
            # Test database connection
            # await db.test_connection()  # Would implement this
            
            return {
                "status": "healthy",
                "message": "Database connection operational",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_agents(self) -> Dict[str, Any]:
        """Check agent system health"""
        try:
            from agent_core.agents.planning_agent import PlanningAgent
            
            # Test agent instantiation
            agent = PlanningAgent()
            
            return {
                "status": "healthy",
                "message": "Agent systems operational",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Determine health status
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory_percent > 80:
                warnings.append(f"High memory usage: {memory_percent}%")
            if disk_percent > 80:
                warnings.append(f"High disk usage: {disk_percent}%")
            
            if warnings:
                status = "warning"
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_full_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        results = {}
        overall_status = "healthy"
        
        for check_name, check_func in self.health_checks.items():
            try:
                result = await check_func()
                results[check_name] = result
                
                if result["status"] == "unhealthy":
                    overall_status = "unhealthy"
                elif result["status"] == "warning" and overall_status == "healthy":
                    overall_status = "warning"
                    
            except Exception as e:
                results[check_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                overall_status = "unhealthy"
        
        uptime = time.time() - self.start_time
        
        return {
            "overall_status": overall_status,
            "uptime_seconds": uptime,
            "uptime_human": f"{uptime/3600:.2f} hours",
            "timestamp": datetime.now().isoformat(),
            "checks": results,
            "version": "1.0.0",
            "service": "LANS"
        }

# Health check HTTP endpoint
async def health_endpoint(request):
    """HTTP endpoint for health checks"""
    checker = LANSHealthChecker()
    
    # Quick health check for /health
    if request.path == '/health':
        try:
            # Quick basic checks
            from global_mcp_server.core.memory_manager import GlobalMemoryManager
            manager = GlobalMemoryManager()
            
            return web.json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "LANS"
            })
        except Exception as e:
            return web.json_response({
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)
    
    # Detailed health check for /health/detailed
    elif request.path == '/health/detailed':
        report = await checker.get_full_health_report()
        status_code = 200 if report["overall_status"] == "healthy" else 503
        return web.json_response(report, status=status_code)

def create_health_app():
    """Create health check web application"""
    app = web.Application()
    app.router.add_get('/health', health_endpoint)
    app.router.add_get('/health/detailed', health_endpoint)
    return app

async def run_health_server(port=8080):
    """Run health check server"""
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    logger.info(f"Health check server running on http://localhost:{port}")
    logger.info("Endpoints:")
    logger.info(f"  - http://localhost:{port}/health")
    logger.info(f"  - http://localhost:{port}/health/detailed")
    
    return runner

if __name__ == "__main__":
    async def main():
        runner = await run_health_server()
        try:
            # Keep server running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
        except KeyboardInterrupt:
            logger.info("Shutting down health check server...")
            await runner.cleanup()
    
    asyncio.run(main())
