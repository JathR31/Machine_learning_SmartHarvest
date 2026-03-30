"""
Test predictions for years 2025-2030 with exact same inputs
"""
import requests

API_URL = "http://127.0.0.1:5000/api/predict"

base_data = {
    "MUNICIPALITY": "ATOK",
    "FARM_TYPE": "IRRIGATED",
    "MONTH": "August",
    "CROP": "CABBAGE",
    "Area_planted_ha": 10
}

test_years = [2025, 2026, 2027, 2028, 2029, 2030]

print("="*80)
print("TESTING: Years 2025-2030 with Identical Inputs")
print("="*80)
print(f"\nFixed Parameters:")
print(f"  Municipality: {base_data['MUNICIPALITY']}")
print(f"  Farm Type: {base_data['FARM_TYPE']}")
print(f"  Month: {base_data['MONTH']}")
print(f"  Crop: {base_data['CROP']}")
print(f"  Area Planted: {base_data['Area_planted_ha']} ha")
print("\n" + "-"*80)
print(f"{'YEAR':<10} {'PREDICTED (MT)':<20} {'CHANGE FROM PREVIOUS'}")
print("-"*80)

results = []
for i, year in enumerate(test_years):
    test_data = base_data.copy()
    test_data["YEAR"] = year
    
    try:
        response = requests.post(API_URL, json=test_data)
        if response.status_code == 200:
            result = response.json()
            predicted = result['prediction']['production_mt']
            results.append({'year': year, 'predicted': predicted})
            
            if i > 0:
                change = predicted - results[i-1]['predicted']
                change_pct = (change / results[i-1]['predicted'] * 100) if results[i-1]['predicted'] > 0 else 0
                print(f"{year:<10} {predicted:<20.2f} {change:+.2f} MT ({change_pct:+.2f}%)")
            else:
                print(f"{year:<10} {predicted:<20.2f} (baseline)")
        else:
            print(f"{year:<10} ERROR: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"{year:<10} ERROR: {str(e)}")

print("-"*80)

if len(results) > 1:
    predictions = [r['predicted'] for r in results]
    unique_predictions = len(set(predictions))
    
    print(f"\n{'SUMMARY:'}")
    print(f"  Years tested: {len(results)}")
    print(f"  Unique prediction values: {unique_predictions}")
    print(f"  Minimum prediction: {min(predictions):.2f} MT (Year {results[predictions.index(min(predictions))]['year']})")
    print(f"  Maximum prediction: {max(predictions):.2f} MT (Year {results[predictions.index(max(predictions))]['year']})")
    print(f"  Total variation: {max(predictions) - min(predictions):.2f} MT")
    print(f"  Average prediction: {sum(predictions)/len(predictions):.2f} MT")
    
    print(f"\n{'YEAR-BY-YEAR COMPARISON:'}")
    for r in results:
        print(f"  {r['year']}: {r['predicted']:.2f} MT")
    
    if unique_predictions == 1:
        print("\n❌ PROBLEM: All predictions are IDENTICAL!")
        print("   Year is not affecting predictions at all.")
    elif unique_predictions <= 3:
        print(f"\n⚠️  WARNING: Only {unique_predictions} unique values across 6 years")
        print("   Year has very minimal effect on predictions.")
    else:
        print("\n✓ Year is affecting predictions")

print("\n" + "="*80)
print("ANALYSIS:")
print("="*80)
print("Based on the feature importance from model training:")
print("  - Area planted: 28.91% (dominant)")
print("  - YEAR: 8.66% (moderate)")
print("  - CROP: 7.78% (moderate)")
print("  - Farm Type: 8.35%")
print("  - Municipality: varies by location")
print("\nIf predictions are identical or very similar, it means:")
print("1. The model learned that year doesn't significantly affect production")
print("2. OR the model is plateauing for years beyond training data (2015-2024)")
print("="*80)
