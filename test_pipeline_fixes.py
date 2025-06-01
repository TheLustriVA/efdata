#!/usr/bin/env python3
"""
Test script to verify pipeline fixes work correctly.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'econdata'))

def test_expenditure_pipeline_validation():
    """Test expenditure pipeline validation with edge cases."""
    from econdata.pipelines.abs_expenditure_pipeline import ABSExpenditurePipeline
    
    pipeline = ABSExpenditurePipeline()
    
    # Test case 1: Valid item with zero amount
    valid_item_zero = {
        'spider': 'abs_gfs',
        'data_type': 'expenditure',
        'reference_period': '2024-06-30',
        'level_of_government': 'Commonwealth',
        'expenditure_type': 'Test Expenditure',
        'amount': 0.0,  # This should NOT trigger validation error
        'source_file': 'test.xlsx'
    }
    
    errors = pipeline._validate_expenditure_item(valid_item_zero)
    assert len(errors) == 0, f"Zero amount should be valid: {errors}"
    print("✓ Zero amount validation passed")
    
    # Test case 2: Item with missing amount (None)
    invalid_item = {
        'spider': 'abs_gfs', 
        'data_type': 'expenditure',
        'reference_period': '2024-06-30',
        'level_of_government': 'Commonwealth',
        'expenditure_type': 'Test Expenditure',
        'amount': None,
        'source_file': 'test.xlsx'
    }
    
    errors = pipeline._validate_expenditure_item(invalid_item)
    assert len(errors) == 1, f"Missing amount should trigger error: {errors}"
    assert "Missing required field: amount" in errors[0]
    print("✓ Missing amount validation passed")
    
    # Test case 3: Wrong spider should be skipped
    wrong_spider_item = {
        'spider': 'wrong_spider',
        'data_type': 'expenditure',
    }
    
    result = pipeline.process_item(wrong_spider_item, None)
    assert result == wrong_spider_item, "Wrong spider should be skipped"
    print("✓ Spider filtering passed")

def test_taxation_pipeline_validation():
    """Test taxation pipeline validation."""
    from econdata.pipelines.abs_taxation_pipeline import ABSTaxationPipeline
    from itemadapter import ItemAdapter
    
    pipeline = ABSTaxationPipeline()
    
    # Test case 1: Valid item with zero amount
    valid_item_zero = {
        'spider': 'abs_gfs',
        'data_type': 'taxation', 
        'reference_period': '2024-06-30',
        'level_of_government': 'Commonwealth',
        'revenue_type': 'GST',
        'amount': 0.0,
        'source_file': 'test.xlsx'
    }
    
    adapter = ItemAdapter(valid_item_zero)
    errors = pipeline._validate_item(adapter)
    assert len(errors) == 0, f"Zero amount should be valid: {errors}"
    print("✓ Taxation zero amount validation passed")
    
    # Test case 2: Wrong data type should be skipped
    wrong_type_item = {
        'spider': 'abs_gfs',
        'data_type': 'expenditure',  # Wrong type for taxation pipeline
    }
    
    result = pipeline.process_item(wrong_type_item, None)
    assert result == wrong_type_item, "Wrong data type should be skipped"
    print("✓ Taxation data type filtering passed")

def main():
    """Run all tests."""
    print("Testing Pipeline Fixes")
    print("=" * 30)
    
    try:
        test_expenditure_pipeline_validation()
        test_taxation_pipeline_validation()
        
        print("\n" + "=" * 30)
        print("✅ All tests passed! Pipeline fixes working correctly.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())