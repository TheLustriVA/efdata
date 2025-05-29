import os
import time
import functools
from sqlite3 import Cursor
import psycopg2
from typing import Union
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from frontend.data.definitions import (
    EUD, ISO_3166_CODES,
    ANZUS, FIVE_EYES, AUKUS, G20, OECD, APEC, CPTPP, RCEP,
    PACIFIC_ISLANDS_FORUM, EAST_ASIA_SUMMIT, ASEAN_REGIONAL_FORUM,
    COMMONWEALTH_OF_NATIONS, QUAD, IORA, ANTARCTIC_TREATY
)

# Configure logging for country mapping debugging and performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance metrics tracking
class PerformanceMetrics:
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.avg_filter_time = 0.0
    
    def log_cache_hit(self):
        self.cache_hits += 1
    
    def log_cache_miss(self):
        self.cache_misses += 1
    
    def log_request(self, filter_time: float):
        self.total_requests += 1
        self.avg_filter_time = ((self.avg_filter_time * (self.total_requests - 1)) + filter_time) / self.total_requests
    
    def get_cache_ratio(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    def log_metrics(self):
        logger.info(f"Performance Metrics - Cache Hit Ratio: {self.get_cache_ratio():.2%}, "
                   f"Avg Filter Time: {self.avg_filter_time:.4f}s, Total Requests: {self.total_requests}")

# Global performance metrics instance
perf_metrics = PerformanceMetrics()

# Country name aliases for database to ISO code mapping
# Maps common database country name variations to their ISO 3166-1 Alpha-3 codes
COUNTRY_NAME_ALIASES = {
    # United States variations
    "United States": "USA",
    "United States of America": "USA",
    "US": "USA",
    "USA": "USA",
    
    # Russia variations
    "Russia": "RUS",
    "Russian Federation": "RUS",
    
    # South Korea variations
    "South Korea": "KOR",
    "Korea, Republic of": "KOR",
    "Republic of Korea": "KOR",
    
    # Czech Republic variations
    "Czech Republic": "CZE",
    "Czechia": "CZE",
    
    # United Kingdom variations
    "United Kingdom": "GBR",
    "UK": "GBR",
    "Great Britain": "GBR",
    "United Kingdom of Great Britain and Northern Ireland": "GBR",
    
    # Iran variations
    "Iran": "IRN",
    "Iran, Islamic Republic of": "IRN",
    
    # Venezuela variations
    "Venezuela": "VEN",
    "Venezuela, Bolivarian Republic of": "VEN",
    
    # Bolivia variations
    "Bolivia": "BOL",
    "Bolivia, Plurinational State of": "BOL",
    
    # Tanzania variations
    "Tanzania": "TZA",
    "Tanzania, United Republic of": "TZA",
    
    # Moldova variations
    "Moldova": "MDA",
    "Moldova, Republic of": "MDA",
    
    # Syria variations
    "Syria": "SYR",
    "Syrian Arab Republic": "SYR",
    
    # North Korea variations
    "North Korea": "PRK",
    "Korea, Democratic People's Republic of": "PRK",
    
    # Vietnam variations
    "Vietnam": "VNM",
    "Viet Nam": "VNM",
    
    # Laos variations
    "Laos": "LAO",
    "Lao People's Democratic Republic": "LAO",
    
    # Taiwan variations
    "Taiwan": "TWN",
    "Taiwan, Province of China": "TWN",
    
    # Hong Kong variations
    "Hong Kong": "HKG",
    
    # Macau variations
    "Macau": "MAC",
    "Macao": "MAC",
    
    # Turkey variations
    "Turkey": "TUR",
    "Türkiye": "TUR",
    
    # Netherlands variations
    "Netherlands": "NLD",
    "Netherlands, Kingdom of the": "NLD",
    
    # Congo variations
    "Congo": "COG",
    "Congo, Democratic Republic of the": "COD",
    "Democratic Republic of Congo": "COD",
    "DRC": "COD",
    
    # Palestine variations
    "Palestine": "PSE",
    "Palestine, State of": "PSE",
    
    # Eswatini variations
    "Swaziland": "SWZ",
    "Eswatini": "SWZ",
    
    # North Macedonia variations
    "Macedonia": "MKD",
    "North Macedonia": "MKD",
    "Former Yugoslav Republic of Macedonia": "MKD",
    
    # Brunei variations
    "Brunei": "BRN",
    "Brunei Darussalam": "BRN",
    
    # Myanmar variations
    "Myanmar": "MMR",
    "Burma": "MMR",
    
    # Timor-Leste variations
    "East Timor": "TLS",
    "Timor-Leste": "TLS",
    
    # Cabo Verde variations
    "Cape Verde": "CPV",
    "Cabo Verde": "CPV",
    
    # Micronesia variations
    "Micronesia": "FSM",
    "Micronesia, Federated States of": "FSM",
    
    # Marshall Islands variations
    "Marshall Islands": "MHL",
    
    # Solomon Islands variations
    "Solomon Islands": "SLB",
    
    # Ivory Coast variations
    "Ivory Coast": "CIV",
    "Côte d'Ivoire": "CIV"
}

@functools.lru_cache(maxsize=512)
def normalize_country_name(country_name: str) -> str:
    """
    Normalize country name for consistent ISO code mapping with caching.
    
    Args:
        country_name: Raw country name from database
        
    Returns:
        Normalized country name or ISO code if alias found
    """
    if not country_name:
        return country_name
    
    # First try direct alias lookup (case-insensitive)
    country_name_cleaned = country_name.strip()
    
    # Check exact match first
    if country_name_cleaned in COUNTRY_NAME_ALIASES:
        result = COUNTRY_NAME_ALIASES[country_name_cleaned]
        logger.debug(f"Country alias match: '{country_name_cleaned}' -> '{result}'")
        perf_metrics.log_cache_hit()
        return result
    
    # Check case-insensitive match
    for alias, iso_code in COUNTRY_NAME_ALIASES.items():
        if country_name_cleaned.lower() == alias.lower():
            logger.debug(f"Country case-insensitive alias match: '{country_name_cleaned}' -> '{iso_code}'")
            perf_metrics.log_cache_hit()
            return iso_code
    
    # No alias found, return original name
    logger.debug(f"No alias found for country: '{country_name_cleaned}'")
    perf_metrics.log_cache_miss()
    return country_name_cleaned

@functools.lru_cache(maxsize=128)
def get_country_name_to_iso_mapping() -> dict:
    """
    Create cached mapping of country names to ISO codes.
    
    Returns:
        Dictionary mapping country names to ISO 3166-1 Alpha-3 codes
    """
    country_name_to_iso = {}
    for country_dict in ISO_3166_CODES:
        for iso_code, country_name in country_dict.items():
            country_name_to_iso[country_name] = iso_code
    
    logger.info(f"Created country name to ISO mapping with {len(country_name_to_iso)} entries")
    return country_name_to_iso

@functools.lru_cache(maxsize=64)
def get_bloc_countries_set(bloc_name: str) -> set:
    """
    Get cached set of countries for a specific bloc.
    
    Args:
        bloc_name: Name of the bloc
        
    Returns:
        Set of ISO 3166-1 Alpha-3 country codes for the bloc
    """
    if bloc_name not in AVAILABLE_BLOCS:
        raise ValueError(f"Unknown bloc: {bloc_name}")
    
    bloc_set = AVAILABLE_BLOCS[bloc_name].copy()
    logger.debug(f"Cached bloc '{bloc_name}' with {len(bloc_set)} countries")
    return bloc_set

def get_iso_code_for_country(db_country_name: str, country_name_to_iso: dict) -> str:
    """
    Get ISO code for a database country name with improved error handling.
    
    Args:
        db_country_name: Country name from database
        country_name_to_iso: Pre-computed mapping dictionary
        
    Returns:
        ISO 3166-1 Alpha-3 code or None if not found
    """
    if not db_country_name:
        return None
    
    try:
        # Normalize the country name to handle variations
        normalized_country = normalize_country_name(db_country_name)
        
        # Try to get ISO code - first check if normalized result is already an ISO code
        if len(normalized_country) == 3 and normalized_country.isupper():
            # Normalized result is likely an ISO code
            logger.debug(f"Direct ISO mapping: '{db_country_name}' -> '{normalized_country}'")
            return normalized_country
        elif normalized_country in country_name_to_iso:
            # Normalized result is a country name that maps to ISO code
            iso_code = country_name_to_iso[normalized_country]
            logger.debug(f"Country name mapping: '{db_country_name}' -> '{normalized_country}' -> '{iso_code}'")
            return iso_code
        else:
            # Try original name as fallback
            if db_country_name in country_name_to_iso:
                iso_code = country_name_to_iso[db_country_name]
                logger.debug(f"Fallback mapping: '{db_country_name}' -> '{iso_code}'")
                return iso_code
            else:
                logger.warning(f"No ISO mapping found for country: '{db_country_name}' (normalized: '{normalized_country}')")
                return None
    except Exception as e:
        logger.error(f"Error mapping country '{db_country_name}' to ISO code: {str(e)}")
        return None

load_dotenv("/home/websinthe/code/econcell/.env")

DB_HOST = os.getenv("PSQL_HOST")
DB_PORT = os.getenv("PSQL_PORT")
DB_NAME = os.getenv("PSQL_DB")
DB_USER = os.getenv("PSQL_USER")
DB_PASSWORD = os.getenv("PSQL_PW")

app = FastAPI()

# --- CORS Configuration ---
# Define the list of origins that are allowed to make cross-origin requests.
# If your HTML file is opened directly in the browser (file:// protocol),
# "null" is the origin you need to allow.
# If you serve your HTML file from a local web server (e.g., http://localhost:8000 or http://127.0.0.1:5500),
# add that specific origin.
origins = [
    "http://localhost",          # General localhost, covers any port if HTML served from localhost
    "http://localhost:8000",     # Example: if you use `python -m http.server 8000`
    "http://127.0.0.1",        # General 127.0.0.1
    "http://127.0.0.1:5501",     # Example: VS Code Live Server default port
    "null",                      # Allows requests from `file:///` origins (local HTML files)
    # Add any other specific origins your frontend might be served from.
    # For development, you might temporarily use ["*"] to allow all origins,
    # but be more specific for production.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # List of allowed origins
    allow_credentials=True,      # Allows cookies to be included in requests (if needed)
    allow_methods=["*"],         # Allows all standard HTTP methods (GET, POST, etc.)
    allow_headers=["*"],         # Allows all headers
)

def iso_code_to_country_name(iso_code):
    """Convert ISO 3166-1 Alpha-3 code to country name"""
    for country_dict in ISO_3166_CODES:
        if iso_code in country_dict:
            return country_dict[iso_code]
    return iso_code  # Return the code itself if not found

def get_latest_xrates(filter:list[str] = None)->dict:
    """
    Get latest exchange rates with optimized filtering and caching.
    
    Args:
        filter: Optional set of ISO 3166-1 Alpha-3 country codes to filter by
        
    Returns:
        Dictionary containing exchange rate data
    """
    filter_start_time = time.time()
    
    try:
        db_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        db_conn.autocommit = False
    except psycopg2.OperationalError as e:
        logger.error(f"Unable to connect to the database: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

    with db_conn:
        with db_conn.cursor() as cursor:
            price_list = []
            
            get_xrates_sql = """select base_currency, target_currency, country, currency_name, exchange_rate
            from exchange_rates
            inner join currencies
            on target_currency = code
            where last_updated_utc = (
                select max(last_updated_utc)
                from exchange_rates
                )
            """
            
            cursor.execute(get_xrates_sql)
            forex_full = cursor.fetchall()

            if filter:
                # Use cached country name to ISO mapping for better performance
                country_name_to_iso = get_country_name_to_iso_mapping()
                
                # Convert filter to set for O(1) lookups
                filter_set = set(filter) if not isinstance(filter, set) else filter
                
                logger.info(f"Filtering exchange rates for {len(filter_set)} countries: {sorted(list(filter_set))}")
                
                # Pre-compute EUR countries in filter for efficient EUR handling
                eur_countries_in_filter = filter_set.intersection(EUD) if filter_set else set()
                
                filtered_prices = []
                mapping_failures = []
                
                for price in forex_full:
                    db_country_name = price[2]
                    
                    # Use optimized ISO code mapping function
                    country_iso = get_iso_code_for_country(db_country_name, country_name_to_iso)
                    
                    # Check if this country should be included in the filter
                    if country_iso and country_iso in filter_set:
                        filtered_prices.append(price)
                        logger.debug(f"Country '{db_country_name}' (ISO: {country_iso}) included in filter")
                    # Special handling for EUR - check if any filtered countries use EUR
                    elif price[1] == "EUR" and eur_countries_in_filter:
                        filtered_prices.append(price)
                        logger.debug(f"EUR entry included for countries: {sorted(list(eur_countries_in_filter))}")
                    else:
                        if not country_iso:
                            mapping_failures.append(db_country_name)
                        logger.debug(f"Country '{db_country_name}' ({'unmapped' if not country_iso else country_iso}) not in filter")
                
                # Log mapping failures as a summary to reduce log noise
                if mapping_failures:
                    logger.warning(f"Failed to map {len(mapping_failures)} countries to ISO codes: {sorted(set(mapping_failures))}")
                
                filter_end_time = time.time()
                filter_duration = filter_end_time - filter_start_time
                
                logger.info(f"Filtered results: {len(filtered_prices)} entries from {len(forex_full)} total in {filter_duration:.4f}s")
                perf_metrics.log_request(filter_duration)
                perf_metrics.log_metrics()
                
                forex_prices = filtered_prices
            else:
                forex_prices = forex_full
            
            # Process the exchange rate data (filtered or unfiltered)
            for price in forex_prices:
               
                # Check if this is a EUR (Euro) exchange rate entry
                if price[1] == "EUR":
                    print(f"Processing EUR entry with rate: {price[4]}")
                    # Extract the EUR exchange rate value
                    eur_exchange_rate = float(price[4])
                    
                    # If filtering is enabled, only create entries for EUR countries in the filter
                    if filter:
                        eur_countries_to_include = filter.intersection(EUD)
                    else:
                        eur_countries_to_include = EUD
                    
                    # Create individual price entries for each relevant EU country
                    for eu_country_code in eur_countries_to_include:
                        country_name = iso_code_to_country_name(eu_country_code)
                        price_list.append(
                            {
                                "base_currency": price[0],
                                "target_currency": price[1],
                                "country": country_name,
                                "currency_name": price[3],
                                "exchange_rate": eur_exchange_rate
                            }
                        )
                    print(f"Created {len(eur_countries_to_include)} EUR entries for EU countries")
                else:
                    # For non-EUR currencies, add the original entry
                    price_list.append(
                        {
                            "base_currency" : price[0],
                            "target_currency" : price[1],
                            "country" : price[2],
                            "currency_name" : price[3],
                            "exchange_rate" : float(price[4])
                        }
                    )
                
                forex_list = { "price_list" : price_list }
        
            return forex_list
    
# Define available blocs with their corresponding sets
AVAILABLE_BLOCS = {
    "anzus": ANZUS,
    "five-eyes": FIVE_EYES,
    "aukus": AUKUS,
    "g20": G20,
    "oecd": OECD,
    "apec": APEC,
    "cptpp": CPTPP,
    "rcep": RCEP,
    "pacific-islands-forum": PACIFIC_ISLANDS_FORUM,
    "east-asia-summit": EAST_ASIA_SUMMIT,
    "asean-regional-forum": ASEAN_REGIONAL_FORUM,
    "commonwealth-of-nations": COMMONWEALTH_OF_NATIONS,
    "quad": QUAD,
    "iora": IORA,
    "antarctic-treaty": ANTARCTIC_TREATY
}

def get_bloc_exchange_rates(bloc_name: str):
    """
    Get exchange rates for a specific bloc with optimized caching.
    
    Args:
        bloc_name: Name of the bloc to get exchange rates for
        
    Returns:
        JSONResponse with exchange rates and bloc metadata
    """
    request_start_time = time.time()
    
    try:
        # Use cached bloc countries set for better performance
        bloc_countries = get_bloc_countries_set(bloc_name)
        
        logger.info(f"Processing bloc '{bloc_name}' with {len(bloc_countries)} countries")
        
        result = get_latest_xrates(filter=bloc_countries)
        
        # Check if any data was returned
        if not result or not result.get("price_list"):
            raise HTTPException(
                status_code=404,
                detail=f"No exchange rate data found for bloc '{bloc_name}'"
            )
        
        request_duration = time.time() - request_start_time
        
        # Add metadata about the bloc with performance info
        result["bloc_info"] = {
            "name": bloc_name,
            "countries_in_bloc": len(bloc_countries),
            "exchange_rates_found": len(result["price_list"]),
            "bloc_countries": sorted(list(bloc_countries)),
            "processing_time_seconds": round(request_duration, 4),
            "cache_hit_ratio": round(perf_metrics.get_cache_ratio(), 4)
        }
        
        logger.info(f"Bloc '{bloc_name}' processed in {request_duration:.4f}s with {len(result['price_list'])} results")
        
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
                "X-API-Version": "1.0",
                "X-Bloc-Name": bloc_name,
                "X-Countries-Count": str(len(bloc_countries))
            }
        )
    
    except ValueError as e:
        # Handle unknown bloc error from get_bloc_countries_set
        raise HTTPException(
            status_code=404,
            detail=f"Bloc '{bloc_name}' not found. Available blocs: {', '.join(AVAILABLE_BLOCS.keys())}"
        )
    except Exception as e:
        logger.error(f"Error processing bloc '{bloc_name}': {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving exchange rates for bloc '{bloc_name}': {str(e)}"
        )

