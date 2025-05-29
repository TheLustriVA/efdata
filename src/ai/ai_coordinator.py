"""
AI Coordinator for EconCell Platform

Central coordination hub that integrates model orchestration, task queuing,
load balancing, and memory management for economic analysis workflows.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import json
import os

from .model_orchestrator import ModelOrchestrator, ModelPriority, ModelStatus
from .task_queue import TaskQueue, TaskType, TaskPriority, TaskStatus
from .load_balancer import LoadBalancer, LoadBalancingStrategy
from .memory_manager import MemoryManager, MemoryType, MemoryPriority

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of economic analysis workflows"""
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    DATA_ANALYSIS = "data_analysis"
    VERIFICATION = "verification"
    POLICY_ANALYSIS = "policy_analysis"
    FORECASTING = "forecasting"
    RESEARCH_SYNTHESIS = "research_synthesis"
    REPORT_GENERATION = "report_generation"
    MONTE_CARLO_SIMULATION = "monte_carlo_simulation"
    CELLULAR_AUTOMATA = "cellular_automata"


@dataclass
class AnalysisRequest:
    """Request for economic analysis"""
    analysis_type: AnalysisType
    content: str
    context: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    preferred_models: Optional[List[str]] = None
    verification_required: bool = True
    timeout_seconds: int = 300
    callback: Optional[Callable[[Any], Awaitable[None]]] = None


@dataclass
class AnalysisResult:
    """Result of economic analysis"""
    request_id: str
    analysis_type: AnalysisType
    primary_result: Any
    verification_results: Optional[List[Any]] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0
    models_used: List[str] = None
    metadata: Dict[str, Any] = None


