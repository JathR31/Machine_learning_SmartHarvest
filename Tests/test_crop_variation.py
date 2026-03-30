"""
Test to verify that different crops produce different predictions
with all other parameters held constant.
"""

import requests
import json

API_URL = "http://127.0.0.1:5000/api/predict"

# Test with same parameters but different crops
test_crops = ["CABBAGE", "GARDEN PEAS", "BROCCOLI", "CARROTS", "WHITE POTATO"]

base_data = {
    "MUNICIPALITY": "ITOGON",
    "FARM_TYPE": "IRRIGATED",
    "YEAR": 2025,
    "MONTH": "December",
    "Area_planted_ha": 10,
    "Area_harvested_ha": 10,
    "Productivity_mt_ha": 15
}

print("=" * 80)
print("TESTING: Different Crops with Same Parameters")
print("=" * 80)
print(f"\nBase Parameters:")
print(f"  Municipality: {base_data['MUNICIPALITY']}")
print(f"  Farm Type: {base_data['FARM_TYPE']}")
print(f"  Year: {base_data['YEAR']}")
print(f"  Month: {base_data['MONTH']}")
print(f"  Area Planted: {base_data['Area_planted_ha']} ha")
print(f"  Area Harvested: {base_data['Area_harvested_ha']} ha")
print(f"  Productivity: {base_data['Productivity_mt_ha']} MT/ha")
print("\n" + "-" * 80)
print(f"{'CROP':<20} {'PREDICTED (MT)':<20} {'EXPECTED (MT)':<20} {'DIFFERENCE'}")
print("-" * 80)

results = []
for crop in test_crops:
    test_data = base_data.copy()
    test_data["CROP"] = crop
    
    try:
        response = requests.post(API_URL, json=test_data)
        if response.status_code == 200:
            result = response.json()
            predicted = result['prediction']['production_mt']
            expected = result['prediction']['expected_from_productivity']
            difference = result['prediction']['difference']
            
            results.append({
                'crop': crop,
                'predicted': predicted,
                'expected': expected,
                'difference': difference
            })
            
            print(f"{crop:<20} {predicted:<20.2f} {expected:<20.2f} {difference:+.2f}")
        else:
            print(f"{crop:<20} ERROR: {response.status_code}")
    except Exception as e:
        print(f"{crop:<20} ERROR: {str(e)}")

print("-" * 80)

# Check if predictions are different
if len(results) > 1:
    predictions = [r['predicted'] for r in results]
    unique_predictions = set(predictions)
    
    print(f"\n{'RESULTS:'}")
    print(f"  Total crops tested: {len(results)}")
    print(f"  Unique predictions: {len(unique_predictions)}")
    print(f"  Range: {min(predictions):.2f} MT to {max(predictions):.2f} MT")
    print(f"  Variation: {max(predictions) - min(predictions):.2f} MT")
    
    if len(unique_predictions) == 1:
        print("\n⚠️  WARNING: All predictions are the same! Bug still exists.")
    else:
        print("\n✓ SUCCESS: Different crops produce different predictions!")
        
print("\n" + "=" * 80)
