# -*- coding: utf-8 -*-
# @Time    : 2021.12.29
# @Author  : Syh
# 需求：从highD数据集中提取紧密跟驰场景，充当VAE训练集

import os
import math
from re import L
import numpy as np
from tqdm import tqdm

from data_management.read_csv import *
from extract_scenario import *


# TODO：将所有场景转换为VAE所需要的样本格式（仅提取关键属性的时间序列）
def VAE_follow_sample(scenario_rootpath):
    """该方法用来将识别出来的所有危险场景转换为VAE派生所需的样本
    跟驰场景：本车速度、前车速度、相对距离
    :param arguments: 储存危险场景的根目录
    :return: None
    """
    scenario_path = []
    scenario_name = []
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for filename in filenames:
            if '.csv' in filename:
                name = filename.split('.')[0]
                scenario_path.append(os.path.join(filepath, filename))
                scenario_name.append(name)
    num = len(scenario_path)
    data = np.empty((num, 125, 3), dtype=np.float64)
    data1 = np.empty((math.floor(num / 2), 125, 3), dtype=np.float64)
    data2 = np.empty((math.floor(num / 2), 125, 3), dtype=np.float64)
    for i, path in enumerate(scenario_path):
        id_list = df_to_list(path, 'id')
        ego_id = id_list[0]
        pre_list = df_to_list(path, 'precedingId')
        v_list = df_to_list(path, 'xVelocity')
        x_list = df_to_list(path, 'x')
        if 'follow' in path:  # 跟驰场景
            ego_v = []
            pre_v = []
            delta_dis = []
            pre_id = pre_list[0]
            index_pre = [x for (x, m) in enumerate(id_list) if m == pre_id]  # ego前车对应的索引集合
            for index, id in enumerate(id_list):
                if id == ego_id:  # ego
                    ego_v.append(abs(v_list[index]))
                    pre_v.append(abs(v_list[index_pre[index]]))
                    delta_x = abs(x_list[index] - x_list[index_pre[index]])
                    delta_dis.append(delta_x)
        temp_array = np.empty((125, 3), dtype=np.float64)
        for j in range(125):
            temp_array[j, 0] = ego_v[j]
            temp_array[j, 1] = pre_v[j]
            temp_array[j, 2] = delta_dis[j]
        data[i] = temp_array
        if i < math.floor(num / 2):
            data1[i] = temp_array
        elif math.floor(num / 2) <= i < 2 * math.floor(num / 2):
            data2[i - math.floor(num / 2)] = temp_array
    np.save(os.path.abspath("../VAE_sample/follow_ttc.npy"), data)
    np.save(os.path.abspath("../VAE_sample/follow1_ttc.npy"), data1)
    np.save(os.path.abspath("../VAE_sample/follow2_ttc.npy"), data2)


