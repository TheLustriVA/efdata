#!/usr/bin/env python3
"""
Simple test script for ABS spider dry-run functionality.
"""

import sys
import os
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_spider_import():
    """Test that the spider can be imported."""
    try:
        from econdata.spiders.abs_data import ABSGFSSpider
        print("✓ Spider import successful")
        return True
    except ImportError as e:
        print(f"✗ Spider import failed: {e}")
        return False

def test_spider_test_mode():
    """Test that spider initializes in test mode."""
    try:
        from econdata.spiders.abs_data import ABSGFSSpider
        
        # Create spider with test mode
        spider = ABSGFSSpider(test_mode=True)
        
        # Check test mode settings
        assert spider.test_mode == True, "Test mode not set"
        assert spider.max_test_files == 1, "Max test files incorrect"
        assert spider.custom_settings['CLOSESPIDER_ITEMCOUNT'] == 10, "Item count limit not set"
        assert spider.custom_settings['DOWNLOAD_MAXSIZE'] == 5 * 1024 * 1024, "Download size limit not set"
        
        print("✓ Test mode initialization successful")
        print(f"  - Max files: {spider.max_test_files}")
        print(f"  - Item limit: {spider.custom_settings['CLOSESPIDER_ITEMCOUNT']}")
        print(f"  - Size limit: {spider.custom_settings['DOWNLOAD_MAXSIZE'] / 1024 / 1024}MB")
        return True
        
    except Exception as e:
        print(f"✗ Test mode initialization failed: {e}")
        return False

def test_pipeline_import():
    """Test that pipelines can be imported."""
    try:
        from econdata.pipelines.abs_taxation_pipeline import ABSTaxationPipeline
        from econdata.pipelines.abs_test_pipeline import ABSTestPipeline
        print("✓ Pipeline imports successful")
        return True
    except ImportError as e:
        print(f"✗ Pipeline import failed: {e}")
        return False

def test_scheduler_command():
    """Test that dry-run command exists in scheduler."""
    try:
        # Read scheduler file
        scheduler_path = Path(__file__).parent.parent.parent / 'scheduler' / 'start_scheduler.py'
        content = scheduler_path.read_text()
        
        assert 'test-abs-dry' in content, "Dry-run command not found in scheduler"
        assert 'ABS_TEST_MODE' in content, "Test mode environment variable not set"
        
        print("✓ Scheduler dry-run command configured")
        return True
        
    except Exception as e:
        print(f"✗ Scheduler check failed: {e}")
        return False

def main():
    """Run all tests."""
    print("ABS Spider Dry-Run Test Suite")
    print("=" * 40)
    
    tests = [
        test_spider_import,
        test_spider_test_mode,
        test_pipeline_import,
        test_scheduler_command,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n✅ All tests passed! Ready for dry-run testing.")
        print("\nTo run a dry-run test:")
        print("  python src/scheduler/start_scheduler.py test-abs-dry")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix issues before proceeding.")
        return 1

if __name__ == '__main__':
    sys.exit(main())