# -*- coding: utf-8 -*-
# @Time         : 2022.1016
# @Author       : Syh
# @Description  : 场景提取的相关子函数

import os
from tqdm import tqdm
import shutil
import pandas as pd
import xodr_writer as openD
import xosc_writer as openS
import xodr_changer as openD_C

def write_test(csv_path, test_path, df_xlist, df_ylist):
    '''
    将进行过轨迹延拓的场景重构成OnSite测试所用的试卷形式
    '''
    df = pd.read_csv(csv_path)
    drop_list = range(10, 24, 1)
    df = df.drop(df.columns[drop_list], axis=1)
    grouped = df.groupby(['id'], sort=False)  # 将df按照车辆id进行group
    df_scenario = pd.DataFrame()
    count = 0
    for group_id, df_rows in grouped:
        if count == 0:  # ego
            ego_id = group_id
            ego_frame = df_rows['frame'].values.tolist()
            ego_start = ego_frame[0]
            ego_end = ego_frame[-1]
            df_base = df_rows[['frame', 'id']]
            df_scenario = df_rows.drop(df.columns[[2, 3]], axis=1)
            col_name = df_scenario.columns.tolist()
            col_name.insert(2, 'x')
            col_name.insert(3, 'y')
            df_scenario = df_scenario.reindex(columns=col_name)
            df_scenario['x'] = df_xlist[[group_id]]
            df_scenario['y'] = df_ylist[[group_id * -1]]
            count += 1
        else:
            df_nonego = df_base.copy(deep=True)  # 深拷贝，使得复制的df拥有自己的数据与索引，而非与df_base共用
            df_nonego['id'].replace(ego_id, group_id, inplace=True)
            frame_highD = df_rows['frame'].values.tolist()
            width_highD = df_rows['width'].values.tolist()
            height_highD = df_rows['height'].values.tolist()
            xv_highD = df_rows['xVelocity'].values.tolist()
            yv_highD = df_rows['yVelocity'].values.tolist()
            xa_highD = df_rows['xAcceleration'].values.tolist()
            ya_highD = df_rows['yAcceleration'].values.tolist()
            laneid_highD = df_rows['laneId'].values.tolist()
            # 将相关属性按照列表分别储存
            width, height, xv, yv, xa, ya, laneid = [[] for i in range(7)]
            start_frame = df_rows['frame'].values.tolist()[0]
            end_frame = df_rows['frame'].values.tolist()[-1]
            df_nonego = pd.concat([df_nonego, df_xlist[[group_id]]], axis=1)
            df_nonego = pd.concat([df_nonego, df_ylist[[group_id * -1]]], axis=1)
            df_nonego.columns = ['frame', 'id', 'x', 'y']
            for index, rows in df_nonego.iterrows():
                current_frame = rows['frame']
                if current_frame < start_frame:  # 向后延拓部分
                    width.append(df_rows['width'].values.tolist()[0])
                    height.append(df_rows['height'].values.tolist()[0])
                    xv.append(df_rows['xVelocity'].values.tolist()[0])
                    yv.append(0)
                    xa.append(0)
                    ya.append(0)
                    laneid.append(df_rows['laneId'].values.tolist()[0])
            if start_frame >= ego_start and end_frame <= ego_end:  # nonego的实际时间窗口小于ego
                width.extend(width_highD)  # 实际数据非延拓部分
                height.extend(height_highD)
                xv.extend(xv_highD)
                yv.extend(yv_highD)
                xa.extend(xa_highD)
                ya.extend(ya_highD)
                laneid.extend(laneid_highD)
            else:
                for frame in ego_frame:
                    if frame in frame_highD:
                        width.append(width_highD[frame_highD.index(frame)])
                        height.append(height_highD[frame_highD.index(frame)])
                        xv.append(xv_highD[frame_highD.index(frame)])
                        yv.append(yv_highD[frame_highD.index(frame)])
                        xa.append(xa_highD[frame_highD.index(frame)])
                        ya.append(ya_highD[frame_highD.index(frame)])
                        laneid.append(laneid_highD[frame_highD.index(frame)])
            for index, rows in df_nonego.iterrows():
                current_frame = rows['frame']
                if current_frame > end_frame:  # 向前延拓部分
                    width.append(df_rows['width'].values.tolist()[-1])
                    height.append(df_rows['height'].values.tolist()[-1])
                    xv.append(df_rows['xVelocity'].values.tolist()[-1])
                    yv.append(0)
                    xa.append(0)
                    ya.append(0)
                    laneid.append(df_rows['laneId'].values.tolist()[-1])
            # 将各列表加入dataframe中
            col_name = df_scenario.columns.tolist()
            df_nonego = df_nonego.reindex(columns=col_name)
            df_nonego['width'] = width
            df_nonego['height'] = height
            df_nonego['xVelocity'] = xv
            df_nonego['yVelocity'] = yv
            df_nonego['xAcceleration'] = xa
            df_nonego['yAcceleration'] = ya
            df_nonego['laneId'] = laneid
            # 加入场景df
            df_scenario = pd.concat([df_scenario, df_nonego])
            count += 1
    '''
    在df中补充ego前车信息
    '''
    grouped = df_scenario.groupby(['id'], sort=False)  # 将df按照车辆id进行group
    preced = []
    preced_xv, preced_x, preced_y, preced_yv, preced_xa, preced_ya = [[] for _ in range(6)]
    ego_x = []
    ego_laneid = []
    ego_frame = []
    nonego_frame, nonego_id, nonego_x, nonego_y, nonego_laneid, nonego_xv, nonego_yv, nonego_xa, nonego_ya = [[] for _ in range(9)]
    count = 0
    for group_id, rows in grouped:
        if count == 0:  # ego
            ego_frame = rows['frame'].values.tolist()
            ego_x = rows['x'].values.tolist()
            ego_laneid = rows['laneId'].values.tolist()
            count += 1
        else:
            nonego_frame.extend(rows['frame'].values.tolist())
            nonego_id.extend(rows['id'].values.tolist())
            nonego_x.extend(rows['x'].values.tolist())
            nonego_y.extend(rows['y'].values.tolist())
            nonego_laneid.extend(rows['laneId'].values.tolist())
            nonego_xv.extend(rows['xVelocity'].values.tolist())
            nonego_yv.extend(rows['yVelocity'].values.tolist())
            nonego_xa.extend(rows['xAcceleration'].values.tolist())
            nonego_ya.extend(rows['yAcceleration'].values.tolist())
            count += 1
    if ego_x[0] < ego_x[-1]:  # 下行方向
        for i_ego, x_ego in enumerate(ego_x):
            temp_index = []
            temp_dis = []
            for i, x in enumerate(nonego_x):
                if nonego_frame[i] == ego_frame[i_ego] and nonego_laneid[i] == ego_laneid[i_ego] and x > x_ego:  # 位于ego前方
                    temp_index.append(i)
                    temp_dis.append(x - x_ego)
            if len(temp_dis) == 0:  # ego前方无车
                preced.append(-99)
                preced_x.append(-99)
                preced_y.append(-99)
                preced_xv.append(-99)
                preced_yv.append(-99)
                preced_xa.append(-99)
                preced_ya.append(-99)
            else:
                preced_index = temp_index[temp_dis.index(min(temp_dis))]
                preced.append(nonego_id[preced_index])
                preced_x.append(nonego_x[preced_index])
                preced_y.append(nonego_y[preced_index])
                preced_xv.append(nonego_xv[preced_index])
                preced_yv.append(nonego_yv[preced_index])
                preced_xa.append(nonego_xa[preced_index])
                preced_ya.append(nonego_ya[preced_index])
    else:
        for i_ego, x_ego in enumerate(ego_x):
            temp_index = []
            temp_dis = []
            for i, x in enumerate(nonego_x):
                if nonego_frame[i] == ego_frame[i_ego] and nonego_laneid[i] == ego_laneid[i_ego] and x < x_ego:  # 位于ego前方
                    temp_index.append(i)
                    temp_dis.append(x - x_ego)
            if len(temp_dis) == 0:  # ego前方无车
                preced.append(-999)
                preced_x.append(-999)
                preced_y.append(-999)
                preced_xv.append(-999)
                preced_yv.append(-999)
                preced_xa.append(-999)
                preced_ya.append(-999)
            else:
                preced_index = temp_index[temp_dis.index(min(temp_dis))]
                preced.append(nonego_id[preced_index])
                preced_x.append(nonego_x[preced_index])
                preced_y.append(nonego_y[preced_index])
                preced_xv.append(nonego_xv[preced_index])
                preced_yv.append(nonego_yv[preced_index])
                preced_xa.append(nonego_xa[preced_index])
                preced_ya.append(nonego_ya[preced_index])
    # 非主车部分用0补全
    length = len(ego_x) + len(nonego_x)
    preced = list(preced + [-999] * (length - len(preced)))
    preced_x = list(preced_x + [-999] * (length - len(preced_x)))
    preced_y = list(preced_y + [-999] * (length - len(preced_y)))
    preced_xv = list(preced_xv + [-999] * (length - len(preced_xv)))
    preced_yv = list(preced_yv + [-999] * (length - len(preced_yv)))
    preced_xa = list(preced_xa + [-999] * (length - len(preced_xa)))
    preced_ya = list(preced_ya + [-999] * (length - len(preced_ya)))
    # 将ego前车信息添加至df
    col_name = df_scenario.columns.tolist()
    col_name.append('precedingId')
    col_name.append('precedingX')
    col_name.append('precedingY')
    col_name.append('precedingXVelocity')
    col_name.append('precedingYVelocity')
    col_name.append('precedingXAcceleration')
    col_name.append('precedingYAcceleration')
    df_scenario = df_scenario.reindex(columns=col_name)
    df_scenario['precedingId'] = preced
    df_scenario['precedingX'] = preced_x
    df_scenario['precedingY'] = preced_y
    df_scenario['precedingXVelocity'] = preced_xv
    df_scenario['precedingYVelocity'] = preced_yv
    df_scenario['precedingXAcceleration'] = preced_xa
    df_scenario['precedingYAcceleration'] = preced_ya

    df_scenario.to_csv(test_path, index=None)
    return