@app.get("/")
def read_root():
    """Get all exchange rates"""
    try:
        result = get_latest_xrates()
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "public, max-age=300",  # Cache for 5 minutes
                "X-API-Version": "1.0"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving exchange rates: {str(e)}"
        )

@app.get("/blocs")
def list_available_blocs():
    """List all available blocs"""
    return JSONResponse(
        content={
            "available_blocs": list(AVAILABLE_BLOCS.keys()),
            "total_blocs": len(AVAILABLE_BLOCS),
            "description": "Australian-affiliated multi-national blocs"
        },
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "X-API-Version": "1.0"
        }
    )

# Individual bloc endpoints
@app.get("/anzus")
def get_anzus_rates():
    """Get exchange rates for ANZUS countries (Australia, New Zealand, United States)"""
    return get_bloc_exchange_rates("anzus")

@app.get("/five-eyes")
def get_five_eyes_rates():
    """Get exchange rates for Five Eyes countries (Australia, Canada, New Zealand, United Kingdom, United States)"""
    return get_bloc_exchange_rates("five-eyes")

@app.get("/aukus")
def get_aukus_rates():
    """Get exchange rates for AUKUS countries (Australia, United Kingdom, United States)"""
    return get_bloc_exchange_rates("aukus")

@app.get("/g20")
def get_g20_rates():
    """Get exchange rates for G20 member countries"""
    return get_bloc_exchange_rates("g20")