def VAE_cutin_sample(scenario_rootpath, train_dataset, length):
    '''将主车危险换道场景转换为VAE派生所需的训练集，输出两版——特征构造及传统坐标
    涉及场景参与者：目标车道后车1，执行换道车2，目标车道前车3
    特征构造: v1, delta_y21, delta_x21, delta_x23
    padding: 场景长度不统一，需要参照最长的场景进行padding
    '''
    scenario_path = []
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for dirname in dirnames:
            dir_path = os.path.join(filepath, dirname)
            for filepath1, dirnames1, filenames1 in os.walk(dir_path):
                for filename in filenames1:
                    if '.csv' in filename and 'cutin' in filename:
                        scenario_path.append(os.path.join(filepath1, filename))

    # 初始化array
    data1 = np.zeros((1, length, 5), dtype=np.float64)  # 领域知识特征值
    data2 = np.zeros((1, length, 6), dtype=np.float64)  # 传统特征值
    count = 0  # 合法训练样本计数器
    pbar_iteration = tqdm(total=len(scenario_path), desc='[scenarios]')
    for i, path in enumerate(scenario_path):
        id_list = df_to_list(path, 'id')
        frame_list = df_to_list(path, 'frame')
        ego_id = id_list[0]
        pre_list = df_to_list(path, 'precedingId')
        lane_list = df_to_list(path, 'laneId')
        v_list = df_to_list(path, 'xVelocity')
        x_list = df_to_list(path, 'x')
        y_list = df_to_list(path, 'y')
        vy_list = df_to_list(path, 'yVelocity')

        # 获取ego被cutin前后的两辆前车id
        ego_pre = [pre_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        ego_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        pre_id = [i for i in ego_pre if i != 0]  # 删去0，避免车辆时间窗小于ego而产生的误判情况
        car2_id, car3_id = pre_id[-1], pre_id[0]
        car2_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == car2_id]
        car3_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == car3_id]
        if ego_lane[-1] != car2_lane[-1] or ego_lane[-1] != car3_lane[-1]:  # 通过车道判断是否为ego换道后的前后车
            continue

        # 获取三车的frame列表
        ego_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        car2_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == car2_id]
        car3_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == car3_id]

        # 根据三车的时间窗，确定统一的时间窗范围
        start_frame = max(ego_frame[0], car2_frame[0], car3_frame[0])
        end_frame = min(ego_frame[-1], car2_frame[-1], car3_frame[-1])

        # 根据时间窗，提取出对应的属性值
        v1 = [abs(v_list[i]) for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        v2 = [abs(v_list[i]) for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]
        v3 = [abs(v_list[i]) for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car3_id]

        x1 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        x2 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]
        x3 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car3_id]

        y1 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        y2 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]
        y3 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car3_id]

        vy2 = [vy_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]

        # padding，前推至场景长度为10s(length frames)
        def padding(att):
            att = [att[0]] * (length - len(att)) + att
            return att
        if len(v1) != length:
            continue

        if len(v1) < length:
            continue
            v1 = padding(v1)
            v2 = padding(v2)
            v3 = padding(v3)
            y1 = padding(y1)
            y2 = padding(y2)
            y3 = padding(y3)
            vy2 = [0] * (length - len(vy2)) + vy2
            # 车辆横坐标需二次计算
            steps = length - len(x1)
            if x1[0] > x1[-1]:  # 上行方向
                for i in range(steps):
                    next1 = x1[0] + v1[0] / 25
                    x1.insert(0, next1)
                    next2 = x2[0] + v2[0] / 25
                    x2.insert(0, next2)
                    next3 = x3[0] + v3[0] / 25
                    x3.insert(0, next3)
            else:  # 下行方向
                for i in range(steps):
                    next1 = x1[0] - v1[0] / 25
                    x1.insert(0, next1)
                    next2 = x2[0] - v2[0] / 25
                    x2.insert(0, next2)
                    next3 = x3[0] - v3[0] / 25
                    x3.insert(0, next3)
        elif len(v1) > length:
            start_point = len(v1) - length
            v1 = v1[start_point:]
            v2 = v2[start_point:]
            v3 = v3[start_point:]
            y1 = y1[start_point:]
            y2 = y2[start_point:]
            y3 = y3[start_point:]
            x1 = x1[start_point:]
            x2 = x2[start_point:]
            x3 = x3[start_point:]
            vy2 = vy2[start_point:]

        # 计算相关特征值
        flag = []
        if x1[0] < x1[-1]:  # 下行方向
            delta_y21 = [y2[i] - y1[i] for i in range(len(y2))]
            delta_x21 = [x2[i] - x1[i] for i in range(len(x2))]
            delta_x23 = [x2[i] - x3[i] for i in range(len(x2))]
            flag.append(1)
        elif x1[0] > x1[-1]:  # 上行方向
            delta_y21 = [(y2[i] - y1[i]) * -1 for i in range(len(y2))]
            delta_x21 = [(x2[i] - x1[i]) * -1 for i in range(len(x2))]
            delta_x23 = [(x2[i] - x3[i]) * -1 for i in range(len(x2))]
            flag.append(0)

        # 特征值存入array
        temp_array1 = np.empty((length, 5), dtype=np.float64)
        temp_array1[:, 0] = v1
        temp_array1[:, 1] = delta_x21
        temp_array1[:, 2] = delta_x23
        temp_array1[:, 3] = delta_y21
        temp_array1[:, 4] = vy2
        temp_array2 = np.empty((length, 6), dtype=np.float64)
        temp_array2[:, 0] = x1
        temp_array2[:, 1] = x2
        temp_array2[:, 2] = x3
        temp_array2[:, 3] = y1
        temp_array2[:, 4] = y2
        temp_array2[:, 5] = y3

        # 并入训练集
        data1 = np.concatenate((data1, temp_array1.reshape(1, length, 5)), axis=0)
        data2 = np.concatenate((data2, temp_array2.reshape(1, length, 6)), axis=0)
        count += 1
        pbar_iteration.update(1)
    pbar_iteration.write('[*] Finish sampling')
    pbar_iteration.close()
    # 输出np.array——'*_param.npy'基于领域知识的训练集，'*_xy'传统训练集
    data1 = np.delete(data1, 0, axis=0)  # 删除初始化的zeros
    data2 = np.delete(data2, 0, axis=0)
    if count % 2 == 0:
        sample1 = np.split(data1, 2, axis=0)
        sample2 = np.split(data2, 2, axis=0)
    else:
        data1 = np.delete(data1, 0, axis=0)  # 删除第一个样本
        data2 = np.delete(data2, 0, axis=0)
        sample1 = np.split(data1, 2, axis=0)
        sample2 = np.split(data2, 2, axis=0)
    np.save(os.path.join(train_dataset, 'cutin1_param.npy'), sample1[0])
    np.save(os.path.join(train_dataset, 'cutin2_param.npy'), sample1[1])
    np.save(os.path.join(train_dataset, 'cutin1_xy.npy'), sample2[0])
    np.save(os.path.join(train_dataset, 'cutin2_xy.npy'), sample2[1])
    return flag


