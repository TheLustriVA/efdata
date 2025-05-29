import json

with open("country_codes.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

for country in payload['countries']:
    print(f"{country['country']} --> {country['currency']} --> {country['code']}")