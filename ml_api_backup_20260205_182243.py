"""
Flask API for Benguet Crop Production ML Model
This API serves predictions from the trained Random Forest model
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
model = joblib.load(os.path.join(MODEL_DIR, 'best_rf_model.pkl'))
preprocessor = joblib.load(os.path.join(MODEL_DIR, 'preprocessor.pkl'))

with open(os.path.join(MODEL_DIR, 'model_metadata.json'), 'r') as f:
    metadata = json.load(f)

with open(os.path.join(MODEL_DIR, 'categorical_values.json'), 'r') as f:
    categorical_values = json.load(f)

with open(os.path.join(MODEL_DIR, 'feature_info.json'), 'r') as f:
    feature_info = json.load(f)

# Load pre-generated forecasts
with open(os.path.join(MODEL_DIR, 'forecasts_all.json'), 'r') as f:
    forecasts_all = json.load(f)

with open(os.path.join(MODEL_DIR, 'trends.json'), 'r') as f:
    trends_all = json.load(f)

with open(os.path.join(MODEL_DIR, 'historical_aggregates.json'), 'r') as f:
    historical_aggregates = json.load(f)

with open(os.path.join(MODEL_DIR, 'forecast_metadata.json'), 'r') as f:
    forecast_metadata = json.load(f)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_type': metadata['model_type'],
        'training_date': metadata['training_date'],
        'version': '1.0.0'
    })


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Get model information and available values"""
    return jsonify({
        'metadata': metadata,
        'available_values': categorical_values,
        'feature_info': feature_info
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Make a prediction
    
    Expected JSON input:
    {
        "MUNICIPALITY": "ATOK",
        "FARM_TYPE": "IRRIGATED",
        "YEAR": 2024,
        "MONTH": "JAN" or 1,
        "CROP": "CABBAGE",
        "Area_planted_ha": 10.5
    }
    
    NOTE: Area_harvested_ha and Productivity_mt_ha are optional for backward compatibility
    but are NOT used by the new model
    """
    try:
        data = request.get_json()
        
        # Validate required fields (NEW MODEL - simpler inputs)
        required_fields = [
            'MUNICIPALITY', 'FARM_TYPE', 'YEAR', 'MONTH', 
            'CROP', 'Area_planted_ha'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Convert month to string format for categorical encoding (model expects string months)
        month = data['MONTH']
        if isinstance(month, str):
            # Handle both full month names and 3-letter abbreviations
            month_input = month.upper().strip()
            month_map = {
                'JAN': 'JAN', 'JANUARY': 'JAN',
                'FEB': 'FEB', 'FEBRUARY': 'FEB',
                'MAR': 'MAR', 'MARCH': 'MAR',
                'APR': 'APR', 'APRIL': 'APR',
                'MAY': 'MAY',
                'JUN': 'JUN', 'JUNE': 'JUN',
                'JUL': 'JUL', 'JULY': 'JUL',
                'AUG': 'AUG', 'AUGUST': 'AUG',
                'SEP': 'SEP', 'SEPTEMBER': 'SEP',
                'OCT': 'OCT', 'OCTOBER': 'OCT',
                'NOV': 'NOV', 'NOVEMBER': 'NOV',
                'DEC': 'DEC', 'DECEMBER': 'DEC'
            }
            month_str = month_map.get(month_input, 'JAN')
        else:
            # Convert numeric month to string
            month_str = {
                1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
                7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
            }.get(int(month), 'JAN')
        
        # Create input dataframe (NEW MODEL - only needs Area_planted)
        input_data = pd.DataFrame([{
            'MUNICIPALITY': data['MUNICIPALITY'].upper(),
            'FARM TYPE': data['FARM_TYPE'].upper(),
            'YEAR': int(data['YEAR']),
            'MONTH': month_str,
            'CROP': data['CROP'].upper(),
            'Area planted(ha)': float(data['Area_planted_ha'])
        }])
        
        # Validate categorical values
        if input_data['MUNICIPALITY'].iloc[0] not in categorical_values['MUNICIPALITY']:
            return jsonify({
                'error': f'Invalid MUNICIPALITY. Must be one of: {categorical_values["MUNICIPALITY"]}'
            }), 400
        
        if input_data['FARM TYPE'].iloc[0] not in categorical_values['FARM TYPE']:
            return jsonify({
                'error': f'Invalid FARM_TYPE. Must be one of: {categorical_values["FARM TYPE"]}'
            }), 400
        
        if input_data['CROP'].iloc[0] not in categorical_values['CROP']:
            return jsonify({
                'error': f'Invalid CROP. Must be one of: {categorical_values["CROP"]}'
            }), 400
        
        # Make prediction (model is a Pipeline that includes preprocessing)
        prediction = model.predict(input_data)[0]
        
        # Calculate expected production for comparison (if provided - backward compatibility)
        area_harvested = float(data.get('Area_harvested_ha', data['Area_planted_ha']))
        productivity = float(data.get('Productivity_mt_ha', 0))
        expected_from_productivity = area_harvested * productivity if productivity > 0 else None
        
        response_data = {
            'success': True,
            'prediction': {
                'production_mt': round(prediction, 2),
                'confidence_score': round(metadata.get('test_r2_score', metadata.get('best_cv_score', 0)), 4)
            },
            'input': {
                'municipality': input_data['MUNICIPALITY'].iloc[0],
                'farm_type': input_data['FARM TYPE'].iloc[0],
                'year': int(input_data['YEAR'].iloc[0]),
                'month': input_data['MONTH'].iloc[0],
                'crop': input_data['CROP'].iloc[0],
                'area_planted_ha': float(input_data['Area planted(ha)'].iloc[0])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add comparison metrics if productivity was provided (backward compatibility)
        if expected_from_productivity is not None:
            response_data['prediction']['expected_from_productivity'] = round(expected_from_productivity, 2)
            response_data['prediction']['difference'] = round(prediction - expected_from_productivity, 2)
            response_data['input']['area_harvested_ha'] = area_harvested
            response_data['input']['productivity_mt_ha'] = productivity
        
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


@app.route('/api/batch-predict', methods=['POST'])
def batch_predict():
    """
    Make predictions for multiple inputs
    
    Expected JSON input:
    {
        "predictions": [
            {
                "MUNICIPALITY": "ATOK",
                "FARM_TYPE": "IRRIGATED",
                ...
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if 'predictions' not in data or not isinstance(data['predictions'], list):
            return jsonify({
                'error': 'Expected "predictions" array in request body'
            }), 400
        
        results = []
        for idx, item in enumerate(data['predictions']):
            # Add index for tracking
            item['_index'] = idx
            
            # Make single prediction (reuse the predict logic)
            try:
                # Convert month to string format for categorical encoding (model expects string months)
                month = item['MONTH']
                if isinstance(month, str):
                    # Handle both full month names and 3-letter abbreviations
                    month_input = month.upper().strip()
                    month_map = {
                        'JAN': 'JAN', 'JANUARY': 'JAN',
                        'FEB': 'FEB', 'FEBRUARY': 'FEB',
                        'MAR': 'MAR', 'MARCH': 'MAR',
                        'APR': 'APR', 'APRIL': 'APR',
                        'MAY': 'MAY',
                        'JUN': 'JUN', 'JUNE': 'JUN',
                        'JUL': 'JUL', 'JULY': 'JUL',
                        'AUG': 'AUG', 'AUGUST': 'AUG',
                        'SEP': 'SEP', 'SEPTEMBER': 'SEP',
                        'OCT': 'OCT', 'OCTOBER': 'OCT',
                        'NOV': 'NOV', 'NOVEMBER': 'NOV',
                        'DEC': 'DEC', 'DECEMBER': 'DEC'
                    }
                    month_str = month_map.get(month_input, 'JAN')
                else:
                    # Convert numeric month to string
                    month_str = {
                        1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
                        7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'
                    }.get(int(month), 'JAN')
                
                input_data = pd.DataFrame([{
                    'MUNICIPALITY': item['MUNICIPALITY'].upper(),
                    'FARM TYPE': item['FARM_TYPE'].upper(),
                    'YEAR': int(item['YEAR']),
                    'MONTH': month_str,
                    'CROP': item['CROP'].upper(),
                    'Area planted(ha)': float(item['Area_planted_ha'])
                }])
                
                # Make prediction (model is a Pipeline that includes preprocessing)
                prediction = model.predict(input_data)[0]
                
                results.append({
                    'index': idx,
                    'success': True,
                    'prediction': round(prediction, 2),
                    'input': item
                })
                
            except Exception as e:
                results.append({
                    'index': idx,
                    'success': False,
                    'error': str(e),
                    'input': item
                })
        
        return jsonify({
            'success': True,
            'total': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/available-options', methods=['GET'])
def available_options():
    """Get available categorical options for the form"""
    return jsonify({
        'municipalities': sorted(categorical_values['MUNICIPALITY']),
        'farm_types': sorted(categorical_values['FARM TYPE']),
        'crops': sorted(categorical_values['CROP']),
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
        ]
    })


@app.route('/api/forecast', methods=['POST'])
def forecast():
    """
    Get time-series forecast for crop production (from pre-generated data)
    
    Expected JSON input:
    {
        "CROP": "BROCCOLI",
        "MUNICIPALITY": "BAKUN"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'CROP' not in data:
            return jsonify({
                'error': 'Missing required field: CROP'
            }), 400
        
        if 'MUNICIPALITY' not in data:
            return jsonify({
                'error': 'Missing required field: MUNICIPALITY'
            }), 400
        
        crop = data['CROP'].upper()
        municipality = data['MUNICIPALITY'].upper()
        
        # Create lookup key
        key = f"{crop}_{municipality}"
        
        # Check if forecast exists
        if key not in forecasts_all:
            return jsonify({
                'success': False,
                'error': f'No forecast data available for {crop} in {municipality}',
                'available_crops': sorted(set([k.split('_')[0] for k in forecasts_all.keys()])),
                'available_municipalities': sorted(set([k.split('_')[1] for k in forecasts_all.keys()]))
            }), 404
        
        # Get pre-generated data
        forecast_data = forecasts_all[key]
        trend_data = trends_all[key]
        historical_data = historical_aggregates[key]
        
        # Build response
        result = {
            'success': True,
            'crop': crop,
            'municipality': municipality,
            'forecast': forecast_data['forecast'],
            'historical': {
                'average': historical_data['average'],
                'min': historical_data['min'],
                'max': historical_data['max'],
                'last_year': historical_data['last_year'],
                'last_production': historical_data['last_production'],
                'years_available': historical_data['years_available']
            },
            'trend': {
                'direction': trend_data['direction'],
                'growth_rate_percent': trend_data['growth_rate_percent'],
                'slope': trend_data['slope']
            },
            'metadata': {
                'generated_date': forecast_data['last_update'],
                'source': 'pre-generated',
                'forecast_years': len(forecast_data['forecast'])
            }
        }
        
        return jsonify(result)
            
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()
        }), 500


@app.route('/api/top-crops', methods=['POST'])
def top_crops():
    """
    Get top 5 crops by production for a municipality (historical + predictions)
    
    Expected JSON input:
    {
        "MUNICIPALITY": "ATOK",
        "YEAR": 2025  // Optional, if not provided shows both historical and predicted
    }
    """
    try:
        data = request.get_json()
        
        # Validate required field
        if 'MUNICIPALITY' not in data:
            return jsonify({
                'error': 'Missing required field: MUNICIPALITY'
            }), 400
        
        municipality = data['MUNICIPALITY'].upper()
        target_year = data.get('YEAR', None)
        
        # Load historical data
        df = pd.read_csv('fulldataset.csv')
        df['Production(mt)'] = pd.to_numeric(df['Production(mt)'], errors='coerce')
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
        
        # Filter by municipality
        muni_data = df[df['MUNICIPALITY'].str.upper() == municipality].copy()
        
        if len(muni_data) == 0:
            return jsonify({
                'success': False,
                'error': f'No data found for municipality: {municipality}',
                'available_municipalities': sorted(df['MUNICIPALITY'].unique().tolist())
            }), 404
        
        # Get historical top 5 crops (averaged across all years)
        historical_avg = muni_data.groupby('CROP')['Production(mt)'].mean().sort_values(ascending=False)
        historical_top5 = historical_avg.head(5)
        
        # Get year-by-year historical data for top 5 crops
        top5_crops = historical_top5.index.tolist()
        yearly_historical = {}
        
        for crop in top5_crops:
            crop_data = muni_data[muni_data['CROP'] == crop].groupby('YEAR')['Production(mt)'].sum()
            yearly_historical[crop] = {
                'years': crop_data.index.tolist(),
                'production': crop_data.values.tolist(),
                'average': float(crop_data.mean())
            }
        
        # Get predictions for 2025+ using pre-generated forecasts
        predictions_2025_plus = {}
        
        for crop in top5_crops:
            key = f"{crop}_{municipality}"
            if key in forecasts_all:
                forecast_data = forecasts_all[key]['forecast']
                predictions_2025_plus[crop] = {
                    'forecasts': forecast_data,
                    'average_forecast': sum(f['production'] for f in forecast_data) / len(forecast_data)
                }
        
        # If target year is specified, get specific year data
        if target_year:
            if target_year <= 2024:
                # Historical year
                year_data = muni_data[muni_data['YEAR'] == target_year].groupby('CROP')['Production(mt)'].sum().sort_values(ascending=False)
                top5_year = year_data.head(5)
                
                result = {
                    'success': True,
                    'municipality': municipality,
                    'year': int(target_year),
                    'type': 'historical',
                    'top_crops': [
                        {
                            'rank': i+1,
                            'crop': crop,
                            'production': float(production)
                        }
                        for i, (crop, production) in enumerate(top5_year.items())
                    ]
                }
            else:
                # Future year - use forecasts
                year_predictions = {}
                for crop in top5_crops:
                    key = f"{crop}_{municipality}"
                    if key in forecasts_all:
                        for forecast in forecasts_all[key]['forecast']:
                            if forecast['year'] == target_year:
                                year_predictions[crop] = forecast['production']
                                break
                
                # Sort by predicted production
                sorted_predictions = sorted(year_predictions.items(), key=lambda x: x[1], reverse=True)
                
                result = {
                    'success': True,
                    'municipality': municipality,
                    'year': int(target_year),
                    'type': 'predicted',
                    'top_crops': [
                        {
                            'rank': i+1,
                            'crop': crop,
                            'production': float(production)
                        }
                        for i, (crop, production) in enumerate(sorted_predictions[:5])
                    ]
                }
        else:
            # Return both historical and predictions
            result = {
                'success': True,
                'municipality': municipality,
                'historical_top5': {
                    'crops': [
                        {
                            'rank': i+1,
                            'crop': crop,
                            'average_production': float(production),
                            'yearly_data': yearly_historical[crop]
                        }
                        for i, (crop, production) in enumerate(historical_top5.items())
                    ],
                    'years_covered': f"{int(muni_data['YEAR'].min())}-{int(muni_data['YEAR'].max())}"
                },
                'predicted_top5': {
                    'crops': [
                        {
                            'rank': i+1,
                            'crop': crop,
                            'forecasts': predictions_2025_plus[crop]['forecasts'],
                            'average_forecast': predictions_2025_plus[crop]['average_forecast']
                        }
                        for i, crop in enumerate(top5_crops) if crop in predictions_2025_plus
                    ],
                    'years_covered': '2025-2030'
                }
            }
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'details': traceback.format_exc()                                                                                                                                   
        }), 500


if __name__ == '__main__':
    # Run the Flask app
    # For production, use a proper WSGI server like Gunicorn
    app.run(host='127.0.0.1', port=5000, debug=True)
