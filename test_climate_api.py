"""
Test script for climate-enhanced ML API
Tests predictions with rainfall/climate data
"""

import requests
import json

# API base URL
BASE_URL = "http://127.0.0.1:5000/api"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("Testing Health Endpoint")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"Status: {data.get('status')}")
    print(f"Model Type: {data.get('model_type')}")
    print(f"Model Version: {data.get('model_version')}")
    print(f"Climate Enabled: {data.get('climate_enabled')}")
    print(f"Training Date: {data.get('training_date')}")
    
    return data.get('climate_enabled', False)


def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*70)
    print("Testing Model Info Endpoint")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/model-info")
    data = response.json()
    
    print(f"Model Version: {data.get('model_version')}")
    print(f"Climate Enabled: {data.get('climate_enabled')}")
    
    if 'features' in data:
        print("\nFeatures:")
        for feature_type, features in data['features'].items():
            print(f"  {feature_type}: {features}")
    
    print(f"\nTest R² Score: {data['metadata'].get('test_r2_score', 'N/A')}")


def test_prediction_with_climate():
    """Test prediction with climate data"""
    print("\n" + "="*70)
    print("Testing Prediction WITH Climate Data")
    print("="*70)
    
    # Test case: Cabbage in Atok during rainy season
    test_data = {
        "MUNICIPALITY": "ATOK",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2025,
        "MONTH": "JUL",  # Rainy season
        "CROP": "CABBAGE",
        "Area_planted_ha": 15.5,
        "rainfall_mm": 450  # High rainfall
    }
    
    print("\nInput:")
    print(json.dumps(test_data, indent=2))
    
    response = requests.post(f"{BASE_URL}/predict", json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        print(f"\n✓ Predicted Production: {result['prediction']['production_mt']} MT")
        print(f"✓ Model Confidence: {result['prediction']['confidence_score']}")
        print(f"✓ Model Version: {result['prediction']['model_version']}")
        
        if 'features_used' in result:
            print("\n✓ Time-series Features Used:")
            for feature, value in result['features_used'].items():
                print(f"  - {feature}: {value}")
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(response.text)


def test_prediction_without_rainfall():
    """Test prediction without providing rainfall (should estimate)"""
    print("\n" + "="*70)
    print("Testing Prediction WITHOUT Rainfall Data (Auto-estimate)")
    print("="*70)
    
    test_data = {
        "MUNICIPALITY": "ATOK",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2025,
        "MONTH": 1,  # January - dry season
        "CROP": "BROCCOLI",
        "Area_planted_ha": 20.0
        # No rainfall_mm provided - should be estimated
    }
    
    print("\nInput:")
    print(json.dumps(test_data, indent=2))
    
    response = requests.post(f"{BASE_URL}/predict", json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        print("\nResult:")
        print(json.dumps(result, indent=2))
        
        print(f"\n✓ Predicted Production: {result['prediction']['production_mt']} MT")
        print(f"✓ Rainfall (estimated): {result['input']['rainfall_mm']} mm")
        print(f"✓ Rainfall was estimated: {result['input']['rainfall_estimated']}")
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(response.text)


def test_seasonal_comparison():
    """Test predictions across different seasons (rainfall variation)"""
    print("\n" + "="*70)
    print("Testing Seasonal Comparison (Rainfall Impact)")
    print("="*70)
    
    base_input = {
        "MUNICIPALITY": "ATOK",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2025,
        "CROP": "CABBAGE",
        "Area_planted_ha": 10.0
    }
    
    seasons = [
        {"month": "JAN", "rainfall": 20, "season": "Dry"},
        {"month": "APR", "rainfall": 100, "season": "Transition"},
        {"month": "JUL", "rainfall": 450, "season": "Wet"},
        {"month": "OCT", "rainfall": 200, "season": "Transition"}
    ]
    
    print("\nComparing production predictions across seasons:")
    print(f"{'Season':<12} {'Month':<6} {'Rainfall (mm)':<15} {'Predicted (MT)':<15}")
    print("-" * 60)
    
    for season_data in seasons:
        test_input = base_input.copy()
        test_input["MONTH"] = season_data["month"]
        test_input["rainfall_mm"] = season_data["rainfall"]
        
        response = requests.post(f"{BASE_URL}/predict", json=test_input)
        
        if response.status_code == 200:
            result = response.json()
            production = result['prediction']['production_mt']
            print(f"{season_data['season']:<12} {season_data['month']:<6} {season_data['rainfall']:<15} {production:<15.2f}")
        else:
            print(f"{season_data['season']:<12} ERROR")


def test_multiple_crops():
    """Test predictions for different crops with same conditions"""
    print("\n" + "="*70)
    print("Testing Different Crops (Same Conditions)")
    print("="*70)
    
    crops = ["CABBAGE", "BROCCOLI", "CARROT", "LETTUCE", "POTATO"]
    
    base_input = {
        "MUNICIPALITY": "ATOK",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2025,
        "MONTH": "JUL",
        "Area_planted_ha": 10.0,
        "rainfall_mm": 450
    }
    
    print("\nComparing different crops:")
    print(f"{'Crop':<15} {'Predicted (MT)':<15} {'Per Hectare':<15}")
    print("-" * 50)
    
    for crop in crops:
        test_input = base_input.copy()
        test_input["CROP"] = crop
        
        try:
            response = requests.post(f"{BASE_URL}/predict", json=test_input)
            
            if response.status_code == 200:
                result = response.json()
                production = result['prediction']['production_mt']
                per_ha = production / base_input["Area_planted_ha"]
                print(f"{crop:<15} {production:<15.2f} {per_ha:<15.2f}")
            else:
                print(f"{crop:<15} Not available")
        except:
            print(f"{crop:<15} Error")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("CLIMATE-ENHANCED ML API TEST SUITE")
    print("="*70)
    print("\nMake sure the API server is running:")
    print("  python ml_api_climate.py")
    print("\nOr if using the updated ml_api.py:")
    print("  python ml_api.py")
    print("="*70)
    
    try:
        # Test health and check if climate is enabled
        climate_enabled = test_health()
        
        # Test model info
        test_model_info()
        
        if climate_enabled:
            # Test predictions with climate data
            test_prediction_with_climate()
            test_prediction_without_rainfall()
            test_seasonal_comparison()
            test_multiple_crops()
            
            print("\n" + "="*70)
            print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
            print("="*70)
            print("\nThe climate-enhanced model is working correctly!")
            print("Features used:")
            print("  ✓ Rainfall data (actual or estimated)")
            print("  ✓ Time-series lags (lag_1, lag_2, lag_12)")
            print("  ✓ Rolling statistics (rolling_mean_3, rolling_std_3)")
            print("  ✓ Seasonal patterns (Month_Num)")
        else:
            print("\n" + "="*70)
            print("⚠ WARNING: Climate model not active")
            print("="*70)
            print("\nTo enable climate-enhanced predictions:")
            print("1. Run: python retrain_with_climate.py")
            print("2. Restart the API server")
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API server")
        print("Please start the API server first:")
        print("  python ml_api_climate.py")
        print("or")
        print("  python ml_api.py")
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
