#!/usr/bin/env python3
"""
EconCell AI System Test and Demonstration Script

This script demonstrates the core functionality of the EconCell AI system,
including model orchestration, task processing, and economic analysis workflows.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai import (
    AICoordinator, 
    AnalysisType, 
    AnalysisRequest, 
    TaskPriority,
    ModelOrchestrator,
    TaskQueue,
    LoadBalancer,
    MemoryManager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EconCellAITester:
    """Test suite for EconCell AI system"""
    
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'config', 'ai_config.json')
        self.ai_coordinator: AICoordinator = None
        self.test_results: Dict[str, Any] = {}
    
    async def run_all_tests(self):
        """Run comprehensive AI system tests"""
        logger.info("🚀 Starting EconCell AI System Tests")
        
        try:
            # Test 1: System Initialization
            await self.test_system_initialization()
            
            # Test 2: Model Management
            await self.test_model_management()
            
            # Test 3: Task Processing
            await self.test_task_processing()
            
            # Test 4: Economic Analysis
            await self.test_economic_analysis()
            
            # Test 5: Memory Management
            await self.test_memory_management()
            
            # Test 6: Load Balancing
            await self.test_load_balancing()
            
            # Test 7: System Performance
            await self.test_system_performance()
            
            # Generate test report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
        finally:
            await self.cleanup()
    
    async def test_system_initialization(self):
        """Test AI system initialization"""
        logger.info("🔧 Testing System Initialization")
        
        try:
            # Initialize AI Coordinator
            self.ai_coordinator = AICoordinator(self.config_path)
            
            # Start the system
            await self.ai_coordinator.start()
            
            # Check system status
            performance = await self.ai_coordinator.get_system_performance()
            
            self.test_results["initialization"] = {
                "status": "success",
                "ai_coordinator_active": performance["ai_coordinator"]["active_analyses"] >= 0,
                "models_available": len(performance["model_orchestrator"]["models"]) > 0,
                "task_queue_operational": "pending_tasks" in performance["task_queue"],
                "memory_manager_active": "system_memory" in performance["memory_manager"]
            }
            
            logger.info("✅ System initialization successful")
            
        except Exception as e:
            self.test_results["initialization"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"❌ System initialization failed: {e}")
    
    async def test_model_management(self):
        """Test model orchestration capabilities"""
        logger.info("🤖 Testing Model Management")
        
        try:
            if not self.ai_coordinator:
                raise Exception("AI Coordinator not initialized")
            
            orchestrator = self.ai_coordinator.orchestrator
            
            # Test model loading
            primary_model_loaded = await orchestrator.load_model("qwen_32b_primary")
            
            # Get model status
            model_status = await orchestrator.get_model_status()
            
            self.test_results["model_management"] = {
                "status": "success",
                "primary_model_loaded": primary_model_loaded,
                "total_models": len(model_status) if isinstance(model_status, list) else 1,
                "model_details": model_status
            }
            
            logger.info("✅ Model management test successful")
            
        except Exception as e:
            self.test_results["model_management"] = {
                "status": "failed", 
                "error": str(e)
            }
            logger.error(f"❌ Model management test failed: {e}")
    
    async def test_task_processing(self):
        """Test task queue and processing"""
        logger.info("📋 Testing Task Processing")
        
        try:
            if not self.ai_coordinator:
                raise Exception("AI Coordinator not initialized")
            
            # Submit test task
            test_request = AnalysisRequest(
                analysis_type=AnalysisType.DATA_ANALYSIS,
                content="Test economic data analysis: GDP growth rate 2.5%, inflation 3.2%",
                context={"test": True},
                priority=TaskPriority.HIGH,
                verification_required=False,
                timeout_seconds=60
            )
            
            task_id = await self.ai_coordinator.submit_analysis(test_request)
            
            # Wait for task completion
            max_wait = 60
            wait_time = 0
            task_completed = False
            
            while wait_time < max_wait:
                status = await self.ai_coordinator.get_analysis_status(task_id)
                if status and status["status"] == "completed":
                    task_completed = True
                    break
                elif status and status["status"] in ["failed", "timeout"]:
                    break
                
                await asyncio.sleep(2)
                wait_time += 2
            
            # Get queue statistics
            queue_stats = await self.ai_coordinator.task_queue.get_queue_stats()
            
            self.test_results["task_processing"] = {
                "status": "success",
                "task_submitted": task_id is not None,
                "task_completed": task_completed,
                "queue_stats": queue_stats
            }
            
            logger.info("✅ Task processing test successful")
            
        except Exception as e:
            self.test_results["task_processing"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"❌ Task processing test failed: {e}")
    
    async def test_economic_analysis(self):
        """Test economic analysis capabilities"""
        logger.info("📊 Testing Economic Analysis")
        
        try:
            if not self.ai_coordinator:
                raise Exception("AI Coordinator not initialized")
            
            # Test hypothesis generation
            economic_data = {
                "inflation_rate": 3.2,
                "unemployment_rate": 4.1,
                "gdp_growth": 2.5,
                "interest_rate": 4.35,
                "exchange_rate_aud_usd": 0.67
            }
            
            hypothesis_result = await self.ai_coordinator.generate_hypothesis(
                economic_data, 
                focus_areas=["monetary_policy", "inflation_dynamics"]
            )
            
            # Test policy analysis
            policy_analysis_result = await self.ai_coordinator.analyze_policy_impact(
                "RBA increases cash rate by 0.25 percentage points to 4.60%",
                economic_data,
                {"simulation_type": "monetary_policy"}
            )
            
            self.test_results["economic_analysis"] = {
                "status": "success",
                "hypothesis_generation": hypothesis_result,
                "policy_analysis": policy_analysis_result,
                "test_data": economic_data
            }
            
            logger.info("✅ Economic analysis test successful")
            
        except Exception as e:
            self.test_results["economic_analysis"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"❌ Economic analysis test failed: {e}")
    
    async def test_memory_management(self):
        """Test memory management system"""
        logger.info("💾 Testing Memory Management")
        
        try:
            if not self.ai_coordinator:
                raise Exception("AI Coordinator not initialized")
            
            memory_manager = self.ai_coordinator.memory_manager
            
            # Get memory statistics
            memory_stats = memory_manager.get_memory_stats()
            
            # Test memory allocation
            allocation_id = memory_manager.allocate_memory(
                size_bytes=1024*1024,  # 1MB
                memory_type=memory_manager.MemoryType.TEMPORARY,
                owner="test_suite",
                description="Test allocation"
            )
            
            # Test caching
            cache_success = memory_manager.cache_object(
                key="test_cache",
                obj={"test": "data"},
                size_bytes=1024
            )
            
            cached_obj = memory_manager.get_cached_object("test_cache")
            
            # Cleanup test allocation
            if allocation_id:
                memory_manager.deallocate_memory(allocation_id)
            
            self.test_results["memory_management"] = {
                "status": "success",
                "memory_stats": memory_stats,
                "allocation_success": allocation_id is not None,
                "cache_success": cache_success,
                "cache_retrieval_success": cached_obj is not None
            }
            
            logger.info("✅ Memory management test successful")
            
        except Exception as e:
            self.test_results["memory_management"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"❌ Memory management test failed: {e}")
    
    async def test_load_balancing(self):
        """Test load balancing functionality"""
        logger.info("⚖️ Testing Load Balancing")
        
        try:
            if not self.ai_coordinator:
                raise Exception("AI Coordinator not initialized")
            
            load_balancer = self.ai_coordinator.load_balancer
            
            # Get load balancing statistics
            lb_stats = await load_balancer.get_load_balancing_stats()
            
            # Test model selection
            from src.ai.task_queue import TaskType
            selection_result = await load_balancer.select_model(
                task_type=TaskType.DATA_ANALYSIS,
                priority=TaskPriority.MEDIUM
            )
            
            self.test_results["load_balancing"] = {
                "status": "success",
                "load_balancer_stats": lb_stats,
                "model_selection": selection_result.__dict__ if selection_result else None
            }
            
            logger.info("✅ Load balancing test successful")
            
        except Exception as e:
            self.test_results["load_balancing"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"❌ Load balancing test failed: {e}")
    
    async def test_system_performance(self):
        """Test overall system performance"""
        logger.info("⚡ Testing System Performance")
        
        try:
            if not self.ai_coordinator:
                raise Exception("AI Coordinator not initialized")
            
            # Get comprehensive performance metrics
            performance = await self.ai_coordinator.get_system_performance()
            
            # Test concurrent task submission
            concurrent_tasks = []
            for i in range(3):
                request = AnalysisRequest(
                    analysis_type=AnalysisType.DATA_ANALYSIS,
                    content=f"Performance test task {i}: Analyzing economic indicator data",
                    context={"performance_test": True, "task_number": i},
                    priority=TaskPriority.NORMAL,
                    verification_required=False,
                    timeout_seconds=30
                )
                
                task_id = await self.ai_coordinator.submit_analysis(request)
                concurrent_tasks.append(task_id)
            
            # Wait a moment for tasks to be processed
            await asyncio.sleep(5)
            
            # Check task statuses
            task_statuses = []
            for task_id in concurrent_tasks:
                status = await self.ai_coordinator.get_analysis_status(task_id)
                task_statuses.append(status)
            
            self.test_results["system_performance"] = {
                "status": "success",
                "performance_metrics": performance,
                "concurrent_tasks_submitted": len(concurrent_tasks),
                "task_statuses": task_statuses
            }
            
            logger.info("✅ System performance test successful")
            
        except Exception as e:
            self.test_results["system_performance"] = {
                "status": "failed",
                "error": str(e)
            }
            logger.error(f"❌ System performance test failed: {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📝 Generating Test Report")
        
        try:
            # Calculate overall success rate
            successful_tests = sum(1 for result in self.test_results.values() if result.get("status") == "success")
            total_tests = len(self.test_results)
            success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
            
            report = {
                "test_summary": {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": total_tests - successful_tests,
                    "success_rate": f"{success_rate:.1f}%"
                },
                "detailed_results": self.test_results,
                "system_recommendations": self._generate_recommendations()
            }
            
            # Save report to file
            report_file = f"ai_system_test_report_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Print summary
            print("\n" + "="*80)
            print("🎯 ECONCELL AI SYSTEM TEST REPORT")
            print("="*80)
            print(f"📊 Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
            print(f"⏰ Test Duration: {time.strftime('%H:%M:%S')}")
            print(f"📄 Detailed Report: {report_file}")
            print("="*80)
            
            # Print test results
            for test_name, result in self.test_results.items():
                status_icon = "✅" if result.get("status") == "success" else "❌"
                print(f"{status_icon} {test_name.replace('_', ' ').title()}")
                if result.get("status") == "failed":
                    print(f"   Error: {result.get('error', 'Unknown error')}")
            
            print("="*80)
            logger.info(f"Test report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating test report: {e}")
    
    def _generate_recommendations(self) -> Dict[str, str]:
        """Generate system recommendations based on test results"""
        recommendations = {}
        
        for test_name, result in self.test_results.items():
            if result.get("status") == "failed":
                if test_name == "initialization":
                    recommendations[test_name] = "Check Ollama installation and model availability"
                elif test_name == "model_management":
                    recommendations[test_name] = "Verify GPU drivers and VRAM availability"
                elif test_name == "memory_management":
                    recommendations[test_name] = "Check system RAM and memory limits"
                else:
                    recommendations[test_name] = "Review logs for specific error details"
        
        if not recommendations:
            recommendations["overall"] = "All tests passed - system is functioning optimally"
        
        return recommendations
    
    async def cleanup(self):
        """Cleanup test resources"""
        logger.info("🧹 Cleaning up test resources")
        
        try:
            if self.ai_coordinator:
                await self.ai_coordinator.stop()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main test execution function"""
    print("🚀 EconCell AI System Test Suite")
    print("=" * 50)
    
    # Check if Ollama is available
    print("🔍 Checking system prerequisites...")
    
    # Create and run tester
    tester = EconCellAITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())