def VAE_cutin_sample_v(scenario_rootpath, train_dataset, length):
    '''将后车危险切入场景转换为VAE派生所需的训练集，输出逻辑场景参数序列
    涉及场景参与者：目标车道后车1(ego)，执行换道车2
    特征构造: delta_x, delta_y, vx_cutin, vy_cutin
    padding: 不padding，直接删去长度不足的场景
    '''
    scenario_path = []
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for dirname in dirnames:
            dir_path = os.path.join(filepath, dirname)
            for filepath1, dirnames1, filenames1 in os.walk(dir_path):
                for filename in filenames1:
                    if '.csv' in filename and 'cutin' in filename:
                        scenario_path.append(os.path.join(filepath1, filename))

    # 初始化array
    data2 = np.zeros((1, length, 4), dtype=np.float64)  # 传统特征值
    count = 0  # 合法训练样本计数器
    pbar_iteration = tqdm(total=len(scenario_path), desc='[scenarios]')
    for i, path in enumerate(scenario_path):
        id_list = df_to_list(path, 'id')
        frame_list = df_to_list(path, 'frame')
        ego_id = id_list[0]
        pre_list = df_to_list(path, 'precedingId')
        lane_list = df_to_list(path, 'laneId')
        x_list = df_to_list(path, 'x')
        y_list = df_to_list(path, 'y')
        vx_list = df_to_list(path, 'xVelocity')
        vy_list = df_to_list(path, 'yVelocity')

        # 获取ego被cutin前后的两辆前车id
        ego_pre = [pre_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        ego_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        pre_id = [i for i in ego_pre if i != 0]  # 删去0，避免车辆时间窗小于ego而产生的误判情况
        car2_id = pre_id[-1]
        car2_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == car2_id]
        if ego_lane[-1] != car2_lane[-1]:  # 通过车道判断是否为ego换道后的前后车
            continue

        # 获取三车的frame列表
        ego_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        car2_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == car2_id]

        # 根据三车的时间窗，确定统一的时间窗范围
        start_frame = max(ego_frame[0], car2_frame[0])
        end_frame = min(ego_frame[-1], car2_frame[-1])

        # 根据时间窗，提取出对应的属性值
        x1 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        x2 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]

        y1 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        y2 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]

        vx_cutin = [vx_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]
        vy_cutin = [vy_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]

        if len(x1) < length:
            continue
        elif len(x1) > length:
            start_point = len(x1) - length
            y1 = y1[start_point:]
            y2 = y2[start_point:]
            x1 = x1[start_point:]
            x2 = x2[start_point:]
            vx_cutin = vx_cutin[start_point:]
            vy_cutin = vy_cutin[start_point:]

        # TODO: 上下行方向统一
        if x1[-1] < x1[0]:
            x1 = [-i for i in x1]
            x2 = [-i for i in x2]
            y1 = [-i for i in y1]
            y2 = [-i for i in y2]
            vx_cutin = [-i for i in vx_cutin]
            vy_cutin = [-i for i in vy_cutin]
        
        # TODO：换道方向过滤，选出向内侧车道执行换道的场景
        if y2[-1] > y2[0]:
            continue
     
        # 计算逻辑场景参数
        delta_x = [x1[i] - x2[i] for i in range(len(x1))]
        delta_y = [y1[i] - y2[i] for i in range(len(y1))]

        # 特征值存入array
        temp_array2 = np.empty((length, 4), dtype=np.float64)
        temp_array2[:, 0] = delta_x
        temp_array2[:, 1] = delta_y
        temp_array2[:, 3] = vx_cutin
        temp_array2[:, 4] = vy_cutin

        # 并入训练集
        data2 = np.concatenate((data2, temp_array2.reshape(1, length, 4)), axis=0)
        count += 1
        pbar_iteration.update(1)
    pbar_iteration.write('[*] Finish sampling')
    pbar_iteration.close()

    # 输出np.array——'*_param.npy'基于领域知识的训练集，'*_xy'传统训练集
    data2 = np.delete(data2, 0, axis=0)  # 删除初始化的zeros
    sample2 = np.split(data2, 2, axis=0)
    np.save(os.path.join(train_dataset, 'cutin1_xy.npy'), sample2[0])
    np.save(os.path.join(train_dataset, 'cutin2_xy.npy'), sample2[1])
    return


