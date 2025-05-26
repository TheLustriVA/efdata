#!/usr/bin/env python3

"""
Integration Example: Using the refactored ISO code matching function

This example demonstrates how to use the refactored combine_iso_currency_and_country_codes
function with the existing data structures from definitions.py.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from iso_code_matcher import combine_iso_currency_and_country_codes, create_iso_3166_lookup_function

# Import the original data structures (these would come from definitions.py)
# For this example, I'll define simplified versions
def get_original_data_structures():
    """
    Get the original data structures from definitions.py
    In a real implementation, these would be imported directly.
    """
    
    # Simplified ISO_4217_CODES (from the original file)
    iso_4217_codes = [
        {"country": "United States", "currency": "United States Dollar", "code": "USD"},
        {"country": "Australia", "currency": "Australian Dollar", "code": "AUD"},
        {"country": "United Kingdom", "currency": "Pound Sterling", "code": "GBP"},
        {"country": "European Union", "currency": "Euro", "code": "EUR"},
        {"country": "Japan", "currency": "Japanese Yen", "code": "JPY"},
        {"country": "Canada", "currency": "Canadian Dollar", "code": "CAD"},
        {"country": "Switzerland", "currency": "Swiss Franc", "code": "CHF"},
        {"country": "China", "currency": "Chinese Renminbi", "code": "CNY"},
    ]
    
    # Simplified country name mappings (from the original file)
    country_name_mappings = {
        "United States": "United States of America",
        "United Kingdom": "United Kingdom of Great Britain and Northern Ireland",
        "European Union": "Germany",  # Simplified mapping for Euro
    }
    
    # Simplified ISO 3166 country to code mapping (from the original file)
    iso_3166_country_to_code = {
        "United States of America": "USA",
        "Australia": "AUS", 
        "United Kingdom of Great Britain and Northern Ireland": "GBR",
        "Germany": "DEU",
        "Japan": "JPN",
        "Canada": "CAN",
        "Switzerland": "CHE",
        "China": "CHN",
    }
    
    return iso_4217_codes, country_name_mappings, iso_3166_country_to_code


def demonstrate_original_vs_refactored():
    """
    Demonstrate the difference between original approach and refactored function.
    """
    print("=== ISO Code Matching: Original vs Refactored Approach ===\n")
    
    # Get the data structures
    iso_4217_codes, country_name_mappings, iso_3166_country_to_code = get_original_data_structures()
    
    print("1. ORIGINAL APPROACH (Inline Code):")
    print("   - Code was embedded directly in definitions.py")
    print("   - No reusability or modularity")
    print("   - Limited error handling")
    print("   - No type hints or comprehensive documentation\n")
    
    # Simulate original approach
    combined_iso_codes_original = []
    unmatched_countries_original = []
    
    # Original inline code logic (simplified)
    def find_iso_3166_code_original(country_name):
        if country_name in country_name_mappings:
            mapped_name = country_name_mappings[country_name]
            if mapped_name in iso_3166_country_to_code:
                return iso_3166_country_to_code[mapped_name]
        if country_name in iso_3166_country_to_code:
            return iso_3166_country_to_code[country_name]
        return None
    
    for entry in iso_4217_codes:
        country_name = entry["country"]
        iso_3166_code = find_iso_3166_code_original(country_name)
        
        if iso_3166_code:
            combined_entry = {
                "country": country_name,
                "currency": entry["currency"],
                "currency_code": entry["code"],
                "country_code": iso_3166_code
            }
            combined_iso_codes_original.append(combined_entry)
        else:
            unmatched_countries_original.append(country_name)
    
    print("2. REFACTORED APPROACH (Standalone Function):")
    print("   - Modular, reusable function")
    print("   - Comprehensive type hints and documentation")
    print("   - Input validation and error handling")
    print("   - Separation of concerns\n")
    
    # Use refactored approach
    lookup_func = create_iso_3166_lookup_function(
        country_name_mappings, 
        iso_3166_country_to_code
    )
    
    combined_iso_codes_refactored, unmatched_countries_refactored = combine_iso_currency_and_country_codes(
        iso_4217_codes,
        lookup_func
    )
    
    # Compare results
    print("3. RESULTS COMPARISON:")
    print(f"   Original approach - Combined: {len(combined_iso_codes_original)}, Unmatched: {len(unmatched_countries_original)}")
    print(f"   Refactored approach - Combined: {len(combined_iso_codes_refactored)}, Unmatched: {len(unmatched_countries_refactored)}")
    print(f"   Results identical: {combined_iso_codes_original == combined_iso_codes_refactored and unmatched_countries_original == unmatched_countries_refactored}\n")
    
    # Display sample results
    print("4. SAMPLE COMBINED ENTRIES:")
    for i, entry in enumerate(combined_iso_codes_refactored[:5], 1):
        print(f"   {i}. {entry['country']} ({entry['country_code']}) - {entry['currency']} ({entry['currency_code']})")
    
    if unmatched_countries_refactored:
        print(f"\n5. UNMATCHED COUNTRIES:")
        for i, country in enumerate(unmatched_countries_refactored, 1):
            print(f"   {i}. {country}")
    else:
        print(f"\n5. All countries were successfully matched!")


def demonstrate_error_handling():
    """
    Demonstrate the error handling capabilities of the refactored function.
    """
    print("\n\n=== Error Handling Demonstration ===\n")
    
    # Test with invalid input types
    print("1. Testing with invalid input types:")
    
    try:
        # Test with non-list input
        combine_iso_currency_and_country_codes("not a list", lambda x: x)
    except TypeError as e:
        print(f"   ✓ Caught TypeError: {e}")
    
    try:
        # Test with non-callable lookup function
        combine_iso_currency_and_country_codes([], "not callable")
    except ValueError as e:
        print(f"   ✓ Caught ValueError: {e}")
    
    # Test with malformed data
    print("\n2. Testing with malformed data:")
    malformed_data = [
        {"country": "Valid Country", "currency": "Valid Currency", "code": "VAL"},
        {"country": "Missing Currency"},  # Missing required keys
        "not a dictionary",  # Wrong type
        {"country": "Another Valid", "currency": "Valid Currency", "code": "AV2"},
    ]
    
    def simple_lookup(country_name):
        return "XXX" if country_name == "Valid Country" else None
    
    combined, unmatched = combine_iso_currency_and_country_codes(malformed_data, simple_lookup)
    print(f"   ✓ Processed malformed data: {len(combined)} valid entries, {len(unmatched)} unmatched")
    print(f"   ✓ Function gracefully handled invalid entries")


def demonstrate_flexibility():
    """
    Demonstrate the flexibility of the refactored approach.
    """
    print("\n\n=== Flexibility Demonstration ===\n")
    
    print("1. Custom lookup function for specific use case:")
    
    # Create a custom lookup function for a specific region
    def asia_pacific_lookup(country_name):
        """Custom lookup focusing on Asia-Pacific region"""
        mappings = {
            "Australia": "AUS",
            "New Zealand": "NZL", 
            "Japan": "JPN",
            "South Korea": "KOR",
            "Singapore": "SGP"
        }
        return mappings.get(country_name)
    
    asia_pacific_currencies = [
        {"country": "Australia", "currency": "Australian Dollar", "code": "AUD"},
        {"country": "Japan", "currency": "Japanese Yen", "code": "JPY"},
        {"country": "Singapore", "currency": "Singapore Dollar", "code": "SGD"},
        {"country": "Unknown Asian Country", "currency": "Unknown Currency", "code": "XXX"},
    ]
    
    combined, unmatched = combine_iso_currency_and_country_codes(
        asia_pacific_currencies, 
        asia_pacific_lookup
    )
    
    print(f"   ✓ Processed {len(asia_pacific_currencies)} Asia-Pacific entries")
    print(f"   ✓ Successfully matched: {len(combined)}")
    print(f"   ✓ Unmatched: {len(unmatched)}")
    
    print("\n2. Function can be easily extended and customized:")
    print("   ✓ Different lookup strategies")
    print("   ✓ Custom data validation")
    print("   ✓ Integration with databases or APIs")
    print("   ✓ Batch processing capabilities")


if __name__ == "__main__":
    # Run all demonstrations
    demonstrate_original_vs_refactored()
    demonstrate_error_handling()
    demonstrate_flexibility()
    
    print("\n\n=== Summary ===")
    print("The refactored function provides:")
    print("✓ Better code organization and modularity")
    print("✓ Comprehensive documentation and type hints")
    print("✓ Robust error handling and input validation")
    print("✓ Improved testability and maintainability")
    print("✓ Preserved original functionality and behavior")
    print("✓ Enhanced flexibility for different use cases")