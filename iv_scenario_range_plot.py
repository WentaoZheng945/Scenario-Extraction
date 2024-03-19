import os
import numpy as np
import matplotlib.pyplot as plt

from data_management.read_csv import *
from extract_scenario import *

# 获得所有highD数据文件路径
path_index = list(range(1, 60 + 1))
for i in path_index:
    i = 23
    scenario_name = []  # 用于将场景按HighD原始文件夹分类
    print(i)
    highD_index = i
    if i < 10:
        input_path = os.path.join("../highD-dataset-v1.0/data/0" + str(i) + "_tracks.csv")
        input_static_path = os.path.join("../highD-dataset-v1.0/data/0" + str(i) + "_tracksMeta.csv")
        input_meta_path = os.path.join("../highD-dataset-v1.0/data/0" + str(i) + "_recordingMeta.csv")
    else:
        input_path = os.path.join("../highD-dataset-v1.0/data/" + str(i) + "_tracks.csv")
        input_static_path = os.path.join("../highD-dataset-v1.0/data/" + str(i) + "_tracksMeta.csv")
        input_meta_path = os.path.join("../highD-dataset-v1.0/data/" + str(i) + "_recordingMeta.csv")
    created_arguments = create_args(input_path, input_static_path, input_meta_path)
    tracks = read_track_csv(created_arguments)
    tracks_meta = read_static_info(created_arguments)
    recording_meta = read_meta_info(created_arguments)
    frame_rate = recording_meta[FRAME_RATE]
    num_lane = len(recording_meta[UPPER_LANE_MARKINGS])
    location_id = recording_meta[LOCATION_ID]
    # 遍历车辆
    for j in range(len(tracks)):
        ego = tracks[j]
        Mttc = []
        frame = []
        Ci = []  # 事故危险度指标
        initial_frame = tracks_meta[j + 1][INITIAL_FRAME]
        final_frame = tracks_meta[j + 1][FINAL_FRAME]
        ego_id = tracks_meta[j + 1][ID]
        num_frame = tracks_meta[j + 1][NUM_FRAMES]
        current_index = 0
        control_flag = 0
        # TODO:计算ego每一帧画面下对应的MTTC
        while current_index < num_frame:
            # ego没有前车进行跟驰，MTTC设为inf
            if ego[PRECEDING_ID][current_index] == 0:
                '''
                current_frame = initial_frame + current_index
                Mttc.append(float('inf'))
                frame.append(current_frame)
                Ci.append(0)
                '''
            # ego存在跟驰行为，计算MTTC
            else:
                mttc = float('inf')
                current_frame = initial_frame + current_index
                pre_track = tracks[ego[PRECEDING_ID][current_index] - 1]  # index = id -1
                pre_current_index = np.where(pre_track[FRAME] == current_frame)[0][0]  # 确定ego前车属性表中对应当前帧的索引值，np.where返回元组([index])
                dist = abs(ego[DHW][current_index])
                # dist = abs(pre_track[BBOX][pre_current_index][0] - ego[BBOX][current_index][0]) - ego[BBOX][current_index][2]  # GPS在车身位置未知，直接采用dhw
                delta_v = abs(ego[X_VELOCITY][current_index]) - abs(pre_track[X_VELOCITY][pre_current_index])
                delta_a = ego[X_ACCELERATION][current_index] - pre_track[X_ACCELERATION][pre_current_index]
                delta_v2 = (ego[X_VELOCITY][current_index] - pre_track[X_VELOCITY][pre_current_index])**2
                if delta_a != 0:
                    t1 = (delta_v * (-1) - (delta_v2 + 2 * delta_a * dist)**0.5) / delta_a
                    t2 = (delta_v * (-1) + (delta_v2 + 2 * delta_a * dist)**0.5) / delta_a
                    if t1 > 0 and t2 > 0:
                        mttc = min(t1, t2)
                    elif t1 * t2 <= 0 and max(t1, t2) > 0:
                        mttc = max(t1, t2)
                elif delta_a == 0 and delta_v > 0:
                    mttc = dist / delta_v
                if mttc != float('inf') and mttc != 0:
                    ci = (
                        ((abs(ego[X_VELOCITY][current_index]) + ego[X_ACCELERATION][current_index] * mttc)**2 - (abs(pre_track[X_VELOCITY][pre_current_index])
                         + pre_track[X_ACCELERATION][pre_current_index] * mttc)**2) / (2 * mttc)
                    )
                else:
                    ci = 0
                Mttc.append(mttc)
                frame.append(current_frame)
                Ci.append(ci)
            current_index += 1
        if len(Mttc) > 0 and i == 23:
            if min(Mttc) <= 4:
                highrisk_index = Mttc.index(min(Mttc))
                if highrisk_index >= 125 and len(Mttc) - highrisk_index >= 125:
                    plt.figure(1)
                    plt.plot(frame[highrisk_index - 125:highrisk_index + 125], Mttc[highrisk_index - 125:highrisk_index + 125])
                    # plt.xlim([4750, 4860])
                    plt.ylim([0, 15])
                    plt.show()

            
