"""
Load Balancer for EconCell AI Model Distribution

Intelligently distributes tasks across available models based on capabilities,
current load, performance metrics, and resource utilization.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict, deque

from .model_orchestrator import ModelOrchestrator, ModelPriority, ModelStatus
from .task_queue import TaskType, TaskPriority

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RESOURCE_AWARE = "resource_aware"
    PERFORMANCE_BASED = "performance_based"
    INTELLIGENT = "intelligent"  # AI-driven load balancing


@dataclass
class ModelMetrics:
    """Performance metrics for a model"""
    model_name: str
    current_load: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_rate: float = 0.0
    throughput_per_minute: float = 0.0
    resource_efficiency: float = 1.0
    health_score: float = 1.0
    last_request_time: float = field(default_factory=time.time)
    
    def update_response_time(self, response_time: float):
        """Update response time metrics"""
        self.response_times.append(response_time)
        if self.response_times:
            self.average_response_time = statistics.mean(self.response_times)
    
    def calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests
    
    def calculate_throughput(self, time_window: float = 300) -> float:
        """Calculate throughput in requests per minute"""
        current_time = time.time()
        if current_time - self.last_request_time > time_window:
            return 0.0
        
        # This is a simplified calculation - in practice you'd track timestamps
        time_minutes = time_window / 60
        return self.successful_requests / time_minutes if time_minutes > 0 else 0.0


@dataclass
class LoadBalancingDecision:
    """Result of load balancing decision"""
    selected_model: str
    confidence: float
    reasoning: str
    alternative_models: List[str] = field(default_factory=list)
    estimated_wait_time: float = 0.0
    estimated_processing_time: float = 0.0


class LoadBalancer:
    """
    Intelligent load balancer for distributing AI tasks across models
    
    Features:
    - Multiple load balancing strategies
    - Real-time performance monitoring
    - Adaptive model selection
    - Resource-aware distribution
    - Predictive load balancing
    """
    
    def __init__(self, 
                 orchestrator: ModelOrchestrator,
                 strategy: LoadBalancingStrategy = LoadBalancingStrategy.INTELLIGENT):
        """
        Initialize the load balancer
        
        Args:
            orchestrator: Model orchestrator instance
            strategy: Load balancing strategy to use
        """
        self.orchestrator = orchestrator
        self.strategy = strategy
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.round_robin_index = 0
        
        # Task-model affinity tracking
        self.task_model_performance: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        
        # Load balancing weights for weighted strategies
        self.model_weights: Dict[str, float] = {}
        
        # Performance tracking
        self._performance_lock = asyncio.Lock()
        self._metrics_update_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.config = {
            "response_time_weight": 0.3,
            "error_rate_weight": 0.25,
            "load_weight": 0.2,
            "health_weight": 0.15,
            "resource_weight": 0.1,
            "min_requests_for_stats": 5,
            "performance_window": 300,  # 5 minutes
            "adaptive_weight_adjustment": True
        }
        
        logger.info(f"LoadBalancer initialized with strategy: {strategy.value}")
    
    async def start(self):
        """Start the load balancer background tasks"""
        logger.info("Starting LoadBalancer")
        self._metrics_update_task = asyncio.create_task(self._update_metrics_periodically())
        await self._initialize_model_metrics()
    
    async def stop(self):
        """Stop the load balancer"""
        logger.info("Stopping LoadBalancer")
        if self._metrics_update_task:
            self._metrics_update_task.cancel()
            try:
                await self._metrics_update_task
            except asyncio.CancelledError:
                pass
    
    async def select_model(self, 
                          task_type: TaskType,
                          priority: TaskPriority = TaskPriority.NORMAL,
                          preferred_model: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> Optional[LoadBalancingDecision]:
        """
        Select the best model for a given task
        
        Args:
            task_type: Type of task to be processed
            priority: Task priority level
            preferred_model: Preferred model if specified
            context: Additional context for decision making
            
        Returns:
            LoadBalancingDecision with selected model and reasoning
        """
        # Get available models
        model_status = await self.orchestrator.get_model_status()
        if isinstance(model_status, dict):
            model_status = [model_status]
        
        available_models = [
            model for model in model_status 
            if model["status"] == ModelStatus.READY.value and 
               model["current_requests"] < self._get_model_capacity(model["name"])
        ]
        
        if not available_models:
            logger.warning("No available models for task selection")
            return None
        
        # If preferred model is available and suitable, use it
        if preferred_model:
            preferred_available = next(
                (model for model in available_models if model["name"] == preferred_model), 
                None
            )
            if preferred_available and self._is_model_suitable(preferred_model, task_type):
                return LoadBalancingDecision(
                    selected_model=preferred_model,
                    confidence=0.9,
                    reasoning="Preferred model specified and available",
                    estimated_wait_time=0.0,
                    estimated_processing_time=self._estimate_processing_time(preferred_model, task_type)
                )
        
        # Apply load balancing strategy
        if self.strategy == LoadBalancingStrategy.INTELLIGENT:
            return await self._intelligent_selection(available_models, task_type, priority, context)
        elif self.strategy == LoadBalancingStrategy.PERFORMANCE_BASED:
            return await self._performance_based_selection(available_models, task_type, priority)
        elif self.strategy == LoadBalancingStrategy.RESOURCE_AWARE:
            return await self._resource_aware_selection(available_models, task_type, priority)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_selection(available_models, task_type)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return await self._weighted_round_robin_selection(available_models, task_type)
        else:  # ROUND_ROBIN
            return await self._round_robin_selection(available_models, task_type)
    
    async def record_task_completion(self, 
                                   model_name: str, 
                                   task_type: TaskType,
                                   response_time: float,
                                   success: bool):
        """
        Record task completion metrics
        
        Args:
            model_name: Name of the model that processed the task
            task_type: Type of task that was processed
            response_time: Time taken to process the task
            success: Whether the task completed successfully
        """
        async with self._performance_lock:
            if model_name not in self.model_metrics:
                self.model_metrics[model_name] = ModelMetrics(model_name=model_name)
            
            metrics = self.model_metrics[model_name]
            metrics.total_requests += 1
            metrics.current_load = max(0, metrics.current_load - 1)
            
            if success:
                metrics.successful_requests += 1
                metrics.update_response_time(response_time)
            else:
                metrics.failed_requests += 1
            
            metrics.error_rate = metrics.calculate_error_rate()
            metrics.throughput_per_minute = metrics.calculate_throughput()
            metrics.last_request_time = time.time()
            
            # Update task-model performance tracking
            task_model_key = (task_type.value, model_name)
            self.task_model_performance[task_model_key].append(response_time if success else float('inf'))
            
            # Keep only recent performance data
            if len(self.task_model_performance[task_model_key]) > 50:
                self.task_model_performance[task_model_key] = \
                    self.task_model_performance[task_model_key][-50:]
    
    async def record_task_assignment(self, model_name: str):
        """Record that a task has been assigned to a model"""
        async with self._performance_lock:
            if model_name not in self.model_metrics:
                self.model_metrics[model_name] = ModelMetrics(model_name=model_name)
            
            self.model_metrics[model_name].current_load += 1
    
    async def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Get comprehensive load balancing statistics"""
        async with self._performance_lock:
            stats = {
                "strategy": self.strategy.value,
                "total_models": len(self.model_metrics),
                "model_metrics": {},
                "task_model_performance": {},
                "system_load": await self._calculate_system_load()
            }
            
            # Model-specific metrics
            for model_name, metrics in self.model_metrics.items():
                stats["model_metrics"][model_name] = {
                    "current_load": metrics.current_load,
                    "total_requests": metrics.total_requests,
                    "success_rate": (metrics.successful_requests / metrics.total_requests 
                                   if metrics.total_requests > 0 else 0.0),
                    "error_rate": metrics.error_rate,
                    "average_response_time": metrics.average_response_time,
                    "throughput_per_minute": metrics.throughput_per_minute,
                    "health_score": metrics.health_score,
                    "resource_efficiency": metrics.resource_efficiency
                }
            
            # Task-model performance
            for (task_type, model_name), times in self.task_model_performance.items():
                if len(times) >= self.config["min_requests_for_stats"]:
                    valid_times = [t for t in times if t != float('inf')]
                    if valid_times:
                        stats["task_model_performance"][f"{task_type}_{model_name}"] = {
                            "average_time": statistics.mean(valid_times),
                            "median_time": statistics.median(valid_times),
                            "min_time": min(valid_times),
                            "max_time": max(valid_times),
                            "sample_size": len(valid_times),
                            "success_rate": len(valid_times) / len(times)
                        }
            
            return stats
    
    async def _intelligent_selection(self, 
                                   available_models: List[Dict[str, Any]], 
                                   task_type: TaskType,
                                   priority: TaskPriority,
                                   context: Optional[Dict[str, Any]]) -> LoadBalancingDecision:
        """
        Intelligent model selection using multiple factors
        """
        model_scores = []
        
        for model_info in available_models:
            model_name = model_info["name"]
            
            if not self._is_model_suitable(model_name, task_type):
                continue
            
            score = await self._calculate_model_score(model_name, task_type, priority, context)
            model_scores.append((model_name, score, self._get_score_reasoning(model_name, score)))
        
        if not model_scores:
            return None
        
        # Sort by score (highest first)
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        selected_model, best_score, reasoning = model_scores[0]
        alternatives = [model for model, _, _ in model_scores[1:3]]  # Top 2 alternatives
        
        return LoadBalancingDecision(
            selected_model=selected_model,
            confidence=min(1.0, best_score),
            reasoning=reasoning,
            alternative_models=alternatives,
            estimated_wait_time=self._estimate_wait_time(selected_model),
            estimated_processing_time=self._estimate_processing_time(selected_model, task_type)
        )
    
    async def _performance_based_selection(self, 
                                         available_models: List[Dict[str, Any]], 
                                         task_type: TaskType,
                                         priority: TaskPriority) -> LoadBalancingDecision:
        """
        Select model based on historical performance for similar tasks
        """
        best_model = None
        best_performance = float('inf')
        
        for model_info in available_models:
            model_name = model_info["name"]
            
            if not self._is_model_suitable(model_name, task_type):
                continue
            
            # Get historical performance for this task type
            task_model_key = (task_type.value, model_name)
            if task_model_key in self.task_model_performance:
                times = self.task_model_performance[task_model_key]
                valid_times = [t for t in times if t != float('inf')]
                
                if len(valid_times) >= self.config["min_requests_for_stats"]:
                    avg_time = statistics.mean(valid_times)
                    if avg_time < best_performance:
                        best_performance = avg_time
                        best_model = model_name
        
        # If no historical data, fall back to least connections
        if not best_model:
            return await self._least_connections_selection(available_models, task_type)
        
        return LoadBalancingDecision(
            selected_model=best_model,
            confidence=0.8,
            reasoning=f"Best historical performance for {task_type.value} ({best_performance:.2f}s avg)",
            estimated_processing_time=best_performance
        )
    
    async def _resource_aware_selection(self, 
                                      available_models: List[Dict[str, Any]], 
                                      task_type: TaskType,
                                      priority: TaskPriority) -> LoadBalancingDecision:
        """
        Select model based on current resource utilization
        """
        best_model = None
        best_efficiency = 0.0
        
        for model_info in available_models:
            model_name = model_info["name"]
            
            if not self._is_model_suitable(model_name, task_type):
                continue
            
            # Calculate resource efficiency score
            current_load = model_info["current_requests"]
            max_capacity = self._get_model_capacity(model_name)
            load_ratio = current_load / max_capacity if max_capacity > 0 else 1.0
            
            # Prefer models with lower load but consider their capabilities
            efficiency = (1.0 - load_ratio) * self._get_model_capability_score(model_name, task_type)
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_model = model_name
        
        if not best_model:
            best_model = available_models[0]["name"]
            best_efficiency = 0.5
        
        return LoadBalancingDecision(
            selected_model=best_model,
            confidence=min(1.0, best_efficiency),
            reasoning=f"Best resource efficiency score: {best_efficiency:.2f}",
            estimated_wait_time=self._estimate_wait_time(best_model)
        )
    
    async def _least_connections_selection(self, 
                                         available_models: List[Dict[str, Any]], 
                                         task_type: TaskType) -> LoadBalancingDecision:
        """
        Select model with least current connections
        """
        suitable_models = [
            model for model in available_models 
            if self._is_model_suitable(model["name"], task_type)
        ]
        
        if not suitable_models:
            return None
        
        # Sort by current load (ascending)
        suitable_models.sort(key=lambda x: x["current_requests"])
        
        selected_model = suitable_models[0]["name"]
        current_load = suitable_models[0]["current_requests"]
        
        return LoadBalancingDecision(
            selected_model=selected_model,
            confidence=0.7,
            reasoning=f"Least connections: {current_load} current requests",
            estimated_wait_time=current_load * 30  # Rough estimate
        )
    
    async def _weighted_round_robin_selection(self, 
                                            available_models: List[Dict[str, Any]], 
                                            task_type: TaskType) -> LoadBalancingDecision:
        """
        Weighted round robin selection based on model capabilities
        """
        suitable_models = [
            model for model in available_models 
            if self._is_model_suitable(model["name"], task_type)
        ]
        
        if not suitable_models:
            return None
        
        # Calculate weights if not already done
        await self._update_model_weights(suitable_models, task_type)
        
        # Select based on weighted round robin
        total_weight = sum(self.model_weights.get(model["name"], 1.0) for model in suitable_models)
        
        if total_weight == 0:
            return await self._round_robin_selection(available_models, task_type)
        
        # This is a simplified implementation - full weighted round robin would maintain state
        weights = [(model["name"], self.model_weights.get(model["name"], 1.0) / total_weight) 
                  for model in suitable_models]
        weights.sort(key=lambda x: x[1], reverse=True)
        
        selected_model = weights[0][0]
        weight = weights[0][1]
        
        return LoadBalancingDecision(
            selected_model=selected_model,
            confidence=weight,
            reasoning=f"Weighted round robin: weight {weight:.2f}",
            estimated_wait_time=self._estimate_wait_time(selected_model)
        )
    
    async def _round_robin_selection(self, 
                                   available_models: List[Dict[str, Any]], 
                                   task_type: TaskType) -> LoadBalancingDecision:
        """
        Simple round robin selection
        """
        suitable_models = [
            model for model in available_models 
            if self._is_model_suitable(model["name"], task_type)
        ]
        
        if not suitable_models:
            return None
        
        # Simple round robin
        selected_model = suitable_models[self.round_robin_index % len(suitable_models)]["name"]
        self.round_robin_index += 1
        
        return LoadBalancingDecision(
            selected_model=selected_model,
            confidence=0.6,
            reasoning="Round robin selection",
            estimated_wait_time=self._estimate_wait_time(selected_model)
        )
    
    async def _calculate_model_score(self, 
                                   model_name: str, 
                                   task_type: TaskType,
                                   priority: TaskPriority,
                                   context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate comprehensive score for model selection
        """
        if model_name not in self.model_metrics:
            return 0.5  # Default score for unknown models
        
        metrics = self.model_metrics[model_name]
        score = 0.0
        
        # Response time factor (lower is better)
        if metrics.average_response_time > 0:
            response_time_score = max(0, 1.0 - (metrics.average_response_time / 120))  # Normalize to 2 minutes
            score += response_time_score * self.config["response_time_weight"]
        else:
            score += 0.5 * self.config["response_time_weight"]
        
        # Error rate factor (lower is better)
        error_rate_score = 1.0 - metrics.error_rate
        score += error_rate_score * self.config["error_rate_weight"]
        
        # Load factor (lower load is better)
        max_capacity = self._get_model_capacity(model_name)
        load_ratio = metrics.current_load / max_capacity if max_capacity > 0 else 1.0
        load_score = max(0, 1.0 - load_ratio)
        score += load_score * self.config["load_weight"]
        
        # Health score
        score += metrics.health_score * self.config["health_weight"]
        
        # Resource efficiency
        score += metrics.resource_efficiency * self.config["resource_weight"]
        
        # Model capability for specific task type
        capability_score = self._get_model_capability_score(model_name, task_type)
        score *= capability_score  # Multiply to emphasize capability importance
        
        return min(1.0, score)
    
    def _is_model_suitable(self, model_name: str, task_type: TaskType) -> bool:
        """Check if a model is suitable for a specific task type"""
        # This would be expanded based on actual model capabilities
        # For now, assume all models can handle all tasks but with different efficiency
        return True
    
    def _get_model_capacity(self, model_name: str) -> int:
        """Get maximum concurrent requests for a model"""
        # This would come from model configuration
        capacity_map = {
            "qwen_32b_primary": 2,
            "llama_70b_verification": 1,
            "qwen_7b_specialized": 3
        }
        return capacity_map.get(model_name, 1)
    
    def _get_model_capability_score(self, model_name: str, task_type: TaskType) -> float:
        """Get capability score for model-task combination"""
        # This would be based on model specialization and training
        capability_matrix = {
            "qwen_32b_primary": {
                TaskType.HYPOTHESIS_GENERATION: 0.9,
                TaskType.DATA_ANALYSIS: 0.9,
                TaskType.POLICY_ANALYSIS: 0.8,
                TaskType.FORECASTING: 0.8,
                TaskType.RESEARCH_SYNTHESIS: 0.9,
            },
            "llama_70b_verification": {
                TaskType.VERIFICATION: 0.95,
                TaskType.DATA_ANALYSIS: 0.8,
                TaskType.RESEARCH_SYNTHESIS: 0.85,
            },
            "qwen_7b_specialized": {
                TaskType.DATA_ENRICHMENT: 0.9,
                TaskType.ANOMALY_DETECTION: 0.8,
                TaskType.REPORT_GENERATION: 0.7,
            }
        }
        
        model_capabilities = capability_matrix.get(model_name, {})
        return model_capabilities.get(task_type, 0.6)  # Default capability
    
    def _estimate_wait_time(self, model_name: str) -> float:
        """Estimate wait time for a model"""
        if model_name not in self.model_metrics:
            return 30.0  # Default estimate
        
        metrics = self.model_metrics[model_name]
        queue_time = metrics.current_load * metrics.average_response_time
        return max(0, queue_time)
    
    def _estimate_processing_time(self, model_name: str, task_type: TaskType) -> float:
        """Estimate processing time for a specific model and task type"""
        task_model_key = (task_type.value, model_name)
        
        if task_model_key in self.task_model_performance:
            times = self.task_model_performance[task_model_key]
            valid_times = [t for t in times if t != float('inf')]
            
            if len(valid_times) >= 3:
                return statistics.median(valid_times)
        
        # Fall back to general model performance
        if model_name in self.model_metrics:
            return self.model_metrics[model_name].average_response_time
        
        return 60.0  # Default estimate
    
    def _get_score_reasoning(self, model_name: str, score: float) -> str:
        """Generate human-readable reasoning for model selection"""
        if model_name not in self.model_metrics:
            return f"Selected {model_name} with default scoring (score: {score:.2f})"
        
        metrics = self.model_metrics[model_name]
        factors = []
        
        if metrics.average_response_time < 30:
            factors.append("fast response time")
        if metrics.error_rate < 0.1:
            factors.append("low error rate")
        if metrics.current_load == 0:
            factors.append("no current load")
        if metrics.health_score > 0.8:
            factors.append("good health")
        
        reasoning = f"Selected {model_name} (score: {score:.2f})"
        if factors:
            reasoning += f" - {', '.join(factors)}"
        
        return reasoning
    
    async def _initialize_model_metrics(self):
        """Initialize metrics for all known models"""
        model_status = await self.orchestrator.get_model_status()
        if isinstance(model_status, dict):
            model_status = [model_status]
        
        for model_info in model_status:
            model_name = model_info["name"]
            if model_name not in self.model_metrics:
                self.model_metrics[model_name] = ModelMetrics(model_name=model_name)
                self.model_metrics[model_name].health_score = model_info.get("health_score", 1.0)
    
    async def _update_model_weights(self, models: List[Dict[str, Any]], task_type: TaskType):
        """Update model weights for weighted round robin"""
        for model_info in models:
            model_name = model_info["name"]
            capability_score = self._get_model_capability_score(model_name, task_type)
            
            # Adjust weight based on recent performance
            if model_name in self.model_metrics:
                metrics = self.model_metrics[model_name]
                performance_factor = 1.0 - metrics.error_rate
                response_time_factor = max(0.1, 1.0 - (metrics.average_response_time / 120))
                
                weight = capability_score * performance_factor * response_time_factor
            else:
                weight = capability_score
            
            self.model_weights[model_name] = max(0.1, weight)
    
    async def _update_metrics_periodically(self):
        """Background task to update model metrics"""
        while True:
            try:
                await self._update_model_health_scores()
                await asyncio.sleep(60)  # Update every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(30)
    
    async def _update_model_health_scores(self):
        """Update health scores for all models"""
        model_status = await self.orchestrator.get_model_status()
        if isinstance(model_status, dict):
            model_status = [model_status]
        
        async with self._performance_lock:
            for model_info in model_status:
                model_name = model_info["name"]
                if model_name in self.model_metrics:
                    self.model_metrics[model_name].health_score = model_info.get("health_score", 1.0)
    
    async def _calculate_system_load(self) -> Dict[str, float]:
        """Calculate overall system load metrics"""
        total_requests = sum(metrics.current_load for metrics in self.model_metrics.values())
        total_capacity = sum(self._get_model_capacity(name) for name in self.model_metrics.keys())
        
        avg_response_time = 0.0
        if self.model_metrics:
            response_times = [m.average_response_time for m in self.model_metrics.values() if m.average_response_time > 0]
            if response_times:
                avg_response_time = statistics.mean(response_times)
        
        return {
            "utilization_ratio": total_requests / total_capacity if total_capacity > 0 else 0.0,
            "average_response_time": avg_response_time,
            "total_active_requests": total_requests,
            "total_capacity": total_capacity
        }