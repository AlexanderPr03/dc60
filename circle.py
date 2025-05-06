import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

data = pd.read_csv('slice_csv_data.csv')

print(data)
z_low = -0.53339
z_high = 0.64874
y_low = 0
y_high = 1.48716
circle_radius = 0.1


criterion = (data['Y'] > y_low) & (data['Y'] < y_high) & (data['Z'] > z_low) & (data['Z'] < z_high)
data = data[criterion]
random_point = data.sample()

y0 = random_point['Y'].values[0]
z0 = random_point['Z'].values[0]

circle_points = np.zeros(shape=(360,2))
# print(circle_points[5])
for i in range(0, 360):
    rad = math.radians(i)
    rx = math.cos(rad) * circle_radius
    ry = math.sin(rad) * circle_radius
    print(circle_points[i].shape)


    circle_points[i,0:2] = [y0 + rx, z0 + ry]




fig, ax = plt.subplots()
plt.xlabel('Y')
plt.ylabel('Z')
ax.scatter(data['Y'], data['Z'], c='blue', s=1)
ax.scatter(circle_points[:,0], circle_points[:,1], c='red', s=2 )





hstep = 0.1
Ly = abs(y_high - y_low)
Lz = abs(z_high - z_low)
ny = int(round(Ly / hstep))
nz = int(round(Lz / hstep))
y = np.linspace(y_low, y_high, ny)
z = np.linspace(z_low, z_high, nz)

yg, zg = np.meshgrid(y, z)

plt.plot(yg, zg, marker = 'o', color = 'k', linestyle = 'none')

plt.show()