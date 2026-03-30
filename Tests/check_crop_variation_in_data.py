"""
Check if different crops actually have different productivity in the training data
"""
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('fulldataset.csv')

# Convert to numeric
df['Productivity(mt/ha)'] = pd.to_numeric(df['Productivity(mt/ha)'], errors='coerce')
df['Production(mt)'] = pd.to_numeric(df['Production(mt)'], errors='coerce')
df['Area harvested(ha)'] = pd.to_numeric(df['Area harvested(ha)'], errors='coerce')

# Remove invalid data
df = df.dropna(subset=['Productivity(mt/ha)', 'Production(mt)', 'CROP'])

# Group by crop and calculate statistics
crop_stats = df.groupby('CROP').agg({
    'Productivity(mt/ha)': ['mean', 'std', 'min', 'max', 'count'],
    'Production(mt)': ['mean', 'std', 'min', 'max']
}).round(2)

print("="*100)
print("PRODUCTIVITY BY CROP TYPE (Historical Data)")
print("="*100)
print(crop_stats)
print("\n" + "="*100)

# Calculate coefficient of variation for each crop
print("\nPRODUCTIVITY VARIATION:")
print("-"*100)
for crop in df['CROP'].unique():
    crop_data = df[df['CROP'] == crop]['Productivity(mt/ha)']
    mean_prod = crop_data.mean()
    std_prod = crop_data.std()
    cv = (std_prod / mean_prod * 100) if mean_prod > 0 else 0
    print(f"{crop:<20} Mean: {mean_prod:>8.2f} MT/ha  |  Std: {std_prod:>8.2f}  |  CV: {cv:>6.2f}%")

print("\n" + "="*100)
print("OVERALL STATISTICS")
print("="*100)
print(f"Overall mean productivity: {df['Productivity(mt/ha)'].mean():.2f} MT/ha")
print(f"Overall std productivity:  {df['Productivity(mt/ha)'].std():.2f} MT/ha")
print(f"Range: {df['Productivity(mt/ha)'].min():.2f} - {df['Productivity(mt/ha)'].max():.2f} MT/ha")

# Check if crops have significantly different productivity
crop_means = df.groupby('CROP')['Productivity(mt/ha)'].mean().sort_values()
print("\n" + "="*100)
print("CROP RANKING BY AVERAGE PRODUCTIVITY")
print("="*100)
for crop, prod in crop_means.items():
    print(f"{crop:<20} {prod:>8.2f} MT/ha")

print("\n" + "="*100)
print("VERDICT:")
print("="*100)
max_diff = crop_means.max() - crop_means.min()
print(f"Difference between highest and lowest crop: {max_diff:.2f} MT/ha")
if max_diff < 2:
    print("⚠️  CROPS HAVE VERY SIMILAR PRODUCTIVITY - Model correctly learned minimal crop impact")
elif max_diff < 5:
    print("⚙️  MODERATE CROP VARIATION - Model could learn more crop-specific patterns")
else:
    print("✓  SIGNIFICANT CROP VARIATION - Retraining could help capture crop differences")
