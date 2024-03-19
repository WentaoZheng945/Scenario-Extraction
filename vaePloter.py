import matplotlib.pyplot as plt
import numpy as np

data_path = r"C:\Users\15251\Desktop\OnSite\VAE_sample\cutin2_param.npy"
tra_data = np.load(data_path)
for i in range(tra_data.shape[0]):
    if '_xy' in data_path:
        x1 = tra_data[i, :, 0].tolist()
        x2 = tra_data[i, :, 1].tolist()
        x3 = tra_data[i, :, 2].tolist()
        y1 = tra_data[i, :, 3].tolist()
        y2 = tra_data[i, :, 4].tolist()
        y3 = tra_data[i, :, 5].tolist()
    else:
        v1 = tra_data[i, :, 0].tolist()
        delta_x21 = tra_data[i, :, 1].tolist()
        delta_x23 = tra_data[i, :, 2].tolist()
        delta_y21 = tra_data[i, :, 3].tolist()
        x1 = [0]
        for v in v1:
            temp = x1[-1] + v * 0.04
            x1.append(temp)
        x1 = x1[:-1]
        y1 = [5] * len(x1)
        x2 = [x1[i] + delta_x21[i] for i in range(len(x1))]
        y2 = [y1[i] + delta_y21[i] for i in range(len(x1))]
        x3 = [x2[i] - delta_x23[i] for i in range(len(x1))]
        y3 = [5] * len(x1)

    x_min = min(min(x1), min(x2), min(x3)) - 10
    x_max = max(max(x1), max(x2), max(x3)) + 10
    y_min = min(min(y1), min(y2), min(y3)) - 10
    y_max = max(max(y1), max(y2), max(y3)) + 10

    plt.ion()
    plt.subplot()
    for i in range(len(x1)):
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)
        if 'lanechange' in data_path:
            plt.scatter(x1[i], y1[i], c='b')
            plt.scatter(x2[i], y2[i], c='r')
            plt.scatter(x3[i], y3[i], c='b')
        elif 'cutin' in data_path:
            plt.scatter(x1[i], y1[i], c='r')
            plt.scatter(x2[i], y2[i], c='b')
            plt.scatter(x3[i], y3[i], c='b')
        plt.pause(1e-7)
        plt.clf()
    plt.ioff()
    # plt.show()
