# -*- coding: utf-8 -*-
# @Time    : 2021.09.27
# @Author  : Syh
# 需求：从highD数据集中提取危险场景，并实现每个场景对应一个文件夹储存

import os
import shutil
import numpy as np

from data_management.read_csv import *
from extract_scenario import *


# TODO Q1:这部分代码我理解下来和论文中有些出入，好像只取到了最危险时刻前10s的作为时间切片

'''
场景提取主函数
利用creat_args()方法实现对highD三种数据文件的路径储存
read_track_csv实现对tracks.csv的读取及数据重构，以list对象返回当前csv中所有车辆的属性序列，利用tracks[index][attributes]进行属性值提取
read_static_info实现对tracksMeta.csv的读取及数据重构，以dict返回当前csv中所有车辆的属性，利用tracks_meta[id][attributes]进行属性提取
'''
follow_count = 0  # 紧密跟驰场景计数器
cutin_count = 0  # 主车被侧方插入场景计数器
lanechanging_count = 0  # 主车换道插入场景计数器
# 单主车场景
scenario_rootpath = os.path.abspath("../scenarios")  # 储存场景的根目录路径
index_output_path = os.path.abspath("../scenarios/index.csv")  # 场景标签索引文档的路径
scenario_zippath = os.path.abspath("../scenarios_zip")  # 场景压缩包的根目录路径
GANsample_rootpath = os.path.abspath("../GAN_sample")  # GAN样本库的根目录路径
openS_rootpath = os.path.abspath('../OpenSCENARIO/HighD')  # OpenX场景库根目录路径
# 双主车场景
scenario_2ego_rootpath = os.path.abspath("../scenarios_2ego")  # 储存场景的根目录路径
index_2ego_output_path = os.path.abspath("../scenarios_2ego/index.csv")  # 场景标签索引文档的路径
scenario_2ego_zippath = os.path.abspath("../scenarios_2ego_zip")  # 场景压缩包的根目录路径
openS_2ego_rootpath = os.path.abspath('../OpenSCENARIO/HighD_2ego')  # OpenX场景库根目录路径

