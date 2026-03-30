import pandas as pd

# Load the dataset
df = pd.read_csv('fulldataset.csv')

# Filter for CABBAGE in ATOK for year 2024
cabbage_atok_2024 = df[
    (df['CROP'].str.upper() == 'CABBAGE') & 
    (df['MUNICIPALITY'].str.upper() == 'ATOK') & 
    (df['YEAR'] == 2024)
]

print("=" * 80)
print("CABBAGE in ATOK - 2024 Data Verification")
print("=" * 80)

if len(cabbage_atok_2024) > 0:
    # Calculate totals - ensure numeric columns
    total_production = pd.to_numeric(cabbage_atok_2024['Production(mt)'], errors='coerce').sum()
    total_area_harvested = pd.to_numeric(cabbage_atok_2024['Area harvested(ha)'], errors='coerce').sum()
    avg_productivity = pd.to_numeric(cabbage_atok_2024['Productivity(mt/ha)'], errors='coerce').mean()
    
    # Convert MT to KG for comparison with web app
    total_production_kg = total_production * 1000
    
    print(f"\nTotal Production: {total_production:.2f} MT ({total_production_kg:.2f} kg)")
    print(f"Total Area Harvested: {total_area_harvested:.2f} ha")
    print(f"Average Productivity: {avg_productivity:.2f} MT/ha")
    print(f"Number of Records: {len(cabbage_atok_2024)}")
    
    print("\n" + "-" * 80)
    print("COMPARISON WITH WEB APP")
    print("-" * 80)
    
    # Expected from web app screenshot (in kg, but labeled as kg in display)
    expected_production = 21143.64  # This is in MT from web app
    expected_area_ha = 1185.92
    expected_productivity = 16.47  # This is in kg/ha from web app
    
    print(f"\n{'Metric':<30} {'Web App':<20} {'Dataset':<20} {'Match?'}")
    print("-" * 80)
    
    # Compare production (web app shows MT, not kg despite "kg" label)
    match_prod = "YES" if abs(total_production - expected_production) < 0.01 else "NO"
    print(f"{'Total Production (MT)':<30} {expected_production:<20.2f} {total_production:<20.2f} {match_prod}")
    
    # Compare area harvested
    match_area = "YES" if abs(total_area_harvested - expected_area_ha) < 0.01 else "NO"
    print(f"{'Area Harvested (ha)':<30} {expected_area_ha:<20.2f} {total_area_harvested:<20.2f} {match_area}")
    
    # Compare productivity (web app shows kg/ha which is actually MT/ha * 1000)
    actual_productivity_mt_ha = total_production / total_area_harvested if total_area_harvested > 0 else 0
    match_prod_rate = "YES" if abs(actual_productivity_mt_ha - expected_productivity) < 0.01 else "NO"
    print(f"{'Productivity (MT/ha)':<30} {expected_productivity:<20.2f} {actual_productivity_mt_ha:<20.2f} {match_prod_rate}")
    
    print("\n" + "-" * 80)
    print("FARM TYPE DISTRIBUTION (2024)")
    print("-" * 80)
    
    # Group by farm type
    farm_type_summary = cabbage_atok_2024.groupby('FARM TYPE').apply(
        lambda x: pd.Series({
            'Production(mt)': pd.to_numeric(x['Production(mt)'], errors='coerce').sum(),
            'Area harvested(ha)': pd.to_numeric(x['Area harvested(ha)'], errors='coerce').sum()
        }), include_groups=False
    )
    
    for farm_type in farm_type_summary.index:
        prod = farm_type_summary.loc[farm_type, 'Production(mt)']
        area = farm_type_summary.loc[farm_type, 'Area harvested(ha)']
        percentage = (prod / total_production) * 100
        prod_kg = prod * 1000
        
        print(f"{farm_type:<15} {prod_kg:>12,.2f} kg  ({area:>8.2f} ha)  {percentage:>5.1f}%")
    
    # Compare with web app percentages
    print("\n" + "-" * 80)
    print("FARM TYPE PERCENTAGE COMPARISON")
    print("-" * 80)
    
    web_app_irrigated_pct = 40.3
    web_app_rainfed_pct = 59.7
    web_app_irrigated_mt = 8520.33  # Web app shows "kg" but actually MT
    web_app_rainfed_mt = 12623.31   # Web app shows "kg" but actually MT
    
    if 'IRRIGATED' in farm_type_summary.index:
        irrigated_prod_mt = farm_type_summary.loc['IRRIGATED', 'Production(mt)']
        irrigated_pct = (farm_type_summary.loc['IRRIGATED', 'Production(mt)'] / total_production) * 100
        
        match_irr_pct = "YES" if abs(irrigated_pct - web_app_irrigated_pct) < 0.5 else "NO"
        match_irr_mt = "YES" if abs(irrigated_prod_mt - web_app_irrigated_mt) < 0.01 else "NO"
        
        print(f"IRRIGATED % : Web App = {web_app_irrigated_pct:.1f}%, Dataset = {irrigated_pct:.1f}% {match_irr_pct}")
        print(f"IRRIGATED MT: Web App = {web_app_irrigated_mt:.2f}, Dataset = {irrigated_prod_mt:.2f} {match_irr_mt}")
    
    if 'RAINFED' in farm_type_summary.index:
        rainfed_prod_mt = farm_type_summary.loc['RAINFED', 'Production(mt)']
        rainfed_pct = (farm_type_summary.loc['RAINFED', 'Production(mt)'] / total_production) * 100
        
        match_rf_pct = "YES" if abs(rainfed_pct - web_app_rainfed_pct) < 0.5 else "NO"
        match_rf_mt = "YES" if abs(rainfed_prod_mt - web_app_rainfed_mt) < 0.01 else "NO"
        
        print(f"RAINFED %   : Web App = {web_app_rainfed_pct:.1f}%, Dataset = {rainfed_pct:.1f}% {match_rf_pct}")
        print(f"RAINFED MT  : Web App = {web_app_rainfed_mt:.2f}, Dataset = {rainfed_prod_mt:.2f} {match_rf_mt}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION:")
    if match_prod == "YES" and match_area == "YES" and match_prod_rate == "YES":
        print("ALL METRICS MATCH! The web app is displaying ACCURATE data.")
    else:
        print("Some metrics don't match. Please investigate discrepancies.")
    print("=" * 80)
    
else:
    print("\nNo data found for CABBAGE in ATOK for 2024")
