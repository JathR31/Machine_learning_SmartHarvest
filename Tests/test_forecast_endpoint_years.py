import requests
import json

print("=" * 80)
print("Testing /api/forecast Endpoint with Extended Years")
print("=" * 80)

url = "http://127.0.0.1:5000/api/forecast"

# Test: BROCCOLI in ATOK (same as web app screenshot)
data = {
    "CROP": "BROCCOLI",
    "MUNICIPALITY": "ATOK"
}

print("\nRequest:")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print("\n" + "-" * 80)

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ SUCCESS!\n")
        
        print("FORECAST SUMMARY")
        print("-" * 80)
        print(f"Crop: {result['crop']}")
        print(f"Municipality: {result['municipality']}")
        print(f"Trend Direction: {result['trend']['direction']}")
        print(f"Annual Growth Rate: {result['trend']['growth_rate_percent']:.2f}%")
        print(f"Trend Slope: {result['trend']['slope']:.2f} MT/year")
        
        print("\n" + "-" * 80)
        print("FORECAST PREDICTIONS")
        print("-" * 80)
        print(f"Number of forecast years: {len(result['forecast'])}")
        print()
        
        print(f"{'YEAR':<10} {'PREDICTED (MT)':<20} {'YOY GROWTH'}")
        print("-" * 80)
        
        for i, forecast_item in enumerate(result['forecast']):
            year = forecast_item['year']
            production = forecast_item['production']
            
            if i == 0:
                last_prod = result['historical']['last_production']
                yoy_pct = ((production - last_prod) / last_prod) * 100
                yoy_growth = f"{yoy_pct:+.2f}%"
            else:
                prev_production = result['forecast'][i-1]['production']
                yoy_pct = ((production - prev_production) / prev_production) * 100
                yoy_growth = f"{yoy_pct:+.2f}%"
            
            print(f"{year:<10} {production:<20.2f} {yoy_growth}")
        
        print("\n" + "=" * 80)
        print("COMPARISON WITH WEB APP")
        print("=" * 80)
        
        # Expected from web app screenshot
        expected_2025 = 1014.95
        expected_2026 = 955.69
        
        actual_2025 = result['forecast'][0]['production'] if len(result['forecast']) > 0 else None
        actual_2026 = result['forecast'][1]['production'] if len(result['forecast']) > 1 else None
        
        print(f"\n{'Metric':<30} {'Web App':<20} {'API':<20} {'Match?'}")
        print("-" * 80)
        
        if actual_2025:
            match_2025 = "YES" if abs(actual_2025 - expected_2025) < 50 else "NO"
            print(f"{'2025 Production (MT)':<30} {expected_2025:<20.2f} {actual_2025:<20.2f} {match_2025}")
        
        if actual_2026:
            match_2026 = "YES" if abs(actual_2026 - expected_2026) < 50 else "NO"
            print(f"{'2026 Production (MT)':<30} {expected_2026:<20.2f} {actual_2026:<20.2f} {match_2026}")
        
        print(f"\n{'Years Available':<30} {'2 years':<20} {len(result['forecast'])} years")
        
        if len(result['forecast']) >= 6:
            print("\n✅ API SUPPORTS FORECASTS THROUGH 2030!")
            print(f"   Years covered: 2025-{result['forecast'][-1]['year']}")
        elif len(result['forecast']) == 2:
            print("\n⚠️  API ONLY SHOWS 2 YEARS (2025-2026)")
            print("   Need to update web app to request extended forecasts or")
            print("   the forecasts_all.json needs to be reloaded by the API.")
        
    else:
        print(f"❌ ERROR: Status Code {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to API. Make sure ml_api.py is running!")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
