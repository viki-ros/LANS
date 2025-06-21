"""
Overfitting Prevention Module for LANS Memory System
==================================================

This module implements comprehensive overfitting prevention mechanisms
to ensure knowledge generalization and prevent domain lock-in.
"""

import asyncio
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import json
import math


@dataclass
class OverfittingConfig:
    """Configuration for overfitting prevention mechanisms."""
    
    # Memory Storage Limits - Relaxed for LLM collaboration
    max_domain_ratio: float = 0.9  # Allow 90% from one domain for focused collaboration
    max_pattern_frequency: int = 500  # Increased for diverse content patterns
    diversity_threshold: float = 0.8  # 80% similarity allowed for related memories
    generalization_threshold: float = 0.2  # More relaxed cross-domain performance
    
    # Importance & Retention - Optimized for LLM use
    compression_factor: float = 0.9  # Less aggressive compression
    retention_threshold: float = 0.05  # Keep more memories
    forgetting_constant: int = 60  # Longer retention period
    recency_decay_constant: int = 120  # Slower decay for collaboration
    
    # Validation Requirements - Balanced for collaboration
    validation_threshold: float = 0.5  # More permissive validation
    cross_domain_bonus: float = 0.3  # Higher bonus for cross-domain knowledge
    min_related_domains: int = 1  # Reduced minimum for focused collaboration
    
    # Audit Settings - Production optimized
    audit_frequency_days: int = 14  # Bi-weekly audits
    consolidation_similarity: float = 0.95  # Only consolidate very similar memories
    stale_knowledge_days: int = 365  # Longer retention for valuable knowledge
    
    # LLM Collaboration Features
    enable_cross_agent_sharing: bool = True
    cross_agent_similarity_threshold: float = 0.7
    collaboration_memory_bonus: float = 0.4
    agent_memory_quota_per_domain: int = 200

