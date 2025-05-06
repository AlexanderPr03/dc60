import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('slice_csv_data.csv')

print(data)
z_low = -0.53339
z_high = 0.64874
y_low = 0
y_high = 1.48716


criterion = (data['Y'] > y_low) & (data['Y'] < y_high) & (data['Z'] > z_low) & (data['Z'] < z_high)
data = data[criterion]
# print(data)


fig, ax = plt.subplots()
ax.scatter(data['Y'], data['Z'], c='blue', s=1)


#uniform meshgrid
hstep = 0.1
Ly = abs(y_high - y_low)
Lz = abs(z_high - z_low)
ny = int(round(Ly / hstep))
nz = int(round(Lz / hstep))
y = np.linspace(y_low, y_high, ny)
z = np.linspace(z_low, z_high, nz)

yg, zg = np.meshgrid(y, z)

plt.plot(yg, zg, marker = 'o', color = 'k', linestyle = 'none')

#circle generator check



plt.show()                                                                                                                                                                                                           