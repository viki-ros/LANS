"""
Memory Introspection for LANS ICE

Provides insights into agent memory usage, working memory state,
and context buffer contents for the System Monitor view.
"""

import asyncio
import logging
import psutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import gc

logger = logging.getLogger(__name__)


class MemoryIntrospector:
    """Provides memory introspection capabilities for LANS agents"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss
        self.memory_history: List[Dict[str, Any]] = []
        self.max_history_length = 100
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        try:
            memory_info = self.process.memory_info()
            
            return {
                "rss": memory_info.rss,  # Resident Set Size
                "vms": memory_info.vms,  # Virtual Memory Size
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "percent": self.process.memory_percent(),
                "baseline_mb": round(self.baseline_memory / 1024 / 1024, 2),
                "growth_mb": round((memory_info.rss - self.baseline_memory) / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"error": str(e)}
    
    async def get_memory_state(self) -> Dict[str, Any]:
        """Get comprehensive memory state information"""
        try:
            # Basic memory usage
            usage = await self.get_memory_usage()
            
            # Python garbage collection stats
            gc_stats = self._get_gc_stats()
            
            # Object counts
            object_counts = self._get_object_counts()
            
            # Memory components (simulated for now)
            components = await self._get_memory_components()
            
            state = {
                "usage": usage,
                "gc_stats": gc_stats,
                "object_counts": object_counts,
                "components": components,
                "timestamp": self._get_timestamp()
            }
            
            # Add to history
            self._add_to_history(state)
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting memory state: {e}")
            return {"error": str(e)}
    
    def _get_gc_stats(self) -> Dict[str, Any]:
        """Get Python garbage collection statistics"""
        try:
            stats = gc.get_stats()
            return {
                "collections": [
                    {
                        "generation": i,
                        "collections": stat["collections"],
                        "collected": stat["collected"],
                        "uncollectable": stat["uncollectable"]
                    }
                    for i, stat in enumerate(stats)
                ],
                "total_objects": len(gc.get_objects()),
                "garbage_objects": len(gc.garbage)
            }
        except Exception as e:
            logger.error(f"Error getting GC stats: {e}")
            return {"error": str(e)}
    
    def _get_object_counts(self) -> Dict[str, int]:
        """Get counts of different object types"""
        try:
            objects = gc.get_objects()
            type_counts: Dict[str, int] = {}
            
            for obj in objects:
                obj_type = type(obj).__name__
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            # Return top 10 most common types
            sorted_counts = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_counts[:10])
            
        except Exception as e:
            logger.error(f"Error getting object counts: {e}")
            return {"error": str(e)}
    
    async def _get_memory_components(self) -> Dict[str, Any]:
        """Get simulated memory component breakdown"""
        try:
            # This would ideally interface with actual LANS memory components
            # For now, provide a realistic simulation
            
            total_mb = (await self.get_memory_usage()).get("rss_mb", 0)
            
            return {
                "working_memory": {
                    "size_mb": round(total_mb * 0.3, 2),
                    "description": "Current task execution context",
                    "components": [
                        "active_command",
                        "execution_state",
                        "temporary_variables"
                    ]
                },
                "context_buffer": {
                    "size_mb": round(total_mb * 0.2, 2),
                    "description": "Attached files and context",
                    "components": [
                        "file_contents",
                        "url_content",
                        "conversation_history"
                    ]
                },
                "knowledge_base": {
                    "size_mb": round(total_mb * 0.15, 2),
                    "description": "Long-term knowledge and patterns",
                    "components": [
                        "code_patterns",
                        "best_practices",
                        "project_history"
                    ]
                },
                "system_overhead": {
                    "size_mb": round(total_mb * 0.35, 2),
                    "description": "Framework and system memory",
                    "components": [
                        "python_runtime",
                        "libraries",
                        "websocket_connections"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting memory components: {e}")
            return {"error": str(e)}
    
    def _add_to_history(self, state: Dict[str, Any]):
        """Add memory state to history"""
        self.memory_history.append(state)
        
        # Keep only recent history
        if len(self.memory_history) > self.max_history_length:
            self.memory_history = self.memory_history[-self.max_history_length:]
    
    def get_memory_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get memory usage history"""
        if limit is None:
            return self.memory_history.copy()
        else:
            return self.memory_history[-limit:] if limit > 0 else []
    
    async def get_memory_trends(self) -> Dict[str, Any]:
        """Get memory usage trends and analysis"""
        try:
            if len(self.memory_history) < 2:
                return {"error": "Insufficient history for trend analysis"}
            
            # Extract memory usage over time
            usage_history = [
                state["usage"]["rss_mb"] 
                for state in self.memory_history 
                if "usage" in state and "rss_mb" in state["usage"]
            ]
            
            if len(usage_history) < 2:
                return {"error": "Insufficient memory data for trends"}
            
            # Calculate trends
            current = usage_history[-1]
            previous = usage_history[-2]
            avg_usage = sum(usage_history) / len(usage_history)
            min_usage = min(usage_history)
            max_usage = max(usage_history)
            
            # Calculate growth rate (MB per sample)
            recent_samples = usage_history[-10:] if len(usage_history) >= 10 else usage_history
            if len(recent_samples) >= 2:
                growth_rate = (recent_samples[-1] - recent_samples[0]) / len(recent_samples)
            else:
                growth_rate = 0
            
            return {
                "current_mb": current,
                "change_mb": current - previous,
                "average_mb": round(avg_usage, 2),
                "min_mb": min_usage,
                "max_mb": max_usage,
                "growth_rate_per_sample": round(growth_rate, 3),
                "samples_count": len(usage_history),
                "trend": "increasing" if growth_rate > 0.1 else "decreasing" if growth_rate < -0.1 else "stable"
            }
            
        except Exception as e:
            logger.error(f"Error calculating memory trends: {e}")
            return {"error": str(e)}
    
    async def detect_memory_leaks(self) -> Dict[str, Any]:
        """Simple memory leak detection"""
        try:
            trends = await self.get_memory_trends()
            
            if "error" in trends:
                return trends
            
            # Simple heuristics for leak detection
            warnings = []
            
            if trends["growth_rate_per_sample"] > 1.0:  # Growing by more than 1MB per sample
                warnings.append("High memory growth rate detected")
            
            if trends["current_mb"] > trends["average_mb"] * 1.5:
                warnings.append("Current usage significantly above average")
            
            if len(self.memory_history) >= 20:
                # Check if memory has been consistently growing
                recent_usage = [
                    state["usage"]["rss_mb"] 
                    for state in self.memory_history[-20:] 
                    if "usage" in state and "rss_mb" in state["usage"]
                ]
                
                if len(recent_usage) >= 10:
                    first_half_avg = sum(recent_usage[:10]) / 10
                    second_half_avg = sum(recent_usage[10:]) / len(recent_usage[10:])
                    
                    if second_half_avg > first_half_avg * 1.2:
                        warnings.append("Consistent memory growth over recent samples")
            
            return {
                "leak_probability": len(warnings) / 3.0,  # Score from 0 to 1
                "warnings": warnings,
                "recommendation": self._get_memory_recommendation(len(warnings), trends)
            }
            
        except Exception as e:
            logger.error(f"Error detecting memory leaks: {e}")
            return {"error": str(e)}
    
    def _get_memory_recommendation(self, warning_count: int, trends: Dict[str, Any]) -> str:
        """Get memory optimization recommendations"""
        if warning_count == 0:
            return "Memory usage appears normal"
        elif warning_count == 1:
            return "Monitor memory usage closely"
        elif warning_count == 2:
            return "Consider restarting the agent to clear memory"
        else:
            return "High memory usage detected - immediate restart recommended"
    
    async def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return results"""
        try:
            before_usage = await self.get_memory_usage()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Wait a moment for memory to be freed
            await asyncio.sleep(0.1)
            
            after_usage = await self.get_memory_usage()
            
            return {
                "objects_collected": collected,
                "memory_before_mb": before_usage.get("rss_mb", 0),
                "memory_after_mb": after_usage.get("rss_mb", 0),
                "memory_freed_mb": round(
                    before_usage.get("rss_mb", 0) - after_usage.get("rss_mb", 0), 2
                )
            }
            
        except Exception as e:
            logger.error(f"Error forcing garbage collection: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
