import requests
import json

# Test the forecast endpoint
url = "http://127.0.0.1:5000/api/forecast"

data = {
    "CROP": "BROCCOLI",
    "MUNICIPALITY": "ATOK"
}

print("=" * 80)
print("Testing /api/forecast endpoint")
print("=" * 80)
print(f"\nRequest URL: {url}")
print(f"Request Data: {json.dumps(data, indent=2)}")
print("\n" + "-" * 80)

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ SUCCESS!")
        print("\n" + "=" * 80)
        print("FORECAST SUMMARY")
        print("=" * 80)
        print(f"Crop: {result['crop']}")
        print(f"Municipality: {result['municipality']}")
        print(f"Trend Direction: {result['trend']['direction']}")
        print(f"Annual Growth Rate: {result['trend']['growth_rate_percent']:.2f}%")
        print(f"Trend Slope: {result['trend']['slope']:.2f} MT/year")
        
        print("\n" + "-" * 80)
        print("HISTORICAL CONTEXT")
        print("-" * 80)
        print(f"Historical Average (10 years): {result['historical']['average']:.2f} MT")
        print(f"Last Year (2024): {result['historical']['last_production']:.2f} MT")
        print(f"Historical Min: {result['historical']['min']:.2f} MT")
        print(f"Historical Max: {result['historical']['max']:.2f} MT")
        
        print("\n" + "-" * 80)
        print("FORECAST PREDICTIONS")
        print("-" * 80)
        print(f"{'YEAR':<10} {'PREDICTED (MT)':<20} {'YOY GROWTH':<15} {'AVG. TREND'}")
        print("-" * 80)
        
        forecasts = result['forecast']
        avg_trend = result['trend']['growth_rate_percent']
        
        for i, forecast_item in enumerate(forecasts):
            year = forecast_item['year']
            production = forecast_item['production']
            
            if i == 0:
                yoy_growth = "baseline"
                # Calculate YoY from last historical year
                if 'last_production' in result['historical']:
                    last_prod = result['historical']['last_production']
                    yoy_pct = ((production - last_prod) / last_prod) * 100
                    yoy_growth = f"{yoy_pct:+.2f}%"
            else:
                prev_production = forecasts[i-1]['production']
                yoy_pct = ((production - prev_production) / prev_production) * 100
                yoy_growth = f"{yoy_pct:+.2f}%"
            
            print(f"{year:<10} {production:<20.2f} {yoy_growth:<15} {avg_trend:+.2f}%/year")
        
        print("\n" + "=" * 80)
        print("COMPARISON WITH WEB APP SCREENSHOT")
        print("=" * 80)
        
        # Expected values from screenshot
        expected_2025 = 1039.68
        expected_2026 = 995.40
        expected_trend = -0.63
        expected_slope = -6.46
        
        actual_2025 = forecasts[0]['production'] if len(forecasts) > 0 else None
        actual_2026 = forecasts[1]['production'] if len(forecasts) > 1 else None
        actual_trend = result['trend']['growth_rate_percent']
        actual_slope = result['trend']['slope']
        
        print(f"\n{'Metric':<30} {'Expected':<20} {'Actual':<20} {'Match?'}")
        print("-" * 80)
        
        if actual_2025:
            match_2025 = "✅" if abs(actual_2025 - expected_2025) < 0.01 else "❌"
            print(f"{'2025 Production':<30} {expected_2025:<20.2f} {actual_2025:<20.2f} {match_2025}")
        
        if actual_2026:
            match_2026 = "✅" if abs(actual_2026 - expected_2026) < 0.01 else "❌"
            print(f"{'2026 Production':<30} {expected_2026:<20.2f} {actual_2026:<20.2f} {match_2026}")
        
        match_trend = "✅" if abs(actual_trend - expected_trend) < 0.01 else "❌"
        print(f"{'Annual Growth Rate (%)':<30} {expected_trend:<20.2f} {actual_trend:<20.2f} {match_trend}")
        
        match_slope = "✅" if abs(actual_slope - expected_slope) < 0.01 else "❌"
        print(f"{'Trend Slope (MT/year)':<30} {expected_slope:<20.2f} {actual_slope:<20.2f} {match_slope}")
        
        print("\n" + "=" * 80)
        
    else:
        print(f"❌ ERROR: Status Code {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to API. Make sure ml_api.py is running!")
    print("\nTo start the API, run: python ml_api.py")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
