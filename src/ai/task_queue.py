"""
Task Queue System for EconCell AI Orchestration

Manages task queuing, prioritization, and distribution for economic analysis workflows.
Supports different task types with appropriate priority handling and load balancing.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict
import heapq

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of economic analysis tasks"""
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    DATA_ANALYSIS = "data_analysis"
    VERIFICATION = "verification"
    POLICY_ANALYSIS = "policy_analysis"
    FORECASTING = "forecasting"
    RESEARCH_SYNTHESIS = "research_synthesis"
    REPORT_GENERATION = "report_generation"
    DATA_ENRICHMENT = "data_enrichment"
    ANOMALY_DETECTION = "anomaly_detection"
    MONTE_CARLO = "monte_carlo"
    CELLULAR_AUTOMATA = "cellular_automata"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0    # Immediate processing required
    HIGH = 1        # High priority tasks
    NORMAL = 2      # Standard priority
    LOW = 3         # Background processing
    BATCH = 4       # Bulk processing tasks


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class Task:
    """Individual task representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.DATA_ANALYSIS
    priority: TaskPriority = TaskPriority.NORMAL
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    preferred_model: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 300
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_model: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    callback: Optional[Callable[[Any], Awaitable[None]]] = None
    
    def __lt__(self, other):
        """Comparison for priority queue ordering"""
        if self.priority.value == other.priority.value:
            return self.created_at < other.created_at
        return self.priority.value < other.priority.value


@dataclass
class QueueStats:
    """Queue statistics and metrics"""
    total_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_wait_time: float = 0.0
    average_processing_time: float = 0.0
    throughput_per_minute: float = 0.0
    task_type_distribution: Dict[str, int] = field(default_factory=dict)
    model_utilization: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class TaskQueue:
    """
    Advanced task queue system for coordinating AI model workloads
    
    Features:
    - Priority-based task scheduling
    - Task type-specific routing
    - Retry logic with exponential backoff
    - Comprehensive monitoring and metrics
    - Callback support for async workflows
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize the task queue system
        
        Args:
            max_queue_size: Maximum number of tasks in queue
        """
        self.max_queue_size = max_queue_size
        self.tasks: Dict[str, Task] = {}
        self.priority_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        
        # Queue management
        self._queue_lock = asyncio.Lock()
        self._processing_lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        
        # Statistics tracking
        self.stats = QueueStats()
        self._stats_lock = asyncio.Lock()
        
        # Background task references
        self._processor_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Callbacks for external integration
        self.task_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("TaskQueue initialized with max_queue_size: %d", max_queue_size)
    
    async def start(self):
        """Start the task queue processing"""
        if self._processor_task is not None:
            logger.warning("TaskQueue already started")
            return
        
        logger.info("Starting TaskQueue background processors")
        self._stop_event.clear()
        
        # Start background tasks
        self._processor_task = asyncio.create_task(self._process_queue())
        self._monitor_task = asyncio.create_task(self._monitor_queue())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_tasks())
        
        logger.info("TaskQueue started successfully")
    
    async def stop(self):
        """Stop the task queue processing"""
        logger.info("Stopping TaskQueue")
        self._stop_event.set()
        
        # Cancel background tasks
        if self._processor_task:
            self._processor_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Wait for tasks to complete
        tasks_to_wait = [t for t in [self._processor_task, self._monitor_task, self._cleanup_task] if t]
        if tasks_to_wait:
            await asyncio.gather(*tasks_to_wait, return_exceptions=True)
        
        logger.info("TaskQueue stopped")
    
    async def submit_task(self, 
                         task_type: TaskType,
                         content: str,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         context: Optional[Dict[str, Any]] = None,
                         preferred_model: Optional[str] = None,
                         timeout_seconds: int = 300,
                         callback: Optional[Callable[[Any], Awaitable[None]]] = None) -> str:
        """
        Submit a new task to the queue
        
        Args:
            task_type: Type of task to perform
            content: Task content/input
            priority: Task priority level
            context: Additional context information
            preferred_model: Preferred model for processing
            timeout_seconds: Task timeout in seconds
            callback: Optional callback function for results
            
        Returns:
            Task ID for tracking
        """
        if len(self.tasks) >= self.max_queue_size:
            raise RuntimeError(f"Queue is full (max_size: {self.max_queue_size})")
        
        task = Task(
            task_type=task_type,
            content=content,
            priority=priority,
            context=context or {},
            preferred_model=preferred_model,
            timeout_seconds=timeout_seconds,
            callback=callback
        )
        
        async with self._queue_lock:
            self.tasks[task.id] = task
            heapq.heappush(self.priority_queue, task)
            task.status = TaskStatus.QUEUED
        
        # Update statistics
        await self._update_stats_on_submit(task)
        
        # Trigger callbacks
        await self._trigger_callbacks("task_submitted", task)
        
        logger.debug(f"Submitted task {task.id} of type {task_type.value} with priority {priority.value}")
        return task.id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status information or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "task_type": task.task_type.value,
            "priority": task.priority.value,
            "status": task.status.value,
            "created_at": task.created_at,
            "assigned_at": task.assigned_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "assigned_model": task.assigned_model,
            "retry_count": task.retry_count,
            "error": task.error,
            "processing_time": self._calculate_processing_time(task),
            "wait_time": self._calculate_wait_time(task)
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # Can only cancel pending, queued, or assigned tasks
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        async with self._queue_lock:
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
            
            # Remove from priority queue if still there
            if task in self.priority_queue:
                self.priority_queue.remove(task)
                heapq.heapify(self.priority_queue)
            
            # Remove from running tasks if currently running
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
        
        await self._trigger_callbacks("task_cancelled", task)
        logger.info(f"Cancelled task {task_id}")
        return True
    
    async def get_next_task(self, 
                           model_name: str,
                           supported_task_types: Optional[List[TaskType]] = None) -> Optional[Task]:
        """
        Get the next task for a specific model
        
        Args:
            model_name: Name of the requesting model
            supported_task_types: Types of tasks the model can handle
            
        Returns:
            Next task to process or None if no suitable tasks
        """
        async with self._queue_lock:
            if not self.priority_queue:
                return None
            
            # Find the highest priority task that matches model capabilities
            suitable_tasks = []
            
            for i, task in enumerate(self.priority_queue):
                if task.status != TaskStatus.QUEUED:
                    continue
                
                # Check if model supports this task type
                if supported_task_types and task.task_type not in supported_task_types:
                    continue
                
                # Check if this is the preferred model or no preference
                if task.preferred_model and task.preferred_model != model_name:
                    continue
                
                suitable_tasks.append((i, task))
            
            if not suitable_tasks:
                return None
            
            # Get highest priority task (lowest index in heap)
            index, task = suitable_tasks[0]
            
            # Remove from priority queue
            self.priority_queue.pop(index)
            heapq.heapify(self.priority_queue)
            
            # Mark as assigned
            task.status = TaskStatus.ASSIGNED
            task.assigned_at = time.time()
            task.assigned_model = model_name
            self.running_tasks[task.id] = task
        
        await self._trigger_callbacks("task_assigned", task)
        logger.debug(f"Assigned task {task.id} to model {model_name}")
        return task
    
    async def complete_task(self, task_id: str, result: Any) -> bool:
        """
        Mark a task as completed with results
        
        Args:
            task_id: Task identifier
            result: Task execution result
            
        Returns:
            True if completed successfully, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task or task.status not in [TaskStatus.ASSIGNED, TaskStatus.RUNNING]:
            return False
        
        async with self._processing_lock:
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.result = result
            
            # Move from running to completed
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            self.completed_tasks[task_id] = task
        
        # Update statistics
        await self._update_stats_on_complete(task)
        
        # Execute callback if provided
        if task.callback:
            try:
                await task.callback(result)
            except Exception as e:
                logger.error(f"Callback error for task {task_id}: {e}")
        
        await self._trigger_callbacks("task_completed", task)
        logger.debug(f"Completed task {task_id}")
        return True
    
    async def fail_task(self, task_id: str, error: str, retry: bool = True) -> bool:
        """
        Mark a task as failed
        
        Args:
            task_id: Task identifier
            error: Error description
            retry: Whether to retry the task
            
        Returns:
            True if handled successfully, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        task.error = error
        task.retry_count += 1
        
        # Decide whether to retry
        should_retry = (retry and 
                       task.retry_count <= task.max_retries and
                       task.status in [TaskStatus.ASSIGNED, TaskStatus.RUNNING])
        
        async with self._processing_lock:
            if should_retry:
                # Reset task for retry with exponential backoff
                task.status = TaskStatus.QUEUED
                task.assigned_at = None
                task.started_at = None
                task.assigned_model = None
                
                # Add delay based on retry count
                delay = min(60, 2 ** task.retry_count)  # Max 60 second delay
                task.created_at = time.time() + delay
                
                # Re-queue the task
                async with self._queue_lock:
                    heapq.heappush(self.priority_queue, task)
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]
                
                logger.warning(f"Retrying task {task_id} (attempt {task.retry_count}/{task.max_retries}) after {delay}s delay")
            else:
                # Mark as permanently failed
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()
                
                # Move from running to failed
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                self.failed_tasks[task_id] = task
                
                logger.error(f"Task {task_id} failed permanently: {error}")
        
        await self._update_stats_on_fail(task)
        await self._trigger_callbacks("task_failed" if not should_retry else "task_retry", task)
        return True
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        async with self._stats_lock:
            # Update real-time stats
            self.stats.pending_tasks = len(self.priority_queue)
            self.stats.running_tasks = len(self.running_tasks)
            self.stats.completed_tasks = len(self.completed_tasks)
            self.stats.failed_tasks = len(self.failed_tasks)
            self.stats.total_tasks = len(self.tasks)
            
            # Calculate throughput
            current_time = time.time()
            recent_completions = [
                task for task in self.completed_tasks.values()
                if task.completed_at and current_time - task.completed_at < 300  # Last 5 minutes
            ]
            self.stats.throughput_per_minute = len(recent_completions) / 5.0
            
            return {
                "total_tasks": self.stats.total_tasks,
                "pending_tasks": self.stats.pending_tasks,
                "running_tasks": self.stats.running_tasks,
                "completed_tasks": self.stats.completed_tasks,
                "failed_tasks": self.stats.failed_tasks,
                "average_wait_time": self.stats.average_wait_time,
                "average_processing_time": self.stats.average_processing_time,
                "throughput_per_minute": self.stats.throughput_per_minute,
                "task_type_distribution": dict(self.stats.task_type_distribution),
                "model_utilization": dict(self.stats.model_utilization),
                "queue_capacity_used": f"{(len(self.tasks) / self.max_queue_size) * 100:.1f}%"
            }
    
    def register_callback(self, event_type: str, callback: Callable[[Task], Awaitable[None]]):
        """Register a callback for queue events"""
        self.task_callbacks[event_type].append(callback)
        logger.debug(f"Registered callback for event type: {event_type}")
    
    async def _process_queue(self):
        """Background task to process the queue"""
        logger.info("Started queue processor")
        
        while not self._stop_event.is_set():
            try:
                # Check for timed out tasks
                await self._check_timeouts()
                
                # Brief pause to prevent busy waiting
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(5)
        
        logger.info("Queue processor stopped")
    
    async def _monitor_queue(self):
        """Background task to monitor queue health and performance"""
        logger.info("Started queue monitor")
        
        while not self._stop_event.is_set():
            try:
                stats = await self.get_queue_stats()
                
                # Log periodic stats
                if stats["total_tasks"] > 0:
                    logger.info(
                        f"Queue stats: Total={stats['total_tasks']}, "
                        f"Pending={stats['pending_tasks']}, Running={stats['running_tasks']}, "
                        f"Completed={stats['completed_tasks']}, Failed={stats['failed_tasks']}, "
                        f"Throughput={stats['throughput_per_minute']:.1f}/min"
                    )
                
                # Check for potential issues
                if stats["pending_tasks"] > self.max_queue_size * 0.8:
                    logger.warning(f"Queue approaching capacity: {stats['queue_capacity_used']}")
                
                if stats["failed_tasks"] > stats["completed_tasks"] * 0.1:
                    logger.warning(f"High failure rate: {stats['failed_tasks']} failures vs {stats['completed_tasks']} completions")
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue monitor error: {e}")
                await asyncio.sleep(30)
        
        logger.info("Queue monitor stopped")
    
    async def _cleanup_old_tasks(self):
        """Background task to clean up old completed/failed tasks"""
        logger.info("Started task cleanup")
        
        while not self._stop_event.is_set():
            try:
                current_time = time.time()
                cleanup_threshold = current_time - (24 * 3600)  # 24 hours
                
                # Clean up old completed tasks
                old_completed = [
                    task_id for task_id, task in self.completed_tasks.items()
                    if task.completed_at and task.completed_at < cleanup_threshold
                ]
                
                for task_id in old_completed:
                    del self.completed_tasks[task_id]
                    del self.tasks[task_id]
                
                # Clean up old failed tasks
                old_failed = [
                    task_id for task_id, task in self.failed_tasks.items()
                    if task.completed_at and task.completed_at < cleanup_threshold
                ]
                
                for task_id in old_failed:
                    del self.failed_tasks[task_id]
                    del self.tasks[task_id]
                
                if old_completed or old_failed:
                    logger.info(f"Cleaned up {len(old_completed)} completed and {len(old_failed)} failed tasks")
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task cleanup error: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes
        
        logger.info("Task cleanup stopped")
    
    async def _check_timeouts(self):
        """Check for and handle timed out tasks"""
        current_time = time.time()
        timed_out_tasks = []
        
        for task_id, task in self.running_tasks.items():
            if (task.started_at and 
                current_time - task.started_at > task.timeout_seconds):
                timed_out_tasks.append(task_id)
        
        for task_id in timed_out_tasks:
            await self.fail_task(task_id, "Task timeout", retry=True)
            logger.warning(f"Task {task_id} timed out after {task.timeout_seconds} seconds")
    
    async def _update_stats_on_submit(self, task: Task):
        """Update statistics when a task is submitted"""
        async with self._stats_lock:
            self.stats.task_type_distribution[task.task_type.value] = \
                self.stats.task_type_distribution.get(task.task_type.value, 0) + 1
    
    async def _update_stats_on_complete(self, task: Task):
        """Update statistics when a task completes"""
        async with self._stats_lock:
            if task.assigned_model:
                if task.assigned_model not in self.stats.model_utilization:
                    self.stats.model_utilization[task.assigned_model] = {
                        "completed_tasks": 0,
                        "total_processing_time": 0,
                        "average_processing_time": 0
                    }
                
                model_stats = self.stats.model_utilization[task.assigned_model]
                model_stats["completed_tasks"] += 1
                
                processing_time = self._calculate_processing_time(task)
                if processing_time:
                    model_stats["total_processing_time"] += processing_time
                    model_stats["average_processing_time"] = \
                        model_stats["total_processing_time"] / model_stats["completed_tasks"]
    
    async def _update_stats_on_fail(self, task: Task):
        """Update statistics when a task fails"""
        # Could add failure-specific statistics here
        pass
    
    async def _trigger_callbacks(self, event_type: str, task: Task):
        """Trigger registered callbacks for an event"""
        callbacks = self.task_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                await callback(task)
            except Exception as e:
                logger.error(f"Callback error for event {event_type}: {e}")
    
    def _calculate_processing_time(self, task: Task) -> Optional[float]:
        """Calculate task processing time"""
        if task.started_at and task.completed_at:
            return task.completed_at - task.started_at
        return None
    
    def _calculate_wait_time(self, task: Task) -> Optional[float]:
        """Calculate task wait time"""
        if task.assigned_at:
            return task.assigned_at - task.created_at
        return None