import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('slice_csv_data.csv')

z_low = -0.53339
z_high = 0.64874
y_low = 0
y_high = 1.48716


criterion = (data['Y'] > y_low) & (data['Y'] < y_high) & (data['Z'] > z_low) & (data['Z'] < z_high)
data = data[criterion]
# print(data)


fig, ax = plt.subplots()
ax.scatter(data['Y'], data['Z'], c='blue', s=1)

plt.show()