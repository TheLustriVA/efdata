"""
Model Orchestrator for EconCell AI System

Manages multiple LLM models, coordinates task distribution, and handles
model lifecycle management for economic analysis workflows.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from concurrent.futures import ThreadPoolExecutor
import psutil
import GPUtil

logger = logging.getLogger(__name__)


class ModelPriority(Enum):
    """Model priority levels for resource allocation"""
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"


class ModelStatus(Enum):
    """Model operational status"""
    LOADING = "loading"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    UNLOADED = "unloaded"


@dataclass
class ModelConfig:
    """Configuration for individual models"""
    name: str
    model_path: str
    priority: ModelPriority
    gpu_memory_gb: float
    ram_memory_gb: float
    max_concurrent_requests: int = 1
    specialized_domains: List[str] = field(default_factory=list)
    api_endpoint: Optional[str] = None
    model_type: str = "ollama"  # ollama, vllm, transformers
    context_length: int = 32768
    temperature: float = 0.7


@dataclass
class ModelInstance:
    """Runtime model instance information"""
    config: ModelConfig
    status: ModelStatus = ModelStatus.UNLOADED
    current_requests: int = 0
    total_requests: int = 0
    average_response_time: float = 0.0
    error_count: int = 0
    last_used: float = field(default_factory=time.time)
    health_score: float = 1.0


class ModelOrchestrator:
    """
    Central orchestrator for managing multiple LLM models in the EconCell system.
    
    Handles model loading, request routing, resource management, and health monitoring
    for optimal performance across different economic analysis tasks.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Model Orchestrator
        
        Args:
            config_path: Path to model configuration JSON file
        """
        self.models: Dict[str, ModelInstance] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_running = False
        self._lock = asyncio.Lock()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize models based on configuration
        self._initialize_models()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load model configuration from file or use defaults"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration optimized for RTX 5090 + 184GB RAM setup
        return {
            "models": [
                {
                    "name": "qwen_32b_primary",
                    "model_path": "qwen/qwq-32b-preview",
                    "priority": "high",
                    "gpu_memory_gb": 32.0,
                    "ram_memory_gb": 8.0,
                    "max_concurrent_requests": 2,
                    "specialized_domains": ["economic_analysis", "hypothesis_generation", "reasoning"],
                    "api_endpoint": "http://localhost:11434",
                    "model_type": "ollama",
                    "context_length": 32768,
                    "temperature": 0.3
                },
                {
                    "name": "llama_70b_verification",
                    "model_path": "llama3.1:70b",
                    "priority": "medium",
                    "gpu_memory_gb": 24.0,
                    "ram_memory_gb": 12.0,
                    "max_concurrent_requests": 1,
                    "specialized_domains": ["verification", "cross_checking", "validation"],
                    "api_endpoint": "http://localhost:11434",
                    "model_type": "ollama",
                    "context_length": 128000,
                    "temperature": 0.1
                },
                {
                    "name": "qwen_7b_specialized",
                    "model_path": "qwen2.5:7b",
                    "priority": "low",
                    "gpu_memory_gb": 8.0,
                    "ram_memory_gb": 4.0,
                    "max_concurrent_requests": 3,
                    "specialized_domains": ["data_enrichment", "classification", "summarization"],
                    "api_endpoint": "http://localhost:11434",
                    "model_type": "ollama",
                    "context_length": 32768,
                    "temperature": 0.5
                }
            ],
            "resource_limits": {
                "max_gpu_memory_gb": 60.0,  # Leave 4GB free on RTX 5090
                "max_ram_memory_gb": 160.0,  # Leave 24GB free from 184GB total
                "gpu_utilization_threshold": 0.85,
                "ram_utilization_threshold": 0.90
            },
            "health_check_interval": 30,
            "request_timeout": 300,
            "retry_attempts": 3
        }
    
    def _initialize_models(self):
        """Initialize model instances from configuration"""
        for model_config in self.config["models"]:
            config = ModelConfig(**model_config)
            instance = ModelInstance(config=config)
            self.models[config.name] = instance
            logger.info(f"Initialized model configuration: {config.name}")
    
    def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        self.is_running = True
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._resource_monitor())
        logger.info("Started background monitoring tasks")
    
    async def _health_monitor(self):
        """Background task to monitor model health and performance"""
        while self.is_running:
            try:
                for model_name, instance in self.models.items():
                    if instance.status == ModelStatus.READY:
                        # Perform health check
                        health_score = await self._check_model_health(model_name)
                        instance.health_score = health_score
                        
                        # Log health issues
                        if health_score < 0.5:
                            logger.warning(f"Model {model_name} health score low: {health_score}")
                
                await asyncio.sleep(self.config["health_check_interval"])
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _resource_monitor(self):
        """Monitor system resource usage and adjust model allocation"""
        while self.is_running:
            try:
                # Check GPU usage
                gpu_info = GPUtil.getGPUs()
                if gpu_info:
                    gpu_usage = gpu_info[0].memoryUtil
                    if gpu_usage > self.config["resource_limits"]["gpu_utilization_threshold"]:
                        logger.warning(f"High GPU utilization: {gpu_usage:.2%}")
                        await self._handle_resource_pressure("gpu")
                
                # Check RAM usage
                ram_usage = psutil.virtual_memory().percent / 100
                if ram_usage > self.config["resource_limits"]["ram_utilization_threshold"]:
                    logger.warning(f"High RAM utilization: {ram_usage:.2%}")
                    await self._handle_resource_pressure("ram")
                
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Resource monitor error: {e}")
                await asyncio.sleep(30)
    
    async def load_model(self, model_name: str) -> bool:
        """
        Load a specific model into memory
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            True if successfully loaded, False otherwise
        """
        if model_name not in self.models:
            logger.error(f"Unknown model: {model_name}")
            return False
        
        instance = self.models[model_name]
        
        if instance.status == ModelStatus.READY:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        logger.info(f"Loading model: {model_name}")
        instance.status = ModelStatus.LOADING
        
        try:
            # Check resource availability
            if not await self._check_resource_availability(instance.config):
                logger.error(f"Insufficient resources for model: {model_name}")
                instance.status = ModelStatus.ERROR
                return False
            
            # Load model based on type
            if instance.config.model_type == "ollama":
                success = await self._load_ollama_model(instance)
            elif instance.config.model_type == "vllm":
                success = await self._load_vllm_model(instance)
            else:
                logger.error(f"Unsupported model type: {instance.config.model_type}")
                success = False
            
            if success:
                instance.status = ModelStatus.READY
                instance.last_used = time.time()
                logger.info(f"Successfully loaded model: {model_name}")
                return True
            else:
                instance.status = ModelStatus.ERROR
                instance.error_count += 1
                logger.error(f"Failed to load model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            instance.status = ModelStatus.ERROR
            instance.error_count += 1
            return False
    
    async def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if successfully unloaded, False otherwise
        """
        if model_name not in self.models:
            logger.error(f"Unknown model: {model_name}")
            return False
        
        instance = self.models[model_name]
        
        if instance.status == ModelStatus.UNLOADED:
            logger.info(f"Model {model_name} already unloaded")
            return True
        
        if instance.current_requests > 0:
            logger.warning(f"Cannot unload model {model_name} - active requests: {instance.current_requests}")
            return False
        
        logger.info(f"Unloading model: {model_name}")
        
        try:
            # Unload based on model type
            if instance.config.model_type == "ollama":
                success = await self._unload_ollama_model(instance)
            elif instance.config.model_type == "vllm":
                success = await self._unload_vllm_model(instance)
            else:
                success = True  # Default success for unknown types
            
            if success:
                instance.status = ModelStatus.UNLOADED
                logger.info(f"Successfully unloaded model: {model_name}")
                return True
            else:
                logger.error(f"Failed to unload model: {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {e}")
            return False
    
    async def route_request(self, 
                          task_type: str, 
                          content: str, 
                          preferred_model: Optional[str] = None,
                          priority: ModelPriority = ModelPriority.MEDIUM) -> Optional[str]:
        """
        Route a request to the most appropriate available model
        
        Args:
            task_type: Type of task (economic_analysis, verification, etc.)
            content: Content to process
            preferred_model: Specific model to use if available
            priority: Request priority level
            
        Returns:
            Selected model name or None if no suitable model available
        """
        async with self._lock:
            # If preferred model specified and available, use it
            if preferred_model and preferred_model in self.models:
                instance = self.models[preferred_model]
                if (instance.status == ModelStatus.READY and 
                    instance.current_requests < instance.config.max_concurrent_requests):
                    return preferred_model
            
            # Find best available model for task
            candidates = []
            
            for model_name, instance in self.models.items():
                if (instance.status == ModelStatus.READY and
                    instance.current_requests < instance.config.max_concurrent_requests):
                    
                    score = self._calculate_model_score(instance, task_type, priority)
                    candidates.append((model_name, score))
            
            if not candidates:
                logger.warning("No available models for request routing")
                return None
            
            # Sort by score (highest first) and return best match
            candidates.sort(key=lambda x: x[1], reverse=True)
            selected_model = candidates[0][0]
            
            logger.debug(f"Routed {task_type} task to model: {selected_model}")
            return selected_model
    
    def _calculate_model_score(self, 
                              instance: ModelInstance, 
                              task_type: str, 
                              priority: ModelPriority) -> float:
        """Calculate suitability score for model-task combination"""
        score = instance.health_score
        
        # Domain specialization bonus
        if task_type in instance.config.specialized_domains:
            score += 0.3
        
        # Priority matching
        if instance.config.priority.value == priority.value:
            score += 0.2
        
        # Load balancing - prefer less busy models
        load_factor = instance.current_requests / instance.config.max_concurrent_requests
        score -= load_factor * 0.2
        
        # Performance history
        if instance.total_requests > 0:
            avg_response_time = instance.average_response_time
            if avg_response_time < 30:  # Fast responses get bonus
                score += 0.1
            elif avg_response_time > 120:  # Slow responses get penalty
                score -= 0.1
        
        # Error rate penalty
        if instance.total_requests > 0:
            error_rate = instance.error_count / instance.total_requests
            score -= error_rate * 0.3
        
        return max(0.0, score)
    
    async def _check_resource_availability(self, config: ModelConfig) -> bool:
        """Check if sufficient resources are available for model"""
        # Check GPU memory availability
        try:
            gpu_info = GPUtil.getGPUs()
            if gpu_info:
                available_gpu_memory = (1 - gpu_info[0].memoryUtil) * gpu_info[0].memoryTotal / 1024  # GB
                if available_gpu_memory < config.gpu_memory_gb:
                    logger.warning(f"Insufficient GPU memory: need {config.gpu_memory_gb}GB, available {available_gpu_memory:.1f}GB")
                    return False
        except Exception as e:
            logger.warning(f"Could not check GPU availability: {e}")
        
        # Check RAM availability
        available_ram = psutil.virtual_memory().available / (1024**3)  # GB
        if available_ram < config.ram_memory_gb:
            logger.warning(f"Insufficient RAM: need {config.ram_memory_gb}GB, available {available_ram:.1f}GB")
            return False
        
        return True
    
    async def _check_model_health(self, model_name: str) -> float:
        """Perform health check on a model and return health score"""
        instance = self.models[model_name]
        
        try:
            # Simple health check - test basic functionality
            start_time = time.time()
            
            # For Ollama models, we could do a simple API ping
            if instance.config.model_type == "ollama":
                # This would be implemented with actual Ollama API call
                # For now, return based on current status and error rate
                pass
            
            response_time = time.time() - start_time
            
            # Calculate health score based on various factors
            health_score = 1.0
            
            # Response time factor
            if response_time > 10:
                health_score -= 0.2
            elif response_time > 5:
                health_score -= 0.1
            
            # Error rate factor
            if instance.total_requests > 0:
                error_rate = instance.error_count / instance.total_requests
                health_score -= error_rate * 0.5
            
            # Time since last use factor
            time_since_use = time.time() - instance.last_used
            if time_since_use > 3600:  # 1 hour
                health_score -= 0.1
            
            return max(0.0, min(1.0, health_score))
            
        except Exception as e:
            logger.error(f"Health check failed for model {model_name}: {e}")
            return 0.0
    
    async def _handle_resource_pressure(self, resource_type: str):
        """Handle high resource utilization by unloading low-priority models"""
        logger.info(f"Handling {resource_type} resource pressure")
        
        # Find candidates for unloading (low priority, not currently busy)
        candidates = []
        for model_name, instance in self.models.items():
            if (instance.status == ModelStatus.READY and 
                instance.current_requests == 0 and
                instance.config.priority == ModelPriority.LOW):
                candidates.append((model_name, instance.last_used))
        
        # Sort by last used time (oldest first)
        candidates.sort(key=lambda x: x[1])
        
        # Unload oldest low-priority model
        if candidates:
            model_to_unload = candidates[0][0]
            logger.info(f"Unloading model {model_to_unload} to free {resource_type} resources")
            await self.unload_model(model_to_unload)
    
    async def _load_ollama_model(self, instance: ModelInstance) -> bool:
        """Load model using Ollama API"""
        try:
            # This would implement actual Ollama API calls
            # For now, simulate loading
            await asyncio.sleep(1)  # Simulate loading time
            logger.info(f"Loaded Ollama model: {instance.config.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load Ollama model: {e}")
            return False
    
    async def _unload_ollama_model(self, instance: ModelInstance) -> bool:
        """Unload model using Ollama API"""
        try:
            # This would implement actual Ollama API calls
            await asyncio.sleep(0.5)  # Simulate unloading time
            logger.info(f"Unloaded Ollama model: {instance.config.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload Ollama model: {e}")
            return False
    
    async def _load_vllm_model(self, instance: ModelInstance) -> bool:
        """Load model using vLLM"""
        try:
            # This would implement actual vLLM model loading
            await asyncio.sleep(2)  # Simulate loading time
            logger.info(f"Loaded vLLM model: {instance.config.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load vLLM model: {e}")
            return False
    
    async def _unload_vllm_model(self, instance: ModelInstance) -> bool:
        """Unload model using vLLM"""
        try:
            # This would implement actual vLLM model unloading
            await asyncio.sleep(1)  # Simulate unloading time
            logger.info(f"Unloaded vLLM model: {instance.config.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload vLLM model: {e}")
            return False
    
    async def get_model_status(self, model_name: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get status information for models
        
        Args:
            model_name: Specific model name, or None for all models
            
        Returns:
            Model status information
        """
        def format_model_status(instance: ModelInstance) -> Dict[str, Any]:
            return {
                "name": instance.config.name,
                "status": instance.status.value,
                "priority": instance.config.priority.value,
                "current_requests": instance.current_requests,
                "total_requests": instance.total_requests,
                "average_response_time": instance.average_response_time,
                "error_count": instance.error_count,
                "health_score": instance.health_score,
                "last_used": instance.last_used,
                "specialized_domains": instance.config.specialized_domains,
                "gpu_memory_gb": instance.config.gpu_memory_gb,
                "ram_memory_gb": instance.config.ram_memory_gb
            }
        
        if model_name:
            if model_name in self.models:
                return format_model_status(self.models[model_name])
            else:
                raise ValueError(f"Unknown model: {model_name}")
        else:
            return [format_model_status(instance) for instance in self.models.values()]
    
    async def shutdown(self):
        """Gracefully shutdown the orchestrator"""
        logger.info("Shutting down Model Orchestrator")
        self.is_running = False
        
        # Unload all models
        for model_name in list(self.models.keys()):
            await self.unload_model(model_name)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Model Orchestrator shutdown complete")