def VAE_cutin_sample_xy(scenario_rootpath, train_dataset, length):
    '''将后车危险切入场景转换为VAE派生所需的训练集，输出最大最小归一化后的轨迹坐标
    涉及场景参与者：目标车道后车1(ego)，执行换道车2
    特征构造: x_ego, x_pre, y_ego, y_cutin
    padding: 不padding，直接删去长度不足的场景
    '''
    scenario_path = []
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for dirname in dirnames:
            dir_path = os.path.join(filepath, dirname)
            for filepath1, dirnames1, filenames1 in os.walk(dir_path):
                for filename in filenames1:
                    if '.csv' in filename and 'cutin' in filename:
                        scenario_path.append(os.path.join(filepath1, filename))

    # 初始化array
    data2 = np.zeros((1, length, 4), dtype=np.float64)  # 传统特征值
    count = 0  # 合法训练样本计数器
    pbar_iteration = tqdm(total=len(scenario_path), desc='[scenarios]')
    for i, path in enumerate(scenario_path):
        id_list = df_to_list(path, 'id')
        frame_list = df_to_list(path, 'frame')
        ego_id = id_list[0]
        pre_list = df_to_list(path, 'precedingId')
        lane_list = df_to_list(path, 'laneId')
        x_list = df_to_list(path, 'x')
        y_list = df_to_list(path, 'y')

        # 获取ego被cutin前后的两辆前车id
        ego_pre = [pre_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        ego_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        pre_id = [i for i in ego_pre if i != 0]  # 删去0，避免车辆时间窗小于ego而产生的误判情况
        car2_id = pre_id[-1]
        car2_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == car2_id]
        if ego_lane[-1] != car2_lane[-1]:  # 通过车道判断是否为ego换道后的前后车
            continue

        # 获取三车的frame列表
        ego_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        car2_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == car2_id]

        # 根据三车的时间窗，确定统一的时间窗范围
        start_frame = max(ego_frame[0], car2_frame[0])
        end_frame = min(ego_frame[-1], car2_frame[-1])

        # 根据时间窗，提取出对应的属性值
        x1 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        x2 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]

        y1 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        y2 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car2_id]

        # padding，前推至场景长度为10s(length frames)
        def padding(att):
            att = [att[0]] * (length - len(att)) + att
            return att
        if len(x1) != length:
            continue

        if len(x1) < length:
            continue
        elif len(x1) > length:
            start_point = len(x1) - length
            y1 = y1[start_point:]
            y2 = y2[start_point:]
            x1 = x1[start_point:]
            x2 = x2[start_point:]

        # TODO: 上下行方向统一
        if x1[-1] < x1[0]:
            x1 = [-i for i in x1]
            x2 = [-i for i in x2]
            y1 = [-i for i in y1]
            y2 = [-i for i in y2]

        # 特征值存入array
        temp_array2 = np.empty((length, 4), dtype=np.float64)
        temp_array2[:, 0] = x1
        temp_array2[:, 1] = x2
        temp_array2[:, 3] = y1
        temp_array2[:, 4] = y2

        # 并入训练集
        data2 = np.concatenate((data2, temp_array2.reshape(1, length, 4)), axis=0)
        count += 1
        pbar_iteration.update(1)
    pbar_iteration.write('[*] Finish sampling')
    pbar_iteration.close()

    # 输出np.array——'*_param.npy'基于领域知识的训练集，'*_xy'传统训练集
    data2 = np.delete(data2, 0, axis=0)  # 删除初始化的zeros

    # 最大值最小值归一化
    if count % 2 != 0:
        data2 = np.delete(data2, 0, axis=0)  # 删除第一个样本
    x_min, x_max = np.min(data2[:, :, :2]), np.max(data2[:, :, 2:])
    y_min, y_max = np.min(data2[:, :, :2]), np.max(data2[:, :, 2:])
    temp1 = (data2[:, :, :2] - x_min) / (x_max - x_min)
    temp2 = (data2[:, :, 2:] - y_min) / (y_max - y_min)
    final_data = np.concatenate((temp1, temp2), axis=2)
    sample2 = np.split(final_data, 2, axis=0)
    np.save(os.path.join(train_dataset, 'cutin1_xy.npy'), sample2[0])
    np.save(os.path.join(train_dataset, 'cutin2_xy.npy'), sample2[1])
    return


