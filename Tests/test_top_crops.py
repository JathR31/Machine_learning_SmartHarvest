import requests
import json

print("=" * 80)
print("Testing /api/top-crops Endpoint")
print("=" * 80)

url = "http://127.0.0.1:5000/api/top-crops"

# Test 1: Get historical + predicted top 5 crops for ATOK
print("\n[TEST 1] Historical + Predicted Top 5 Crops for ATOK")
print("-" * 80)

data = {
    "MUNICIPALITY": "ATOK"
}

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ SUCCESS!\n")
        
        # Historical Top 5
        print("HISTORICAL TOP 5 CROPS (Average Production)")
        print(f"Years Covered: {result['historical_top5']['years_covered']}")
        print("-" * 80)
        
        for crop_data in result['historical_top5']['crops']:
            print(f"{crop_data['rank']}. {crop_data['crop']:<20} {crop_data['average_production']:>12,.2f} MT (avg)")
        
        # Predicted Top 5
        print("\n" + "=" * 80)
        print("PREDICTED TOP 5 CROPS (2025-2026 Forecast)")
        print(f"Years Covered: {result['predicted_top5']['years_covered']}")
        print("-" * 80)
        
        for crop_data in result['predicted_top5']['crops']:
            print(f"\n{crop_data['rank']}. {crop_data['crop']}")
            print(f"   Average Forecast: {crop_data['average_forecast']:>12,.2f} MT")
            print(f"   Year-by-Year:")
            for forecast in crop_data['forecasts']:
                print(f"     {forecast['year']}: {forecast['production']:>12,.2f} MT")
        
    else:
        print(f"❌ ERROR: Status Code {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to API. Make sure ml_api.py is running!")
    print("\nTo start the API, run: python ml_api.py")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")


# Test 2: Get top 5 crops for a specific year (2024 - historical)
print("\n\n" + "=" * 80)
print("[TEST 2] Top 5 Crops for ATOK in 2024 (Historical)")
print("-" * 80)

data = {
    "MUNICIPALITY": "ATOK",
    "YEAR": 2024
}

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ SUCCESS!\n")
        print(f"Municipality: {result['municipality']}")
        print(f"Year: {result['year']}")
        print(f"Type: {result['type']}")
        print("-" * 80)
        
        for crop_data in result['top_crops']:
            print(f"{crop_data['rank']}. {crop_data['crop']:<20} {crop_data['production']:>12,.2f} MT")
    else:
        print(f"❌ ERROR: Status Code {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to API")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")


# Test 3: Get top 5 crops for a specific year (2025 - predicted)
print("\n\n" + "=" * 80)
print("[TEST 3] Top 5 Crops for ATOK in 2025 (Predicted)")
print("-" * 80)

data = {
    "MUNICIPALITY": "ATOK",
    "YEAR": 2025
}

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ SUCCESS!\n")
        print(f"Municipality: {result['municipality']}")
        print(f"Year: {result['year']}")
        print(f"Type: {result['type']}")
        print("-" * 80)
        
        for crop_data in result['top_crops']:
            print(f"{crop_data['rank']}. {crop_data['crop']:<20} {crop_data['production']:>12,.2f} MT")
    else:
        print(f"❌ ERROR: Status Code {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to API")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")


print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
