#!/usr/bin/env python3
"""
Test script for RBA Circular Flow Pipeline
Runs the CSV ingestion independently of Scrapy spiders for testing
"""

import sys
import os
import logging
from unittest.mock import Mock

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from econdata.econdata.pipelines import RBACircularFlowPipeline
from econdata.econdata.settings import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_rba_pipeline():
    """Test the RBA pipeline functionality"""
    
    # Mock crawler with settings
    mock_crawler = Mock()
    mock_crawler.settings = Mock()
    mock_crawler.settings.get = lambda key, default=None: {
        'DB_HOST': DB_HOST,
        'DB_PORT': DB_PORT,
        'DB_NAME': DB_NAME,
        'DB_USER': DB_USER,
        'DB_PASSWORD': DB_PASSWORD
    }.get(key, default)
    
    # Mock spider
    mock_spider = Mock()
    mock_spider.name = 'test_spider'
    
    try:
        print("=== RBA Circular Flow Pipeline Test ===")
        print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        print(f"User: {DB_USER}")
        
        # Initialize pipeline
        pipeline = RBACircularFlowPipeline.from_crawler(mock_crawler)
        
        # Test pipeline lifecycle
        print("\n1. Opening pipeline...")
        pipeline.open_spider(mock_spider)
        
        print("\n2. Pipeline opened successfully!")
        print(f"Downloads directory: {pipeline.downloads_dir}")
        print(f"Processed files: {len(pipeline.processed_files)}")
        
        # Close pipeline
        print("\n3. Closing pipeline...")
        pipeline.close_spider(mock_spider)
        
        print("\n✅ Pipeline test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rba_pipeline()
    sys.exit(0 if success else 1)