def VAE_lanechange_sample(scenario_rootpath, train_dataset, length):
    '''将主车危险换道场景转换为VAE派生所需的训练集，输出两版——特征构造及传统坐标
    涉及场景参与者：目标车道后车1，执行换道车2，目标车道前车3
    特征构造: v1, v2, v3, delta_y21, delta_x21, delta_x23
    padding: 场景长度不统一，需要参照最长的场景进行padding
    '''
    scenario_path = []
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for dirname in dirnames:
            dir_path = os.path.join(filepath, dirname)
            for filepath1, dirnames1, filenames1 in os.walk(dir_path):
                for filename in filenames1:
                    if '.csv' in filename and 'cutin' in filename:
                        scenario_path.append(os.path.join(filepath1, filename))

    # 初始化array
    data1 = np.zeros((1, length, 6), dtype=np.float64)  # 领域知识特征值
    data2 = np.zeros((1, length, 6), dtype=np.float64)  # 传统特征值
    count = 0  # 合法训练样本计数器
    for i, path in enumerate(scenario_path):
        id_list = df_to_list(path, 'id')
        frame_list = df_to_list(path, 'frame')
        ego_id = id_list[0]
        pre_list = df_to_list(path, 'precedingId')
        follow_list = df_to_list(path, 'followingId')
        lane_list = df_to_list(path, 'laneId')
        v_list = df_to_list(path, 'xVelocity')
        x_list = df_to_list(path, 'x')
        y_list = df_to_list(path, 'y')

        # 获取ego执行换道后的前后车id
        ego_pre = [pre_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        ego_follow = [follow_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        ego_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        car3_id = [i for i in ego_pre if i != 0][-1]  # 删去0，避免车辆时间窗小于ego而产生的误判情况
        car3_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == car3_id]
        car1_id = [i for i in ego_follow if i != 0][-1]
        car1_lane = [lane_list[i] for i, id_ in enumerate(id_list) if id_ == car1_id]
        if ego_lane[-1] != car3_lane[-1] or ego_lane[-1] != car1_lane[-1]:  # 通过车道判断是否为ego换道后的前后车
            continue

        # 获取三车的frame列表
        ego_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == ego_id]
        car3_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == car3_id]
        car1_frame = [frame_list[i] for i, id_ in enumerate(id_list) if id_ == car1_id]

        # 根据三车的时间窗，确定统一的时间窗范围
        start_frame = max(ego_frame[0], car3_frame[0], car1_frame[0])
        end_frame = min(ego_frame[-1], car3_frame[-1], car1_frame[-1])

        # 根据时间窗，提取出对应的属性值
        v1 = [abs(v_list[i]) for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car1_id]
        v2 = [abs(v_list[i]) for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        v3 = [abs(v_list[i]) for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car3_id]

        x1 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car1_id]
        x2 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        x3 = [x_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car3_id]

        y1 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car1_id]
        y2 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == ego_id]
        y3 = [y_list[i] for i, frame in enumerate(frame_list) if start_frame <= frame and end_frame >= frame and id_list[i] == car3_id]

        # padding，前推至场景长度为10s(length frames)
        def padding(att):
            att = [att[0]] * (length - len(att)) + att
            return att

        if len(v1) < length:
            v1 = padding(v1)
            v2 = padding(v2)
            v3 = padding(v3)
            y1 = padding(y1)
            y2 = padding(y2)
            y3 = padding(y3)
            # 车辆横坐标需二次计算
            steps = length - len(x1)
            if x1[0] > x1[-1]:  # 上行方向
                for i in range(steps):
                    next1 = x1[0] + v1[0] / 25
                    x1.insert(0, next1)
                    next2 = x2[0] + v1[0] / 25
                    x2.insert(0, next2)
                    next3 = x3[0] + v1[0] / 25
                    x3.insert(0, next3)
            else:  # 下行方向
                for i in range(steps):
                    next1 = x1[0] - v1[0] / 25
                    x1.insert(0, next1)
                    next2 = x2[0] - v1[0] / 25
                    x2.insert(0, next2)
                    next3 = x3[0] - v1[0] / 25
                    x3.insert(0, next3)
        elif len(v1) > length:
            start_point = len(v1) - length
            v1 = v1[start_point:]
            v2 = v2[start_point:]
            v3 = v3[start_point:]
            y1 = y1[start_point:]
            y2 = y2[start_point:]
            y3 = y3[start_point:]
            x1 = x1[start_point:]
            x2 = x2[start_point:]
            x3 = x3[start_point:]

        # 计算相关特征值
        delta_y21 = [y2[i] - y1[i] for i in range(len(y2))]
        delta_x21 = [x2[i] - x1[i] for i in range(len(x2))]
        delta_x23 = [x2[i] - x3[i] for i in range(len(x2))]

        # 特征值存入array
        temp_array1 = np.empty((length, 6), dtype=np.float64)
        temp_array1[:, 0] = v1
        temp_array1[:, 1] = v2
        temp_array1[:, 2] = v3
        temp_array1[:, 3] = delta_x21
        temp_array1[:, 4] = delta_x23
        temp_array1[:, 5] = delta_y21
        temp_array2 = np.empty((length, 6), dtype=np.float64)
        temp_array2[:, 0] = x1
        temp_array2[:, 1] = x2
        temp_array2[:, 2] = x3
        temp_array2[:, 3] = y1
        temp_array2[:, 4] = y2
        temp_array2[:, 5] = y3

        # 并入训练集
        data1 = np.concatenate((data1, temp_array1.reshape(1, length, 6)), axis=0)
        data2 = np.concatenate((data2, temp_array2.reshape(1, length, 6)), axis=0)
        count += 1
    # 输出np.array——'*_param.npy'基于领域知识的训练集，'*_xy'传统训练集
    data1 = np.delete(data1, 0, axis=0)  # 删除初始化的zeros
    data2 = np.delete(data2, 0, axis=0)
    if count % 2 == 0:
        sample1 = np.split(data1, 2, axis=0)
        sample2 = np.split(data2, 2, axis=0)
    else:
        data1 = np.delete(data1, 0, axis=0)  # 删除第一个样本
        data2 = np.delete(data2, 0, axis=0)
        sample1 = np.split(data1, 2, axis=0)
        sample2 = np.split(data2, 2, axis=0)
    np.save(os.path.join(train_dataset, 'lanechange1_param.npy'), sample1[0])
    np.save(os.path.join(train_dataset, 'lanechange2_param.npy'), sample2[1])
    np.save(os.path.join(train_dataset, 'lanechange1_xy.npy'), sample2[0])
    np.save(os.path.join(train_dataset, 'lanechange2_xy.npy'), sample2[1])


