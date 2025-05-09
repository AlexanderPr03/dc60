import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import seaborn as sns
from math import pi as pi
from math import pow as pow



sns.set_theme()

data = pd.read_csv('slice_csv_data.csv')

z_low = -0.53339
step = 0.0000001
z_high = 0.64874
y_low = 0
y_high = 1.48716
circle_radius = 0.1
make_heatmap = False # Set to false to run the code faster if we don't need the heatmap
#uniform meshgrid
ysafe_high = y_high - circle_radius
ysafe_low = y_low + circle_radius
zsafe_high = z_high - circle_radius
zsafe_low = z_low + circle_radius
hstep = 0.1
Ly = abs(ysafe_high - ysafe_low)
Lz = abs(zsafe_high - zsafe_low)
ny = int(round(Ly / hstep))
nz = int(round(Lz / hstep))
y = np.linspace(ysafe_low, ysafe_high, ny)
z = np.linspace(zsafe_low, zsafe_high, nz)


yg, zg = np.meshgrid(y, z)

plt.plot(yg, zg, marker = 'o', color = 'k', linestyle = 'none')

criterion = (data['Y'] > y_low) & (data['Y'] < y_high) & (data['Z'] > z_low) & (data['Z'] < z_high)
data = data[criterion]

print(yg)
y0 = yg[3][3]
z0 = zg[3][3]
# print(y0)
# print(z0)
criterion_2 = (data['Y'] > y0 - circle_radius) & (data['Y'] < y0 + circle_radius) & (data['Z'] > z0 - circle_radius) & (data['Z'] < z0 + circle_radius)
data_circle = data[criterion_2].copy()
circle_points = np.zeros(shape=(360,2))
# print(circle_points[5])
for i in range(0, 360):
    rad = math.radians(i)
    rx = math.cos(rad) * circle_radius
    ry = math.sin(rad) * circle_radius
    # print(circle_points[i].shape)


    circle_points[i,0:2] = [y0 + rx, z0 + ry]

sector_angles = np.zeros((6, 2))
for i in range(0, 360, 60):
    rad = math.radians(i)
    sector_angles[int(i/60)] = [i, (i+60) % 360]

sectors = [[],[],[],[],[],[]]
# sector_points = [[],[],[],[],[],[]]
for (index, row) in data_circle.iterrows():
    i=0
    for (a1,a2) in sector_angles:
        distance = math.sqrt((row['Y'] - y0) ** 2 + (row['Z'] - z0) ** 2)
        # Check if the distance from the center of the circle is lower than the radius of the circle
        criteria_1 = (distance < circle_radius)

        distance = np.array([row['Y'] - y0, row['Z'] - z0 ])

        # p1 = (y0 + circle_radius * math.cos(math.radians((a1))), z0 + circle_radius * math.sin(math.radians((a1))))
        # p2 = (y0 + circle_radius * math.cos(math.radians((a2))), z0 + circle_radius * math.sin(math.radians((a2))))

        # The vectors that represent the radius boundaries of the sector
        p1 = np.array([circle_radius * math.cos(math.radians((a1))), circle_radius * math.sin(math.radians((a1)))])
        p2 = np.array([circle_radius * math.cos(math.radians((a2))), circle_radius * math.sin(math.radians((a2)))])

        # The third length of the triangle
        l3_1 = p1 - distance
        l3_2 = p2 - distance

        # The angle
        # print(( (p1[0]**2 + p1[1]**2) + (distance[0]**2 + distance[1]**2) - (l3_1[0]**2 + l3_1[1]**2)  )/ (2 * math.sqrt((p1[0]**2 + p1[1]**2))* math.sqrt((distance[0]**2 + distance[1]**2)) ))

        # Calculating the angles between our point and each of the 2 boundaries
        try:
            angle_1 = math.acos(( (p1[0]**2 + p1[1]**2) + (distance[0]**2 + distance[1]**2) - (l3_1[0]**2 + l3_1[1]**2)  ) / (2.0 * math.sqrt((p1[0]**2 + p1[1]**2))* math.sqrt((distance[0]**2 + distance[1]**2)) ))
            angle_2 = math.acos(( (p2[0]**2 + p2[1]**2) + (distance[0]**2 + distance[1]**2) - (l3_2[0]**2 + l3_2[1]**2)  ) / (2.0 * math.sqrt((p2[0]**2 + p2[1]**2))* math.sqrt((distance[0]**2 + distance[1]**2)) ))
        except:
            print('error')
        # 60 deg in rad
        angle = (2*pi*60)/360
        criteria_2 = ((angle_1 < angle ) & (angle_2 < angle))

        if ((criteria_1) & criteria_2):
            sectors[i].append(row)

        i+=1




fig, ax = plt.subplots()
plt.xlabel('Y')
plt.ylabel('Z')

colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']

#Background points
ax.scatter(data['Y'], data['Z'], c='grey', s=1, alpha=0.3)

for i, sector_points in enumerate(sectors):
    y_vals = [row['Y'] for row in sector_points]
    z_vals = [row['Z'] for row in sector_points]

    ax.scatter(y_vals, z_vals,
               c=colors[i], s=1,
               label=f'Sector {i + 1} ({sector_angles[i, 0]:.0f}°-{sector_angles[i, 1]:.0f}°)')

ax.scatter(circle_points[:,0], circle_points[:,1], c='black', s=1)
ax.scatter([y0], [z0], c='black', s=10, marker='x')


ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.title(f'(Y={y0:.3f}, Z={z0:.3f})')
plt.tight_layout()
plt.plot(yg, zg, marker = 'o', color = 'k', linestyle = 'none')
plt.show()

#TRYING TO MAKE A HEATMAP OF PRESSURES
if (make_heatmap):
    data_circle['Y_bin'] = np.round(data_circle['Y'] / step) * step
    data_circle['Z_bin'] = np.round(data_circle['Z'] / step) * step

    pressure_matrix = data_circle.pivot_table(index='Z', columns='Y', values='Total Pressure', aggfunc='mean')
    print(pressure_matrix)
    # Plot
    plt.figure(figsize=(10, 8))

    mask = pressure_matrix.isna()

    sns.heatmap(pressure_matrix, mask=mask, cmap='viridis')
    plt.title('Total Pressure')
    plt.xlabel('Y')
    plt.ylabel('Z')
    plt.show()


