"""
LLM-Powered Data Enrichment Pipeline for EconCell

Enhances raw economic data with AI-generated metadata, classifications,
and contextual information using the EconCell AI system.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
from itemadapter import ItemAdapter

# Import AI system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.ai import AICoordinator, AnalysisType, AnalysisRequest, TaskPriority

logger = logging.getLogger(__name__)


class LLMEnrichmentPipeline:
    """
    Pipeline for enriching economic data using LLM analysis
    
    Features:
    - Automatic data categorization and tagging
    - Economic indicator relationship detection
    - Context-aware metadata generation
    - Data quality assessment
    - Anomaly flagging
    - Trend analysis and insights
    """
    
    def __init__(self):
        self.ai_coordinator: Optional[AICoordinator] = None
        self.enrichment_cache: Dict[str, Any] = {}
        self.processing_stats = {
            "items_processed": 0,
            "items_enriched": 0,
            "enrichment_failures": 0,
            "cache_hits": 0,
            "average_processing_time": 0.0
        }
        
        # Configuration
        self.config = {
            "enable_caching": True,
            "cache_ttl_hours": 24,
            "batch_processing": True,
            "batch_size": 10,
            "enrichment_timeout": 30,
            "min_data_size_for_enrichment": 100,  # Minimum data size in characters
            "enable_async_processing": True
        }
        
        # Enrichment categories
        self.enrichment_categories = [
            "economic_indicators",
            "policy_relevance", 
            "data_quality",
            "trend_analysis",
            "anomaly_detection",
            "relationship_mapping",
            "australian_context"
        ]
        
        logger.info("LLMEnrichmentPipeline initialized")
    
    def open_spider(self, spider):
        """Initialize the pipeline when spider starts"""
        try:
            # Initialize AI Coordinator
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', '..', '..', 'config', 'ai_config.json'
            )
            
            self.ai_coordinator = AICoordinator(config_path)
            
            # Start AI system in background
            asyncio.create_task(self._start_ai_system())
            
            logger.info("LLMEnrichmentPipeline opened successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLMEnrichmentPipeline: {e}")
            # Continue without AI enrichment if initialization fails
            self.ai_coordinator = None
    
    def close_spider(self, spider):
        """Cleanup when spider closes"""
        try:
            if self.ai_coordinator:
                # Stop AI system
                asyncio.create_task(self._stop_ai_system())
            
            # Log final statistics
            logger.info(f"LLMEnrichmentPipeline stats: {self.processing_stats}")
            
        except Exception as e:
            logger.error(f"Error closing LLMEnrichmentPipeline: {e}")
    
    def process_item(self, item, spider):
        """Process individual items with LLM enrichment"""
        start_time = time.time()
        
        try:
            adapter = ItemAdapter(item)
            
            # Skip enrichment if AI system not available
            if not self.ai_coordinator:
                logger.debug("AI system not available - skipping enrichment")
                return item
            
            # Determine if item should be enriched
            if not self._should_enrich_item(adapter):
                return item
            
            # Generate cache key
            cache_key = self._generate_cache_key(adapter)
            
            # Check cache first
            if self.config["enable_caching"] and cache_key in self.enrichment_cache:
                cached_data = self.enrichment_cache[cache_key]
                if self._is_cache_valid(cached_data):
                    self._apply_cached_enrichment(adapter, cached_data)
                    self.processing_stats["cache_hits"] += 1
                    logger.debug(f"Applied cached enrichment for item")
                    return item
            
            # Perform LLM enrichment
            enrichment_data = self._enrich_item_sync(adapter, spider)
            
            if enrichment_data:
                # Apply enrichment to item
                self._apply_enrichment(adapter, enrichment_data)
                
                # Cache the enrichment
                if self.config["enable_caching"]:
                    self.enrichment_cache[cache_key] = {
                        "data": enrichment_data,
                        "timestamp": time.time()
                    }
                
                self.processing_stats["items_enriched"] += 1
                logger.debug(f"Successfully enriched item with categories: {list(enrichment_data.keys())}")
            else:
                self.processing_stats["enrichment_failures"] += 1
                logger.warning("Failed to enrich item - no enrichment data returned")
            
            # Update processing statistics
            processing_time = time.time() - start_time
            self._update_processing_stats(processing_time)
            
            return item
            
        except Exception as e:
            logger.error(f"Error in LLM enrichment pipeline: {e}")
            self.processing_stats["enrichment_failures"] += 1
            return item
    
    async def _start_ai_system(self):
        """Start the AI coordination system"""
        try:
            if self.ai_coordinator:
                await self.ai_coordinator.start()
                logger.info("AI system started for data enrichment")
        except Exception as e:
            logger.error(f"Failed to start AI system: {e}")
    
    async def _stop_ai_system(self):
        """Stop the AI coordination system"""
        try:
            if self.ai_coordinator:
                await self.ai_coordinator.stop()
                logger.info("AI system stopped")
        except Exception as e:
            logger.error(f"Error stopping AI system: {e}")
    
    def _should_enrich_item(self, adapter: ItemAdapter) -> bool:
        """Determine if an item should be enriched"""
        # Check if item has sufficient data
        content_fields = ['description', 'content', 'text', 'data']
        total_content_length = 0
        
        for field in content_fields:
            if field in adapter:
                value = adapter.get(field, '')
                if isinstance(value, str):
                    total_content_length += len(value)
        
        if total_content_length < self.config["min_data_size_for_enrichment"]:
            return False
        
        # Check if item is economic data
        economic_indicators = [
            'gdp', 'inflation', 'unemployment', 'interest', 'exchange',
            'trade', 'export', 'import', 'monetary', 'fiscal', 'policy',
            'rba', 'reserve', 'bank', 'economy', 'economic'
        ]
        
        item_text = str(adapter._item).lower()
        return any(indicator in item_text for indicator in economic_indicators)
    
    def _generate_cache_key(self, adapter: ItemAdapter) -> str:
        """Generate cache key for an item"""
        import hashlib
        
        # Create hash from key item fields
        key_fields = ['url', 'title', 'description', 'timestamp']
        key_data = []
        
        for field in key_fields:
            if field in adapter:
                key_data.append(str(adapter[field]))
        
        key_string = '|'.join(key_data)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached enrichment data is still valid"""
        if not self.config["enable_caching"]:
            return False
        
        cache_age_hours = (time.time() - cached_data["timestamp"]) / 3600
        return cache_age_hours < self.config["cache_ttl_hours"]
    
    def _enrich_item_sync(self, adapter: ItemAdapter, spider) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for item enrichment"""
        try:
            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run enrichment asynchronously
            if loop.is_running():
                # If loop is already running, we need to handle this differently
                # For now, skip async enrichment in running loop context
                logger.debug("Event loop already running - skipping async enrichment")
                return None
            else:
                return loop.run_until_complete(self._enrich_item_async(adapter, spider))
                
        except Exception as e:
            logger.error(f"Error in synchronous enrichment wrapper: {e}")
            return None
    
    async def _enrich_item_async(self, adapter: ItemAdapter, spider) -> Optional[Dict[str, Any]]:
        """Asynchronously enrich an item using AI analysis"""
        try:
            if not self.ai_coordinator:
                return None
            
            # Prepare enrichment content
            enrichment_content = self._prepare_enrichment_content(adapter)
            
            # Create analysis request
            request = AnalysisRequest(
                analysis_type=AnalysisType.DATA_ANALYSIS,
                content=enrichment_content,
                context={
                    "enrichment_categories": self.enrichment_categories,
                    "data_source": getattr(spider, 'name', 'unknown'),
                    "processing_timestamp": time.time()
                },
                priority=TaskPriority.LOW,  # Data enrichment is lower priority
                verification_required=False,
                timeout_seconds=self.config["enrichment_timeout"]
            )
            
            # Submit analysis
            task_id = await self.ai_coordinator.submit_analysis(request)
            
            # Wait for completion (with timeout)
            max_wait_time = self.config["enrichment_timeout"]
            wait_interval = 1.0
            elapsed_time = 0.0
            
            while elapsed_time < max_wait_time:
                status = await self.ai_coordinator.get_analysis_status(task_id)
                
                if status and status["status"] == "completed":
                    result = status.get("result")
                    if result:
                        return self._parse_enrichment_result(result)
                    break
                elif status and status["status"] in ["failed", "timeout"]:
                    logger.warning(f"Enrichment analysis failed: {status.get('error', 'Unknown error')}")
                    break
                
                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval
            
            # Cancel task if still running
            await self.ai_coordinator.cancel_analysis(task_id)
            logger.warning(f"Enrichment analysis timed out after {max_wait_time} seconds")
            return None
            
        except Exception as e:
            logger.error(f"Error in async item enrichment: {e}")
            return None
    
    def _prepare_enrichment_content(self, adapter: ItemAdapter) -> str:
        """Prepare content for LLM enrichment analysis"""
        item_data = {}
        
        # Extract key fields
        key_fields = [
            'title', 'description', 'content', 'text', 'data',
            'url', 'source', 'timestamp', 'category', 'tags'
        ]
        
        for field in key_fields:
            if field in adapter:
                value = adapter[field]
                if value is not None:
                    item_data[field] = str(value)[:1000]  # Limit field length
        
        # Create enrichment prompt
        content = f"""
        Economic Data Enrichment Analysis
        
        Please analyze the following economic data item and provide structured enrichment information:
        
        Data Item:
        {json.dumps(item_data, indent=2)}
        
        Required Enrichment Categories:
        
        1. Economic Indicators:
           - Identify key economic indicators mentioned
           - Classify indicator types (monetary, fiscal, trade, etc.)
           - Assess data relevance to Australian economy
        
        2. Policy Relevance:
           - Identify policy implications
           - Assess relevance to RBA monetary policy
           - Note fiscal policy connections
        
        3. Data Quality:
           - Assess completeness and reliability
           - Identify potential data issues
           - Rate data quality (1-10 scale)
        
        4. Trend Analysis:
           - Identify trend patterns if apparent
           - Note seasonal considerations
           - Highlight significant changes
        
        5. Anomaly Detection:
           - Flag unusual values or patterns
           - Note data inconsistencies
           - Assess need for verification
        
        6. Relationship Mapping:
           - Identify relationships to other economic indicators
           - Map to RBA circular flow components
           - Note cross-sector impacts
        
        7. Australian Context:
           - Assess relevance to Australian economic conditions
           - Identify region-specific factors
           - Note international implications
        
        Please provide response as structured JSON with each category as a key.
        """
        
        return content
    
    def _parse_enrichment_result(self, result: Any) -> Optional[Dict[str, Any]]:
        """Parse LLM enrichment result into structured format"""
        try:
            if isinstance(result, str):
                # Try to parse JSON from string result
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    return json.loads(json_str)
                else:
                    # Create structured result from text
                    return {"analysis": result, "format": "text"}
            elif isinstance(result, dict):
                return result
            else:
                return {"raw_result": str(result)}
                
        except Exception as e:
            logger.error(f"Error parsing enrichment result: {e}")
            return {"error": str(e), "raw_result": str(result)}
    
    def _apply_enrichment(self, adapter: ItemAdapter, enrichment_data: Dict[str, Any]):
        """Apply enrichment data to the item"""
        try:
            # Add enrichment metadata
            adapter["llm_enrichment"] = enrichment_data
            adapter["enrichment_timestamp"] = datetime.now().isoformat()
            adapter["enrichment_version"] = "1.0"
            
            # Extract and apply specific enrichments
            if "economic_indicators" in enrichment_data:
                indicators = enrichment_data["economic_indicators"]
                if isinstance(indicators, dict):
                    adapter["economic_indicators"] = indicators.get("indicators", [])
                    adapter["indicator_types"] = indicators.get("types", [])
            
            if "policy_relevance" in enrichment_data:
                policy_data = enrichment_data["policy_relevance"]
                if isinstance(policy_data, dict):
                    adapter["policy_implications"] = policy_data.get("implications", [])
                    adapter["rba_relevance"] = policy_data.get("rba_relevance", "unknown")
            
            if "data_quality" in enrichment_data:
                quality_data = enrichment_data["data_quality"]
                if isinstance(quality_data, dict):
                    adapter["data_quality_score"] = quality_data.get("score", 5)
                    adapter["data_quality_issues"] = quality_data.get("issues", [])
            
            if "anomaly_detection" in enrichment_data:
                anomaly_data = enrichment_data["anomaly_detection"]
                if isinstance(anomaly_data, dict):
                    adapter["anomalies_detected"] = anomaly_data.get("anomalies", [])
                    adapter["anomaly_flags"] = anomaly_data.get("flags", [])
            
            if "australian_context" in enrichment_data:
                context_data = enrichment_data["australian_context"]
                if isinstance(context_data, dict):
                    adapter["australian_relevance"] = context_data.get("relevance", "unknown")
                    adapter["regional_factors"] = context_data.get("factors", [])
            
            logger.debug("Applied enrichment data to item")
            
        except Exception as e:
            logger.error(f"Error applying enrichment to item: {e}")
    
    def _apply_cached_enrichment(self, adapter: ItemAdapter, cached_data: Dict[str, Any]):
        """Apply cached enrichment data to item"""
        try:
            enrichment_data = cached_data["data"]
            self._apply_enrichment(adapter, enrichment_data)
            
            # Mark as cached
            adapter["enrichment_cached"] = True
            adapter["enrichment_cache_timestamp"] = cached_data["timestamp"]
            
        except Exception as e:
            logger.error(f"Error applying cached enrichment: {e}")
    
    def _update_processing_stats(self, processing_time: float):
        """Update processing statistics"""
        self.processing_stats["items_processed"] += 1
        
        # Update average processing time
        total_items = self.processing_stats["items_processed"]
        current_avg = self.processing_stats["average_processing_time"]
        
        self.processing_stats["average_processing_time"] = (
            (current_avg * (total_items - 1) + processing_time) / total_items
        )
        
        # Log statistics periodically
        if total_items % 100 == 0:
            logger.info(f"LLM enrichment stats: {self.processing_stats}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        stats = self.processing_stats.copy()
        
        if stats["items_processed"] > 0:
            stats["enrichment_success_rate"] = (
                stats["items_enriched"] / stats["items_processed"]
            )
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / stats["items_processed"]
            )
        else:
            stats["enrichment_success_rate"] = 0.0
            stats["cache_hit_rate"] = 0.0
        
        return stats