class AICoordinator:
    """
    Central AI coordination system for EconCell platform
    
    Integrates and coordinates:
    - Model orchestration and lifecycle management
    - Task queuing and prioritization
    - Intelligent load balancing
    - Memory management and optimization
    - Multi-model verification workflows
    - Economic analysis pipelines
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the AI Coordinator
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize core components
        self.orchestrator = ModelOrchestrator(config_path)
        self.task_queue = TaskQueue(max_queue_size=self.config.get("max_queue_size", 10000))
        self.load_balancer = LoadBalancer(
            self.orchestrator, 
            LoadBalancingStrategy(self.config.get("load_balancing_strategy", "intelligent"))
        )
        self.memory_manager = MemoryManager(self.config.get("memory_config"))
        
        # Analysis tracking
        self.active_analyses: Dict[str, AnalysisRequest] = {}
        self.completed_analyses: Dict[str, AnalysisResult] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_processing_time": 0.0,
            "verification_success_rate": 0.0
        }
        
        # Verification workflows
        self.verification_models = self.config.get("verification_models", ["llama_70b_verification"])
        self.consensus_threshold = self.config.get("consensus_threshold", 0.7)
        
        # Background tasks
        self._processor_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        logger.info("AICoordinator initialized with load balancing strategy: %s", 
                   self.load_balancer.strategy.value)
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        return {
            "max_queue_size": 10000,
            "load_balancing_strategy": "intelligent",
            "verification_models": ["llama_70b_verification"],
            "consensus_threshold": 0.7,
            "multi_model_verification": True,
            "max_concurrent_analyses": 10,
            "analysis_timeout_seconds": 300,
            "memory_config": {
                "max_system_ram_usage": int(160 * 1024**3),
                "max_gpu_memory_usage": int(60 * 1024**3)
            },
            "economic_context": {
                "focus_region": "Australia",
                "primary_data_sources": ["RBA", "ABS", "Treasury"],
                "specialization_areas": [
                    "monetary_policy",
                    "trade_analysis", 
                    "commodity_economics",
                    "policy_impact_assessment"
                ]
            }
        }
    
    async def start(self):
        """Start the AI Coordinator and all subsystems"""
        logger.info("Starting AICoordinator")
        
        try:
            # Start all subsystems
            await self.orchestrator.load_model("qwen_32b_primary")  # Load primary model
            await self.task_queue.start()
            await self.load_balancer.start()
            await self.memory_manager.start()
            
            # Start background processing
            self._stop_event.clear()
            self._processor_task = asyncio.create_task(self._process_analyses())
            self._monitor_task = asyncio.create_task(self._monitor_system())
            
            logger.info("AICoordinator started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start AICoordinator: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the AI Coordinator and cleanup resources"""
        logger.info("Stopping AICoordinator")
        
        # Stop background tasks
        self._stop_event.set()
        
        if self._processor_task:
            self._processor_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()
        
        # Wait for tasks to complete
        tasks_to_wait = [t for t in [self._processor_task, self._monitor_task] if t]
        if tasks_to_wait:
            await asyncio.gather(*tasks_to_wait, return_exceptions=True)
        
        # Stop subsystems
        await self.task_queue.stop()
        await self.load_balancer.stop()
        await self.memory_manager.stop()
        await self.orchestrator.shutdown()
        
        logger.info("AICoordinator stopped")
    
    async def submit_analysis(self, request: AnalysisRequest) -> str:
        """
        Submit an economic analysis request
        
        Args:
            request: Analysis request with parameters
            
        Returns:
            Request ID for tracking
        """
        # Convert analysis type to task type
        task_type = self._analysis_to_task_type(request.analysis_type)
        
        # Add economic context to the request
        enhanced_context = self._enhance_context(request.context)
        enhanced_content = self._enhance_content(request.content, request.analysis_type)
        
        # Submit to task queue
        task_id = await self.task_queue.submit_task(
            task_type=task_type,
            content=enhanced_content,
            priority=request.priority,
            context=enhanced_context,
            preferred_model=request.preferred_models[0] if request.preferred_models else None,
            timeout_seconds=request.timeout_seconds,
            callback=request.callback
        )
        
        # Track the analysis
        self.active_analyses[task_id] = request
        
        logger.info(f"Submitted {request.analysis_type.value} analysis with task ID: {task_id}")
        return task_id
    
    async def get_analysis_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an analysis request"""
        task_status = await self.task_queue.get_task_status(request_id)
        
        if not task_status:
            # Check completed analyses
            if request_id in self.completed_analyses:
                result = self.completed_analyses[request_id]
                return {
                    "status": "completed",
                    "result": result,
                    "processing_time": result.processing_time,
                    "models_used": result.models_used
                }
            return None
        
        return {
            "status": task_status["status"],
            "created_at": task_status["created_at"],
            "processing_time": task_status.get("processing_time", 0),
            "assigned_model": task_status.get("assigned_model"),
            "retry_count": task_status.get("retry_count", 0)
        }
    
    async def cancel_analysis(self, request_id: str) -> bool:
        """Cancel an active analysis"""
        success = await self.task_queue.cancel_task(request_id)
        
        if success and request_id in self.active_analyses:
            del self.active_analyses[request_id]
        
        return success
    
    async def run_multi_model_verification(self, 
                                         content: str, 
                                         primary_result: Any,
                                         analysis_type: AnalysisType) -> List[Any]:
        """
        Run multi-model verification on analysis results
        
        Args:
            content: Original analysis content
            primary_result: Result to verify
            analysis_type: Type of analysis
            
        Returns:
            List of verification results from different models
        """
        verification_tasks = []
        verification_content = self._prepare_verification_content(content, primary_result, analysis_type)
        
        for model_name in self.verification_models:
            # Check if model is available
            model_status = await self.orchestrator.get_model_status(model_name)
            if model_status and model_status["status"] == ModelStatus.READY.value:
                
                task_id = await self.task_queue.submit_task(
                    task_type=TaskType.VERIFICATION,
                    content=verification_content,
                    priority=TaskPriority.HIGH,
                    preferred_model=model_name,
                    timeout_seconds=120
                )
                
                verification_tasks.append(task_id)
        
        # Wait for verification results
        verification_results = []
        for task_id in verification_tasks:
            # This is simplified - in practice you'd wait for task completion
            # and handle the async nature properly
            status = await self.task_queue.get_task_status(task_id)
            if status and status.get("status") == "completed":
                verification_results.append(status.get("result"))
        
        return verification_results
    
    async def generate_hypothesis(self, 
                                economic_data: Dict[str, Any],
                                focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate economic hypotheses from data patterns
        
        Args:
            economic_data: Economic dataset to analyze
            focus_areas: Specific areas to focus hypothesis generation
            
        Returns:
            Generated hypotheses with confidence scores
        """
        context = {
            "data_sources": list(economic_data.keys()),
            "focus_areas": focus_areas or self.config["economic_context"]["specialization_areas"],
            "region": self.config["economic_context"]["focus_region"]
        }
        
        content = self._format_hypothesis_content(economic_data, focus_areas)
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.HYPOTHESIS_GENERATION,
            content=content,
            context=context,
            priority=TaskPriority.HIGH,
            preferred_models=["qwen_32b_primary"]
        )
        
        task_id = await self.submit_analysis(request)
        
        # Wait for completion (simplified for demonstration)
        # In practice, this would use proper async waiting mechanisms
        return {"task_id": task_id, "status": "submitted"}
    
    async def analyze_policy_impact(self, 
                                  policy_description: str,
                                  economic_indicators: Dict[str, Any],
                                  simulation_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the potential impact of economic policy changes
        
        Args:
            policy_description: Description of the policy change
            economic_indicators: Current economic indicators
            simulation_parameters: Parameters for policy simulation
            
        Returns:
            Policy impact analysis results
        """
        context = {
            "policy_type": "monetary" if "interest rate" in policy_description.lower() else "fiscal",
            "indicators": list(economic_indicators.keys()),
            "simulation_params": simulation_parameters or {},
            "australian_context": True
        }
        
        content = f"""
        Policy Analysis Request:
        
        Policy Description: {policy_description}
        
        Current Economic Indicators:
        {json.dumps(economic_indicators, indent=2)}
        
        Analysis Requirements:
        - Assess immediate and long-term impacts
        - Consider Australian economic structure
        - Evaluate sector-specific effects
        - Quantify uncertainty ranges
        - Provide policy recommendations
        """
        
        request = AnalysisRequest(
            analysis_type=AnalysisType.POLICY_ANALYSIS,
            content=content,
            context=context,
            priority=TaskPriority.HIGH,
            verification_required=True
        )
        
        task_id = await self.submit_analysis(request)
        return {"task_id": task_id, "status": "submitted"}
    
    async def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        # Get metrics from all subsystems
        orchestrator_status = await self.orchestrator.get_model_status()
        queue_stats = await self.task_queue.get_queue_stats()
        load_balancer_stats = await self.load_balancer.get_load_balancing_stats()
        memory_stats = self.memory_manager.get_memory_stats()
        
        return {
            "ai_coordinator": {
                "active_analyses": len(self.active_analyses),
                "completed_analyses": len(self.completed_analyses),
                "performance_metrics": self.performance_metrics
            },
            "model_orchestrator": {
                "models": orchestrator_status if isinstance(orchestrator_status, list) else [orchestrator_status]
            },
            "task_queue": queue_stats,
            "load_balancer": load_balancer_stats,
            "memory_manager": memory_stats
        }
    
    def _analysis_to_task_type(self, analysis_type: AnalysisType) -> TaskType:
        """Convert analysis type to task type"""
        mapping = {
            AnalysisType.HYPOTHESIS_GENERATION: TaskType.HYPOTHESIS_GENERATION,
            AnalysisType.DATA_ANALYSIS: TaskType.DATA_ANALYSIS,
            AnalysisType.VERIFICATION: TaskType.VERIFICATION,
            AnalysisType.POLICY_ANALYSIS: TaskType.POLICY_ANALYSIS,
            AnalysisType.FORECASTING: TaskType.FORECASTING,
            AnalysisType.RESEARCH_SYNTHESIS: TaskType.RESEARCH_SYNTHESIS,
            AnalysisType.REPORT_GENERATION: TaskType.REPORT_GENERATION,
            AnalysisType.MONTE_CARLO_SIMULATION: TaskType.MONTE_CARLO,
            AnalysisType.CELLULAR_AUTOMATA: TaskType.CELLULAR_AUTOMATA
        }
        return mapping.get(analysis_type, TaskType.DATA_ANALYSIS)
    
    def _enhance_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance context with economic analysis framework"""
        enhanced = context.copy()
        enhanced.update({
            "economic_framework": "Australian macroeconomic analysis",
            "data_sources": self.config["economic_context"]["primary_data_sources"],
            "focus_region": self.config["economic_context"]["focus_region"],
            "analysis_timestamp": time.time(),
            "rba_circular_flow": True,  # Indicates RBA circular flow context
            "verification_enabled": self.config.get("multi_model_verification", True)
        })
        return enhanced
    
    def _enhance_content(self, content: str, analysis_type: AnalysisType) -> str:
        """Enhance content with analysis-specific instructions"""
        economic_context = f"""
        Economic Analysis Context:
        - Focus: Australian economic conditions and policy implications
        - Framework: RBA circular flow model and monetary transmission mechanisms
        - Perspective: Consider both domestic and international factors
        - Methodology: Apply rigorous economic reasoning with quantitative support
        
        Analysis Type: {analysis_type.value}
        
        Original Content:
        {content}
        
        Please provide comprehensive analysis with:
        1. Clear economic reasoning
        2. Quantitative evidence where possible
        3. Policy implications
        4. Uncertainty assessment
        5. Australian-specific considerations
        """
        
        return economic_context
    
    def _prepare_verification_content(self, 
                                    original_content: str, 
                                    primary_result: Any,
                                    analysis_type: AnalysisType) -> str:
        """Prepare content for multi-model verification"""
        return f"""
        Verification Request:
        
        Original Analysis: {analysis_type.value}
        
        Original Content:
        {original_content}
        
        Primary Result to Verify:
        {json.dumps(primary_result, indent=2) if isinstance(primary_result, dict) else str(primary_result)}
        
        Verification Tasks:
        1. Assess the logical consistency of the analysis
        2. Check for factual accuracy
        3. Evaluate the strength of economic reasoning
        4. Identify potential biases or errors
        5. Rate confidence level (0-100%)
        6. Suggest improvements if needed
        
        Please provide structured verification results.
        """
    
    def _format_hypothesis_content(self, 
                                 economic_data: Dict[str, Any],
                                 focus_areas: Optional[List[str]]) -> str:
        """Format content for hypothesis generation"""
        return f"""
        Economic Hypothesis Generation Request:
        
        Economic Data Summary:
        {json.dumps(economic_data, indent=2)}
        
        Focus Areas: {', '.join(focus_areas) if focus_areas else 'General economic patterns'}
        
        Please analyze the provided economic data and generate:
        
        1. Novel Economic Hypotheses:
           - Identify unusual patterns or relationships
           - Propose explanatory mechanisms
           - Consider Australian economic structure
        
        2. Testable Predictions:
           - Specific, measurable predictions
           - Timeline for validation
           - Data requirements for testing
        
        3. Policy Implications:
           - Potential policy responses
           - Expected effectiveness
           - Implementation challenges
        
        4. Research Priorities:
           - Areas requiring deeper investigation
           - Data collection needs
           - Methodological considerations
        
        Format as structured JSON with confidence scores for each hypothesis.
        """
    
    async def _process_analyses(self):
        """Background task to process analysis workflows"""
        logger.info("Started analysis processor")
        
        while not self._stop_event.is_set():
            try:
                # This is where you'd implement the main analysis processing loop
                # For now, just a placeholder that monitors active analyses
                
                for task_id, request in list(self.active_analyses.items()):
                    status = await self.task_queue.get_task_status(task_id)
                    
                    if status and status["status"] == "completed":
                        # Process completed analysis
                        await self._handle_completed_analysis(task_id, request, status)
                    elif status and status["status"] in ["failed", "timeout"]:
                        # Handle failed analysis
                        await self._handle_failed_analysis(task_id, request, status)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis processor error: {e}")
                await asyncio.sleep(10)
        
        logger.info("Analysis processor stopped")
    
    async def _monitor_system(self):
        """Background task to monitor system health"""
        logger.info("Started system monitor")
        
        while not self._stop_event.is_set():
            try:
                # Monitor system performance and health
                performance = await self.get_system_performance()
                
                # Log system status periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    logger.info(
                        f"System status - Active analyses: {performance['ai_coordinator']['active_analyses']}, "
                        f"Queue size: {performance['task_queue']['pending_tasks']}, "
                        f"Memory usage: {performance['memory_manager']['system_memory']['utilization']:.1%}"
                    )
                
                # Check for system issues and alerts
                await self._check_system_health(performance)
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System monitor error: {e}")
                await asyncio.sleep(60)
        
        logger.info("System monitor stopped")
    
    async def _handle_completed_analysis(self, 
                                       task_id: str, 
                                       request: AnalysisRequest,
                                       status: Dict[str, Any]):
        """Handle completed analysis results"""
        try:
            # Create analysis result
            result = AnalysisResult(
                request_id=task_id,
                analysis_type=request.analysis_type,
                primary_result=status.get("result"),
                processing_time=status.get("processing_time", 0),
                models_used=[status.get("assigned_model")],
                metadata={"task_status": status}
            )
            
            # Run verification if required
            if request.verification_required and self.config.get("multi_model_verification"):
                verification_results = await self.run_multi_model_verification(
                    request.content,
                    result.primary_result,
                    request.analysis_type
                )
                result.verification_results = verification_results
                result.confidence_score = self._calculate_confidence_score(
                    result.primary_result,
                    verification_results
                )
            else:
                result.confidence_score = 0.8  # Default confidence without verification
            
            # Store completed analysis
            self.completed_analyses[task_id] = result
            
            # Remove from active analyses
            if task_id in self.active_analyses:
                del self.active_analyses[task_id]
            
            # Update performance metrics
            self.performance_metrics["total_analyses"] += 1
            self.performance_metrics["successful_analyses"] += 1
            self._update_average_processing_time(result.processing_time)
            
            logger.info(f"Completed analysis {task_id} with confidence score {result.confidence_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error handling completed analysis {task_id}: {e}")
    
    async def _handle_failed_analysis(self, 
                                    task_id: str, 
                                    request: AnalysisRequest,
                                    status: Dict[str, Any]):
        """Handle failed analysis"""
        # Remove from active analyses
        if task_id in self.active_analyses:
            del self.active_analyses[task_id]
        
        # Update performance metrics
        self.performance_metrics["total_analyses"] += 1
        self.performance_metrics["failed_analyses"] += 1
        
        logger.warning(f"Analysis {task_id} failed: {status.get('error', 'Unknown error')}")
    
    def _calculate_confidence_score(self, 
                                  primary_result: Any,
                                  verification_results: List[Any]) -> float:
        """Calculate confidence score based on verification results"""
        if not verification_results:
            return 0.5  # Low confidence without verification
        
        # This is a simplified confidence calculation
        # In practice, you'd implement sophisticated consensus algorithms
        consensus_count = 0
        total_verifications = len(verification_results)
        
        for verification in verification_results:
            # Simplified - assume verification results have consensus indicators
            if isinstance(verification, dict) and verification.get("consensus", False):
                consensus_count += 1
        
        consensus_ratio = consensus_count / total_verifications if total_verifications > 0 else 0
        
        # Apply consensus threshold
        if consensus_ratio >= self.consensus_threshold:
            return min(1.0, 0.7 + (consensus_ratio * 0.3))  # 0.7-1.0 range
        else:
            return max(0.1, consensus_ratio * 0.7)  # 0.1-0.7 range
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        total_successful = self.performance_metrics["successful_analyses"]
        current_avg = self.performance_metrics["average_processing_time"]
        
        if total_successful == 1:
            self.performance_metrics["average_processing_time"] = processing_time
        else:
            # Running average calculation
            self.performance_metrics["average_processing_time"] = (
                (current_avg * (total_successful - 1) + processing_time) / total_successful
            )
    
    async def _check_system_health(self, performance: Dict[str, Any]):
        """Check system health and trigger alerts if needed"""
        # Memory usage check
        memory_util = performance["memory_manager"]["system_memory"]["utilization"]
        if memory_util > 0.9:
            logger.warning(f"High memory usage detected: {memory_util:.1%}")
        
        # Queue backlog check
        pending_tasks = performance["task_queue"]["pending_tasks"]
        if pending_tasks > 1000:
            logger.warning(f"Large task queue backlog: {pending_tasks} pending tasks")
        
        # Model health check
        models = performance["model_orchestrator"]["models"]
        unhealthy_models = [
            model for model in models 
            if model.get("health_score", 1.0) < 0.5
        ]
        
        if unhealthy_models:
            logger.warning(f"Unhealthy models detected: {[m['name'] for m in unhealthy_models]}")