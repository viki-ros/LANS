#!/usr/bin/env python3
"""
LANS Production Monitoring Dashboard
Real-time monitoring and alerting for production LANS deployment
"""

import asyncio
import json
import time
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import signal
import sys

class LANSMonitor:
    """Production monitoring for LANS system"""
    
    def __init__(self, health_endpoint="http://localhost:8080"):
        self.health_endpoint = health_endpoint
        self.metrics_history = []
        self.alerts = []
        self.start_time = time.time()
        self.running = True
        
        # Thresholds
        self.thresholds = {
            'cpu_warning': 70,
            'cpu_critical': 85,
            'memory_warning': 70, 
            'memory_critical': 85,
            'disk_warning': 80,
            'disk_critical': 90,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0
        }
    
    def signal_handler(self, signum, frame):
        """Handle shutdown gracefully"""
        print(f"\n🔄 Received signal {signum}, shutting down monitoring...")
        self.running = False
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics for Docker containers
            docker_processes = []
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    if 'docker' in proc.info['name'].lower() or 'postgres' in proc.info['name'].lower():
                        docker_processes.append(proc.info)
            except:
                pass
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'processes': docker_processes
            }
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    async def check_lans_health(self) -> Dict[str, Any]:
        """Check LANS health endpoint"""
        try:
            start_time = time.time()
            
            # Basic health check
            response = requests.get(f"{self.health_endpoint}/health", timeout=5)
            basic_response_time = time.time() - start_time
            
            basic_health = response.json() if response.status_code == 200 else None
            
            # Detailed health check
            start_time = time.time()
            detailed_response = requests.get(f"{self.health_endpoint}/health/detailed", timeout=10)
            detailed_response_time = time.time() - start_time
            
            detailed_health = detailed_response.json() if detailed_response.status_code == 200 else None
            
            return {
                'timestamp': datetime.now().isoformat(),
                'basic_health': basic_health,
                'detailed_health': detailed_health,
                'response_times': {
                    'basic': basic_response_time,
                    'detailed': detailed_response_time
                },
                'status_codes': {
                    'basic': response.status_code,
                    'detailed': detailed_response.status_code
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'status': 'unreachable'
            }
    
    def check_alerts(self, metrics: Dict[str, Any], health: Dict[str, Any]):
        """Check for alert conditions"""
        current_time = datetime.now()
        new_alerts = []
        
        # System resource alerts
        if 'cpu' in metrics and metrics['cpu']['percent'] > self.thresholds['cpu_critical']:
            new_alerts.append({
                'level': 'CRITICAL',
                'type': 'CPU',
                'message': f"CPU usage critical: {metrics['cpu']['percent']:.1f}%",
                'timestamp': current_time.isoformat(),
                'value': metrics['cpu']['percent']
            })
        elif 'cpu' in metrics and metrics['cpu']['percent'] > self.thresholds['cpu_warning']:
            new_alerts.append({
                'level': 'WARNING', 
                'type': 'CPU',
                'message': f"CPU usage high: {metrics['cpu']['percent']:.1f}%",
                'timestamp': current_time.isoformat(),
                'value': metrics['cpu']['percent']
            })
        
        # Memory alerts
        if 'memory' in metrics and metrics['memory']['percent'] > self.thresholds['memory_critical']:
            new_alerts.append({
                'level': 'CRITICAL',
                'type': 'MEMORY',
                'message': f"Memory usage critical: {metrics['memory']['percent']:.1f}%",
                'timestamp': current_time.isoformat(),
                'value': metrics['memory']['percent']
            })
        elif 'memory' in metrics and metrics['memory']['percent'] > self.thresholds['memory_warning']:
            new_alerts.append({
                'level': 'WARNING',
                'type': 'MEMORY', 
                'message': f"Memory usage high: {metrics['memory']['percent']:.1f}%",
                'timestamp': current_time.isoformat(),
                'value': metrics['memory']['percent']
            })
        
        # Health check alerts
        if 'error' in health:
            new_alerts.append({
                'level': 'CRITICAL',
                'type': 'HEALTH',
                'message': f"Health check failed: {health['error']}",
                'timestamp': current_time.isoformat()
            })
        elif 'detailed_health' in health and health['detailed_health']:
            if health['detailed_health'].get('overall_status') == 'unhealthy':
                new_alerts.append({
                    'level': 'CRITICAL',
                    'type': 'HEALTH',
                    'message': "LANS health check reports unhealthy status",
                    'timestamp': current_time.isoformat()
                })
        
        # Response time alerts
        if 'response_times' in health:
            basic_time = health['response_times'].get('basic', 0)
            if basic_time > self.thresholds['response_time_critical']:
                new_alerts.append({
                    'level': 'CRITICAL',
                    'type': 'PERFORMANCE',
                    'message': f"Health check response time critical: {basic_time:.2f}s",
                    'timestamp': current_time.isoformat(),
                    'value': basic_time
                })
        
        # Add new alerts
        self.alerts.extend(new_alerts)
        
        # Keep only recent alerts (last 24 hours)
        cutoff_time = current_time - timedelta(hours=24)
        self.alerts = [alert for alert in self.alerts 
                      if datetime.fromisoformat(alert['timestamp']) > cutoff_time]
        
        return new_alerts
    
    def print_dashboard(self, metrics: Dict[str, Any], health: Dict[str, Any]):
        """Print monitoring dashboard"""
        os.system('clear')  # Clear screen
        
        print("🧠 LANS Production Monitoring Dashboard")
        print("=" * 50)
        print(f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⚡ Uptime: {(time.time() - self.start_time)/3600:.2f} hours")
        print()
        
        # System Metrics
        print("📊 System Metrics:")
        if 'cpu' in metrics:
            cpu_status = "🔴" if metrics['cpu']['percent'] > 85 else "🟡" if metrics['cpu']['percent'] > 70 else "🟢"
            print(f"  {cpu_status} CPU: {metrics['cpu']['percent']:.1f}% ({metrics['cpu']['count']} cores)")
        
        if 'memory' in metrics:
            mem_status = "🔴" if metrics['memory']['percent'] > 85 else "🟡" if metrics['memory']['percent'] > 70 else "🟢"
            mem_gb = metrics['memory']['used'] / (1024**3)
            mem_total_gb = metrics['memory']['total'] / (1024**3)
            print(f"  {mem_status} Memory: {metrics['memory']['percent']:.1f}% ({mem_gb:.1f}GB / {mem_total_gb:.1f}GB)")
        
        if 'disk' in metrics:
            disk_status = "🔴" if metrics['disk']['percent'] > 90 else "🟡" if metrics['disk']['percent'] > 80 else "🟢"
            disk_gb = metrics['disk']['used'] / (1024**3)
            disk_total_gb = metrics['disk']['total'] / (1024**3)
            print(f"  {disk_status} Disk: {metrics['disk']['percent']:.1f}% ({disk_gb:.1f}GB / {disk_total_gb:.1f}GB)")
        
        print()
        
        # LANS Health
        print("🏥 LANS Health:")
        if 'error' in health:
            print(f"  🔴 Status: UNREACHABLE - {health['error']}")
        elif 'detailed_health' in health and health['detailed_health']:
            status = health['detailed_health'].get('overall_status', 'unknown')
            status_icon = "🟢" if status == "healthy" else "🟡" if status == "warning" else "🔴"
            print(f"  {status_icon} Overall Status: {status.upper()}")
            
            if 'response_times' in health:
                basic_time = health['response_times']['basic']
                detailed_time = health['response_times']['detailed']
                print(f"  ⚡ Response Times: Basic {basic_time:.2f}s, Detailed {detailed_time:.2f}s")
            
            # Individual component health
            if 'checks' in health['detailed_health']:
                print("  🔧 Components:")
                for component, result in health['detailed_health']['checks'].items():
                    comp_status = result.get('status', 'unknown')
                    comp_icon = "🟢" if comp_status == "healthy" else "🟡" if comp_status == "warning" else "🔴"
                    print(f"    {comp_icon} {component}: {comp_status}")
        
        print()
        
        # Recent Alerts
        print("🚨 Recent Alerts:")
        recent_alerts = [alert for alert in self.alerts[-5:]]  # Last 5 alerts
        if recent_alerts:
            for alert in recent_alerts:
                level_icon = "🔴" if alert['level'] == 'CRITICAL' else "🟡"
                time_str = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
                print(f"  {level_icon} [{time_str}] {alert['level']}: {alert['message']}")
        else:
            print("  🟢 No recent alerts")
        
        print()
        print("Press Ctrl+C to stop monitoring...")
    
    async def run_monitoring(self, interval: int = 30):
        """Run monitoring loop"""
        print("🚀 Starting LANS production monitoring...")
        print(f"📡 Health endpoint: {self.health_endpoint}")
        print(f"⏱️  Update interval: {interval} seconds")
        
        while self.running:
            try:
                # Collect metrics
                metrics = await self.get_system_metrics()
                health = await self.check_lans_health()
                
                # Store metrics history
                self.metrics_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics,
                    'health': health
                })
                
                # Keep only recent history (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    entry for entry in self.metrics_history
                    if datetime.fromisoformat(entry['timestamp']) > cutoff_time
                ]
                
                # Check for alerts
                new_alerts = self.check_alerts(metrics, health)
                
                # Print alerts immediately
                for alert in new_alerts:
                    level_icon = "🔴" if alert['level'] == 'CRITICAL' else "🟡"
                    print(f"\n{level_icon} ALERT: {alert['message']}")
                
                # Update dashboard
                self.print_dashboard(metrics, health)
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(interval)
        
        print("\n🔄 Monitoring stopped.")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LANS Production Monitor')
    parser.add_argument('--health-endpoint', default='http://localhost:8080',
                       help='Health check endpoint URL')
    parser.add_argument('--interval', type=int, default=30,
                       help='Update interval in seconds')
    
    args = parser.parse_args()
    
    monitor = LANSMonitor(args.health_endpoint)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, monitor.signal_handler)
    signal.signal(signal.SIGTERM, monitor.signal_handler)
    
    try:
        asyncio.run(monitor.run_monitoring(args.interval))
    except KeyboardInterrupt:
        print("\n🔄 Monitoring stopped by user.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
