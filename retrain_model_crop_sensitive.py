"""
Retrain Random Forest Model with Better Crop Sensitivity

This script creates a new model that:
1. Removes Area_harvested and Productivity from inputs (they create the target)
2. Forces the model to learn crop-specific production patterns
3. Makes crop type actually influential in predictions
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("RETRAINING MODEL FOR BETTER CROP SENSITIVITY")
print("="*80)

# Load dataset
print("\n1. Loading data...")
df = pd.read_csv('fulldataset.csv')
print(f"   Loaded {len(df)} records")

# Clean data
print("\n2. Cleaning data...")
df['Production(mt)'] = pd.to_numeric(df['Production(mt)'], errors='coerce')
df['Area planted(ha)'] = pd.to_numeric(df['Area planted(ha)'], errors='coerce')
df['Area harvested(ha)'] = pd.to_numeric(df['Area harvested(ha)'], errors='coerce')
df['Productivity(mt/ha)'] = pd.to_numeric(df['Productivity(mt/ha)'], errors='coerce')

# Remove invalid rows
df = df.dropna(subset=['Production(mt)', 'Area planted(ha)'])
df = df[df['Production(mt)'] > 0]
df = df[df['Area planted(ha)'] > 0]

print(f"   After cleaning: {len(df)} records")

# NEW: Use only these features (NO Area_harvested, NO Productivity)
feature_columns = ['MUNICIPALITY', 'FARM TYPE', 'YEAR', 'MONTH', 'CROP', 'Area planted(ha)']
target_column = 'Production(mt)'

X = df[feature_columns].copy()
y = df[target_column].copy()

print(f"\n3. Feature selection:")
print(f"   Input features: {feature_columns}")
print(f"   Target: {target_column}")
print(f"   Shape: {X.shape}")

# Split data
print("\n4. Splitting data (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"   Training set: {X_train.shape[0]} samples")
print(f"   Test set: {X_test.shape[0]} samples")

# Define categorical and numerical features
categorical_features = ['MUNICIPALITY', 'FARM TYPE', 'MONTH', 'CROP']
numerical_features = ['YEAR', 'Area planted(ha)']

print(f"\n5. Feature engineering:")
print(f"   Categorical: {categorical_features}")
print(f"   Numerical: {numerical_features}")

# Create preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), 
         categorical_features),
        ('num', 'passthrough', numerical_features)
    ],
    remainder='drop'
)

# Create pipeline
rf_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(random_state=42, n_jobs=-1))
])

# Hyperparameter tuning (reduced grid for faster training)
print("\n6. Hyperparameter tuning (this will take 10-20 minutes)...")
param_grid = {
    'model__n_estimators': [100, 200],
    'model__max_depth': [20, 50, 100],
    'model__min_samples_split': [2, 5]
}

grid_search = GridSearchCV(
    rf_pipeline,
    param_grid,
    cv=5,
    scoring='r2',
    n_jobs=-1,
    verbose=1
)

print("   Starting training...")
grid_search.fit(X_train, y_train)

print(f"\n7. Best parameters found:")
for param, value in grid_search.best_params_.items():
    print(f"   {param}: {value}")

# Evaluate
print("\n8. Model evaluation:")
best_model = grid_search.best_estimator_

y_pred_train = best_model.predict(X_train)
y_pred_test = best_model.predict(X_test)

train_r2 = r2_score(y_train, y_pred_train)
test_r2 = r2_score(y_test, y_pred_test)
test_mae = mean_absolute_error(y_test, y_pred_test)
test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

print(f"   Training R²:  {train_r2:.4f}")
print(f"   Test R²:      {test_r2:.4f}")
print(f"   Test MAE:     {test_mae:.2f} MT")
print(f"   Test RMSE:    {test_rmse:.2f} MT")

# Feature importance
print("\n9. Feature importance analysis:")
rf_model = best_model.named_steps['model']
feature_names = best_model.named_steps['preprocessor'].get_feature_names_out()
importances = rf_model.feature_importances_

importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': importances
}).sort_values('Importance', ascending=False)

print("\n   Top 10 features:")
for idx, row in importance_df.head(10).iterrows():
    print(f"   {row['Feature']:<40} {row['Importance']:.6f} ({row['Importance']*100:.2f}%)")

# Check CROP importance
crop_features = [f for f in feature_names if 'CROP' in f]
crop_importance = importance_df[importance_df['Feature'].isin(crop_features)]['Importance'].sum()
print(f"\n   TOTAL CROP IMPORTANCE: {crop_importance:.6f} ({crop_importance*100:.2f}%)")

if crop_importance < 0.05:
    print("   ⚠️  Warning: CROP importance still low!")
else:
    print("   ✓ CROP importance improved!")

# Save model
print("\n10. Saving model artifacts...")
model_dir = 'model_artifacts'

joblib.dump(best_model, f'{model_dir}/best_rf_model.pkl')
print(f"   ✓ Model saved")

# Save preprocessor separately
preprocessor_from_model = best_model.named_steps['preprocessor']
joblib.dump(preprocessor_from_model, f'{model_dir}/preprocessor.pkl')
print(f"   ✓ Preprocessor saved")

# Save metadata
metadata = {
    'model_type': 'Random Forest Regressor (Crop-Sensitive)',
    'best_params': {k.replace('model__', ''): v for k, v in grid_search.best_params_.items()},
    'training_date': str(datetime.now()),
    'target_variable': target_column,
    'input_features': feature_columns,
    'categorical_features': categorical_features,
    'n_samples_train': len(X_train),
    'best_cv_score': grid_search.best_score_,
    'test_r2_score': test_r2,
    'test_mae': test_mae,
    'test_rmse': test_rmse,
    'crop_importance': float(crop_importance),
    'note': 'Retrained without Area_harvested and Productivity to improve crop sensitivity'
}

with open(f'{model_dir}/model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=4)
print(f"   ✓ Metadata saved")

# Save categorical values
categorical_values = {
    col: sorted(df[col].dropna().unique().tolist())
    for col in categorical_features
}

with open(f'{model_dir}/categorical_values.json', 'w') as f:
    json.dump(categorical_values, f, indent=4)
print(f"   ✓ Categorical values saved")

# Save feature info
feature_info = {
    'categorical_features': categorical_features,
    'numerical_features': numerical_features,
    'feature_names': list(feature_names),
    'model_features': feature_columns,
    'n_features': len(feature_names)
}

with open(f'{model_dir}/feature_info.json', 'w') as f:
    json.dump(feature_info, f, indent=4)
print(f"   ✓ Feature info saved")

print("\n" + "="*80)
print("MODEL RETRAINING COMPLETE!")
print("="*80)
print("\nNext steps:")
print("1. Update ml_api.py to use new features (remove Productivity input)")
print("2. Restart Flask API")
print("3. Test predictions with different crops")
print("\n" + "="*80)
