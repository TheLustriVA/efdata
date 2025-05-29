#!/usr/bin/env python3

"""
ISO Code Matching Utilities

This module provides functions to combine ISO 4217 currency codes with ISO 3166 country codes,
creating a unified dataset for economic and geographic data processing.
"""

from typing import Dict, List, Optional, Tuple, Any, Callable


def combine_iso_currency_and_country_codes(
    iso_4217_codes: List[Dict[str, str]],
    country_code_lookup_func: Callable[[str], Optional[str]]
) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Combine ISO 4217 currency codes with ISO 3166 country codes to create a unified dataset.
    
    This function processes a list of ISO 4217 currency entries and attempts to match each
    country name to its corresponding ISO 3166 country code using a provided lookup function.
    Successfully matched entries are combined into a comprehensive dataset, while unmatched
    entries are tracked separately for analysis.
    
    Args:
        iso_4217_codes (List[Dict[str, str]]): List of dictionaries containing ISO 4217 
            currency information. Each dictionary should have the following keys:
            - "country": Name of the country
            - "currency": Name of the currency
            - "code": ISO 4217 currency code (e.g., "USD", "EUR")
            
        country_code_lookup_func (Callable[[str], Optional[str]]): Function that takes a 
            country name as input and returns the corresponding ISO 3166 country code 
            or None if no match is found. This function should handle country name 
            variations and mappings.
    
    Returns:
        Tuple[List[Dict[str, str]], List[str]]: A tuple containing:
            - combined_iso_codes: List of dictionaries with successfully matched entries.
              Each dictionary contains:
                * "country": Original country name from ISO 4217
                * "currency": Currency name
                * "currency_code": ISO 4217 currency code
                * "country_code": ISO 3166 country code
            - unmatched_countries: List of country names that couldn't be matched
              to ISO 3166 codes
    
    Raises:
        TypeError: If iso_4217_codes is not a list or if entries don't have required keys
        ValueError: If country_code_lookup_func is not callable
    
    Example:
        >>> iso_4217_data = [
        ...     {"country": "United States", "currency": "US Dollar", "code": "USD"},
        ...     {"country": "Germany", "currency": "Euro", "code": "EUR"}
        ... ]
        >>> def lookup_country_code(country_name):
        ...     mappings = {"United States": "USA", "Germany": "DEU"}
        ...     return mappings.get(country_name)
        >>> 
        >>> combined, unmatched = combine_iso_currency_and_country_codes(
        ...     iso_4217_data, lookup_country_code
        ... )
        >>> print(f"Combined entries: {len(combined)}")
        Combined entries: 2
        >>> print(f"Unmatched countries: {len(unmatched)}")
        Unmatched countries: 0
    
    Note:
        This function preserves the original functionality of the code from lines 1371-1390
        in site/definitions.py while providing better structure, documentation, and
        error handling.
    """
    # Input validation
    if not isinstance(iso_4217_codes, list):
        raise TypeError("iso_4217_codes must be a list")
    
    if not callable(country_code_lookup_func):
        raise ValueError("country_code_lookup_func must be callable")
    
    # Initialize result containers
    combined_iso_codes: List[Dict[str, str]] = []
    unmatched_countries: List[str] = []
    
    # Process each ISO 4217 currency entry
    for entry in iso_4217_codes:
        # Validate entry structure
        if not isinstance(entry, dict):
            continue  # Skip invalid entries
        
        required_keys = {"country", "currency", "code"}
        if not all(key in entry for key in required_keys):
            continue  # Skip entries missing required keys
        
        # Extract country name from the currency entry
        country_name = entry["country"]
        
        # Attempt to find the corresponding ISO 3166 country code
        iso_3166_code = country_code_lookup_func(country_name)
        
        if iso_3166_code:
            # Create combined entry with both currency and country code information
            combined_entry = {
                "country": country_name,
                "currency": entry["currency"],
                "currency_code": entry["code"],
                "country_code": iso_3166_code
            }
            combined_iso_codes.append(combined_entry)
        else:
            # Track countries that couldn't be matched
            unmatched_countries.append(country_name)
    
    return combined_iso_codes, unmatched_countries


def create_iso_3166_lookup_function(
    country_name_mappings: Dict[str, str],
    iso_3166_country_to_code: Dict[str, str]
) -> Callable[[str], Optional[str]]:
    """
    Create a lookup function for finding ISO 3166 codes from country names.
    
    This function creates and returns a closure that can be used to look up ISO 3166
    country codes from country names, using both direct mappings and exact matches.
    
    Args:
        country_name_mappings (Dict[str, str]): Dictionary mapping country names 
            from one standard (e.g., ISO 4217) to country names used in ISO 3166
        iso_3166_country_to_code (Dict[str, str]): Dictionary mapping ISO 3166 
            country names to their corresponding country codes
    
    Returns:
        Callable[[str], Optional[str]]: A function that takes a country name as input
            and returns the corresponding ISO 3166 country code or None if no match
    
    Example:
        >>> mappings = {"United States": "United States of America"}
        >>> codes = {"United States of America": "USA"}
        >>> lookup_func = create_iso_3166_lookup_function(mappings, codes)
        >>> result = lookup_func("United States")
        >>> print(result)
        USA
    """
    def find_iso_3166_code(country_name: str) -> Optional[str]:
        """
        Find the ISO 3166 code for a given country name.
        
        Args:
            country_name (str): Name of the country to look up
            
        Returns:
            Optional[str]: ISO 3166 country code if found, None otherwise
        """
        # First try direct mapping from country_name_mappings
        if country_name in country_name_mappings:
            mapped_name = country_name_mappings[country_name]
            if mapped_name in iso_3166_country_to_code:
                return iso_3166_country_to_code[mapped_name]
        
        # If no direct mapping, try exact match in iso_3166_country_to_code
        if country_name in iso_3166_country_to_code:
            return iso_3166_country_to_code[country_name]
        
        # Return None if no match found
        return None
        
    return find_iso_3166_code


# Example usage and testing
if __name__ == "__main__":
    # Example data (simplified versions of the original data structures)
    sample_iso_4217_codes = [
        {"country": "United States", "currency": "US Dollar", "code": "USD"},
        {"country": "Germany", "currency": "Euro", "code": "EUR"},
        {"country": "Japan", "currency": "Japanese Yen", "code": "JPY"},
        {"country": "Unknown Country", "currency": "Unknown Currency", "code": "XXX"}
    ]
    
    sample_country_mappings = {
        "United States": "United States of America",
        "Germany": "Germany"
    }
    
    sample_iso_3166_mapping = {
        "United States of America": "USA",
        "Germany": "DEU", 
        "Japan": "JPN"
    }
    
    # Create the lookup function
    lookup_func = create_iso_3166_lookup_function(
        sample_country_mappings, 
        sample_iso_3166_mapping
    )
    
    # Test the main function
    combined_codes, unmatched = combine_iso_currency_and_country_codes(
        sample_iso_4217_codes, 
        lookup_func
    )
    
    print(f"Successfully combined {len(combined_codes)} entries:")
    for entry in combined_codes:
        print(f"  {entry['country']} ({entry['country_code']}) - "
              f"{entry['currency']} ({entry['currency_code']})")
    
    print(f"\nUnmatched countries ({len(unmatched)}):")
    for country in unmatched:
        print(f"  {country}")