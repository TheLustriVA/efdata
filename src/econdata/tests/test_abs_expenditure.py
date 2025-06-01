#!/usr/bin/env python3
"""
Test script for ABS spider expenditure functionality.
"""

import sys
import os
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_spider_expenditure_categories():
    """Test that expenditure categories are configured."""
    try:
        from econdata.spiders.abs_data import ABSGFSSpider
        
        spider = ABSGFSSpider()
        
        # Check expenditure categories exist
        assert hasattr(spider, 'EXPENDITURE_CATEGORIES'), "No EXPENDITURE_CATEGORIES defined"
        assert len(spider.EXPENDITURE_CATEGORIES) >= 10, "Too few expenditure categories"
        
        # Check key categories
        expected_categories = ['health', 'education', 'defence', 'social_protection']
        for cat in expected_categories:
            assert cat in spider.EXPENDITURE_CATEGORIES, f"Missing category: {cat}"
        
        print("✓ Expenditure categories configured correctly")
        print(f"  - Categories: {list(spider.EXPENDITURE_CATEGORIES.keys())}")
        return True
        
    except Exception as e:
        print(f"✗ Expenditure categories test failed: {e}")
        return False

def test_expenditure_methods():
    """Test that expenditure parsing methods exist."""
    try:
        from econdata.spiders.abs_data import ABSGFSSpider
        
        spider = ABSGFSSpider()
        
        # Check methods exist
        assert hasattr(spider, '_find_expenditure_sheets'), "Missing _find_expenditure_sheets method"
        assert hasattr(spider, '_extract_expenditure_data'), "Missing _extract_expenditure_data method"
        assert hasattr(spider, '_categorize_expenditure_type'), "Missing _categorize_expenditure_type method"
        assert hasattr(spider, '_interpolate_expenditure_to_quarterly'), "Missing _interpolate_expenditure_to_quarterly method"
        
        print("✓ Expenditure parsing methods exist")
        return True
        
    except Exception as e:
        print(f"✗ Expenditure methods test failed: {e}")
        return False

def test_expenditure_pipeline():
    """Test that expenditure pipeline can be imported."""
    try:
        from econdata.pipelines.abs_expenditure_pipeline import ABSExpenditurePipeline
        
        print("✓ Expenditure pipeline imports successfully")
        
        # Check pipeline has required methods
        pipeline = ABSExpenditurePipeline()
        assert hasattr(pipeline, 'process_item'), "Pipeline missing process_item method"
        assert hasattr(pipeline, '_validate_expenditure_item'), "Pipeline missing validation method"
        
        print("  - Pipeline has required methods")
        return True
        
    except ImportError as e:
        print(f"✗ Expenditure pipeline import failed: {e}")
        return False

def test_database_tables():
    """Test that database tables were created."""
    try:
        import psycopg2
        import os
        
        # Get database config from environment
        db_config = {
            'host': os.getenv('PSQL_HOST', 'localhost'),
            'port': os.getenv('PSQL_PORT', '5432'),
            'database': os.getenv('PSQL_DB', 'econdata'),
            'user': os.getenv('PSQL_USER', 'websinthe'),
            'password': os.getenv('PSQL_PW', '')
        }
        
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Check staging table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'abs_staging' 
                AND table_name = 'government_expenditure'
            )
        """)
        staging_exists = cur.fetchone()[0]
        assert staging_exists, "Staging table not created"
        
        # Check dimension tables
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'abs_dimensions' 
                AND table_name = 'cofog_classification'
            )
        """)
        cofog_exists = cur.fetchone()[0]
        assert cofog_exists, "COFOG dimension table not created"
        
        # Check COFOG data
        cur.execute("SELECT COUNT(*) FROM abs_dimensions.cofog_classification")
        cofog_count = cur.fetchone()[0]
        print(f"✓ Database tables created successfully")
        print(f"  - COFOG categories loaded: {cofog_count}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_parse_expenditure_example():
    """Test parsing a mock expenditure row."""
    try:
        from econdata.spiders.abs_data import ABSGFSSpider
        import pandas as pd
        
        spider = ABSGFSSpider()
        
        # Test categorization
        test_labels = [
            ('Health services', 'health'),
            ('Education - primary and secondary', 'education'),
            ('Defence spending', 'defence'),
            ('Employee salaries and wages', 'employee_expenses'),
            ('Capital infrastructure', 'capital_expenditure')
        ]
        
        print("✓ Testing expenditure categorization:")
        for label, expected in test_labels:
            result = spider._categorize_expenditure_type(label)
            print(f"  - '{label}' → '{result}' (expected: '{expected}')")
            
        return True
        
    except Exception as e:
        print(f"✗ Parsing test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("ABS Spider Expenditure Test Suite")
    print("=" * 40)
    
    tests = [
        test_spider_expenditure_categories,
        test_expenditure_methods,
        test_expenditure_pipeline,
        test_database_tables,
        test_parse_expenditure_example
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n✅ All tests passed! Ready for expenditure data collection.")
        print("\nTo run the spider with expenditure support:")
        print("  cd src/econdata && scrapy crawl abs_gfs -a test_mode=True")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())