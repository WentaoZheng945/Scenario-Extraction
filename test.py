import pywt
a = pywt.dwtn_max_level((64, 32), 'db6')
print(a)

import numpy as np
a = np.load("C:\\Users\Wentao Zheng\Desktop\map_files\MIA_10316_driveable_area_mat_2019_05_28.npy", allow_pickle=True)
print(a)

import json

with open("C:\\Users\Wentao Zheng\Desktop\map_files\MIA_10316_tableidx_to_laneid_map.json", 'r') as f:
    b = json.load(f)
    print(b)