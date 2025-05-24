from functools import wraps
from .db_utils import get_valid_currencies # Correct relative import
import logging # Suggested: for better logging

logger = logging.getLogger(__name__) # Suggested: logger instance

def currency_filter(func):
    # This is called once when the module is loaded.
    # If currencies can change dynamically without app restart, consider moving this call
    # into the wrapper or providing a refresh mechanism.
    valid_currencies = get_valid_currencies()

    @wraps(func)
    def wrapper(*args, **kwargs):
        target_currency = kwargs.get('target_currency')
        if target_currency in valid_currencies:
            return func(*args, **kwargs)
        else:
            # Suggested: Use logging instead of print for better diagnostics
            logger.warning(f"Skipping invalid currency code: {target_currency}")
            # print(f"Skipping invalid currency code: {target_currency}") # Original line
            return None # Caller must handle this None value

    return wrapper