location = []  # 记录每个危险场景的地点编号
lane = []  # 记录每个危险场景的车道数
danger = []  # 记录每个危险场景的最小MTTC，用于计算其危险度（最值归一化）
crash = []  # 记录每个危险场景的最大CI，用于评估事故危险度
count = 0  # 用于记录场景数，并协助进行场景编号
# 获得所有highD数据文件路径
path_index = list(range(1, 60 + 1))
for i in path_index:
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
    frame_rate = recording_meta[FRAME_RATE]  # 采样率25hz
    num_lane = len(recording_meta[UPPER_LANE_MARKINGS])  # 确定几车道
    location_id = recording_meta[LOCATION_ID]  # 记录下第几个采样点
    # 遍历车辆
    for j in range(len(tracks)):
        ego = tracks[j]  # 遍历每一辆车，分别做主车
        MTTC = []
        CI = []  # 事故危险度指标，0表示最不危险
        initial_frame = tracks_meta[j + 1][INITIAL_FRAME]  # 初始帧
        final_frame = tracks_meta[j + 1][FINAL_FRAME]  # 结束帧
        ego_id = tracks_meta[j + 1][ID]  # 车辆id
        num_frame = tracks_meta[j + 1][NUM_FRAMES]  # 时长多少帧
        current_index = 0  # 用于定位主车的每个scene
        control_flag = 0
        # TODO:计算ego每一帧画面下对应的MTTC
        while current_index < num_frame:
            # ego没有前车进行跟驰，MTTC设为inf
            if ego[PRECEDING_ID][current_index] == 0:
                MTTC.append(float('inf'))
                CI.append(0)
            # ego存在跟驰行为，计算MTTC
            else:
                mttc = float('inf')
                current_frame = initial_frame + current_index
                pre_track = tracks[ego[PRECEDING_ID][current_index] - 1]  # index = id -1，得到前车的轨迹dict
                pre_current_index = np.where(pre_track[FRAME] == current_frame)[0][0]  # 确定ego前车属性表中对应当前帧的索引值，np.where返回元组([index])
                dist = abs(ego[DHW][current_index])  # 前后两车之间距离
                # dist = abs(pre_track[BBOX][pre_current_index][0] - ego[BBOX][current_index][0]) - ego[BBOX][current_index][2]  # GPS在车身位置未知，直接采用dhw
                delta_v = abs(ego[X_VELOCITY][current_index]) - abs(pre_track[X_VELOCITY][pre_current_index])  # 前后两车速度差，后车-前车
                delta_a = ego[X_ACCELERATION][current_index] - pre_track[X_ACCELERATION][pre_current_index]  # 加速度差，后车-前车
                delta_v2 = (ego[X_VELOCITY][current_index] - pre_track[X_VELOCITY][pre_current_index])**2  # 速度差**2
                if delta_a != 0:
                    t1 = (delta_v * (-1) - (delta_v2 + 2 * delta_a * dist)**0.5) / delta_a
                    t2 = (delta_v * (-1) + (delta_v2 + 2 * delta_a * dist)**0.5) / delta_a
                    if t1 > 0 and t2 > 0:
                        mttc = min(t1, t2)
                    elif t1 * t2 <= 0 and max(t1, t2) > 0:
                        mttc = max(t1, t2)
                elif delta_a == 0 and delta_v > 0:
                    mttc = dist / delta_v
                if mttc != float('inf') and mttc != 0:  #
                    ci = (
                        ((abs(ego[X_VELOCITY][current_index]) + ego[X_ACCELERATION][current_index] * mttc)**2 - (abs(pre_track[X_VELOCITY][pre_current_index])
                         + pre_track[X_ACCELERATION][pre_current_index] * mttc)**2) / (2 * mttc)
                    )
                else:
                    ci = 0
                MTTC.append(mttc)
                CI.append(ci)
            current_index += 1
        # TODO:进行危险场景提取
        if min(MTTC) < 4:  # 小于4提取
            highrisk_index = MTTC.index(min(MTTC))  # ego处于高风险时对应的帧数索引
            highrisk_frame = initial_frame + highrisk_index  # 帧数
            '''
            紧密跟驰1：高风险时刻前10s始终跟随同一辆前车且最后5s内与前车的纵向车头时距始终小于2s
            紧密跟驰2：若高风险事件时刻前行驶片段介于5至10s，则全程跟随同一辆车且最后5s纵向车头时距始终小于2s
            紧密跟驰3：若高风险事件时刻前行驶片段小于5s，则全程跟随同一辆车且纵向车头时距始终小于2s（片段取5s）
            '''
            if highrisk_index >= 10 * frame_rate and control_flag == 0:  # 紧密跟驰1：行驶片段>10s
                pre_tracks = ego[PRECEDING_ID][highrisk_index - 10 * frame_rate:highrisk_index]  # 最危险帧的前10s内前车id列表
                thw = ego[THW][highrisk_index - 5 * frame_rate:highrisk_index]  # 最危险帧前5s内前车的车头时距
                if len(set(pre_tracks)) == 1 and ego[PRECEDING_ID][highrisk_index] in pre_tracks and max(thw) <= 2:
                    scenario_type = str(count).rjust(4, '0') + 'follow'
                    follow_count += 1
                    scenario_index = follow_count
                    scenario_len = 10 * frame_rate
                    highrisk_startframe = highrisk_frame - scenario_len
                    control_flag = 1  # 防止同一场景满足多个条件被多次提取
                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                    # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                    lane.append(num_lane)
                    location.append(i)
                    danger.append(min(MTTC))
                    crash.append(max(CI))
                    scenario_name.append(scenario_type + str(scenario_index))
                    count += 1
            elif 5 * frame_rate <= highrisk_index < 10 * frame_rate and control_flag == 0:  # 紧密跟驰2：行驶片段介于5至10s
                pre_tracks = ego[PRECEDING_ID][0:highrisk_index]
                thw = ego[THW][highrisk_index - 5 * frame_rate:highrisk_index]
                if len(set(pre_tracks)) == 1 and ego[PRECEDING_ID][highrisk_index] in pre_tracks and max(thw) <= 2:
                    scenario_type = str(count).rjust(4, '0') + 'follow'
                    follow_count += 1
                    scenario_index = follow_count
                    scenario_len = highrisk_index + 1
                    highrisk_startframe = initial_frame
                    control_flag = 1
                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                    # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                    lane.append(num_lane)
                    location.append(i)
                    danger.append(min(MTTC))
                    crash.append(max(CI))
                    scenario_name.append(scenario_type + str(scenario_index))
                    count += 1
            elif highrisk_index < 5 * frame_rate and control_flag == 0:  # 紧密跟驰3：行驶片段<5s
                pre_tracks = ego[PRECEDING_ID][0:highrisk_index]
                thw = ego[THW][0:highrisk_index]
                if len(set(pre_tracks)) == 1 and ego[PRECEDING_ID][highrisk_index] in pre_tracks and max(thw) <= 2:
                    scenario_type = str(count).rjust(4, '0') + 'follow'
                    follow_count += 1
                    scenario_index = follow_count
                    scenario_len = 5 * frame_rate
                    highrisk_startframe = initial_frame
                    control_flag = 1  # 防止同一场景满足多个条件被多次提取
                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                    # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                    lane.append(num_lane)
                    location.append(i)
                    danger.append(min(MTTC))
                    crash.append(max(CI))
                    scenario_name.append(scenario_type + str(scenario_index))
                    count += 1
            '''
            紧急换道：ego在高风险时刻与前5s的跟驰对象发生变化，ego或高风险时刻的跟驰对象在前后5s内横向偏移距离超过2m，且前2s最小thw<2s或最小ttc<2.7s
            PS. 片段长度不足的取至初始帧或结束帧即可
            '''
            frnotFrames = num_frame - highrisk_index - 1  # 该片段还剩的帧数
            backFrames = highrisk_index + 1  # 该片段已经完成的帧数
            # ego已完成超过5s的行程
            if backFrames > 5 * frame_rate and control_flag == 0:
                pre_tracks = ego[PRECEDING_ID][highrisk_index - 5 * frame_rate:highrisk_index]  # 前5s的前车列表
                lane_id = ego[LANE_ID][highrisk_index - 5 * frame_rate:highrisk_index]  # 前5s的车道列表
                thw = ego[THW][highrisk_index - 2 * frame_rate:highrisk_index]  # 前2s的thw
                initial_ttc = ego[TTC][highrisk_index - 2 * frame_rate:highrisk_index]  # 前两秒的ttc
                ttc = [x for x in initial_ttc if x > 0]  # 剔除ttc中小于零的值（后车速度小于前车）
                if len(set(pre_tracks)) > 1:  # 跟驰对象发生变化
                    if frnotFrames >= 5 * frame_rate:  # ego还剩超过5s的行程
                        y_ego = ego[BBOX][highrisk_index - 5 * frame_rate:highrisk_index + 5 * frame_rate][1]  # ego的y坐标
                        pre_track = tracks[ego[PRECEDING_ID][highrisk_index] - 1]  # 取出ego高风险时刻的跟驰前车属性表
                        pre_index = np.where(pre_track[FRAME] == initial_frame + highrisk_index)[0][0]  # 确定ego高风险时刻对应的前车属性表索引
                        pre_numframe = tracks_meta[ego[PRECEDING_ID][highrisk_index]][NUM_FRAMES]  # ego高风险时刻对应前车的总帧数
                        pre_frnotFrame = pre_numframe - pre_index - 1  # ego高风险时刻对应前车还剩的帧数
                        pre_backFrame = pre_index + 1  # ego高风险时刻对应前车已完成的帧数
                        if pre_backFrame > 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:  # 超过10s,前取5s，后取5s
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame > 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:  # 前够5s，后不够5s，前取5s，后取到结束
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_numframe - 1][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:  # 前不够5s，后够5s，前面从初始开始取，后面取5s
                            y_pre = pre_track[BBOX][0:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:  # 前后都不够5s，从开始取到最后
                            y_pre = pre_track[BBOX][0:pre_numframe - 1][1]
                        deltay_ego = max(y_ego) - min(y_ego)  # 主车y坐标变化
                        deltay_pre = max(y_pre) - min(y_pre)  # 前车y坐标变化
                        if ttc:
                            if (deltay_ego >= 2 or deltay_pre >= 2) and (min(thw) < 2 or min(ttc) < 2.7):
                                if len(set(lane_id)) >= 2:
                                    scenario_type = str(count).rjust(4, '0') + 'lanechanging'  # 主车换道
                                    lanechanging_count += 1
                                    scenario_index = lanechanging_count
                                else:
                                    scenario_type = str(count).rjust(4, '0') + 'cutin'  # 主车被侧方插入
                                    cutin_count += 1
                                    scenario_index = cutin_count
                                control_flag = 1
                                scenario_len = 10 * frame_rate
                                highrisk_startframe = initial_frame + highrisk_index - 5 * frame_rate
                                extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                                # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                                lane.append(num_lane)
                                location.append(i)
                                danger.append(min(MTTC))
                                crash.append(max(CI))
                                scenario_name.append(scenario_type + str(scenario_index))
                                count += 1
                    else:  # ego剩余行程不足5s
                        y_ego = ego[BBOX][highrisk_index - 5 * frame_rate:num_frame - 1][1]  # ego的横向坐标
                        pre_track = tracks[ego[PRECEDING_ID][highrisk_index] - 1]  # 取出ego高风险时刻的跟驰前车属性表
                        pre_index = np.where(pre_track[FRAME] == initial_frame + highrisk_index)[0][0]  # 确定ego高风险时刻对应的前车属性表索引
                        pre_numframe = tracks_meta[ego[PRECEDING_ID][highrisk_index]][NUM_FRAMES]  # ego高风险时刻对应前车的总帧数
                        pre_frnotFrame = pre_numframe - pre_index - 1  # ego高风险时刻对应前车还剩的帧数
                        pre_backFrame = pre_index + 1  # ego高风险时刻对应前车已完成的帧数
                        if pre_backFrame > 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame > 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_numframe - 1][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_numframe - 1][1]
                        deltay_ego = max(y_ego) - min(y_ego)
                        deltay_pre = max(y_pre) - min(y_pre)
                        if ttc:
                            if (deltay_ego >= 2 or deltay_pre >= 2) and (min(thw) < 2 or min(ttc) < 2.7):
                                control_flag = 1
                                if len(set(lane_id)) >= 2:
                                    scenario_type = str(count).rjust(4, '0') + 'lanechanging'  # 主车换道cutin
                                    lanechanging_count += 1
                                    scenario_index = lanechanging_count
                                else:
                                    scenario_type = str(count).rjust(4, '0') + 'cutin'  # 主车被侧方插入
                                    cutin_count += 1
                                    scenario_index = cutin_count
                                scenario_len = 5 * frame_rate + frnotFrames
                                highrisk_startframe = initial_frame + highrisk_index - 5 * frame_rate
                                extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                                # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                                lane.append(num_lane)
                                location.append(i)
                                danger.append(min(MTTC))
                                crash.append(max(CI))
                                scenario_name.append(scenario_type + str(scenario_index))
                                count += 1
            # ego已完成的行程介于2至5s
            elif 2 * frame_rate < backFrames <= 5 * frame_rate and control_flag == 0:
                pre_tracks = ego[PRECEDING_ID][0:highrisk_index]  # 危险场面前几秒的前车列表
                lane_id = ego[LANE_ID][0:highrisk_index]  # 主车前几秒的id
                thw = ego[THW][highrisk_index - 2 * frame_rate:highrisk_index]  # 前两秒的thw
                initial_ttc = ego[TTC][highrisk_index - 2 * frame_rate:highrisk_index]  # 前两秒的ttc
                ttc = [x for x in initial_ttc if x > 0]
                if len(set(pre_tracks)) > 1:  # 跟驰对象发生变化
                    if frnotFrames >= 5 * frame_rate:  # ego还剩超过5s的行程
                        y_ego = ego[BBOX][0:highrisk_index + 5 * frame_rate][1]  # ego的y坐标
                        pre_track = tracks[ego[PRECEDING_ID][highrisk_index] - 1]  # 取出ego高风险时刻的跟驰前车属性表
                        pre_index = np.where(pre_track[FRAME] == initial_frame + highrisk_index)[0][0]  # 确定ego高风险时刻对应的前车属性表索引
                        pre_numframe = tracks_meta[ego[PRECEDING_ID][highrisk_index]][NUM_FRAMES]  # ego高风险时刻对应前车的总帧数
                        pre_frnotFrame = pre_numframe - pre_index - 1  # ego高风险时刻对应前车还剩的帧数
                        pre_backFrame = pre_index + 1  # ego高风险时刻对应前车已完成的帧数
                        if pre_backFrame > 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame > 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_numframe - 1][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_numframe - 1][1]
                        deltay_ego = max(y_ego) - min(y_ego)
                        deltay_pre = max(y_pre) - min(y_pre)
                        if ttc:
                            if (deltay_ego >= 2 or deltay_pre >= 2) and (min(thw) < 2 or min(ttc) < 2.7):
                                control_flag = 1
                                if len(set(lane_id)) >= 2:
                                    scenario_type = str(count).rjust(4, '0') + 'lanechanging'  # 主车换道
                                    lanechanging_count += 1
                                    scenario_index = lanechanging_count
                                else:
                                    scenario_type = str(count).rjust(4, '0') + 'cutin'  # 主车被侧方插入
                                    cutin_count += 1
                                    scenario_index = cutin_count
                                scenario_len = 5 * frame_rate + backFrames
                                highrisk_startframe = initial_frame
                                extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                                # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                                lane.append(num_lane)
                                location.append(i)
                                danger.append(min(MTTC))
                                crash.append(max(CI))
                                scenario_name.append(scenario_type + str(scenario_index))
                                count += 1
                    else:  # ego剩余行程不足5s
                        y_ego = ego[BBOX][0:num_frame - 1][1]  # ego的横向坐标
                        pre_track = tracks[ego[PRECEDING_ID][highrisk_index] - 1]  # 取出ego高风险时刻的跟驰前车属性表
                        pre_index = np.where(pre_track[FRAME] == initial_frame + highrisk_index)[0][0]  # 确定ego高风险时刻对应的前车属性表索引
                        pre_numframe = tracks_meta[ego[PRECEDING_ID][highrisk_index]][NUM_FRAMES]  # ego高风险时刻对应前车的总帧数
                        pre_frnotFrame = pre_numframe - pre_index - 1  # ego高风险时刻对应前车还剩的帧数
                        pre_backFrame = pre_index + 1  # ego高风险时刻对应前车已完成的帧数
                        if pre_backFrame > 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame > 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_numframe - 1][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_numframe - 1][1]
                        deltay_ego = max(y_ego) - min(y_ego)
                        deltay_pre = max(y_pre) - min(y_pre)
                        if ttc:
                            if (deltay_ego >= 2 or deltay_pre >= 2) and (min(thw) < 2 or min(ttc) < 2.7):
                                control_flag = 1
                                if len(set(lane_id)) >= 2:
                                    scenario_type = str(count).rjust(4, '0') + 'lanechanging'  # 主车换道
                                    lanechanging_count += 1
                                    scenario_index = lanechanging_count
                                else:
                                    scenario_type = str(count).rjust(4, '0') + 'cutin'  # 主车被侧方插入
                                    cutin_count += 1
                                    scenario_index = cutin_count
                                scenario_len = num_frame
                                highrisk_startframe = initial_frame
                                extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                                # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                                lane.append(num_lane)
                                location.append(i)
                                danger.append(min(MTTC))
                                crash.append(max(CI))
                                scenario_name.append(scenario_type + str(scenario_index))
                                count += 1
            # ego已完成的行程不足2s
            elif 2 * frame_rate <= backFrames <= 5 * frame_rate and control_flag == 0:
                pre_tracks = ego[PRECEDING_ID][0:highrisk_index]
                lane_id = ego[LANE_ID][0:highrisk_index]
                thw = ego[THW][0:highrisk_index]
                initial_ttc = ego[TTC][0:highrisk_index]
                ttc = [x for x in initial_ttc if x > 0]
                if len(set(pre_tracks)) > 1:  # 跟驰对象发生变化
                    if frnotFrames >= 5 * frame_rate:  # ego还剩超过5s的行程
                        y_ego = ego[BBOX][0:highrisk_index + 5 * frame_rate][1]  # ego的横向坐标
                        pre_track = tracks[ego[PRECEDING_ID][highrisk_index] - 1]  # 取出ego高风险时刻的跟驰前车属性表
                        pre_index = np.where(pre_track[FRAME] == initial_frame + highrisk_index)[0][0]  # 确定ego高风险时刻对应的前车属性表索引
                        pre_numframe = tracks_meta[ego[PRECEDING_ID][highrisk_index]][NUM_FRAMES]  # ego高风险时刻对应前车的总帧数
                        pre_frnotFrame = pre_numframe - pre_index - 1  # ego高风险时刻对应前车还剩的帧数
                        pre_backFrame = pre_index + 1  # ego高风险时刻对应前车已完成的帧数
                        if pre_backFrame > 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame > 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_numframe - 1][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_numframe - 1][1]
                        deltay_ego = max(y_ego) - min(y_ego)
                        deltay_pre = max(y_pre) - min(y_pre)
                        if ttc:
                            if (deltay_ego >= 2 or deltay_pre >= 2) and (min(thw) < 2 or min(ttc) < 2.7):
                                control_flag = 1
                                if len(set(lane_id)) >= 2:
                                    scenario_type = str(count).rjust(4, '0') + 'lanechanging'  # 主车换道cutin
                                    lanechanging_count += 1
                                    scenario_index = lanechanging_count
                                else:
                                    scenario_type = str(count).rjust(4, '0') + 'cutin'  # 主车被侧方插入
                                    cutin_count += 1
                                    scenario_index = cutin_count
                                scenario_len = 5 * frame_rate + backFrames
                                highrisk_startframe = initial_frame
                                extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                                # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                                lane.append(num_lane)
                                location.append(i)
                                danger.append(min(MTTC))
                                crash.append(max(CI))
                                scenario_name.append(scenario_type + str(scenario_index))
                                count += 1
                    else:  # ego剩余行程不足5s
                        y_ego = ego[BBOX][0:num_frame - 1][1]  # ego的横向坐标
                        pre_track = tracks[ego[PRECEDING_ID][highrisk_index] - 1]  # 取出ego高风险时刻的跟驰前车属性表
                        pre_index = np.where(pre_track[FRAME] == initial_frame + highrisk_index)[0][0]  # 确定ego高风险时刻对应的前车属性表索引
                        pre_numframe = tracks_meta[ego[PRECEDING_ID][highrisk_index]][NUM_FRAMES]  # ego高风险时刻对应前车的总帧数
                        pre_frnotFrame = pre_numframe - pre_index - 1  # ego高风险时刻对应前车还剩的帧数
                        pre_backFrame = pre_index + 1  # ego高风险时刻对应前车已完成的帧数
                        if pre_backFrame > 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame > 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][pre_index - 5 * frame_rate:pre_numframe - 1][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame >= 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_index + 5 * frame_rate][1]
                        elif pre_backFrame <= 5 * frame_rate and pre_frnotFrame < 5 * frame_rate:
                            y_pre = pre_track[BBOX][0:pre_numframe - 1][1]
                        deltay_ego = max(y_ego) - min(y_ego)
                        deltay_pre = max(y_pre) - min(y_pre)
                        if ttc:
                            if (deltay_ego >= 2 or deltay_pre >= 2) and (min(thw) < 2 or min(ttc) < 2.7):
                                control_flag = 1
                                if len(set(lane_id)) >= 2:
                                    scenario_type = str(count).rjust(4, '0') + 'lanechanging'  # 主车换道
                                    lanechanging_count += 1
                                    scenario_index = lanechanging_count
                                else:
                                    scenario_type = str(count).rjust(4, '0') + 'cutin'  # 主车被侧方插入
                                    cutin_count += 1
                                    scenario_index = cutin_count
                                scenario_len = num_frame
                                highrisk_startframe = initial_frame
                                extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)
                                # extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_2ego_rootpath)
                                lane.append(num_lane)
                                location.append(i)
                                danger.append(min(MTTC))
                                crash.append(max(CI))
                                scenario_name.append(scenario_type + str(scenario_index))
                                count += 1
    # 将场景按照HighD数据集文件夹结构进行储存
    for name in scenario_name:
        path = os.path.join(scenario_rootpath, name)
        des_path = os.path.join(os.path.join(openS_rootpath, str(i)), name)
        shutil.copytree(path, des_path)
scenario_flag(scenario_rootpath, index_output_path, location, lane, danger, crash)  # 输出场景索引文档
# scenario_zip(scenario_rootpath, scenario_zippath)  # 输出场景压缩包
# GAN_sample(scenario_rootpath, GANsample_rootpath)  # 输出GAN样本库