@app.get("/oecd")
def get_oecd_rates():
    """Get exchange rates for OECD member countries"""
    return get_bloc_exchange_rates("oecd")

@app.get("/apec")
def get_apec_rates():
    """Get exchange rates for APEC member countries"""
    return get_bloc_exchange_rates("apec")

@app.get("/cptpp")
def get_cptpp_rates():
    """Get exchange rates for CPTPP member countries"""
    return get_bloc_exchange_rates("cptpp")

@app.get("/rcep")
def get_rcep_rates():
    """Get exchange rates for RCEP member countries"""
    return get_bloc_exchange_rates("rcep")

@app.get("/pacific-islands-forum")
def get_pacific_islands_forum_rates():
    """Get exchange rates for Pacific Islands Forum member countries"""
    return get_bloc_exchange_rates("pacific-islands-forum")

@app.get("/east-asia-summit")
def get_east_asia_summit_rates():
    """Get exchange rates for East Asia Summit member countries"""
    return get_bloc_exchange_rates("east-asia-summit")

@app.get("/asean-regional-forum")
def get_asean_regional_forum_rates():
    """Get exchange rates for ASEAN Regional Forum member countries"""
    return get_bloc_exchange_rates("asean-regional-forum")

@app.get("/commonwealth-of-nations")
def get_commonwealth_rates():
    """Get exchange rates for Commonwealth of Nations member countries"""
    return get_bloc_exchange_rates("commonwealth-of-nations")

@app.get("/quad")
def get_quad_rates():
    """Get exchange rates for QUAD member countries (Australia, India, Japan, United States)"""
    return get_bloc_exchange_rates("quad")

@app.get("/iora")
def get_iora_rates():
    """Get exchange rates for Indian Ocean Rim Association member countries"""
    return get_bloc_exchange_rates("iora")

@app.get("/antarctic-treaty")
def get_antarctic_treaty_rates():
    """Get exchange rates for Antarctic Treaty member countries"""
    return get_bloc_exchange_rates("antarctic-treaty")