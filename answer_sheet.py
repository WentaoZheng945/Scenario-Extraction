import pandas as pd
from tqdm import tqdm
import os


def write_answerSheet(root_path, answer_path, output_path):
    '''
    将参赛者输出的轨迹数据替换掉主车轨迹，并更新其前车信息

    input：标准场景根目录、参赛者轨迹、输出的答题卡路径
    output：标准答题卡
    '''
    highD_meta = os.path.abspath("../OpenSCENARIO/recording.csv")
    df_recording = pd.read_csv(highD_meta)  # 各类场景信息
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if '_test.csv' in file:  # 获取标准场景
                csv_path = os.path.join(root, file)
            if '.xodr' in file:  # 获取场景对应的HighD索引
                highD_index = int(file[6:-5])
    if int(highD_index) < 10:
        tracksMeta_path = os.path.join("../highD-dataset-v1.0/data/0" + str(highD_index) + "_tracksMeta.csv")
    else:
        tracksMeta_path = os.path.join("../highD-dataset-v1.0/data/" + str(highD_index) + "_tracksMeta.csv")
    df_tracksMeta = pd.read_csv(tracksMeta_path)
    df = pd.read_csv(csv_path)
    grouped = df.groupby(['id'], sort=False)  # 将df按照车辆id进行group
    # 判断答卷是否为空
    if os.path.getsize(answer_path):
        df_answer = pd.read_csv(answer_path)
    else:
        return
    df_scenario = pd.DataFrame()
    count = 0
    for group_id, df_rows in grouped:
        if count == 0:  # ego，替换为参赛者轨迹
            ego_id = group_id
            height = df_tracksMeta[df_tracksMeta['id'] == ego_id]['height'].values.tolist()[0]  # 车宽
            ego_frame = df_rows['frame'].values.tolist()
            df_base = df_rows[['frame', 'id']]
            df_scenario = df_rows.drop(df.columns[[2, 3, 10, 11, 12, 13, 14, 15, 16, 17]], axis=1)
            # 判断主车车道
            ego_y = df_answer['z'].values.tolist()
            laneid = []
            for y in ego_y:
                upper_marking = str(df_recording[df_recording['id'] == int(highD_index)]['upperLaneMarkings'][int(highD_index) - 1]).split(';')
                upper_marking = [float(i) for i in upper_marking]
                lower_marking = str(df_recording[df_recording['id'] == int(highD_index)]['lowerLaneMarkings'][int(highD_index) - 1]).split(';')
                lower_marking = [float(i) for i in lower_marking]
                y_bias = upper_marking[-1] + (lower_marking[0] - upper_marking[-1]) / 2
                y_highD = y_bias - y - height / 2  # 将车辆纵坐标还原至HighD坐标系
                temp = upper_marking + lower_marking
                temp.append(y_highD)
                temp.sort()
                if len(upper_marking) == 3:  # 双车道场景
                    if temp.index(y_highD) == 1:
                        laneid.append(2)
                    elif temp.index(y_highD) == 2:
                        laneid.append(3)
                    elif temp.index(y_highD) == 4:
                        laneid.append(5)
                    elif temp.index(y_highD) == 5:
                        laneid.append(6)
                    else:  # 驶出行车道
                        laneid.append(-999)
                else:  # 三车道场景
                    if temp.index(y_highD) == 1:
                        laneid.append(2)
                    elif temp.index(y_highD) == 2:
                        laneid.append(3)
                    elif temp.index(y_highD) == 3:
                        laneid.append(4)
                    elif temp.index(y_highD) == 5:
                        laneid.append(6)
                    elif temp.index(y_highD) == 6:
                        laneid.append(7)
                    elif temp.index(y_highD) == 7:
                        laneid.append(8)
                    else:
                        laneid.append(-999)
            col_name = df_scenario.columns.tolist()
            col_name.insert(2, 'x')
            col_name.insert(3, 'y')
            col_name.insert(10, 'laneId')
            df_scenario = df_scenario.reindex(columns=col_name)
            df_scenario['x'] = df_answer[['x']]
            df_scenario['y'] = df_answer[['z']]
            df_scenario['laneId'] = pd.DataFrame(laneid)
            count += 1
        else:
            df_nonego = df_base.copy(deep=True)  # 深拷贝，使得复制的df拥有自己的数据与索引，而非与df_base共用
            df_nonego['id'].replace(ego_id, group_id, inplace=True)
            x = df_rows['x'].values.tolist()
            y = df_rows['y'].values.tolist()
            width = df_rows['width'].values.tolist()
            height = df_rows['height'].values.tolist()
            xv = df_rows['xVelocity'].values.tolist()
            yv = df_rows['yVelocity'].values.tolist()
            xa = df_rows['xAcceleration'].values.tolist()
            ya = df_rows['yAcceleration'].values.tolist()
            laneid = df_rows['laneId'].values.tolist()
            # 将各列表加入dataframe中
            col_name = df_scenario.columns.tolist()
            df_nonego = df_nonego.reindex(columns=col_name)
            df_nonego['x'] = x
            df_nonego['y'] = y
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
            print(ego_x[0] < ego_x[-1])
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
    if ego_x[0] < ego_x[1]:  # 下行方向
        for i_ego, x_ego in enumerate(ego_x):
            temp_index = []
            temp_dis = []
            for i, x in enumerate(nonego_x):
                if nonego_frame[i] == ego_frame[i_ego] and nonego_laneid[i] == ego_laneid[i_ego] and x > x_ego:  # 位于ego前方
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
    # 非主车部分用-999补全
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

    df_scenario.to_csv(output_path, index=None)
    return


if __name__ == '__main__':
    answer_rootpath = "E:\\Vertiacl_project\\HAV_virtual_testing\\Data\\highD\\Apollo_test\\25"
    for root, dirs, files in os.walk(answer_rootpath):
        for dir_name in tqdm(dirs):
            root_path = os.path.join(root, dir_name)
            answer_path = os.path.join(root_path, 'output.csv')
            output_path = os.path.join(root_path, 'answerSheet.csv')
            write_answerSheet(root_path, answer_path, output_path)
