"""
Memory Manager for EconCell AI System

Manages memory allocation, optimization, and cleanup for multiple LLM instances
and economic analysis workloads on high-memory systems.
"""

import asyncio
import logging
import time
import gc
import psutil
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict
import weakref

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    logging.warning("GPUtil not available - GPU memory monitoring disabled")

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory being managed"""
    SYSTEM_RAM = "system_ram"
    GPU_MEMORY = "gpu_memory"
    MODEL_WEIGHTS = "model_weights"
    INFERENCE_CACHE = "inference_cache"
    DATA_CACHE = "data_cache"
    TEMPORARY = "temporary"


class MemoryPriority(Enum):
    """Memory allocation priority levels"""
    CRITICAL = 0    # Essential system components
    HIGH = 1        # Active model inference
    MEDIUM = 2      # Cached data and intermediate results
    LOW = 3         # Background processes
    DISPOSABLE = 4  # Can be freed immediately under pressure


@dataclass
class MemoryAllocation:
    """Represents a memory allocation"""
    id: str
    memory_type: MemoryType
    size_bytes: int
    priority: MemoryPriority
    owner: str
    description: str
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    is_pinned: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_system_ram: int = 0
    available_system_ram: int = 0
    used_system_ram: int = 0
    total_gpu_memory: int = 0
    available_gpu_memory: int = 0
    used_gpu_memory: int = 0
    managed_allocations: int = 0
    total_managed_bytes: int = 0
    cache_hit_rate: float = 0.0
    gc_collections: int = 0
    last_cleanup_time: float = 0.0


class MemoryPool:
    """Memory pool for efficient allocation and reuse"""
    
    def __init__(self, memory_type: MemoryType, max_size_bytes: int):
        self.memory_type = memory_type
        self.max_size_bytes = max_size_bytes
        self.allocations: Dict[str, MemoryAllocation] = {}
        self.free_blocks: List[Tuple[int, int]] = []  # (start, size) pairs
        self.total_allocated = 0
        self._lock = threading.RLock()
    
    def allocate(self, size_bytes: int, owner: str, priority: MemoryPriority) -> Optional[str]:
        """Allocate memory from the pool"""
        with self._lock:
            if self.total_allocated + size_bytes > self.max_size_bytes:
                return None
            
            allocation_id = f"{owner}_{int(time.time())}_{len(self.allocations)}"
            allocation = MemoryAllocation(
                id=allocation_id,
                memory_type=self.memory_type,
                size_bytes=size_bytes,
                priority=priority,
                owner=owner,
                description=f"{self.memory_type.value} allocation for {owner}"
            )
            
            self.allocations[allocation_id] = allocation
            self.total_allocated += size_bytes
            
            return allocation_id
    
    def deallocate(self, allocation_id: str) -> bool:
        """Deallocate memory from the pool"""
        with self._lock:
            if allocation_id not in self.allocations:
                return False
            
            allocation = self.allocations[allocation_id]
            self.total_allocated -= allocation.size_bytes
            del self.allocations[allocation_id]
            
            return True
    
    def get_utilization(self) -> float:
        """Get current pool utilization ratio"""
        with self._lock:
            return self.total_allocated / self.max_size_bytes if self.max_size_bytes > 0 else 0.0


class MemoryManager:
    """
    Advanced memory management system for AI workloads
    
    Features:
    - Multi-tier memory management (RAM, GPU, storage)
    - Intelligent caching and eviction policies
    - Memory pressure detection and response
    - Garbage collection optimization
    - Resource pool management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory manager
        
        Args:
            config: Configuration dictionary for memory management
        """
        self.config = config or self._default_config()
        self.allocations: Dict[str, MemoryAllocation] = {}
        self.memory_pools: Dict[MemoryType, MemoryPool] = {}
        self.cache_storage: Dict[str, Any] = {}
        self.weak_refs: Dict[str, weakref.ref] = {}
        
        # Locks for thread safety
        self._allocation_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        self._stats_lock = threading.RLock()
        
        # Background task management
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Statistics tracking
        self.stats = MemoryStats()
        self._update_system_stats()
        
        # Initialize memory pools
        self._initialize_memory_pools()
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.gc_count = 0
        
        logger.info("MemoryManager initialized with total RAM: %.1f GB, GPU memory: %.1f GB", 
                   self.stats.total_system_ram / (1024**3),
                   self.stats.total_gpu_memory / (1024**3))
    
    def _default_config(self) -> Dict[str, Any]:
        """Default memory management configuration"""
        return {
            # Memory limits (in bytes)
            "max_system_ram_usage": int(160 * 1024**3),  # 160GB of 184GB total
            "max_gpu_memory_usage": int(60 * 1024**3),   # 60GB of 64GB GPU memory
            "model_cache_size": int(32 * 1024**3),       # 32GB for model caching
            "data_cache_size": int(16 * 1024**3),        # 16GB for data caching
            "temp_memory_size": int(8 * 1024**3),        # 8GB for temporary allocations
            
            # Thresholds for memory pressure response
            "ram_pressure_threshold": 0.85,              # 85% RAM usage triggers cleanup
            "gpu_pressure_threshold": 0.90,              # 90% GPU usage triggers cleanup
            "critical_memory_threshold": 0.95,           # 95% usage triggers aggressive cleanup
            
            # Cache management
            "cache_ttl_seconds": 3600,                   # 1 hour cache TTL
            "max_cache_entries": 10000,                  # Maximum cache entries
            "cache_cleanup_interval": 300,               # 5 minutes between cache cleanups
            
            # Garbage collection
            "gc_frequency": 60,                          # GC every 60 seconds
            "aggressive_gc_threshold": 0.80,             # Trigger aggressive GC at 80% memory
            
            # Monitoring
            "monitoring_interval": 30,                   # Monitor every 30 seconds
            "stats_update_interval": 10,                # Update stats every 10 seconds
        }
    
    async def start(self):
        """Start the memory manager background tasks"""
        if self._monitor_task is not None:
            logger.warning("MemoryManager already started")
            return
        
        logger.info("Starting MemoryManager background tasks")
        self._stop_event.clear()
        
        # Start background monitoring and cleanup tasks
        self._monitor_task = asyncio.create_task(self._memory_monitor())
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("MemoryManager started successfully")
    
    async def stop(self):
        """Stop the memory manager"""
        logger.info("Stopping MemoryManager")
        self._stop_event.set()
        
        # Cancel background tasks
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Wait for tasks to complete
        tasks_to_wait = [t for t in [self._monitor_task, self._cleanup_task] if t]
        if tasks_to_wait:
            await asyncio.gather(*tasks_to_wait, return_exceptions=True)
        
        # Cleanup all allocations
        await self.cleanup_all()
        
        logger.info("MemoryManager stopped")
    
    def allocate_memory(self, 
                       size_bytes: int,
                       memory_type: MemoryType,
                       owner: str,
                       priority: MemoryPriority = MemoryPriority.MEDIUM,
                       description: str = "",
                       pin_memory: bool = False,
                       metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Allocate memory with specified parameters
        
        Args:
            size_bytes: Size of memory to allocate
            memory_type: Type of memory (RAM, GPU, etc.)
            owner: Owner identifier
            priority: Allocation priority
            description: Human-readable description
            pin_memory: Whether to pin the memory (prevent swapping)
            metadata: Additional metadata
            
        Returns:
            Allocation ID or None if allocation failed
        """
        with self._allocation_lock:
            # Check if we have enough available memory
            if not self._check_memory_availability(size_bytes, memory_type):
                logger.warning(f"Insufficient {memory_type.value} memory for allocation: {size_bytes} bytes")
                return None
            
            # Try to use memory pool first
            if memory_type in self.memory_pools:
                pool_id = self.memory_pools[memory_type].allocate(size_bytes, owner, priority)
                if pool_id:
                    return pool_id
            
            # Create direct allocation
            allocation_id = f"{owner}_{memory_type.value}_{int(time.time())}_{len(self.allocations)}"
            
            allocation = MemoryAllocation(
                id=allocation_id,
                memory_type=memory_type,
                size_bytes=size_bytes,
                priority=priority,
                owner=owner,
                description=description or f"{memory_type.value} allocation",
                is_pinned=pin_memory,
                metadata=metadata or {}
            )
            
            self.allocations[allocation_id] = allocation
            
            # Update statistics
            with self._stats_lock:
                self.stats.managed_allocations += 1
                self.stats.total_managed_bytes += size_bytes
            
            logger.debug(f"Allocated {size_bytes} bytes of {memory_type.value} for {owner}")
            return allocation_id
    
    def deallocate_memory(self, allocation_id: str) -> bool:
        """
        Deallocate memory by allocation ID
        
        Args:
            allocation_id: ID of allocation to free
            
        Returns:
            True if successfully deallocated, False otherwise
        """
        with self._allocation_lock:
            # Try memory pools first
            for pool in self.memory_pools.values():
                if pool.deallocate(allocation_id):
                    return True
            
            # Direct allocation cleanup
            if allocation_id not in self.allocations:
                return False
            
            allocation = self.allocations[allocation_id]
            
            # Remove from cache if present
            with self._cache_lock:
                cache_keys_to_remove = [
                    key for key, value in self.cache_storage.items()
                    if hasattr(value, '_allocation_id') and value._allocation_id == allocation_id
                ]
                for key in cache_keys_to_remove:
                    del self.cache_storage[key]
            
            # Update statistics
            with self._stats_lock:
                self.stats.managed_allocations -= 1
                self.stats.total_managed_bytes -= allocation.size_bytes
            
            del self.allocations[allocation_id]
            
            logger.debug(f"Deallocated {allocation.size_bytes} bytes of {allocation.memory_type.value}")
            return True
    
    def cache_object(self, 
                    key: str, 
                    obj: Any, 
                    size_bytes: Optional[int] = None,
                    ttl_seconds: Optional[int] = None,
                    priority: MemoryPriority = MemoryPriority.MEDIUM) -> bool:
        """
        Cache an object in memory
        
        Args:
            key: Cache key
            obj: Object to cache
            size_bytes: Object size in bytes (estimated if not provided)
            ttl_seconds: Time to live (uses default if not provided)
            priority: Cache priority
            
        Returns:
            True if cached successfully, False otherwise
        """
        with self._cache_lock:
            # Check cache size limits
            if len(self.cache_storage) >= self.config["max_cache_entries"]:
                self._evict_cache_entries(1)
            
            # Estimate size if not provided
            if size_bytes is None:
                size_bytes = self._estimate_object_size(obj)
            
            # Allocate memory for cache entry
            allocation_id = self.allocate_memory(
                size_bytes=size_bytes,
                memory_type=MemoryType.DATA_CACHE,
                owner="cache_manager",
                priority=priority,
                description=f"Cache entry: {key}"
            )
            
            if not allocation_id:
                logger.warning(f"Failed to allocate memory for cache entry: {key}")
                return False
            
            # Create cache entry with metadata
            cache_entry = {
                'object': obj,
                'size_bytes': size_bytes,
                'cached_at': time.time(),
                'ttl_seconds': ttl_seconds or self.config["cache_ttl_seconds"],
                'access_count': 0,
                'last_accessed': time.time(),
                'priority': priority,
                '_allocation_id': allocation_id
            }
            
            self.cache_storage[key] = cache_entry
            
            logger.debug(f"Cached object with key: {key}, size: {size_bytes} bytes")
            return True
    
    def get_cached_object(self, key: str) -> Optional[Any]:
        """
        Retrieve an object from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached object or None if not found/expired
        """
        with self._cache_lock:
            if key not in self.cache_storage:
                self.cache_misses += 1
                return None
            
            entry = self.cache_storage[key]
            current_time = time.time()
            
            # Check if entry has expired
            if current_time - entry['cached_at'] > entry['ttl_seconds']:
                self._remove_cache_entry(key)
                self.cache_misses += 1
                return None
            
            # Update access statistics
            entry['access_count'] += 1
            entry['last_accessed'] = current_time
            
            # Update allocation access time
            if entry['_allocation_id'] in self.allocations:
                allocation = self.allocations[entry['_allocation_id']]
                allocation.last_accessed = current_time
                allocation.access_count += 1
            
            self.cache_hits += 1
            return entry['object']
    
    def remove_cached_object(self, key: str) -> bool:
        """Remove an object from cache"""
        with self._cache_lock:
            return self._remove_cache_entry(key)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        with self._stats_lock:
            self._update_system_stats()
            
            # Calculate cache hit rate
            total_cache_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = (self.cache_hits / total_cache_requests 
                            if total_cache_requests > 0 else 0.0)
            
            # Memory pool statistics
            pool_stats = {}
            for memory_type, pool in self.memory_pools.items():
                pool_stats[memory_type.value] = {
                    "max_size_bytes": pool.max_size_bytes,
                    "allocated_bytes": pool.total_allocated,
                    "utilization": pool.get_utilization(),
                    "allocation_count": len(pool.allocations)
                }
            
            return {
                "system_memory": {
                    "total_bytes": self.stats.total_system_ram,
                    "available_bytes": self.stats.available_system_ram,
                    "used_bytes": self.stats.used_system_ram,
                    "utilization": self.stats.used_system_ram / self.stats.total_system_ram
                },
                "gpu_memory": {
                    "total_bytes": self.stats.total_gpu_memory,
                    "available_bytes": self.stats.available_gpu_memory,
                    "used_bytes": self.stats.used_gpu_memory,
                    "utilization": (self.stats.used_gpu_memory / self.stats.total_gpu_memory 
                                  if self.stats.total_gpu_memory > 0 else 0.0)
                },
                "managed_memory": {
                    "allocations": self.stats.managed_allocations,
                    "total_bytes": self.stats.total_managed_bytes,
                    "average_allocation_size": (self.stats.total_managed_bytes / self.stats.managed_allocations
                                              if self.stats.managed_allocations > 0 else 0)
                },
                "cache": {
                    "entries": len(self.cache_storage),
                    "hit_rate": cache_hit_rate,
                    "hits": self.cache_hits,
                    "misses": self.cache_misses
                },
                "memory_pools": pool_stats,
                "garbage_collection": {
                    "collections": self.gc_count,
                    "last_cleanup": self.stats.last_cleanup_time
                }
            }
    
    async def force_cleanup(self, aggressive: bool = False) -> Dict[str, int]:
        """
        Force memory cleanup
        
        Args:
            aggressive: Whether to perform aggressive cleanup
            
        Returns:
            Dictionary with cleanup statistics
        """
        logger.info(f"Starting {'aggressive' if aggressive else 'normal'} memory cleanup")
        
        cleanup_stats = {
            "cache_entries_removed": 0,
            "allocations_freed": 0,
            "bytes_freed": 0,
            "gc_collections": 0
        }
        
        # Cache cleanup
        if aggressive:
            # Remove all non-pinned, low-priority cache entries
            removed_entries = await self._aggressive_cache_cleanup()
        else:
            # Remove expired and least recently used entries
            removed_entries = await self._normal_cache_cleanup()
        
        cleanup_stats["cache_entries_removed"] = removed_entries
        
        # Memory allocation cleanup
        freed_allocations, freed_bytes = await self._cleanup_unused_allocations(aggressive)
        cleanup_stats["allocations_freed"] = freed_allocations
        cleanup_stats["bytes_freed"] = freed_bytes
        
        # Garbage collection
        if aggressive:
            for i in range(3):  # Multiple GC passes for aggressive cleanup
                collected = gc.collect()
                cleanup_stats["gc_collections"] += collected
                self.gc_count += 1
        else:
            collected = gc.collect()
            cleanup_stats["gc_collections"] = collected
            self.gc_count += 1
        
        with self._stats_lock:
            self.stats.last_cleanup_time = time.time()
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    async def cleanup_all(self):
        """Cleanup all managed memory"""
        logger.info("Cleaning up all managed memory")
        
        # Clear all caches
        with self._cache_lock:
            cache_keys = list(self.cache_storage.keys())
            for key in cache_keys:
                self._remove_cache_entry(key)
        
        # Free all allocations
        with self._allocation_lock:
            allocation_ids = list(self.allocations.keys())
            for allocation_id in allocation_ids:
                self.deallocate_memory(allocation_id)
            
            # Clear memory pools
            for pool in self.memory_pools.values():
                pool.allocations.clear()
                pool.total_allocated = 0
        
        # Final garbage collection
        gc.collect()
        
        logger.info("All managed memory cleaned up")
    
    def _initialize_memory_pools(self):
        """Initialize memory pools for different types"""
        self.memory_pools[MemoryType.MODEL_WEIGHTS] = MemoryPool(
            MemoryType.MODEL_WEIGHTS,
            self.config["model_cache_size"]
        )
        
        self.memory_pools[MemoryType.DATA_CACHE] = MemoryPool(
            MemoryType.DATA_CACHE,
            self.config["data_cache_size"]
        )
        
        self.memory_pools[MemoryType.TEMPORARY] = MemoryPool(
            MemoryType.TEMPORARY,
            self.config["temp_memory_size"]
        )
    
    def _update_system_stats(self):
        """Update system memory statistics"""
        # System RAM statistics
        memory_info = psutil.virtual_memory()
        self.stats.total_system_ram = memory_info.total
        self.stats.available_system_ram = memory_info.available
        self.stats.used_system_ram = memory_info.used
        
        # GPU memory statistics
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    self.stats.total_gpu_memory = int(gpu.memoryTotal * 1024 * 1024)  # Convert MB to bytes
                    self.stats.used_gpu_memory = int(gpu.memoryUsed * 1024 * 1024)
                    self.stats.available_gpu_memory = self.stats.total_gpu_memory - self.stats.used_gpu_memory
            except Exception as e:
                logger.warning(f"Failed to get GPU memory stats: {e}")
    
    def _check_memory_availability(self, size_bytes: int, memory_type: MemoryType) -> bool:
        """Check if requested memory is available"""
        self._update_system_stats()
        
        if memory_type == MemoryType.SYSTEM_RAM:
            return self.stats.available_system_ram >= size_bytes
        elif memory_type == MemoryType.GPU_MEMORY:
            return self.stats.available_gpu_memory >= size_bytes
        else:
            # For managed memory types, check against pool limits
            if memory_type in self.memory_pools:
                pool = self.memory_pools[memory_type]
                return (pool.max_size_bytes - pool.total_allocated) >= size_bytes
            return True
    
    def _estimate_object_size(self, obj: Any) -> int:
        """Estimate the size of an object in bytes"""
        try:
            import sys
            return sys.getsizeof(obj)
        except:
            # Fallback estimation based on object type
            if isinstance(obj, str):
                return len(obj.encode('utf-8'))
            elif isinstance(obj, (list, tuple)):
                return sum(self._estimate_object_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sum(self._estimate_object_size(k) + self._estimate_object_size(v) 
                          for k, v in obj.items())
            else:
                return 1024  # Default 1KB estimate
    
    def _remove_cache_entry(self, key: str) -> bool:
        """Remove a cache entry and its associated memory allocation"""
        if key not in self.cache_storage:
            return False
        
        entry = self.cache_storage[key]
        
        # Deallocate associated memory
        if '_allocation_id' in entry:
            self.deallocate_memory(entry['_allocation_id'])
        
        del self.cache_storage[key]
        return True
    
    def _evict_cache_entries(self, count: int) -> int:
        """Evict least recently used cache entries"""
        if not self.cache_storage:
            return 0
        
        # Sort by last accessed time (oldest first)
        entries = list(self.cache_storage.items())
        entries.sort(key=lambda x: x[1]['last_accessed'])
        
        evicted = 0
        for key, entry in entries[:count]:
            if not entry.get('is_pinned', False):  # Don't evict pinned entries
                self._remove_cache_entry(key)
                evicted += 1
        
        return evicted
    
    async def _memory_monitor(self):
        """Background task to monitor memory usage"""
        logger.info("Started memory monitor")
        
        while not self._stop_event.is_set():
            try:
                self._update_system_stats()
                
                # Check for memory pressure
                ram_utilization = self.stats.used_system_ram / self.stats.total_system_ram
                gpu_utilization = (self.stats.used_gpu_memory / self.stats.total_gpu_memory 
                                 if self.stats.total_gpu_memory > 0 else 0.0)
                
                # Handle memory pressure
                if ram_utilization > self.config["critical_memory_threshold"]:
                    logger.warning("Critical RAM pressure detected - forcing aggressive cleanup")
                    await self.force_cleanup(aggressive=True)
                elif ram_utilization > self.config["ram_pressure_threshold"]:
                    logger.info("RAM pressure detected - performing cleanup")
                    await self.force_cleanup(aggressive=False)
                
                if gpu_utilization > self.config["gpu_pressure_threshold"]:
                    logger.warning("GPU memory pressure detected")
                    # GPU-specific cleanup could be implemented here
                
                # Log memory statistics periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    stats = self.get_memory_stats()
                    logger.info(
                        f"Memory stats - RAM: {ram_utilization:.1%}, "
                        f"GPU: {gpu_utilization:.1%}, "
                        f"Managed: {stats['managed_memory']['allocations']} allocations, "
                        f"Cache: {stats['cache']['entries']} entries ({stats['cache']['hit_rate']:.1%} hits)"
                    )
                
                await asyncio.sleep(self.config["monitoring_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                await asyncio.sleep(30)
        
        logger.info("Memory monitor stopped")
    
    async def _periodic_cleanup(self):
        """Background task for periodic cleanup"""
        logger.info("Started periodic cleanup task")
        
        while not self._stop_event.is_set():
            try:
                await self._normal_cache_cleanup()
                
                # Periodic garbage collection
                if int(time.time()) % self.config["gc_frequency"] == 0:
                    collected = gc.collect()
                    if collected > 0:
                        logger.debug(f"Garbage collection freed {collected} objects")
                    self.gc_count += 1
                
                await asyncio.sleep(self.config["cache_cleanup_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic cleanup error: {e}")
                await asyncio.sleep(60)
        
        logger.info("Periodic cleanup stopped")
    
    async def _normal_cache_cleanup(self) -> int:
        """Normal cache cleanup - remove expired entries"""
        removed_count = 0
        current_time = time.time()
        
        with self._cache_lock:
            expired_keys = []
            for key, entry in self.cache_storage.items():
                if current_time - entry['cached_at'] > entry['ttl_seconds']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                if self._remove_cache_entry(key):
                    removed_count += 1
        
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} expired cache entries")
        
        return removed_count
    
    async def _aggressive_cache_cleanup(self) -> int:
        """Aggressive cache cleanup - remove low priority and old entries"""
        removed_count = 0
        
        with self._cache_lock:
            # Remove all low priority entries
            low_priority_keys = [
                key for key, entry in self.cache_storage.items()
                if entry['priority'] in [MemoryPriority.LOW, MemoryPriority.DISPOSABLE]
            ]
            
            for key in low_priority_keys:
                if self._remove_cache_entry(key):
                    removed_count += 1
            
            # Remove oldest entries if still over limit
            if len(self.cache_storage) > self.config["max_cache_entries"] / 2:
                additional_removed = self._evict_cache_entries(
                    len(self.cache_storage) - self.config["max_cache_entries"] // 2
                )
                removed_count += additional_removed
        
        if removed_count > 0:
            logger.info(f"Aggressive cleanup removed {removed_count} cache entries")
        
        return removed_count
    
    async def _cleanup_unused_allocations(self, aggressive: bool) -> Tuple[int, int]:
        """Cleanup unused memory allocations"""
        freed_allocations = 0
        freed_bytes = 0
        current_time = time.time()
        
        with self._allocation_lock:
            allocations_to_free = []
            
            for allocation_id, allocation in self.allocations.items():
                # Skip pinned allocations unless aggressive cleanup
                if allocation.is_pinned and not aggressive:
                    continue
                
                # Free unused temporary allocations
                if allocation.memory_type == MemoryType.TEMPORARY:
                    if current_time - allocation.last_accessed > 300:  # 5 minutes
                        allocations_to_free.append(allocation_id)
                
                # Free low priority allocations that haven't been accessed
                elif (allocation.priority in [MemoryPriority.LOW, MemoryPriority.DISPOSABLE] and
                      current_time - allocation.last_accessed > 1800):  # 30 minutes
                    allocations_to_free.append(allocation_id)
            
            for allocation_id in allocations_to_free:
                allocation = self.allocations[allocation_id]
                if self.deallocate_memory(allocation_id):
                    freed_allocations += 1
                    freed_bytes += allocation.size_bytes
        
        if freed_allocations > 0:
            logger.debug(f"Freed {freed_allocations} allocations ({freed_bytes} bytes)")
        
        return freed_allocations, freed_bytes