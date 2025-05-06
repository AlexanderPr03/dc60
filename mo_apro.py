import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.interpolate import griddata

# --- Parameters ---
R = 0.2  # Circle radius (adjust based on your data scale)
file_path = 'C:\\Users\\moham\\Downloads\\slice_csv_data (1).xlsx'

# --- Load Data ---
df = pd.read_excel(file_path, sheet_name='Sheet1')
y = df['Y'].values
z = df['Z'].values
P_total = df['Total Pressure'].values

# Define ROI with maximum of 2 on both axes
y_min_roi, y_max_roi = max(min(y), -2), min(max(y), 2)
z_min_roi, z_max_roi = max(min(z), -2), min(max(z), 2)

# Create evaluation grid (limited to 2 on both axes)
grid_y = np.linspace(y_min_roi, y_max_roi, 100)
grid_z = np.linspace(z_min_roi, z_max_roi, 100)
grid_y, grid_z = np.meshgrid(grid_y, grid_z)

# --- DC60 Calculation ---
def calculate_dc60(y, z, P, center, R):
    cy, cz = center
    r = np.sqrt((y-cy)**2 + (z-cz)**2)
    mask = r <= R
    if np.sum(mask) < 10:
        return np.nan
    
    P_circ = P[mask]
    P_avg = np.mean(P_circ)
    
    angles = np.arctan2(z[mask]-cz, y[mask]-cy) * 180/np.pi % 360
    sector_avgs = [np.mean(P_circ[(angles >= a) & (angles < a+60)]) 
                  for a in np.arange(0, 360, 60)]
    
    return (P_avg - min(sector_avgs)) / P_avg

# Calculate DC60 values
dc60_grid = np.array([calculate_dc60(y, z, P_total, (gy, gz), R) 
                     for gy, gz in zip(grid_y.ravel(), grid_z.ravel())])
dc60_grid = dc60_grid.reshape(grid_y.shape)

# --- Plotting ---
plt.figure(figsize=(10, 8))

# Contour plot with custom levels
levels = np.linspace(0, 0.01, 11)
cs = plt.contourf(grid_y, grid_z, dc60_grid, levels=levels, cmap='viridis', extend='max')
plt.colorbar(cs, label='DC60', ticks=levels)

# Set axis limits explicitly to [-2, 2]
plt.xlim(-2, 2)
plt.ylim(-2, 2)

# Formatting
plt.title('DC60 Contour Plot (Y-Z plane)')
plt.xlabel('Y (m)')
plt.ylabel('Z (m)')
plt.gca().set_aspect('equal')
plt.grid(True, alpha=0.3)

# Add annotation
plt.text(0.95, 0.95, "DC60 ≤ 0.01", transform=plt.gca().transAxes,
         ha='right', va='top', bbox=dict(facecolor='white', alpha=0.8))

plt.tight_layout()
plt.show()

print("done")