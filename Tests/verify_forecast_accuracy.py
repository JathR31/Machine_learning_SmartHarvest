"""
Verify the forecast accuracy shown in the web app
Check BROCCOLI in BAKUN for 2025-2026
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Load the dataset
df = pd.read_csv('fulldataset.csv')

# Clean data
df['Production(mt)'] = pd.to_numeric(df['Production(mt)'], errors='coerce')
df['Area planted(ha)'] = pd.to_numeric(df['Area planted(ha)'], errors='coerce')
df['Area harvested(ha)'] = pd.to_numeric(df['Area harvested(ha)'], errors='coerce')
df['Productivity(mt/ha)'] = pd.to_numeric(df['Productivity(mt/ha)'], errors='coerce')
df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')

# Filter for BROCCOLI in BAKUN
broccoli_bakun = df[(df['CROP'] == 'BROCCOLI') & (df['MUNICIPALITY'] == 'BAKUN')].copy()
broccoli_bakun = broccoli_bakun.dropna(subset=['Production(mt)', 'YEAR'])

print("="*80)
print("BROCCOLI PRODUCTION IN BAKUN - HISTORICAL ANALYSIS")
print("="*80)

if len(broccoli_bakun) > 0:
    print(f"\nHistorical Data Available:")
    print(f"  Years: {int(broccoli_bakun['YEAR'].min())} - {int(broccoli_bakun['YEAR'].max())}")
    print(f"  Number of records: {len(broccoli_bakun)}")
    
    # Yearly totals
    yearly_production = broccoli_bakun.groupby('YEAR')['Production(mt)'].sum().sort_index()
    
    print("\n" + "-"*80)
    print("YEARLY TOTAL PRODUCTION:")
    print("-"*80)
    for year, prod in yearly_production.items():
        print(f"  {int(year)}: {prod:,.2f} MT")
    
    # Statistics
    print("\n" + "-"*80)
    print("STATISTICS:")
    print("-"*80)
    print(f"  Average annual production: {yearly_production.mean():,.2f} MT")
    print(f"  Median annual production:  {yearly_production.median():,.2f} MT")
    print(f"  Min annual production:     {yearly_production.min():,.2f} MT")
    print(f"  Max annual production:     {yearly_production.max():,.2f} MT")
    print(f"  Standard deviation:        {yearly_production.std():,.2f} MT")
    
    # Recent trend (last 5 years)
    recent_years = yearly_production.tail(5)
    if len(recent_years) > 1:
        trend = (recent_years.iloc[-1] - recent_years.iloc[0]) / len(recent_years)
        print(f"\n  Recent 5-year trend: {trend:+,.2f} MT/year")
    
    print("\n" + "="*80)
    print("WEB APP FORECAST ANALYSIS")
    print("="*80)
    print("\nWeb app shows: ~500,000 MT for 2025-2026")
    print(f"Historical average: {yearly_production.mean():,.2f} MT")
    print(f"Historical maximum: {yearly_production.max():,.2f} MT")
    
    forecast_value = 500000
    if forecast_value > yearly_production.max() * 10:
        print(f"\n⚠️  WARNING: Forecast ({forecast_value:,} MT) is MORE THAN 10x the historical max!")
        print("   This suggests the forecast may be INACCURATE or using different methodology")
    elif forecast_value > yearly_production.max() * 2:
        print(f"\n⚠️  WARNING: Forecast ({forecast_value:,} MT) is more than 2x the historical max")
        print("   This is unusually high compared to historical data")
    else:
        print(f"\n✓ Forecast appears reasonable based on historical trends")
    
    # Check what the new ML model would predict
    print("\n" + "="*80)
    print("TESTING NEW ML MODEL PREDICTION")
    print("="*80)
    
    import requests
    
    # Get typical area planted for BROCCOLI in BAKUN
    avg_area = broccoli_bakun['Area planted(ha)'].mean()
    print(f"\nAverage area planted historically: {avg_area:.2f} ha")
    
    # Test with ML API
    test_data = {
        "MUNICIPALITY": "BAKUN",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2025,
        "MONTH": "January",
        "CROP": "BROCCOLI",
        "Area_planted_ha": avg_area
    }
    
    try:
        response = requests.post("http://127.0.0.1:5000/api/predict", json=test_data)
        if response.status_code == 200:
            result = response.json()
            ml_prediction = result['prediction']['production_mt']
            print(f"\nML Model prediction for {avg_area:.2f} ha: {ml_prediction:,.2f} MT")
            print(f"Web app forecast: ~500,000 MT")
            print(f"Difference: {abs(500000 - ml_prediction):,.2f} MT")
            
            if abs(500000 - ml_prediction) > 100000:
                print("\n⚠️  LARGE DISCREPANCY: Web app and ML model show very different values!")
        else:
            print(f"\nML API Error: {response.status_code}")
    except Exception as e:
        print(f"\nCould not connect to ML API: {e}")
    
else:
    print("\n⚠️  NO DATA FOUND for BROCCOLI in BAKUN!")
    print("   The forecast cannot be validated against historical data")
    
    # Check if municipality or crop exists
    print("\n" + "-"*80)
    print("DATA AVAILABILITY CHECK:")
    print("-"*80)
    print(f"  BAKUN exists in data: {'BAKUN' in df['MUNICIPALITY'].values}")
    print(f"  BROCCOLI exists in data: {'BROCCOLI' in df['CROP'].values}")
    
    if 'BAKUN' in df['MUNICIPALITY'].values:
        bakun_data = df[df['MUNICIPALITY'] == 'BAKUN']
        print(f"\n  Crops in BAKUN: {sorted(bakun_data['CROP'].unique().tolist())}")
    
    if 'BROCCOLI' in df['CROP'].values:
        broccoli_data = df[df['CROP'] == 'BROCCOLI']
        print(f"\n  Municipalities with BROCCOLI: {sorted(broccoli_data['MUNICIPALITY'].unique().tolist())}")

print("\n" + "="*80)
