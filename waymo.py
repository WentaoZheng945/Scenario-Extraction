import imp


import numpy as np

data = np.loadtxt(open("E:\\Vertiacl_project\\HAV_virtual_testing\\Data\\Waymo\\00000_all_scenario_all_object_info_1.csv", 'rb'), skiprows=1)
print(data[1:10])