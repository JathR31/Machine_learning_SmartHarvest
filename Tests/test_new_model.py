"""
Test the new crop-sensitive model with different crops
"""

import requests
import json

API_URL = "http://127.0.0.1:5000/api/predict"

# Test with same parameters but different crops
test_crops = ["CABBAGE", "GARDEN PEAS", "BROCCOLI", "CARROTS", "WHITE POTATO", "LETTUCE"]

base_data = {
    "MUNICIPALITY": "ATOK",
    "FARM_TYPE": "IRRIGATED",
    "YEAR": 2025,
    "MONTH": "September",
    "Area_planted_ha": 10
}

print("=" * 90)
print("TESTING NEW CROP-SENSITIVE MODEL")
print("=" * 90)
print(f"\nBase Parameters:")
print(f"  Municipality: {base_data['MUNICIPALITY']}")
print(f"  Farm Type: {base_data['FARM_TYPE']}")
print(f"  Year: {base_data['YEAR']}")
print(f"  Month: {base_data['MONTH']}")
print(f"  Area Planted: {base_data['Area_planted_ha']} ha")
print("\n" + "-" * 90)
print(f"{'CROP':<20} {'PREDICTED (MT)':<20} {'HISTORICAL AVG':<20} {'MATCH?'}")
print("-" * 90)

# Historical averages from our earlier analysis
historical_avg = {
    "CABBAGE": 14.97,
    "GARDEN PEAS": 8.33,
    "BROCCOLI": 11.10,
    "CARROTS": 12.50,
    "WHITE POTATO": 14.07,
    "LETTUCE": 10.31
}

results = []
for crop in test_crops:
    test_data = base_data.copy()
    test_data["CROP"] = crop
    
    try:
        response = requests.post(API_URL, json=test_data)
        if response.status_code == 200:
            result = response.json()
            predicted = result['prediction']['production_mt']
            predicted_per_ha = predicted / base_data['Area_planted_ha']
            hist_avg = historical_avg.get(crop, 0)
            
            # Check if prediction is reasonable compared to historical
            match = "✓" if abs(predicted_per_ha - hist_avg) < 5 else "?"
            
            results.append({
                'crop': crop,
                'predicted': predicted,
                'predicted_per_ha': predicted_per_ha,
                'historical': hist_avg
            })
            
            print(f"{crop:<20} {predicted:<20.2f} {hist_avg:<20.2f} {match}")
        else:
            print(f"{crop:<20} ERROR: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"{crop:<20} ERROR: {str(e)}")

print("-" * 90)

# Check if predictions are different
if len(results) > 1:
    predictions = [r['predicted'] for r in results]
    unique_predictions = set(predictions)
    
    print(f"\n{'RESULTS:'}")
    print(f"  Total crops tested: {len(results)}")
    print(f"  Unique predictions: {len(unique_predictions)}")
    print(f"  Range: {min(predictions):.2f} MT to {max(predictions):.2f} MT")
    print(f"  Variation: {max(predictions) - min(predictions):.2f} MT ({(max(predictions) - min(predictions))/min(predictions)*100:.1f}%)")
    
    if len(unique_predictions) == 1:
        print("\n⚠️  WARNING: All predictions are the same! Something is wrong.")
    elif (max(predictions) - min(predictions)) < 10:
        print("\n⚠️  WARNING: Variation is still quite small (less than 10 MT)")
    else:
        print("\n✓✓✓ SUCCESS: Different crops produce significantly different predictions!")
        
    # Show per-hectare predictions
    print(f"\n{'PER-HECTARE PREDICTIONS:'}")
    print(f"  {'CROP':<20} {'PREDICTED':<15} {'HISTORICAL':<15} {'DIFFERENCE'}")
    print("-" * 90)
    for r in results:
        diff = r['predicted_per_ha'] - r['historical']
        print(f"  {r['crop']:<20} {r['predicted_per_ha']:<15.2f} {r['historical']:<15.2f} {diff:+.2f}")
        
print("\n" + "=" * 90)