class MemoryDiversityTracker:
    """Tracks and enforces memory diversity to prevent overfitting."""
    
    def __init__(self, config: OverfittingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Tracking dictionaries
        self.domain_distribution = defaultdict(int)
        self.pattern_frequency = defaultdict(int)
        self.solution_types = defaultdict(int)
        self.topic_clusters = defaultdict(list)
        
        # Statistics
        self.total_memories = 0
        self.rejections = defaultdict(int)
        
    async def track_memory_storage(self, memory: Dict[str, Any]) -> None:
        """Track a newly stored memory for diversity analysis."""
        
        # Track domain distribution
        domain = memory.get('metadata', {}).get('domain', 'general')
        self.domain_distribution[domain] += 1
        
        # Track patterns in content
        patterns = self._extract_patterns(memory.get('content', ''))
        for pattern in patterns:
            self.pattern_frequency[pattern] += 1
        
        # Track solution types
        solution_type = memory.get('metadata', {}).get('solution_type', 'unknown')
        self.solution_types[solution_type] += 1
        
        # Update topic clusters using embedding similarity
        if 'embedding' in memory:
            await self._update_topic_clusters(memory)
        
        self.total_memories += 1
        
    async def should_accept_memory(self, new_memory: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if a new memory should be accepted based on diversity criteria.
        
        Returns:
            Tuple of (should_accept, rejection_reason)
        """
        
        # Allow initial memories to build diversity baseline
        if self.total_memories < 20:
            return True, "Building initial memory diversity baseline"
        
        domain = new_memory.get('metadata', {}).get('domain', 'general')
        
        # Check domain over-representation (only if we have sufficient memories)
        if self.total_memories > 10:
            domain_ratio = self.domain_distribution[domain] / self.total_memories
            if domain_ratio > self.config.max_domain_ratio:
                self.rejections['domain_overrepresentation'] += 1
                return False, f"Domain '{domain}' over-represented ({domain_ratio:.2%})"
        
        # Check pattern over-frequency
        patterns = self._extract_patterns(new_memory.get('content', ''))
        for pattern in patterns:
            if self.pattern_frequency[pattern] > self.config.max_pattern_frequency:
                self.rejections['pattern_overuse'] += 1
                return False, f"Pattern '{pattern}' over-used ({self.pattern_frequency[pattern]} times)"
        
        # Check semantic diversity if embedding available
        if 'embedding' in new_memory:
            is_diverse = await self._check_semantic_diversity(new_memory)
            if not is_diverse:
                self.rejections['semantic_similarity'] += 1
                return False, "Memory too similar to existing memories"
        
        return True, "Memory accepted"
    
    def _extract_patterns(self, content: str) -> List[str]:
        """Extract common patterns from memory content."""
        patterns = []
        
        # Extract code patterns
        if 'def ' in content or 'class ' in content:
            patterns.append('python_code')
        if 'import ' in content:
            patterns.append('import_statement')
        if 'software' in content.lower() or 'development' in content.lower():
            patterns.append('software_concept')
        
        # Extract solution patterns
        if 'error' in content.lower() and 'solution' in content.lower():
            patterns.append('error_solution')
        if 'step' in content.lower() and ('1.' in content or '2.' in content):
            patterns.append('step_by_step')
        
        # Extract domain patterns
        domains = ['navigation', 'perception', 'planning', 'control', 'ai', 'ml']
        for domain in domains:
            if domain in content.lower():
                patterns.append(f'{domain}_related')
        
        return patterns
    
    async def _update_topic_clusters(self, memory: Dict[str, Any]) -> None:
        """Update topic clusters with new memory embedding."""
        embedding = memory['embedding']
        content_summary = memory.get('content', '')[:100]  # First 100 chars
        
        # Simple clustering: group by similarity
        max_similarity = 0
        best_cluster = None
        
        for cluster_id, cluster_memories in self.topic_clusters.items():
            if cluster_memories:
                # Calculate average similarity to cluster
                similarities = []
                for cluster_memory in cluster_memories[-10:]:  # Last 10 in cluster
                    if 'embedding' in cluster_memory:
                        similarity = self._cosine_similarity(embedding, cluster_memory['embedding'])
                        similarities.append(similarity)
                
                if similarities:
                    avg_similarity = np.mean(similarities)
                    if avg_similarity > max_similarity:
                        max_similarity = avg_similarity
                        best_cluster = cluster_id
        
        # Add to existing cluster or create new one
        if max_similarity > 0.8 and best_cluster is not None:
            self.topic_clusters[best_cluster].append(memory)
        else:
            # Create new cluster
            new_cluster_id = f"cluster_{len(self.topic_clusters)}"
            self.topic_clusters[new_cluster_id] = [memory]
    
    async def _check_semantic_diversity(self, new_memory: Dict[str, Any]) -> bool:
        """Check if new memory is semantically diverse enough."""
        new_embedding = new_memory['embedding']
        
        # Be more permissive during initial learning phase
        if len(self.topic_clusters) < 5:
            return True  # Allow initial diversity building
        
        # Check against recent memories (last 50, reduced for performance)
        recent_memories = list(self.topic_clusters.values())[-50:]
        
        similarities = []
        for cluster in recent_memories:
            for memory in cluster[-5:]:  # Last 5 in each cluster
                if 'embedding' in memory:
                    similarity = self._cosine_similarity(new_embedding, memory['embedding'])
                    similarities.append(similarity)
        
        if not similarities:
            return True  # No existing memories to compare
        
        # Require minimum diversity (maximum similarity below threshold)
        # diversity_threshold of 0.6 means allow up to 60% similarity
        max_similarity = max(similarities)
        return max_similarity < self.config.diversity_threshold
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_diversity_metrics(self) -> Dict[str, Any]:
        """Get current diversity metrics."""
        return {
            "total_memories": self.total_memories,
            "domain_distribution": dict(self.domain_distribution),
            "pattern_frequency": dict(self.pattern_frequency),
            "solution_types": dict(self.solution_types),
            "topic_clusters": len(self.topic_clusters),
            "rejections": dict(self.rejections),
            "domain_entropy": self._calculate_domain_entropy(),
            "pattern_diversity": self._calculate_pattern_diversity(),
        }
    
    def _calculate_domain_entropy(self) -> float:
        """Calculate entropy of domain distribution (higher = more diverse)."""
        if self.total_memories == 0:
            return 0.0
        
        probabilities = [count / self.total_memories for count in self.domain_distribution.values()]
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
        
        # Normalize by maximum possible entropy
        max_entropy = math.log2(len(self.domain_distribution)) if self.domain_distribution else 1
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _calculate_pattern_diversity(self) -> float:
        """Calculate diversity of patterns (higher = more diverse)."""
        if not self.pattern_frequency:
            return 1.0
        
        total_patterns = sum(self.pattern_frequency.values())
        if total_patterns == 0:
            return 1.0
            
        max_frequency = max(self.pattern_frequency.values())
        
        # Inverse of max frequency ratio
        return 1.0 - (max_frequency / total_patterns)


class AdaptiveImportanceScorer:
    """Adaptive importance scoring to prevent overfitting to specific patterns."""
    
    def __init__(self, config: OverfittingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.success_rates = defaultdict(lambda: 0.5)  # Default 50% success
        self.domain_performance = defaultdict(lambda: 0.5)
        self.pattern_effectiveness = defaultdict(lambda: 0.5)
        self.cross_domain_usage = defaultdict(int)
        
        # Importance score history for normalization
        self.importance_history = []
        
    async def calculate_importance(self, memory: Dict[str, Any]) -> float:
        """Calculate adaptive importance score for a memory."""
        
        base_importance = memory.get('importance_score', 0.5)
        
        # Domain performance adjustment
        domain = memory.get('metadata', {}).get('domain', 'general')
        domain_performance = self.domain_performance[domain]
        
        # Memory type success rate adjustment
        memory_type = memory.get('memory_type', 'unknown')
        success_rate = self.success_rates[memory_type]
        
        # Recency adjustment with decay
        timestamp = memory.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        days_old = (datetime.now() - timestamp).days
        recency_factor = math.exp(-days_old / self.config.recency_decay_constant)
        
        # Cross-domain usage bonus
        memory_id = memory.get('id', '')
        cross_domain_count = self.cross_domain_usage[memory_id]
        cross_domain_bonus = min(cross_domain_count * self.config.cross_domain_bonus, 0.3)
        
        # Pattern novelty bonus
        patterns = memory.get('metadata', {}).get('patterns', [])
        novelty_bonus = self._calculate_novelty_bonus(patterns)
        
        # Final importance calculation
        adjusted_importance = (
            base_importance * 
            domain_performance * 
            success_rate * 
            recency_factor + 
            cross_domain_bonus + 
            novelty_bonus
        )
        
        # Apply compression if score is inflated
        if adjusted_importance > 0.8:
            adjusted_importance *= self.config.compression_factor
        
        # Cap at 1.0 and store in history
        final_importance = min(adjusted_importance, 1.0)
        self.importance_history.append(final_importance)
        
        # Keep only recent history
        if len(self.importance_history) > 1000:
            self.importance_history = self.importance_history[-1000:]
        
        return final_importance
    
    def _calculate_novelty_bonus(self, patterns: List[str]) -> float:
        """Calculate bonus for novel patterns."""
        if not patterns:
            return 0.0
        
        total_bonus = 0.0
        for pattern in patterns:
            effectiveness = self.pattern_effectiveness[pattern]
            # Bonus for less common but effective patterns
            if effectiveness > 0.6:  # Pattern is effective
                frequency_penalty = min(effectiveness, 0.2)  # But limit bonus
                total_bonus += (0.2 - frequency_penalty)
        
        return min(total_bonus, 0.2)  # Cap total novelty bonus
    
    async def update_performance_metrics(self, memory_id: str, success: bool, 
                                       domain: str, cross_domain_used: bool) -> None:
        """Update performance metrics based on memory usage outcomes."""
        
        # Update success rates
        memory_type = "general"  # Would be extracted from memory
        current_rate = self.success_rates[memory_type]
        # Exponential moving average
        self.success_rates[memory_type] = 0.9 * current_rate + 0.1 * (1.0 if success else 0.0)
        
        # Update domain performance
        current_domain_perf = self.domain_performance[domain]
        self.domain_performance[domain] = 0.9 * current_domain_perf + 0.1 * (1.0 if success else 0.0)
        
        # Track cross-domain usage
        if cross_domain_used:
            self.cross_domain_usage[memory_id] += 1
    
    async def normalize_importance_scores(self, memory_manager) -> Dict[str, int]:
        """Normalize importance scores across all memories to prevent inflation."""
        
        if len(self.importance_history) < 10:
            return {"normalized": 0}
        
        # Calculate percentiles
        percentile_95 = np.percentile(self.importance_history, 95)
        percentile_50 = np.percentile(self.importance_history, 50)
        
        # If top scores are too high, compress them
        if percentile_95 > 0.9:
            compression_needed = True
            self.logger.info(f"Applying importance score compression (95th percentile: {percentile_95:.3f})")
            
            # Would update database here
            # UPDATE memories SET importance_score = importance_score * compression_factor 
            # WHERE importance_score > percentile_95
            
            return {"normalized": 1, "compression_factor": self.config.compression_factor}
        
        return {"normalized": 0}


class KnowledgeValidationFramework:
    """Framework for validating knowledge across domains to ensure generalization."""
    
    def __init__(self, config: OverfittingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Validation test suites
        self.domain_tests = {
            'software': self._create_software_tests(),
            'ai': self._create_ai_tests(),
            'general': self._create_general_tests(),
            'programming': self._create_programming_tests(),
        }
        
        # Cross-domain relationships
        self.domain_relationships = {
            'software': ['programming', 'ai', 'general'],
            'ai': ['programming', 'software', 'general'],
            'programming': ['software', 'ai', 'general'],
            'general': ['software', 'ai', 'programming'],
        }
    
    async def validate_memory_before_storage(self, memory: Dict[str, Any]) -> Tuple[bool, Dict[str, float]]:
        """
        Validate memory across domains before storage.
        
        Returns:
            Tuple of (should_store, validation_scores)
        """
        
        original_domain = memory.get('metadata', {}).get('domain', 'general')
        validation_scores = {}
        
        # Test in original domain
        original_score = await self._test_in_domain(memory, original_domain)
        validation_scores[original_domain] = original_score
        
        # Test in related domains
        related_domains = self.domain_relationships.get(original_domain, [])
        for domain in related_domains[:self.config.min_related_domains]:
            domain_score = await self._test_in_domain(memory, domain)
            validation_scores[domain] = domain_score
        
        # Calculate generalization score
        if len(validation_scores) > 1:
            scores = list(validation_scores.values())
            min_score = min(scores)
            max_score = max(scores)
            generalization_score = min_score / max_score if max_score > 0 else 0.0
        else:
            generalization_score = validation_scores.get(original_domain, 0.0)
        
        # Accept if meets validation threshold
        should_store = generalization_score >= self.config.validation_threshold
        validation_scores['generalization'] = generalization_score
        
        if not should_store:
            self.logger.info(f"Memory rejected: generalization score {generalization_score:.3f} below threshold {self.config.validation_threshold}")
        
        return should_store, validation_scores
    
    async def _test_in_domain(self, memory: Dict[str, Any], domain: str) -> float:
        """Test how well memory knowledge applies in a specific domain."""
        
        content = memory.get('content', '').lower()
        memory_type = memory.get('memory_type', 'general')
        
        # Get domain-specific tests
        domain_tests = self.domain_tests.get(domain, [])
        if not domain_tests:
            return 0.5  # Default score for unknown domain
        
        scores = []
        for test in domain_tests:
            score = await self._apply_test(content, test, memory_type)
            weight = test.get('weight', 1.0)
            scores.append(score * weight)
        
        # Return weighted average, ensuring minimum score of 0.3 for basic applicability
        avg_score = np.mean(scores) if scores else 0.5
        return max(avg_score, 0.3)
    
    async def _apply_test(self, content: str, test: Dict[str, Any], memory_type: str) -> float:
        """Apply a specific test to memory content."""
        
        test_type = test.get('type', 'keyword')
        content_lower = content.lower()
        
        if test_type == 'keyword':
            # Test for presence of relevant keywords
            keywords = test.get('keywords', [])
            if not keywords:
                return 0.5
            matches = sum(1 for keyword in keywords if keyword.lower() in content_lower)
            return min(matches / len(keywords), 1.0)
        
        elif test_type == 'pattern':
            # Test for specific patterns
            patterns = test.get('patterns', [])
            if not patterns:
                return 0.5
            matches = sum(1 for pattern in patterns if pattern.lower() in content.lower())
            return min(matches / len(patterns), 1.0)
        
        elif test_type == 'concept':
            # Test for conceptual understanding (simplified)
            concepts = test.get('concepts', [])
            if not concepts:
                return 0.5
            matches = sum(1 for concept in concepts if concept.lower() in content_lower)
            return min(matches / len(concepts), 1.0)
        
        return 0.5  # Default score
    
    def _create_software_tests(self) -> List[Dict[str, Any]]:
        """Create test suite for software development domain."""
        return [
            {
                'type': 'keyword',
                'keywords': ['api', 'database', 'service', 'authentication', 'deployment', 'testing'],
                'weight': 1.0
            },
            {
                'type': 'pattern',
                'patterns': ['import ', 'class ', 'def ', 'async '],
                'weight': 0.8
            },
            {
                'type': 'concept',
                'concepts': ['architecture', 'framework', 'configuration', 'validation'],
                'weight': 0.6
            }
        ]
    
    def _create_ai_tests(self) -> List[Dict[str, Any]]:
        """Create test suite for AI domain."""
        return [
            {
                'type': 'keyword',
                'keywords': ['model', 'training', 'prediction', 'algorithm', 'neural', 'learning'],
                'weight': 1.0
            },
            {
                'type': 'pattern',
                'patterns': ['train()', 'predict()', 'model.', 'accuracy'],
                'weight': 0.8
            },
            {
                'type': 'concept',
                'concepts': ['optimization', 'generalization', 'overfitting', 'validation'],
                'weight': 0.9
            }
        ]
    
    def _create_programming_tests(self) -> List[Dict[str, Any]]:
        """Create test suite for programming domain."""
        return [
            {
                'type': 'keyword',
                'keywords': ['function', 'class', 'variable', 'loop', 'condition', 'error'],
                'weight': 1.0
            },
            {
                'type': 'pattern',
                'patterns': ['def ', 'class ', 'if ', 'for ', 'while ', 'try:'],
                'weight': 0.9
            },
            {
                'type': 'concept',
                'concepts': ['abstraction', 'encapsulation', 'debugging', 'testing'],
                'weight': 0.7
            }
        ]
    
    def _create_general_tests(self) -> List[Dict[str, Any]]:
        """Create test suite for general domain."""
        return [
            {
                'type': 'keyword',
                'keywords': ['problem', 'solution', 'process', 'step', 'result', 'method'],
                'weight': 1.0
            },
            {
                'type': 'concept',
                'concepts': ['analysis', 'synthesis', 'evaluation', 'application'],
                'weight': 0.8
            }
        ]


class OverfittingPreventionManager:
    """Main manager coordinating all overfitting prevention mechanisms."""
    
    def __init__(self, config: OverfittingConfig = None):
        self.config = config or OverfittingConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.diversity_tracker = MemoryDiversityTracker(self.config)
        self.importance_scorer = AdaptiveImportanceScorer(self.config)
        self.validation_framework = KnowledgeValidationFramework(self.config)
        
        # Audit tracking
        self.last_audit = datetime.now()
        self.audit_results = []
    
    async def process_memory_storage(self, memory: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Process memory storage with overfitting prevention.
        
        Returns:
            Tuple of (should_store, processing_results)
        """
        
        processing_results = {
            'diversity_check': None,
            'validation_scores': None,
            'adjusted_importance': None,
            'final_decision': None
        }
        
        # 1. Check diversity constraints
        should_accept, rejection_reason = await self.diversity_tracker.should_accept_memory(memory)
        processing_results['diversity_check'] = {
            'accepted': should_accept,
            'reason': rejection_reason
        }
        
        if not should_accept:
            processing_results['final_decision'] = 'rejected_diversity'
            return False, processing_results
        
        # 2. Validate across domains
        should_validate, validation_scores = await self.validation_framework.validate_memory_before_storage(memory)
        processing_results['validation_scores'] = validation_scores
        
        if not should_validate:
            processing_results['final_decision'] = 'rejected_validation'
            return False, processing_results
        
        # 3. Calculate adaptive importance
        adjusted_importance = await self.importance_scorer.calculate_importance(memory)
        memory['importance_score'] = adjusted_importance
        processing_results['adjusted_importance'] = adjusted_importance
        
        # 4. Track successful storage
        await self.diversity_tracker.track_memory_storage(memory)
        
        processing_results['final_decision'] = 'accepted'
        return True, processing_results
    
    async def should_perform_audit(self) -> bool:
        """Check if it's time to perform a knowledge audit."""
        time_since_audit = datetime.now() - self.last_audit
        return time_since_audit.days >= self.config.audit_frequency_days
    
    async def perform_knowledge_audit(self, memory_manager) -> Dict[str, Any]:
        """Perform comprehensive knowledge audit."""
        
        self.logger.info("Starting knowledge audit for overfitting prevention")
        
        audit_results = {
            'timestamp': datetime.now(),
            'diversity_metrics': None,
            'importance_normalization': None,
            'stale_knowledge_cleanup': None,
            'consolidation_results': None,
        }
        
        # 1. Get diversity metrics
        diversity_metrics = self.diversity_tracker.get_diversity_metrics()
        audit_results['diversity_metrics'] = diversity_metrics
        
        # 2. Normalize importance scores if needed
        normalization_results = await self.importance_scorer.normalize_importance_scores(memory_manager)
        audit_results['importance_normalization'] = normalization_results
        
        # 3. Clean up stale knowledge
        stale_cleanup = await self._cleanup_stale_knowledge(memory_manager)
        audit_results['stale_knowledge_cleanup'] = stale_cleanup
        
        # 4. Consolidate similar memories
        consolidation = await self._consolidate_similar_memories(memory_manager)
        audit_results['consolidation_results'] = consolidation
        
        # Store audit results
        self.audit_results.append(audit_results)
        self.last_audit = datetime.now()
        
        # Keep only recent audit history
        if len(self.audit_results) > 10:
            self.audit_results = self.audit_results[-10:]
        
        self.logger.info(f"Knowledge audit completed: {audit_results}")
        return audit_results
    
    async def _cleanup_stale_knowledge(self, memory_manager) -> Dict[str, int]:
        """Clean up stale knowledge that may be causing overfitting."""
        
        stale_threshold = datetime.now() - timedelta(days=self.config.stale_knowledge_days)
        
        # Would implement database queries here
        # For now, return mock results
        return {
            'memories_checked': 1000,
            'stale_memories_found': 50,
            'memories_removed': 30,
            'memories_downgraded': 20
        }
    
    async def _consolidate_similar_memories(self, memory_manager) -> Dict[str, int]:
        """Consolidate similar memories to reduce redundancy."""
        
        # Would implement memory consolidation logic here
        # For now, return mock results
        return {
            'similarity_groups_found': 25,
            'memories_consolidated': 75,
            'abstract_memories_created': 25,
            'storage_space_saved_mb': 12.5
        }
    
    def get_overfitting_risk_score(self) -> float:
        """Calculate overall overfitting risk score (0-1, lower is better)."""
        
        diversity_metrics = self.diversity_tracker.get_diversity_metrics()
        
        # Risk factors (higher values = higher risk)
        domain_entropy = diversity_metrics.get('domain_entropy', 0.5)
        pattern_diversity = diversity_metrics.get('pattern_diversity', 0.5)
        
        # Calculate risk (inverse of good metrics)
        risk_factors = [
            1 - domain_entropy,  # Low entropy = high risk
            1 - pattern_diversity,  # Low diversity = high risk
        ]
        
        # Add audit-based risk factors if available
        if self.audit_results:
            latest_audit = self.audit_results[-1]
            stale_ratio = latest_audit.get('stale_knowledge_cleanup', {}).get('stale_memories_found', 0) / 1000
            risk_factors.append(stale_ratio)
        
        return np.mean(risk_factors)
    
    def get_prevention_status(self) -> Dict[str, Any]:
        """Get comprehensive status of overfitting prevention system."""
        
        return {
            'config': {
                'max_domain_ratio': self.config.max_domain_ratio,
                'diversity_threshold': self.config.diversity_threshold,
                'validation_threshold': self.config.validation_threshold,
            },
            'diversity_metrics': self.diversity_tracker.get_diversity_metrics(),
            'overfitting_risk_score': self.get_overfitting_risk_score(),
            'last_audit': self.last_audit.isoformat(),
            'audit_history_count': len(self.audit_results),
            'system_status': 'active'
        }


# Example usage and integration
async def demo_overfitting_prevention():
    """Demonstrate overfitting prevention system."""
    
    print("🛡️ LANS Overfitting Prevention System Demo")
    print("=" * 50)
    
    # Initialize system
    config = OverfittingConfig()
    prevention_manager = OverfittingPreventionManager(config)
    
    # Simulate storing memories
    test_memories = [
        {
            'id': 'mem_1',
            'content': 'ROS2 node creation using rclcpp with publisher setup',
            'memory_type': 'procedural',
            'metadata': {'domain': 'ros2', 'solution_type': 'code_example'},
            'importance_score': 0.8,
            'timestamp': datetime.now(),
            'embedding': np.random.random(384).tolist()  # Mock embedding
        },
        {
            'id': 'mem_2', 
            'content': 'Machine learning model training with validation split',
            'memory_type': 'procedural',
            'metadata': {'domain': 'ai', 'solution_type': 'methodology'},
            'importance_score': 0.7,
            'timestamp': datetime.now(),
            'embedding': np.random.random(384).tolist()
        },
        {
            'id': 'mem_3',
            'content': 'Another ROS2 node example with subscriber callback',
            'memory_type': 'procedural', 
            'metadata': {'domain': 'ros2', 'solution_type': 'code_example'},
            'importance_score': 0.9,
            'timestamp': datetime.now(),
            'embedding': np.random.random(384).tolist()
        }
    ]
    
    # Process each memory
    for i, memory in enumerate(test_memories):
        print(f"\n🧠 Processing Memory {i+1}: {memory['content'][:50]}...")
        
        should_store, results = await prevention_manager.process_memory_storage(memory)
        
        print(f"   Decision: {'✅ ACCEPT' if should_store else '❌ REJECT'}")
        print(f"   Diversity: {results['diversity_check']['reason']}")
        if results['validation_scores']:
            gen_score = results['validation_scores'].get('generalization', 0)
            print(f"   Generalization: {gen_score:.3f}")
        if results['adjusted_importance']:
            print(f"   Adjusted Importance: {results['adjusted_importance']:.3f}")
    
    # Show system status
    print(f"\n📊 System Status:")
    status = prevention_manager.get_prevention_status()
    print(f"   Overfitting Risk Score: {status['overfitting_risk_score']:.3f}")
    print(f"   Domain Entropy: {status['diversity_metrics']['domain_entropy']:.3f}")
    print(f"   Pattern Diversity: {status['diversity_metrics']['pattern_diversity']:.3f}")
    
    print("\n🎯 Overfitting Prevention Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_overfitting_prevention())
