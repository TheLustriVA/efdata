import os
from sqlite3 import Cursor
import psycopg2
from typing import Union
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

def get_latest_xrates(filter:list[str] = None)->dict:
    try:
        db_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        db_conn.autocommit = False
    except db_conn.OperationalError as e:
            print(f"Unable to connect to the database: {e}")
        

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
                pass
            else:
                forex_prices = forex_full
                for price in forex_prices:
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
    
@app.get("/")
def read_root():
    return get_latest_xrates()