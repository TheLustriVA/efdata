import json
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('PSQL_DB')
DB_USER = os.getenv('PSQL_USER')
DB_PASSWORD = os.getenv('PSQL_PW')
DB_HOST = os.getenv('PSQL_HOST')
DB_PORT = os.getenv('PSQL_PORT')

# Path to the JSON file
json_file_path = 'currencies.json'

# Read JSON data from file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Create a cursor object
cur = conn.cursor()

# Debug: List all tables in the public schema
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
tables = cur.fetchall()
print("Tables in public schema:", tables)

# Insert data into the currencies table
for country_info in data['countries']:
    try:
        cur.execute(
            "INSERT INTO public.currencies (country, currency_name, code) VALUES (%s, %s, %s)",
            (country_info['country'], country_info['currency'], country_info['code'])
        )
    except psycopg2.errors.UniqueViolation:
        print(f"Skipping duplicate entry for code: {country_info['code']}")

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()