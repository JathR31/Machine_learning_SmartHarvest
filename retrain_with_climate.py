"""
Enhanced Model Training with Climate Data
Based on COMBINED.ipynb approach - includes rainfall and lagged features
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import joblib
import json
import os
from datetime import datetime

# Configuration
MODEL_DIR = 'model_artifacts'
os.makedirs(MODEL_DIR, exist_ok=True)

def create_lagged_features(df, target_col='Production(mt)', lags=[1, 2, 12]):
    """Create lagged features for time series"""
    df_sorted = df.sort_values('Date')
    
    for lag in lags:
        df_sorted[f'lag_{lag}'] = df_sorted.groupby(['MUNICIPALITY', 'CROP', 'FARM TYPE'])[target_col].shift(lag)
    
    # Add seasonal features
    df_sorted['Month_Num'] = df_sorted['Date'].dt.month
    df_sorted['Year_Num'] = df_sorted['Date'].dt.year
    
    # Calculate rolling statistics
    df_sorted['rolling_mean_3'] = df_sorted.groupby(['MUNICIPALITY', 'CROP', 'FARM TYPE'])[target_col].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    df_sorted['rolling_std_3'] = df_sorted.groupby(['MUNICIPALITY', 'CROP', 'FARM TYPE'])[target_col].transform(
        lambda x: x.rolling(window=3, min_periods=1).std()
    )
    
    return df_sorted

def load_and_prepare_data():
    """Load and prepare the dataset with climate features"""
    print("Loading dataset with actual climate data...")
    
    # Try to load FINAL_MASTER_DATASET.csv first (has actual rainfall data)
    try:
        df = pd.read_csv('FINAL_MASTER_DATASET.csv')
        print(f"✓ Loaded FINAL_MASTER_DATASET.csv with actual rainfall data")
    except FileNotFoundError:
        print("⚠ FINAL_MASTER_DATASET.csv not found, trying fulldataset.csv...")
        df = pd.read_csv('fulldataset.csv')
        print("✓ Loaded fulldataset.csv")
    
    # Clean numeric columns
    numeric_cols = ['Production(mt)', 'Area planted(ha)', 'Area harvested(ha)', 
                    'Productivity(mt/ha)', 'Rain Value (mm)']
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Standardize text columns
    text_cols = ['MUNICIPALITY', 'FARM TYPE', 'MONTH', 'CROP']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
    
    # Create date column
    month_map = {'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6,
                 'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10, 'NOV':11, 'DEC':12}
    df['Month_Num'] = df['MONTH'].map(month_map)
    df['Date'] = pd.to_datetime(df['YEAR'].astype(str) + '-' + df['Month_Num'].astype(str) + '-01')
    
    # Check if rainfall data exists, if not, add simulated data
    if 'Rain Value (mm)' not in df.columns or df['Rain Value (mm)'].isna().all():
        print("⚠ No rainfall data found, adding simulated rainfall patterns...")
        
        rainfall_pattern = {
            1: 20, 2: 30, 3: 50, 4: 100, 5: 200, 6: 350,  # Jan-Jun
            7: 450, 8: 500, 9: 400, 10: 200, 11: 80, 12: 30  # Jul-Dec
        }
        
        municipality_rainfall_factor = {
            'ATOK': 1.2, 'BAKUN': 1.15, 'BOKOD': 1.1, 'BUGUIAS': 1.2,
            'ITOGON': 0.9, 'KABAYAN': 1.1, 'KAPANGAN': 1.0, 'KIBUNGAN': 1.05,
            'LA TRINIDAD': 0.95, 'MANKAYAN': 1.15, 'SABLAN': 0.9, 'TUBA': 0.85, 'TUBLAY': 1.0
        }
        
        df['Rain Value (mm)'] = df.apply(
            lambda row: rainfall_pattern.get(row['Month_Num'], 100) * 
                       municipality_rainfall_factor.get(row['MUNICIPALITY'], 1.0) *
                       np.random.uniform(0.8, 1.2),
            axis=1
        )
    else:
        # Clean existing rainfall data
        df['Rain Value (mm)'] = df['Rain Value (mm)'].fillna(0)
        print(f"✓ Using actual rainfall data")
        print(f"  Rainfall range: {df['Rain Value (mm)'].min():.1f} to {df['Rain Value (mm)'].max():.1f} mm")
        print(f"  Average rainfall: {df['Rain Value (mm)'].mean():.1f} mm")
    
    print(f"\nDataset loaded: {len(df)} records")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"Municipalities: {df['MUNICIPALITY'].nunique()}")
    print(f"Crops: {df['CROP'].nunique()}")
    
    return df

def train_climate_enhanced_model():
    """Train Random Forest model with climate and lagged features"""
    
    # Load data
    df = load_and_prepare_data()
    
    # Create lagged features
    print("\nCreating time-series features...")
    df = create_lagged_features(df, target_col='Production(mt)', lags=[1, 2, 12])
    
    # Remove rows with NaN in lagged features (first 12 months per group)
    df_model = df.dropna(subset=['lag_1', 'lag_2', 'lag_12']).copy()
    
    print(f"Training dataset: {len(df_model)} records after creating lagged features")
    
    # Define features
    categorical_features = ['MUNICIPALITY', 'FARM TYPE', 'MONTH', 'CROP']
    numeric_features = ['Area planted(ha)', 'Rain Value (mm)', 'Month_Num', 'Year_Num',
                       'lag_1', 'lag_2', 'lag_12', 'rolling_mean_3', 'rolling_std_3']
    
    all_features = categorical_features + numeric_features
    
    # Prepare X and y
    X = df_model[all_features].copy()
    y = df_model['Production(mt)'].values
    
    # Handle any remaining NaN in rolling features
    X['rolling_std_3'] = X['rolling_std_3'].fillna(0)
    
    # Create preprocessing pipeline
    # Label encode categorical features
    label_encoders = {}
    for col in categorical_features:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        label_encoders[col] = le
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Random Forest with optimized parameters
    print("\nTraining Random Forest model with climate features...")
    rf_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # Evaluate
    print("\nEvaluating model...")
    train_pred = rf_model.predict(X_train)
    test_pred = rf_model.predict(X_test)
    
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    train_mae = mean_absolute_error(y_train, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    
    print(f"\nTraining Performance:")
    print(f"  R² Score: {train_r2:.4f}")
    print(f"  MAE: {train_mae:.2f} MT")
    print(f"  RMSE: {train_rmse:.2f} MT")
    
    print(f"\nTest Performance:")
    print(f"  R² Score: {test_r2:.4f}")
    print(f"  MAE: {test_mae:.2f} MT")
    print(f"  RMSE: {test_rmse:.2f} MT")
    
    # Cross-validation
    print("\nPerforming 5-fold cross-validation...")
    cv_scores = cross_val_score(rf_model, X, y, cv=5, scoring='r2', n_jobs=-1)
    print(f"CV R² scores: {cv_scores}")
    print(f"Mean CV R² Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': all_features,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))
    
    # Save model and artifacts
    print(f"\nSaving model artifacts to {MODEL_DIR}/...")
    
    # Save the trained model
    joblib.dump(rf_model, os.path.join(MODEL_DIR, 'climate_rf_model.pkl'))
    
    # Save label encoders
    joblib.dump(label_encoders, os.path.join(MODEL_DIR, 'label_encoders.pkl'))
    
    # Save metadata
    metadata = {
        'model_type': 'RandomForestRegressor with Climate Data',
        'training_date': datetime.now().isoformat(),
        'features': all_features,
        'categorical_features': categorical_features,
        'numeric_features': numeric_features,
        'train_r2_score': float(train_r2),
        'test_r2_score': float(test_r2),
        'train_mae': float(train_mae),
        'test_mae': float(test_mae),
        'train_rmse': float(train_rmse),
        'test_rmse': float(test_rmse),
        'cv_mean_r2': float(cv_scores.mean()),
        'cv_std_r2': float(cv_scores.std()),
        'n_estimators': 200,
        'training_samples': len(X_train),
        'test_samples': len(X_test)
    }
    
    with open(os.path.join(MODEL_DIR, 'climate_model_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save categorical values
    categorical_values = {}
    for col in categorical_features:
        categorical_values[col] = sorted(df_model[col].astype(str).unique().tolist())
    
    with open(os.path.join(MODEL_DIR, 'climate_categorical_values.json'), 'w') as f:
        json.dump(categorical_values, f, indent=2)
    
    # Save feature importance
    feature_importance_dict = feature_importance.to_dict('records')
    with open(os.path.join(MODEL_DIR, 'feature_importance_climate.json'), 'w') as f:
        json.dump(feature_importance_dict, f, indent=2)
    
    # Save rainfall pattern for API use (calculate from actual data)
    rainfall_by_month = df.groupby('Month_Num')['Rain Value (mm)'].mean().to_dict()
    rainfall_by_municipality = df.groupby('MUNICIPALITY')['Rain Value (mm)'].mean().to_dict()
    
    with open(os.path.join(MODEL_DIR, 'rainfall_patterns.json'), 'w') as f:
        json.dump({
            'monthly_average': {int(k): float(v) for k, v in rainfall_by_month.items()},
            'municipality_average': {k: float(v) for k, v in rainfall_by_municipality.items()}
        }, f, indent=2)
    
    print("\n✓ Model training complete!")
    print(f"✓ Model saved with {test_r2:.2%} accuracy on test set")
    print(f"✓ Climate features included: Rain Value (mm)")
    print(f"✓ Time-series features included: lag_1, lag_2, lag_12, rolling_mean_3, rolling_std_3")
    
    return rf_model, label_encoders, metadata

if __name__ == '__main__':
    print("=" * 70)
    print("CLIMATE-ENHANCED ML MODEL TRAINING")
    print("=" * 70)
    
    model, encoders, metadata = train_climate_enhanced_model()
    
    print("\n" + "=" * 70)
    print("Training Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update ml_api.py to use the new climate-aware model")
    print("2. Test predictions with: python test_climate_api.py")
    print("3. Restart the API server to use the new model")
