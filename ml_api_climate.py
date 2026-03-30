"""
Flask API for Benguet Crop Production ML Model - Climate Enhanced Version
This API serves predictions from the Random Forest model trained with climate data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for Laravel to access the API

# Load model artifacts
MODEL_DIR = 'model_artifacts'

# Try to load climate-enhanced model first, fallback to basic model
try:
    model = joblib.load(os.path.join(MODEL_DIR, 'climate_rf_model.pkl'))
    label_encoders = joblib.load(os.path.join(MODEL_DIR, 'label_encoders.pkl'))
    
    with open(os.path.join(MODEL_DIR, 'climate_model_metadata.json'), 'r') as f:
        metadata = json.load(f)
    
    with open(os.path.join(MODEL_DIR, 'climate_categorical_values.json'), 'r') as f:
        categorical_values = json.load(f)
    
    with open(os.path.join(MODEL_DIR, 'rainfall_patterns.json'), 'r') as f:
        rainfall_data = json.load(f)
    
    MODEL_TYPE = 'climate_enhanced'
    print("✓ Loaded climate-enhanced model")
    
except FileNotFoundError:
    # Fallback to basic model
    model = joblib.load(os.path.join(MODEL_DIR, 'best_rf_model.pkl'))
    preprocessor = joblib.load(os.path.join(MODEL_DIR, 'preprocessor.pkl'))
    
    with open(os.path.join(MODEL_DIR, 'model_metadata.json'), 'r') as f:
        metadata = json.load(f)
    
    with open(os.path.join(MODEL_DIR, 'categorical_values.json'), 'r') as f:
        categorical_values = json.load(f)
    
    label_encoders = None
    rainfall_data = None
    MODEL_TYPE = 'basic'
    print("⚠ Using basic model (climate model not found)")

# Load pre-generated forecasts if available
try:
    with open(os.path.join(MODEL_DIR, 'forecasts_all.json'), 'r') as f:
        forecasts_all = json.load(f)
    
    with open(os.path.join(MODEL_DIR, 'trends.json'), 'r') as f:
        trends_all = json.load(f)
    
    with open(os.path.join(MODEL_DIR, 'historical_aggregates.json'), 'r') as f:
        historical_aggregates = json.load(f)
    
    with open(os.path.join(MODEL_DIR, 'forecast_metadata.json'), 'r') as f:
        forecast_metadata = json.load(f)
    
    FORECASTS_AVAILABLE = True
except FileNotFoundError:
    FORECASTS_AVAILABLE = False
    print("⚠ Pre-generated forecasts not available")


def estimate_rainfall(month, municipality):
    """Estimate rainfall based on historical patterns"""
    if rainfall_data is None:
        # Default pattern if no rainfall data available
        rainfall_pattern = {
            1: 20, 2: 30, 3: 50, 4: 100, 5: 200, 6: 350,
            7: 450, 8: 500, 9: 400, 10: 200, 11: 80, 12: 30
        }
        return rainfall_pattern.get(month, 100)
    
    # Use actual average from training data
    monthly_avg = rainfall_data.get('monthly_average', {}).get(str(month), 
                  rainfall_data.get('monthly_baseline', {}).get(str(month), 100))
    
    # Try to get municipality-specific average, otherwise use monthly average
    if 'municipality_average' in rainfall_data:
        muni_avg = rainfall_data['municipality_average'].get(municipality, monthly_avg)
        return muni_avg
    elif 'municipality_factors' in rainfall_data:
        factor = rainfall_data['municipality_factors'].get(municipality, 1.0)
        return monthly_avg * factor
    
    return monthly_avg


def get_historical_production(df, municipality, crop, farm_type, months=12):
    """Get recent historical production for lagged features"""
    mask = (
        (df['MUNICIPALITY'].str.upper() == municipality.upper()) &
        (df['CROP'].str.upper() == crop.upper()) &
        (df['FARM TYPE'].str.upper() == farm_type.upper())
    )
    
    recent = df[mask].sort_values('Date').tail(months)
    
    if len(recent) == 0:
        # No history - use overall averages for this crop
        crop_mask = df['CROP'].str.upper() == crop.upper()
        crop_avg = df[crop_mask]['Production(mt)'].mean()
        return [crop_avg] * months if not pd.isna(crop_avg) else [0] * months
    
    return recent['Production(mt)'].tolist()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_type': metadata['model_type'],
        'model_version': MODEL_TYPE,
        'training_date': metadata['training_date'],
        'version': '2.0.0',
        'climate_enabled': MODEL_TYPE == 'climate_enhanced',
        'forecasts_available': FORECASTS_AVAILABLE
    })


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get model information and available values"""
    response = {
        'metadata': metadata,
        'available_values': categorical_values,
        'model_version': MODEL_TYPE,
        'climate_enabled': MODEL_TYPE == 'climate_enhanced'
    }
    
    if MODEL_TYPE == 'climate_enhanced':
        response['features'] = {
            'categorical': metadata.get('categorical_features', []),
            'numeric': metadata.get('numeric_features', []),
            'climate': ['Rain Value (mm)'],
            'time_series': ['lag_1', 'lag_2', 'lag_12', 'rolling_mean_3', 'rolling_std_3']
        }
    
    return jsonify(response)


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Make a prediction with climate-enhanced model
    
    Expected JSON input:
    {
        "MUNICIPALITY": "ATOK",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2024,
        "MONTH": "JAN" or 1,
        "CROP": "CABBAGE",
        "Area_planted_ha": 10.5,
        "rainfall_mm": 150  // Optional - will be estimated if not provided
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['MUNICIPALITY', 'FARM_TYPE', 'YEAR', 'MONTH', 'CROP', 'Area_planted_ha']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Convert month to numeric and string format
        month = data['MONTH']
        if isinstance(month, str):
            month_input = month.upper().strip()
            month_map = {
                'JAN': 1, 'JANUARY': 1, 'FEB': 2, 'FEBRUARY': 2,
                'MAR': 3, 'MARCH': 3, 'APR': 4, 'APRIL': 4,
                'MAY': 5, 'JUN': 6, 'JUNE': 6, 'JUL': 7, 'JULY': 7,
                'AUG': 8, 'AUGUST': 8, 'SEP': 9, 'SEPTEMBER': 9,
                'OCT': 10, 'OCTOBER': 10, 'NOV': 11, 'NOVEMBER': 11,
                'DEC': 12, 'DECEMBER': 12
            }
            month_num = month_map.get(month_input, 1)
            month_str = {v: k for k, v in month_map.items() if len(k) == 3}.get(month_num, 'JAN')
        else:
            month_num = int(month)
            month_str = {
                1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
                7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
            }.get(month_num, 'JAN')
        
        municipality = data['MUNICIPALITY'].upper()
        farm_type = data['FARM_TYPE'].upper()
        crop = data['CROP'].upper()
        year = int(data['YEAR'])
        area_planted = float(data['Area_planted_ha'])
        
        # Get or estimate rainfall
        if 'rainfall_mm' in data and data['rainfall_mm'] is not None:
            rainfall = float(data['rainfall_mm'])
        else:
            rainfall = estimate_rainfall(month_num, municipality)
        
        # Validate categorical values
        if municipality not in categorical_values.get('MUNICIPALITY', []):
            return jsonify({
                'error': f'Invalid MUNICIPALITY. Must be one of: {categorical_values.get("MUNICIPALITY", [])}'
            }), 400
        
        if farm_type not in categorical_values.get('FARM TYPE', []):
            return jsonify({
                'error': f'Invalid FARM_TYPE. Must be one of: {categorical_values.get("FARM TYPE", [])}'
            }), 400
        
        if crop not in categorical_values.get('CROP', []):
            return jsonify({
                'error': f'Invalid CROP. Must be one of: {categorical_values.get("CROP", [])}'
            }), 400
        
        # Make prediction based on model type
        if MODEL_TYPE == 'climate_enhanced':
            # Load historical data for lagged features
            # Try FINAL_MASTER_DATASET.csv first (has actual rainfall), fallback to fulldataset.csv
            try:
                df = pd.read_csv('FINAL_MASTER_DATASET.csv')
            except FileNotFoundError:
                df = pd.read_csv('fulldataset.csv')
            
            df['MUNICIPALITY'] = df['MUNICIPALITY'].str.upper()
            df['CROP'] = df['CROP'].str.upper()
            df['FARM TYPE'] = df['FARM TYPE'].str.upper()
            
            month_map_data = {'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6,
                             'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10, 'NOV':11, 'DEC':12}
            df['Month_Num'] = df['MONTH'].map(month_map_data)
            df['Date'] = pd.to_datetime(df['YEAR'].astype(str) + '-' + df['Month_Num'].astype(str) + '-01')
            df['Production(mt)'] = pd.to_numeric(df['Production(mt)'], errors='coerce').fillna(0)
            
            # Get historical production for lagged features
            hist_production = get_historical_production(df, municipality, crop, farm_type, months=12)
            
            # Calculate lagged and rolling features
            lag_1 = hist_production[-1] if len(hist_production) >= 1 else 0
            lag_2 = hist_production[-2] if len(hist_production) >= 2 else lag_1
            lag_12 = hist_production[0] if len(hist_production) >= 12 else np.mean(hist_production)
            
            rolling_mean_3 = np.mean(hist_production[-3:]) if len(hist_production) >= 3 else np.mean(hist_production)
            rolling_std_3 = np.std(hist_production[-3:]) if len(hist_production) >= 3 else 0
            
            # Create input dataframe
            input_data = pd.DataFrame([{
                'MUNICIPALITY': municipality,
                'FARM TYPE': farm_type,
                'MONTH': month_str,
                'CROP': crop,
                'Area planted(ha)': area_planted,
                'Rain Value (mm)': rainfall,
                'Month_Num': month_num,
                'Year_Num': year,
                'lag_1': lag_1,
                'lag_2': lag_2,
                'lag_12': lag_12,
                'rolling_mean_3': rolling_mean_3,
                'rolling_std_3': rolling_std_3
            }])
            
            # Encode categorical features
            categorical_features = ['MUNICIPALITY', 'FARM TYPE', 'MONTH', 'CROP']
            for col in categorical_features:
                if col in label_encoders:
                    try:
                        input_data[col] = label_encoders[col].transform(input_data[col])
                    except ValueError:
                        # Unknown category - use most common
                        input_data[col] = 0
            
            # Make prediction
            prediction = model.predict(input_data)[0]
            
            response_data = {
                'success': True,
                'prediction': {
                    'production_mt': round(prediction, 2),
                    'confidence_score': round(metadata.get('test_r2_score', 0), 4),
                    'model_version': 'climate_enhanced'
                },
                'input': {
                    'municipality': municipality,
                    'farm_type': farm_type,
                    'year': year,
                    'month': month_str,
                    'crop': crop,
                    'area_planted_ha': area_planted,
                    'rainfall_mm': round(rainfall, 2),
                    'rainfall_estimated': 'rainfall_mm' not in data or data['rainfall_mm'] is None
                },
                'features_used': {
                    'lag_1': round(lag_1, 2),
                    'lag_2': round(lag_2, 2),
                    'lag_12': round(lag_12, 2),
                    'rolling_mean_3': round(rolling_mean_3, 2),
                    'rolling_std_3': round(rolling_std_3, 2)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        else:
            # Use basic model (fallback)
            input_data = pd.DataFrame([{
                'MUNICIPALITY': municipality,
                'FARM TYPE': farm_type,
                'YEAR': year,
                'MONTH': month_str,
                'CROP': crop,
                'Area planted(ha)': area_planted
            }])
            
            prediction = model.predict(input_data)[0]
            
            response_data = {
                'success': True,
                'prediction': {
                    'production_mt': round(prediction, 2),
                    'confidence_score': round(metadata.get('test_r2_score', metadata.get('best_cv_score', 0)), 4),
                    'model_version': 'basic'
                },
                'input': {
                    'municipality': municipality,
                    'farm_type': farm_type,
                    'year': year,
                    'month': month_str,
                    'crop': crop,
                    'area_planted_ha': area_planted
                },
                'timestamp': datetime.now().isoformat()
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()
        }), 500


@app.route('/api/available-options', methods=['GET'])
def available_options():
    """Get available categorical options for the form"""
    return jsonify({
        'municipalities': sorted(categorical_values.get('MUNICIPALITY', [])),
        'farm_types': sorted(categorical_values.get('FARM TYPE', [])),
        'crops': sorted(categorical_values.get('CROP', [])),
        'months': [
            {'value': 1, 'label': 'January'},
            {'value': 2, 'label': 'February'},
            {'value': 3, 'label': 'March'},
            {'value': 4, 'label': 'April'},
            {'value': 5, 'label': 'May'},
            {'value': 6, 'label': 'June'},
            {'value': 7, 'label': 'July'},
            {'value': 8, 'label': 'August'},
            {'value': 9, 'label': 'September'},
            {'value': 10, 'label': 'October'},
            {'value': 11, 'label': 'November'},
            {'value': 12, 'label': 'December'}
        ],
        'climate_enabled': MODEL_TYPE == 'climate_enhanced'
    })


@app.route('/api/forecast', methods=['POST'])
def forecast():
    """Get time-series forecast for crop production"""
    if not FORECASTS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Pre-generated forecasts not available. Please run generate_forecasts.py first.'
        }), 503
    
    try:
        data = request.get_json()
        
        if 'CROP' not in data or 'MUNICIPALITY' not in data:
            return jsonify({
                'error': 'Missing required fields: CROP and MUNICIPALITY'
            }), 400
        
        crop = data['CROP'].upper()
        municipality = data['MUNICIPALITY'].upper()
        key = f"{crop}_{municipality}"
        
        if key not in forecasts_all:
            return jsonify({
                'success': False,
                'error': f'No forecast data available for {crop} in {municipality}'
            }), 404
        
        result = {
            'success': True,
            'crop': crop,
            'municipality': municipality,
            'forecast': forecasts_all[key]['forecast'],
            'historical': historical_aggregates[key],
            'trend': trends_all[key],
            'metadata': {
                'generated_date': forecasts_all[key]['last_update'],
                'model_version': MODEL_TYPE
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    print("=" * 70)
    print(f"Starting ML API Server - {MODEL_TYPE.upper()} Model")
    print("=" * 70)
    print(f"Model Type: {metadata['model_type']}")
    print(f"Training Date: {metadata['training_date']}")
    print(f"Test R² Score: {metadata.get('test_r2_score', 'N/A')}")
    print(f"Climate Features: {'✓ Enabled' if MODEL_TYPE == 'climate_enhanced' else '✗ Disabled'}")
    print("=" * 70)
    
    app.run(host='127.0.0.1', port=5000, debug=True)
