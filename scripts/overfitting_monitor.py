#!/usr/bin/env python3
"""
LANS Overfitting Prevention Monitoring Dashboard
==============================================

Real-time monitoring and alerting for overfitting prevention system.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverfittingMonitor:
    """Real-time monitoring dashboard for overfitting prevention."""
    
    def __init__(self, prevention_manager):
        self.prevention_manager = prevention_manager
        self.alert_thresholds = {
            'high_risk': 0.7,
            'medium_risk': 0.4,
            'low_diversity': 0.3,
            'high_rejection_rate': 0.4
        }
        self.monitoring_history = []
    
    async def get_realtime_status(self) -> Dict[str, Any]:
        """Get comprehensive real-time overfitting status."""
        
        status = self.prevention_manager.get_prevention_status()
        diversity_metrics = status['diversity_metrics']
        
        # Calculate additional metrics
        rejection_count = sum(diversity_metrics['rejections'].values())
        total_processed = diversity_metrics['total_memories'] + rejection_count
        rejection_rate = rejection_count / max(total_processed, 1)
        
        # Determine risk level
        risk_score = status['overfitting_risk_score']
        if risk_score > self.alert_thresholds['high_risk']:
            risk_level = "🔴 HIGH"
        elif risk_score > self.alert_thresholds['medium_risk']:
            risk_level = "🟡 MEDIUM"
        else:
            risk_level = "🟢 LOW"
        
        realtime_status = {
            'timestamp': datetime.now().isoformat(),
            'risk_level': risk_level,
            'risk_score': risk_score,
            'domain_entropy': diversity_metrics['domain_entropy'],
            'pattern_diversity': diversity_metrics['pattern_diversity'],
            'rejection_rate': rejection_rate,
            'total_memories': diversity_metrics['total_memories'],
            'domain_distribution': diversity_metrics['domain_distribution'],
            'rejection_breakdown': diversity_metrics['rejections'],
            'alerts': await self._check_alerts(status)
        }
        
        # Store in monitoring history
        self.monitoring_history.append(realtime_status)
        if len(self.monitoring_history) > 100:  # Keep last 100 records
            self.monitoring_history = self.monitoring_history[-100:]
        
        return realtime_status
    
    async def _check_alerts(self, status: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check for alert conditions."""
        alerts = []
        
        risk_score = status['overfitting_risk_score']
        diversity_metrics = status['diversity_metrics']
        
        # High overfitting risk
        if risk_score > self.alert_thresholds['high_risk']:
            alerts.append({
                'level': 'CRITICAL',
                'message': f"High overfitting risk detected: {risk_score:.3f}",
                'action': 'Review memory storage patterns and adjust thresholds'
            })
        
        # Low domain diversity
        domain_entropy = diversity_metrics['domain_entropy']
        if domain_entropy < self.alert_thresholds['low_diversity']:
            alerts.append({
                'level': 'WARNING',
                'message': f"Low domain diversity: {domain_entropy:.3f}",
                'action': 'Encourage knowledge storage across more domains'
            })
        
        # High rejection rate
        rejection_count = sum(diversity_metrics['rejections'].values())
        total_processed = diversity_metrics['total_memories'] + rejection_count
        rejection_rate = rejection_count / max(total_processed, 1)
        
        if rejection_rate > self.alert_thresholds['high_rejection_rate']:
            alerts.append({
                'level': 'WARNING',
                'message': f"High memory rejection rate: {rejection_rate:.1%}",
                'action': 'Review overfitting prevention thresholds'
            })
        
        # Domain over-concentration
        domain_dist = diversity_metrics['domain_distribution']
        total_memories = sum(domain_dist.values())
        for domain, count in domain_dist.items():
            ratio = count / max(total_memories, 1)
            if ratio > 0.5:  # 50% threshold for alerts
                alerts.append({
                    'level': 'WARNING',
                    'message': f"Domain '{domain}' over-concentrated: {ratio:.1%}",
                    'action': f'Reduce focus on {domain} domain memories'
                })
        
        return alerts
    
    def print_dashboard(self, status: Dict[str, Any]) -> None:
        """Print formatted monitoring dashboard."""
        
        print("\n" + "="*80)
        print("🛡️  LANS OVERFITTING PREVENTION MONITORING DASHBOARD")
        print("="*80)
        print(f"📅 Timestamp: {status['timestamp']}")
        print(f"⚠️  Risk Level: {status['risk_level']}")
        print(f"📊 Risk Score: {status['risk_score']:.3f}")
        print(f"🌐 Domain Entropy: {status['domain_entropy']:.3f}")
        print(f"🔄 Pattern Diversity: {status['pattern_diversity']:.3f}")
        print(f"❌ Rejection Rate: {status['rejection_rate']:.1%}")
        print(f"💾 Total Memories: {status['total_memories']}")
        
        # Domain distribution
        print(f"\n📋 DOMAIN DISTRIBUTION:")
        for domain, count in status['domain_distribution'].items():
            percentage = (count / max(status['total_memories'], 1)) * 100
            bar_length = int(percentage / 5)  # Scale for display
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"   {domain:15} {bar} {percentage:5.1f}% ({count})")
        
        # Rejection breakdown
        print(f"\n🚫 REJECTION BREAKDOWN:")
        total_rejections = sum(status['rejection_breakdown'].values())
        if total_rejections > 0:
            for reason, count in status['rejection_breakdown'].items():
                percentage = (count / total_rejections) * 100
                print(f"   {reason:25} {count:3d} ({percentage:4.1f}%)")
        else:
            print("   No rejections recorded")
        
        # Alerts
        if status['alerts']:
            print(f"\n🚨 ACTIVE ALERTS:")
            for alert in status['alerts']:
                level_emoji = "🔴" if alert['level'] == 'CRITICAL' else "🟡"
                print(f"   {level_emoji} {alert['level']}: {alert['message']}")
                print(f"      Action: {alert['action']}")
        else:
            print(f"\n✅ NO ACTIVE ALERTS - System operating normally")
        
        print("="*80)
    
    async def continuous_monitoring(self, interval_seconds: int = 30) -> None:
        """Run continuous monitoring with specified interval."""
        
        print("🚀 Starting continuous overfitting prevention monitoring...")
        print(f"📊 Monitoring interval: {interval_seconds} seconds")
        
        try:
            while True:
                status = await self.get_realtime_status()
                self.print_dashboard(status)
                
                # Check for critical alerts
                critical_alerts = [a for a in status['alerts'] if a['level'] == 'CRITICAL']
                if critical_alerts:
                    logger.critical(f"CRITICAL OVERFITTING ALERTS: {len(critical_alerts)} detected")
                
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        
        if not self.monitoring_history:
            return {"error": "No monitoring data available"}
        
        # Calculate trends
        recent_data = self.monitoring_history[-10:]  # Last 10 records
        
        risk_scores = [d['risk_score'] for d in recent_data]
        domain_entropies = [d['domain_entropy'] for d in recent_data]
        rejection_rates = [d['rejection_rate'] for d in recent_data]
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'monitoring_period': {
                'start': self.monitoring_history[0]['timestamp'],
                'end': self.monitoring_history[-1]['timestamp'],
                'data_points': len(self.monitoring_history)
            },
            'trends': {
                'risk_score': {
                    'current': risk_scores[-1],
                    'average': sum(risk_scores) / len(risk_scores),
                    'trend': 'increasing' if risk_scores[-1] > risk_scores[0] else 'decreasing'
                },
                'domain_entropy': {
                    'current': domain_entropies[-1],
                    'average': sum(domain_entropies) / len(domain_entropies),
                    'trend': 'increasing' if domain_entropies[-1] > domain_entropies[0] else 'decreasing'
                },
                'rejection_rate': {
                    'current': rejection_rates[-1],
                    'average': sum(rejection_rates) / len(rejection_rates),
                    'trend': 'increasing' if rejection_rates[-1] > rejection_rates[0] else 'decreasing'
                }
            },
            'alert_summary': self._analyze_alert_history(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _analyze_alert_history(self) -> Dict[str, Any]:
        """Analyze alert patterns from monitoring history."""
        
        alert_counts = {'CRITICAL': 0, 'WARNING': 0}
        alert_types = {}
        
        for record in self.monitoring_history:
            for alert in record.get('alerts', []):
                level = alert['level']
                alert_counts[level] += 1
                
                # Count alert types
                message = alert['message']
                if 'overfitting risk' in message:
                    alert_types['overfitting_risk'] = alert_types.get('overfitting_risk', 0) + 1
                elif 'domain diversity' in message:
                    alert_types['domain_diversity'] = alert_types.get('domain_diversity', 0) + 1
                elif 'rejection rate' in message:
                    alert_types['rejection_rate'] = alert_types.get('rejection_rate', 0) + 1
                elif 'over-concentrated' in message:
                    alert_types['domain_concentration'] = alert_types.get('domain_concentration', 0) + 1
        
        return {
            'total_alerts': sum(alert_counts.values()),
            'by_level': alert_counts,
            'by_type': alert_types
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on monitoring data."""
        
        recommendations = []
        
        if not self.monitoring_history:
            return ["Insufficient monitoring data for recommendations"]
        
        latest = self.monitoring_history[-1]
        
        # Risk-based recommendations
        if latest['risk_score'] > 0.7:
            recommendations.append("URGENT: Implement immediate overfitting mitigation measures")
            recommendations.append("Review and tighten memory acceptance thresholds")
        elif latest['risk_score'] > 0.4:
            recommendations.append("Consider adjusting domain diversity requirements")
        
        # Domain diversity recommendations
        if latest['domain_entropy'] < 0.3:
            recommendations.append("Encourage knowledge storage across more diverse domains")
            recommendations.append("Review domain classification for stored memories")
        
        # Rejection rate recommendations
        if latest['rejection_rate'] > 0.4:
            recommendations.append("High rejection rate detected - review prevention thresholds")
            recommendations.append("Consider gradual relaxation of diversity requirements")
        elif latest['rejection_rate'] < 0.1:
            recommendations.append("Low rejection rate - consider tightening prevention criteria")
        
        # Domain concentration recommendations
        domain_dist = latest['domain_distribution']
        total_memories = sum(domain_dist.values())
        for domain, count in domain_dist.items():
            ratio = count / max(total_memories, 1)
            if ratio > 0.5:
                recommendations.append(f"High concentration in '{domain}' domain - diversify knowledge sources")
        
        if not recommendations:
            recommendations.append("System performing optimally - continue current monitoring")
        
        return recommendations


async def demo_monitoring_dashboard():
    """Demonstrate the overfitting prevention monitoring dashboard."""
    
    # Import the overfitting prevention system
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from global_mcp_server.core.overfitting_prevention import OverfittingPreventionManager, OverfittingConfig
    
    print("🚀 Initializing LANS Overfitting Prevention Monitoring...")
    
    # Initialize prevention manager
    config = OverfittingConfig()
    prevention_manager = OverfittingPreventionManager(config)
    
    # Initialize monitor
    monitor = OverfittingMonitor(prevention_manager)
    
    # Simulate some memory processing to generate data
    print("📝 Simulating memory processing for monitoring demo...")
    
    import numpy as np
    from datetime import datetime
    
    test_memories = [
        {
            'id': f'mem_{i}',
            'content': f'Test memory content {i} about {"ROS2" if i % 2 == 0 else "AI"}',
            'memory_type': 'procedural',
            'metadata': {'domain': 'ros2' if i % 2 == 0 else 'ai', 'solution_type': 'example'},
            'importance_score': 0.5 + (i * 0.1),
            'timestamp': datetime.now(),
            'embedding': np.random.random(384).tolist()
        }
        for i in range(10)
    ]
    
    # Process memories to generate monitoring data
    for memory in test_memories:
        await prevention_manager.process_memory_storage(memory)
    
    # Show monitoring dashboard
    print("\n" + "="*80)
    print("📊 OVERFITTING PREVENTION MONITORING DASHBOARD DEMO")
    print("="*80)
    
    # Get and display current status
    status = await monitor.get_realtime_status()
    monitor.print_dashboard(status)
    
    # Generate and display report
    print("\n📋 MONITORING REPORT:")
    print("-" * 80)
    
    # Add a few more monitoring data points for trend analysis
    for i in range(3):
        await asyncio.sleep(0.1)  # Small delay
        await monitor.get_realtime_status()
    
    report = monitor.generate_report()
    
    print(f"📈 Monitoring Period: {report['monitoring_period']['data_points']} data points")
    print(f"📊 Current Risk Score: {report['trends']['risk_score']['current']:.3f}")
    print(f"📊 Average Risk Score: {report['trends']['risk_score']['average']:.3f}")
    print(f"📊 Risk Trend: {report['trends']['risk_score']['trend']}")
    
    print(f"\n🚨 Alert Summary:")
    alert_summary = report['alert_summary']
    print(f"   Total Alerts: {alert_summary['total_alerts']}")
    print(f"   Critical: {alert_summary['by_level']['CRITICAL']}")
    print(f"   Warnings: {alert_summary['by_level']['WARNING']}")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print("\n✅ Monitoring dashboard demo complete!")
    print("💡 Use 'monitor.continuous_monitoring()' for real-time monitoring")


if __name__ == "__main__":
    asyncio.run(demo_monitoring_dashboard())
