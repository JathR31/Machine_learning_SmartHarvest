"""
Extended test to verify crop variations across different parameters
"""

import requests
import json

API_URL = "http://127.0.0.1:5000/api/predict"

test_scenarios = [
    # Scenario 1: Low productivity
    {
        "params": {"MUNICIPALITY": "BUGUIAS", "FARM_TYPE": "RAINFED", "YEAR": 2024, 
                   "MONTH": "June", "Area_planted_ha": 5, "Area_harvested_ha": 5, "Productivity_mt_ha": 8},
        "crops": ["CABBAGE", "LETTUCE", "WHITE POTATO", "CARROTS"]
    },
    # Scenario 2: High productivity
    {
        "params": {"MUNICIPALITY": "ATOK", "FARM_TYPE": "IRRIGATED", "YEAR": 2025, 
                   "MONTH": "March", "Area_planted_ha": 20, "Area_harvested_ha": 20, "Productivity_mt_ha": 25},
        "crops": ["CABBAGE", "BROCCOLI", "CAULIFLOWER", "SNAP BEANS"]
    },
]

for idx, scenario in enumerate(test_scenarios, 1):
    print(f"\n{'='*80}")
    print(f"SCENARIO {idx}: {scenario['params']['MUNICIPALITY']} - {scenario['params']['FARM_TYPE']}")
    print(f"Productivity: {scenario['params']['Productivity_mt_ha']} MT/ha")
    print(f"{'='*80}")
    print(f"{'CROP':<20} {'PREDICTED (MT)':<20} {'EXPECTED (MT)':<20} {'DIFFERENCE'}")
    print("-" * 80)
    
    results = []
    for crop in scenario['crops']:
        test_data = scenario['params'].copy()
        test_data["CROP"] = crop
        
        try:
            response = requests.post(API_URL, json=test_data)
            if response.status_code == 200:
                result = response.json()
                predicted = result['prediction']['production_mt']
                expected = result['prediction']['expected_from_productivity']
                difference = result['prediction']['difference']
                
                results.append(predicted)
                print(f"{crop:<20} {predicted:<20.2f} {expected:<20.2f} {difference:+.2f}")
        except Exception as e:
            print(f"{crop:<20} ERROR: {str(e)}")
    
    if results:
        print("-" * 80)
        print(f"Variation: {max(results) - min(results):.2f} MT (Range: {min(results):.2f} - {max(results):.2f})")
