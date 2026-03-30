"""
Check the feature importance of the trained model
to see if CROP features are being used properly
"""

import joblib
import json
import pandas as pd
import numpy as np

# Load the model and feature info
model = joblib.load('model_artifacts/best_rf_model.pkl')

with open('model_artifacts/feature_info.json', 'r') as f:
    feature_info = json.load(f)

# Check pipeline structure
print("Pipeline steps:", model.named_steps.keys())

# Get the Random Forest from the pipeline (try different possible names)
if 'regressor' in model.named_steps:
    rf_model = model.named_steps['regressor']
elif 'randomforestregressor' in model.named_steps:
    rf_model = model.named_steps['randomforestregressor']
else:
    # Get the last step (should be the model)
    rf_model = list(model.named_steps.values())[-1]
    
print(f"Model type: {type(rf_model)}")

# Get feature importances
feature_names = feature_info['feature_names']
importances = rf_model.feature_importances_

# Create a dataframe
importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': importances
}).sort_values('Importance', ascending=False)

print("="*80)
print("FEATURE IMPORTANCE ANALYSIS")
print("="*80)
print("\nTop 15 Most Important Features:")
print("-"*80)
print(f"{'Rank':<6} {'Feature':<45} {'Importance':<15} {'%'}")
print("-"*80)

for idx, row in importance_df.head(15).iterrows():
    pct = row['Importance'] * 100
    bar = '█' * int(pct * 2)
    print(f"{idx+1:<6} {row['Feature']:<45} {row['Importance']:<15.6f} {pct:>6.2f}% {bar}")

# Analyze CROP feature importance
print("\n" + "="*80)
print("CROP FEATURE ANALYSIS")
print("="*80)

crop_features = [f for f in feature_names if 'CROP' in f]
crop_importance_df = importance_df[importance_df['Feature'].isin(crop_features)]

print(f"\nTotal CROP features: {len(crop_features)}")
print(f"Combined CROP importance: {crop_importance_df['Importance'].sum():.6f} ({crop_importance_df['Importance'].sum()*100:.2f}%)")
print("\nIndividual CROP feature importances:")
print("-"*80)
for idx, row in crop_importance_df.iterrows():
    print(f"{row['Feature']:<45} {row['Importance']:<15.6f} {row['Importance']*100:>6.2f}%")

# Compare with other categorical features
print("\n" + "="*80)
print("CATEGORICAL FEATURE COMPARISON")
print("="*80)

municipality_features = [f for f in feature_names if 'MUNICIPALITY' in f]
farm_type_features = [f for f in feature_names if 'FARM TYPE' in f]
month_features = [f for f in feature_names if 'MONTH' in f]

print(f"\nMUNICIPALITY importance: {importance_df[importance_df['Feature'].isin(municipality_features)]['Importance'].sum():.6f} ({importance_df[importance_df['Feature'].isin(municipality_features)]['Importance'].sum()*100:.2f}%)")
print(f"FARM TYPE importance:    {importance_df[importance_df['Feature'].isin(farm_type_features)]['Importance'].sum():.6f} ({importance_df[importance_df['Feature'].isin(farm_type_features)]['Importance'].sum()*100:.2f}%)")
print(f"MONTH importance:        {importance_df[importance_df['Feature'].isin(month_features)]['Importance'].sum():.6f} ({importance_df[importance_df['Feature'].isin(month_features)]['Importance'].sum()*100:.2f}%)")
print(f"CROP importance:         {crop_importance_df['Importance'].sum():.6f} ({crop_importance_df['Importance'].sum()*100:.2f}%)")

# Check numerical features
print("\n" + "="*80)
print("NUMERICAL FEATURE IMPORTANCE")
print("="*80)
numerical_features = ['num__Area harvested(ha)', 'num__Area planted(ha)', 'num__YEAR', 'remainder__Productivity(mt/ha)']
for feat in numerical_features:
    if feat in feature_names:
        imp = importance_df[importance_df['Feature'] == feat]['Importance'].values[0]
        print(f"{feat:<45} {imp:.6f} {imp*100:>6.2f}%")

print("\n" + "="*80)