def get_highrisk_scenario(scenario_type, scenario_rootpath, threshold):
    '''提取VAE所用的场景数据，其中紧密跟驰场景的长度固定为125帧、危险换道场景长度不定（转换为训练集时进行padding）
    :param arguments: 需要提取的场景类型(follow//cutin//lanechange)、储存训练集的根目录、MTTC阈值
    :return: None
    输出csv文件，命名格式——<场景编号><场景类型>_<场景来源><地图编号>，如0000follow_highD1
    '''
    scenario_count = 0  # 用于记录场景数，并协助进行场景编号
    # 获得所有highD数据文件路径
    path_index = list(range(1, 60 + 1))
    for i in tqdm(path_index):
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
        # 遍历车辆
        for j in range(len(tracks)):
            ego = tracks[j]
            ego_TTC = ego[TTC].tolist()
            for index, ttc in enumerate(ego_TTC):
                if ttc <= 0:
                    ego_TTC[index] = ttc + float('inf')
            MTTC = []
            initial_frame = tracks_meta[j + 1][INITIAL_FRAME]
            ego_id = tracks_meta[j + 1][ID]
            num_frame = tracks_meta[j + 1][NUM_FRAMES]
            current_index = 0
            control_flag = 0
            # TODO:计算ego每一帧画面下对应的MTTC
            while current_index < num_frame:
                # ego没有前车进行跟驰，MTTC设为inf
                if ego[PRECEDING_ID][current_index] == 0:
                    MTTC.append(float('inf'))
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
                    MTTC.append(mttc)
                current_index += 1
            # TODO: 进行紧密跟驰场景提取
            if 0 < min(MTTC) <= threshold and scenario_type == 'follow':
                highrisk_index = ego_TTC.index(min(ego_TTC))  # ego处于高风险时对应的帧数索引
                highrisk_frame = initial_frame + highrisk_index
                '''
                紧密跟驰1：高风险时刻前10s始终跟随同一辆前车且最后5s内与前车的纵向车头时距始终小于2s
                紧密跟驰2：若高风险事件时刻前行驶片段介于5至10s，则全程跟随同一辆车且最后5s纵向车头时距始终小于2s
                【所有场景时长固定5s】
                '''
                if highrisk_index >= 10 * frame_rate and control_flag == 0:  # 紧密跟驰1：行驶片段>10s
                    pre_tracks = ego[PRECEDING_ID][highrisk_index - 10 * frame_rate:highrisk_index]
                    thw = ego[THW][highrisk_index - 5 * frame_rate:highrisk_index]
                    if len(set(pre_tracks)) == 1 and ego[PRECEDING_ID][highrisk_index] in pre_tracks and max(thw) <= 2:
                        scenario_info = str(scenario_count).rjust(4, '0') + 'follow' + '_highD' + str(i)
                        scenario_count += 1
                        scenario_index = ''
                        scenario_len = 5 * frame_rate
                        highrisk_startframe = highrisk_frame - scenario_len
                        control_flag = 1  # 防止同一场景满足多个条件被多次提取
                        extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
                elif 5 * frame_rate <= highrisk_index < 10 * frame_rate and control_flag == 0:  # 紧密跟驰2：行驶片段介于5至10s
                    pre_tracks = ego[PRECEDING_ID][0:highrisk_index]
                    thw = ego[THW][highrisk_index - 5 * frame_rate:highrisk_index]
                    if len(set(pre_tracks)) == 1 and ego[PRECEDING_ID][highrisk_index] in pre_tracks and max(thw) <= 2:
                        scenario_info = str(scenario_count).rjust(4, '0') + 'follow' + '_highD' + str(i)
                        scenario_count += 1
                        scenario_index = ''
                        scenario_len = 5 * frame_rate
                        highrisk_startframe = highrisk_frame - scenario_len
                        control_flag = 1
                        extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
            # TODO: 进行危险换道场景提取
            elif 0 < min(MTTC) <= threshold:
                highrisk_index = ego_TTC.index(min(ego_TTC))  # ego处于高风险时对应的帧数索引
                '''
                危险换道：ego在高风险时刻与前5s的跟驰对象发生变化，ego或高风险时刻的跟驰对象在前后5s内横向偏移距离超过2m，且前2s最小thw<2s或最小ttc<2.7s
                PS. 片段长度不足的取至初始帧或结束帧即可
                '''
                frnotFrames = num_frame - highrisk_index - 1  # 该片段还剩的帧数
                backFrames = highrisk_index + 1  # 该片段已经完成的帧数
                # ego已完成超过5s的行程
                if backFrames > 5 * frame_rate and control_flag == 0:
                    pre_tracks = ego[PRECEDING_ID][highrisk_index - 5 * frame_rate:highrisk_index]
                    lane_id = ego[LANE_ID][highrisk_index - 5 * frame_rate:highrisk_index]
                    thw = ego[THW][highrisk_index - 2 * frame_rate:highrisk_index]
                    initial_ttc = ego[TTC][highrisk_index - 2 * frame_rate:highrisk_index]
                    ttc = [x for x in initial_ttc if x > 0]  # 剔除ttc中小于零的值（后车速度小于前车）
                    if len(set(pre_tracks)) > 1:  # 跟驰对象发生变化
                        if frnotFrames >= 5 * frame_rate:  # ego还剩超过5s的行程
                            y_ego = ego[BBOX][highrisk_index - 5 * frame_rate:highrisk_index + 5 * frame_rate][1]  # ego的横向坐标
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
                                    if len(set(lane_id)) >= 2 and scenario_type == 'lanechange':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'lanechanging' + '_highD' + str(i)  # 主车换道cutin
                                        scenario_count += 1
                                        scenario_index = ''
                                    elif len(set(lane_id)) == 1 and scenario_type == 'cutin':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'cutin' + '_highD' + str(i)  # 主车被侧方插入
                                        scenario_count += 1
                                        scenario_index = ''
                                    control_flag = 1
                                    scenario_len = 10 * frame_rate  # 场景长度
                                    highrisk_startframe = initial_frame + highrisk_index - 5 * frame_rate
                                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
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
                                    if len(set(lane_id)) >= 2 and scenario_type == 'lanechange':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'lanechanging' + '_highD' + str(i)  # 主车换道cutin
                                        scenario_count += 1
                                        scenario_index = ''
                                    elif len(set(lane_id)) == 1 and scenario_type == 'cutin':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'cutin' + '_highD' + str(i)  # 主车被侧方插入
                                        scenario_count += 1
                                        scenario_index = ''
                                    control_flag = 1
                                    scenario_len = 5 * frame_rate + frnotFrames
                                    highrisk_startframe = initial_frame + highrisk_index - 5 * frame_rate
                                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
                # ego已完成的行程介于2至5s
                elif 2 * frame_rate < backFrames <= 5 * frame_rate and control_flag == 0:
                    pre_tracks = ego[PRECEDING_ID][0:highrisk_index]
                    lane_id = ego[LANE_ID][0:highrisk_index]
                    thw = ego[THW][highrisk_index - 2 * frame_rate:highrisk_index]
                    initial_ttc = ego[TTC][highrisk_index - 2 * frame_rate:highrisk_index]
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
                                    if len(set(lane_id)) >= 2 and scenario_type == 'lanechange':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'lanechanging' + '_highD' + str(i)  # 主车换道cutin
                                        scenario_count += 1
                                        scenario_index = ''
                                    elif len(set(lane_id)) == 1 and scenario_type == 'cutin':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'cutin' + '_highD' + str(i)  # 主车被侧方插入
                                        scenario_count += 1
                                        scenario_index = ''
                                    control_flag = 1
                                    scenario_len = 5 * frame_rate + backFrames
                                    highrisk_startframe = initial_frame
                                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
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
                                    if len(set(lane_id)) >= 2 and scenario_type == 'lanechange':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'lanechanging' + '_highD' + str(i)  # 主车换道cutin
                                        scenario_count += 1
                                        scenario_index = ''
                                    elif len(set(lane_id)) == 1 and scenario_type == 'cutin':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'cutin' + '_highD' + str(i)  # 主车被侧方插入
                                        scenario_count += 1
                                        scenario_index = ''
                                    control_flag = 1
                                    scenario_len = num_frame
                                    highrisk_startframe = initial_frame
                                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
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
                                    if len(set(lane_id)) >= 2 and scenario_type == 'lanechange':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'lanechanging' + '_highD' + str(i)  # 主车换道cutin
                                        scenario_count += 1
                                        scenario_index = ''
                                    elif len(set(lane_id)) == 1 and scenario_type == 'cutin':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'cutin' + '_highD' + str(i)  # 主车被侧方插入
                                        scenario_count += 1
                                        scenario_index = ''
                                    control_flag = 1
                                    scenario_len = 5 * frame_rate + backFrames
                                    highrisk_startframe = initial_frame
                                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_info, scenario_index, scenario_rootpath)
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
                                    if len(set(lane_id)) >= 2 and scenario_type == 'lanechange':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'lanechanging' + '_highD' + str(i)  # 主车换道cutin
                                        scenario_count += 1
                                        scenario_index = ''
                                    elif len(set(lane_id)) == 1 and scenario_type == 'cutin':
                                        scenario_info = str(scenario_count).rjust(4, '0') + 'cutin' + '_highD' + str(i)  # 主车被侧方插入
                                        scenario_count += 1
                                        scenario_index = ''
                                    control_flag = 1
                                    scenario_len = num_frame
                                    highrisk_startframe = initial_frame
                                    extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath)


