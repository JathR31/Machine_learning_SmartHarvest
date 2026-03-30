import requests
import json

print("=" * 80)
print("Testing Extended Forecasts (2025-2030) for Top Crops")
print("=" * 80)

url = "http://127.0.0.1:5000/api/top-crops"

# Test: Get top 5 crops with extended forecasts
print("\nGetting Top 5 Crops for ATOK (2025-2030)")
print("-" * 80)

data = {
    "MUNICIPALITY": "ATOK"
}

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ SUCCESS!\n")
        
        # Show predicted top 5 with all years
        print("PREDICTED TOP 5 CROPS (2025-2030 Forecast)")
        print("=" * 80)
        
        for crop_data in result['predicted_top5']['crops']:
            print(f"\n{crop_data['rank']}. {crop_data['crop']}")
            print(f"   6-Year Average: {crop_data['average_forecast']:>12,.2f} MT")
            print(f"   Year-by-Year:")
            for forecast in crop_data['forecasts']:
                print(f"     {forecast['year']}: {forecast['production']:>12,.2f} MT")
        
        # Test specific years
        print("\n\n" + "=" * 80)
        print("YEAR-BY-YEAR TOP 5 COMPARISON")
        print("=" * 80)
        
        test_years = [2024, 2025, 2026, 2027, 2028, 2029, 2030]
        
        for year in test_years:
            data_year = {
                "MUNICIPALITY": "ATOK",
                "YEAR": year
            }
            
            response_year = requests.post(url, json=data_year)
            
            if response_year.status_code == 200:
                result_year = response_year.json()
                
                year_type = result_year['type']
                print(f"\n{year} ({year_type.upper()}):")
                print("-" * 60)
                
                for crop_data in result_year['top_crops'][:3]:  # Show top 3 only
                    print(f"  {crop_data['rank']}. {crop_data['crop']:<20} {crop_data['production']:>12,.2f} MT")
        
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

print("\n" + "=" * 80)
print("Testing Complete!")
print("=" * 80)
print("\nNOTE: The API now supports forecasts through 2030!")
print("You can query any year from 2025-2030 for predictions.")
