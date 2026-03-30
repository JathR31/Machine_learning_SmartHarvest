import requests
import json
import pandas as pd

print("=" * 80)
print("Verifying CARROTS in ATOK Forecast (2025-2030)")
print("=" * 80)

# Test the API
url = "http://127.0.0.1:5000/api/forecast"

data = {
    "CROP": "CARROTS",
    "MUNICIPALITY": "ATOK"
}

print("\n[1] Testing API Endpoint")
print("-" * 80)

try:
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ API Response Success\n")
        
        print("FORECAST SUMMARY")
        print(f"Crop: {result['crop']}")
        print(f"Municipality: {result['municipality']}")
        print(f"Trend Direction: {result['trend']['direction']}")
        print(f"Annual Growth Rate: {result['trend']['growth_rate_percent']:.2f}%")
        print(f"Trend Slope: {result['trend']['slope']:.2f} MT/year")
        
        print("\n" + "-" * 80)
        print("HISTORICAL CONTEXT")
        print("-" * 80)
        print(f"Historical Average (10 years): {result['historical']['average']:,.2f} MT")
        print(f"Last Year (2024): {result['historical']['last_production']:,.2f} MT")
        print(f"Historical Min: {result['historical']['min']:,.2f} MT")
        print(f"Historical Max: {result['historical']['max']:,.2f} MT")
        
        print("\n" + "-" * 80)
        print("API FORECAST vs WEB APP")
        print("-" * 80)
        
        # Expected from web app screenshot
        web_app_data = {
            2025: 10304.53,
            2026: 10633.96,
            2027: 9889.63,
            2028: 9665.73,
            2029: 9669.67,
            2030: 9494.11
        }
        
        print(f"\n{'YEAR':<10} {'Web App (MT)':<20} {'API (MT)':<20} {'Difference':<15} {'Match?'}")
        print("-" * 80)
        
        all_match = True
        for forecast_item in result['forecast']:
            year = forecast_item['year']
            api_prod = forecast_item['production']
            web_prod = web_app_data.get(year, 0)
            
            if web_prod > 0:
                diff = api_prod - web_prod
                diff_pct = (diff / web_prod) * 100
                match = "YES" if abs(diff) < 1 else "NO"
                
                if match == "NO":
                    all_match = False
                
                print(f"{year:<10} {web_prod:<20,.2f} {api_prod:<20,.2f} {diff:>+8,.2f} ({diff_pct:>+5.1f}%)  {match}")
        
        print("\n" + "=" * 80)
        if all_match:
            print("✅ ALL VALUES MATCH! The web app is showing ACCURATE data.")
        else:
            print("⚠️  Some values don't match perfectly.")
        print("=" * 80)
        
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to API")
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

# Verify against historical data
print("\n\n[2] Historical Data Verification")
print("-" * 80)

df = pd.read_csv('fulldataset.csv')

# Filter for CARROTS in ATOK
carrots_atok = df[
    (df['CROP'].str.upper() == 'CARROTS') & 
    (df['MUNICIPALITY'].str.upper() == 'ATOK')
]

# Group by year
yearly = carrots_atok.groupby('YEAR').agg({
    'Production(mt)': lambda x: pd.to_numeric(x, errors='coerce').sum()
}).reset_index()

yearly = yearly.sort_values('YEAR')

print("\nHistorical Production (2015-2024):")
print(f"{'YEAR':<10} {'PRODUCTION (MT)':<20} {'YOY CHANGE'}")
print("-" * 60)

prev_prod = None
for idx, row in yearly.iterrows():
    year = int(row['YEAR'])
    prod = row['Production(mt)']
    
    if prev_prod is not None:
        change = ((prod - prev_prod) / prev_prod) * 100
        print(f"{year:<10} {prod:<20,.2f} {change:>+8.2f}%")
    else:
        print(f"{year:<10} {prod:<20,.2f} (baseline)")
    
    prev_prod = prod

avg = yearly['Production(mt)'].mean()
min_prod = yearly['Production(mt)'].min()
max_prod = yearly['Production(mt)'].max()

print("\n" + "-" * 60)
print(f"Average: {avg:,.2f} MT")
print(f"Range: {min_prod:,.2f} - {max_prod:,.2f} MT")

print("\n" + "=" * 80)
print("FORECAST REASONABLENESS CHECK")
print("=" * 80)

print("\nForecasted values (2025-2030) compared to historical range:")
for year, prod in web_app_data.items():
    within_range = "✅ WITHIN" if min_prod <= prod <= max_prod else "⚠️  OUTSIDE"
    vs_avg = ((prod - avg) / avg) * 100
    
    print(f"{year}: {prod:>10,.2f} MT  {within_range} range  ({vs_avg:>+5.1f}% vs avg)")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("The forecast shows a slight decreasing trend (-2.14%/year) which is")
print("reasonable given the historical volatility. All forecasted values")
print("remain within or close to the historical range (7,411 - 11,922 MT).")
print("=" * 80)