class egoInfo():
    def __init__(self) -> None:
        self.id = -1
        self.num_frame = -1
        self.initial_frame = -1
        pass


class stScenario():
    def __init__(self, scenario_type, scenario_rootpath) -> None:
        self.scenario_type = scenario_type
        self.scenario_rootpath = scenario_rootpath
        return

    def get_standard_scenario(self):
        '''提取VAE所用的标准换道场景数据，场景的长度固定为125帧
        :param arguments: 需要提取的场景类型(cutin//lanechange)、储存训练集的根目录
        :return: None
        输出csv文件，命名格式——<场景编号><场景类型>_<场景来源><地图编号>，如0000follow_highD1
        '''
        self.scenario_count = 0  # 用于记录场景数，并协助进行场景编号
        # 获得所有highD数据文件路径
        path_index = list(range(1, 60 + 1))
        for self.index in tqdm(path_index):
            if self.index < 10:
                self.input_path = os.path.join("../highD-dataset-v1.0/data/0" + str(self.index) + "_tracks.csv")
                input_static_path = os.path.join("../highD-dataset-v1.0/data/0" + str(self.index) + "_tracksMeta.csv")
                input_meta_path = os.path.join("../highD-dataset-v1.0/data/0" + str(self.index) + "_recordingMeta.csv")
            else:
                self.input_path = os.path.join("../highD-dataset-v1.0/data/" + str(self.index) + "_tracks.csv")
                input_static_path = os.path.join("../highD-dataset-v1.0/data/" + str(self.index) + "_tracksMeta.csv")
                input_meta_path = os.path.join("../highD-dataset-v1.0/data/" + str(self.index) + "_recordingMeta.csv")
            created_arguments = create_args(self.input_path, input_static_path, input_meta_path)
            self.tracks = read_track_csv(created_arguments)  # 获取每个场景csv中单车在每一帧下的属性值
            self.tracks_meta = read_static_info(created_arguments)  # 获取每个场景csv中单车的集计信息
            self.recording_meta = read_meta_info(created_arguments)
            # 遍历车辆
            for j in tqdm(range(len(self.tracks))):
                ego = self.tracks[j]
                egoMeta = egoInfo()
                egoMeta.num_frame = self.tracks_meta[j + 1][NUM_FRAMES]
                egoMeta.initial_frame = self.tracks_meta[j + 1][INITIAL_FRAME]
                egoMeta.id = self.tracks_meta[j + 1][ID]
                ego_preID = ego[PRECEDING_ID].tolist()
                current_pre = 0
                for index, pre_id in enumerate(ego_preID):
                    if pre_id != current_pre and pre_id * current_pre != 0:  # 主车前车ID发生变化
                        current_frame = egoMeta.initial_frame + index  # 获得关键事件对应的视频帧
                        new_pre = self.tracks[pre_id - 1]  # 获得ego当前前车的属性集合
                        old_pre = self.tracks[current_pre - 1]  # 获得ego上一前车的属性集合
                        new_index = np.where(new_pre[FRAME] == current_frame)[0][0]  # 获得关键事件对应ego当前前车片段中索引
                        if old_pre[FRAME].tolist()[-1] >= current_frame:
                            old_index = np.where(old_pre[FRAME] == current_frame)[0][0]  # 获得关键事件对应ego上一前车片段中索引
                        else:
                            old_index = -1
                        if ego[LANE_ID][index] == ego[LANE_ID][index - 1]:  # 主车未换道
                            if old_pre[LANE_ID][old_index] == ego[LANE_ID][index]:
                                type_ = 'cutin'  # 否则为cutout，即原前车换道离开本道
                                self.extract_stScenario(index, egoMeta, type_)
                        else:  # 主车执行换道
                            if new_pre[LANE_ID][new_index] != old_pre[LANE_ID][old_index]:
                                type_ = 'lanechange'
                                self.extract_stScenario(index, egoMeta, type_)
                    current_pre = pre_id
        return

    # TODO: 进行危险换道场景提取
    def extract_stScenario(self, critical_index, egoMeta, type_):
        '''完成标准场景的提取，关键事件为ego前车ID发生变化
        对于cutin场景，ego前车ID发生变化，表示car2的cutin行为已经完成(?)，前溯5s
        :param arguments: 关键事件在ego运行过程中对应的帧数索引，ego集计信息，关键事件对应的场景类型
        :return: None
        '''
        frame_rate = self.recording_meta[FRAME_RATE]
        '''
        危险换道：ego在高风险时刻与前5s的跟驰对象发生变化
        PS. 片段长度不足的取至初始帧或结束帧即可
        '''
        frnotFrames = egoMeta.num_frame - critical_index - 1  # 该片段还剩的帧数
        backFrames = critical_index + 1  # 该片段已经完成的帧数
        # ego已完成超过5s的行程
        if backFrames > 2 * frame_rate:
            if frnotFrames >= 3 * frame_rate:  # ego还剩超过5s的行程
                if type_ == self.scenario_type:
                    scenario_info = str(self.scenario_count).rjust(4, '0') + self.scenario_type + '_highD' + str(self.index)  # 主车换道cutin
                    self.scenario_count += 1
                    scenario_index = ''
                    scenario_len = 5 * frame_rate  # 场景长度
                    highrisk_startframe = egoMeta.initial_frame + critical_index - 1 * frame_rate
                    extract_scenario(egoMeta.id, highrisk_startframe, scenario_len, self.input_path, scenario_info, scenario_index, self.scenario_rootpath)
            else:  # ego剩余行程不足5s
                if type_ == self.scenario_type:
                    scenario_info = str(self.scenario_count).rjust(4, '0') + self.scenario_type + '_highD' + str(self.index)  # 主车换道cutin
                    self.scenario_count += 1
                    scenario_index = ''
                    scenario_len = 2 * frame_rate + frnotFrames
                    highrisk_startframe = egoMeta.initial_frame + critical_index - 1 * frame_rate
                    extract_scenario(egoMeta.id, highrisk_startframe, scenario_len, self.input_path, scenario_info, scenario_index, self.scenario_rootpath)
        # ego已完成的行程不足2s
        else:
            if frnotFrames >= 5 * frame_rate:  # ego还剩超过5s的行程
                if type_ == self.scenario_type:
                    scenario_info = str(self.scenario_count).rjust(4, '0') + self.scenario_type + '_highD' + str(self.index)  # 主车换道cutin
                    self.scenario_count += 1
                    scenario_index = ''
                    scenario_len = 5 * frame_rate
                    highrisk_startframe = egoMeta.initial_frame
                    extract_scenario(egoMeta.id, highrisk_startframe, scenario_len, self.input_path, scenario_info, scenario_index, self.scenario_rootpath)
            else:  # ego剩余行程不足5s
                if type_ == self.scenario_type:
                    scenario_info = str(self.scenario_count).rjust(4, '0') + self.scenario_type + '_highD' + str(self.index)  # 主车换道cutin
                    self.scenario_count += 1
                    scenario_index = ''
                    scenario_len = egoMeta.num_frame
                    highrisk_startframe = egoMeta.initial_frame
                    extract_scenario(egoMeta.id, highrisk_startframe, scenario_len, self.input_path, scenario_info, scenario_index, self.scenario_rootpath)
        return


if __name__ == '__main__':
    scenario_rootpath = '../VAE_sample/cutin/std/scenarios'
    train_dataset = '../VAE_sample/cutin/std'
    # stCutin = stScenario('cutin', scenario_rootpath)
    # stCutin.get_standard_scenario()
    flag = VAE_cutin_sample(scenario_rootpath, train_dataset, 125)

