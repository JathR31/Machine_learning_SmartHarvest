import requests
import json

# Test a single prediction
test_data = {
    "MUNICIPALITY": "ITOGON",
    "FARM_TYPE": "IRRIGATED",
    "YEAR": 2025,
    "MONTH": "December",
    "CROP": "CABBAGE",
    "Area_planted_ha": 10,
    "Area_harvested_ha": 10,
    "Productivity_mt_ha": 15
}

try:
    response = requests.post("http://127.0.0.1:5000/api/predict", json=test_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
