import os
import math
import shutil
import pandas as pd
import numpy as np
import extract_scenario as es
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

import xodr_changer as openD_C
import xosc_writer as openS

# TODO：实现子文件夹中所有文件的集中存放
""" openS_rootpath = os.path.abspath('../OpenSCENARIO/HighD')
des_root = os.path.abspath('../OpenSCENARIO/scenario')
for root, dirs, files in os.walk(openS_rootpath):
    print(dirs)
    for i in dirs:
        origin_root = os.path.join(root, i)
        for root1, dirs1, files1 in os.walk(origin_root):
            for name in dirs1:
                origin_path = os.path.join(root1, name)
                des_path = os.path.join(des_root, name)
                shutil.copytree(origin_path, des_path)
    break """

""" # TODO：自动化执行CMD指令，实现对OpenS的esmini自动化播放
esmini_path = os.path.abspath('../OpenSCENARIO/esmini-demo/bin')
scenario_root = os.path.abspath('../OpenSCENARIO/scenario')
for root, dirs, files in os.walk(scenario_root):
    for name in dirs:
        scenario_path = os.path.join(root, name)
        osc_path = os.path.join(scenario_path, name) + '.xosc'
        path_cmd = 'cd ' + esmini_path
        play_cmd = 'esmini.exe --window 60 60 1200 1000  --osc ' + osc_path
        cmd = "e: && " + path_cmd + ' && ' + play_cmd
        os.popen(cmd).read()
 """

""" # TODO：危险场景的提取
# 思路：直接获得ego的起始帧与结束帧，并以此切出所有相关车辆的片段（起始帧缺失的倒推，结束帧缺失的无需处理）
input_path = os.path.abspath('../highD-dataset-v1.0/data/01_tracks.csv')
output_path = 'test.csv'
df = pd.read_csv(input_path)
ego_id = 210
highrisk_startframe = 4551
highrisk_endframe = 4801
ego_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
scenario_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
# 危险场景中的前车部分precedingId
pre_id = ego_df['precedingId'].unique()  # 获得场景中ego所有的前车
for id in pre_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            pre_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            pre_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            pre_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            pre_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, pre_df])  # 将该车片段添加至场景中
# 危险场景中的后车部分followingId
follow_id = ego_df['followingId'].unique()  # 获得场景中ego所有的前车
for id in follow_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            follow_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            follow_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            follow_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            follow_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, follow_df])  # 将该车片段添加至场景中
# 危险场景中的左前车部分leftPrecedingId
leftpre_id = ego_df['leftPrecedingId'].unique()  # 获得场景中ego所有的前车
for id in leftpre_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            leftpre_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            leftpre_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            leftpre_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            leftpre_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, leftpre_df])  # 将该车片段添加至场景中
# 危险场景中的左侧车部分leftAlongsideId
leftalong_id = ego_df['leftAlongsideId'].unique()  # 获得场景中ego所有的前车
for id in leftalong_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            leftalong_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            leftalong_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            leftalong_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            leftalong_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, leftalong_df])  # 将该车片段添加至场景中
# 危险场景中的左后侧部分leftFollowingId
leftfollow_id = ego_df['leftFollowingId'].unique()  # 获得场景中ego所有的前车
for id in leftfollow_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            leftfollow_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            leftfollow_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            leftfollow_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            leftfollow_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, leftfollow_df])  # 将该车片段添加至场景中
# 危险场景中的右前车部分rightPrecedingId
rightpre_id = ego_df['rightPrecedingId'].unique()  # 获得场景中ego所有的前车
for id in rightpre_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            rightpre_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            rightpre_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            rightpre_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            rightpre_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, rightpre_df])  # 将该车片段添加至场景中
# 危险场景中的右侧车部分rightAlongsideId
rightalong_id = ego_df['rightAlongsideId'].unique()  # 获得场景中ego所有的前车
for id in rightalong_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            rightalong_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            rightalong_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            rightalong_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            rightalong_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, rightalong_df])  # 将该车片段添加至场景中
# 危险场景中的右后侧部分rightFollowingId
rightfollow_id = ego_df['rightFollowingId'].unique()  # 获得场景中ego所有的前车
for id in rightfollow_id:
    if id != 0:
        frame_df = df[(df['id'] == id)]['frame']
        if frame_df.min() <= highrisk_startframe and frame_df.max() >= highrisk_endframe:
            rightfollow_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() <= highrisk_startframe and frame_df.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            rightfollow_df = df[(df['id'] == id) & (df['frame'] >= highrisk_startframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            rightfollow_df = df[(df['id'] == id) & (df['frame'] <= highrisk_endframe)]
        elif frame_df.min() > highrisk_startframe and frame_df.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            rightfollow_df = df[(df['id'] == id)]
        scenario_df = pd.concat([scenario_df, rightfollow_df])  # 将该车片段添加至场景中
'''
由于df以ego为参考依次将其周围八辆车的信息纳入df，可能存在同一辆车的帧数跳跃现象，需要对df中每辆车帧数进行排序
'''
groups = scenario_df.groupby('id')  # 将df按车辆id进行分组
final_scenario = pd.DataFrame(columns=list(scenario_df))  # 用于储存清洗完成后的新df
for group_id, rows in groups:  # 保证df中第一辆车为ego
    if group_id == ego_id:
        final_scenario = pd.concat([final_scenario, rows])
for group_id, rows in groups:
    if group_id != ego_id:
        rows.drop_duplicates(subset='frame', keep='first', inplace=True)  # 删除同一车辆中相同帧数
        rows = rows.sort_values(by="frame", ascending=True)  # 对同一辆车按帧数升序排序
        final_scenario = pd.concat([final_scenario, rows])
final_scenario.to_csv(output_path, index=None)
openS.xosc_write(output_path, 'highD_2.xodr', 'test.xosc', 17.665) """

""" # TODO：双主车危险场景的提取
# 思路：直接获得ego的起始帧与结束帧，并以此切出所有相关车辆的片段（起始帧缺失的倒推，结束帧缺失的无需处理）
input_path = os.path.abspath('../highD-dataset-v1.0/data/01_tracks.csv')
scenario_type = 'follow'
output_path = 'test.csv'
df = pd.read_csv(input_path)
ego_id = 210
highrisk_startframe = 4551
highrisk_frame = 4600
highrisk_endframe = 4801
ego_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
scenario_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
if scenario_type == 'follow':  # 紧密跟驰场景，危险时刻的ego前车定义为第二个主车
    ego2_df = ego_df[(df['frame'] == highrisk_frame)]['precedingId']  # 返回series
    for i in ego2_df.index:
        ego2_id = ego2_df.get(i)
nonego_df = ego_df.iloc[:, [-9, -8, -7, -6, -5, -4, -3, -2]].value_counts()
ego2_df = df[(df['id'] == ego2_id)]
scenario_df = pd.concat([ego_df, ego2_df])
print(ego2_df) """

""" # TODO：选取200个HighD单主车场景
scenario_root = os.path.abspath('../OpenSCENARIO/scenario_EKT')
des_root = os.path.abspath('../OpenSCENARIO/200_for_EKT')
follow_count = 0
cutin_count = 0
lanechanging_count = 0
for root, dirs, files in os.walk(scenario_root):
    for name in dirs:
        if 'follow' in name and follow_count < 100:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.xosc', '*.xodr'))
            follow_count += 1
        elif 'cutin' in name and cutin_count < 50:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.xosc', '*.xodr'))
            cutin_count += 1
        elif 'lanechanging' in name and lanechanging_count < 50:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.xosc', '*.xodr'))
            lanechanging_count += 1
    break """

""" # TODO：将EKT交付场景中.csv中的信息仅保留前四列
scenario_root = os.path.abspath('../OpenSCENARIO/200_for_EKT')
for root, dirs, files in os.walk(scenario_root):
    for dir in dirs:
        scenario_path = os.path.join(root, dir)
        for root1, dirs1, files1 in os.walk(scenario_path):
            for file in files1:
                if '.csv' in file:
                    csv_path = os.path.join(root1, file)
                    df = pd.read_csv(csv_path)
                    df1 = df.iloc[:, [0, 1, 2, 3]]
                    df1.to_csv(csv_path, index=None) """

""" # TODO：获得HighD数据集中各文件夹对应的坐标系偏移
scenario_rootpath = os.path.abspath('../OpenSCENARIO/HighD')
highD_meta = os.path.abspath('../OpenSCENARIO/HighD/recording.csv')
output_path = os.path.abspath('../OpenSCENARIO/200_for_EKT/bias.csv')
df_recording = pd.read_csv(highD_meta)
bias_dict = {}
for root, dirs, files in os.walk(scenario_rootpath):
    for highD_index in dirs:
        print(highD_index)
        highD_path = os.path.join(root, highD_index)  # highD数据集单个文件夹路径
        upper_marking = str(df_recording[df_recording['id'] == int(highD_index)]['upperLaneMarkings'][int(highD_index) - 1]).split(';')
        upper_marking = [float(i) for i in upper_marking]
        lower_marking = str(df_recording[df_recording['id'] == int(highD_index)]['lowerLaneMarkings'][int(highD_index) - 1]).split(';')
        lower_marking = [float(i) for i in lower_marking]
        y_bias = upper_marking[-1] + (lower_marking[0] - upper_marking[-1]) / 2
        bias_dict.update({str(highD_index): str(y_bias)})
    break
bias_df = pd.DataFrame([bias_dict]).T
bias_df = bias_df.reset_index().rename(columns={'index': 'id'})
bias_df.to_csv(output_path, index=None) """

""" # TODO：将HighD数据集中的车辆轨迹进行坐标修正
bias_csv = os.path.abspath('../OpenSCENARIO/200_for_EKT/bias.csv')
index_csv = os.path.abspath('../OpenSCENARIO/200_for_EKT/index_EKT.csv')
scenario_root = os.path.abspath('../OpenSCENARIO/200_for_EKT')
bias_df = pd.read_csv(bias_csv)
index_df = pd.read_csv(index_csv)
count = 0
for root, dirs, files in os.walk(scenario_root):
    for name in dirs:
        scenario_path = os.path.join(root, name)
        for root1, dirs1, files1 in os.walk(scenario_path):
            for file in files1:
                if '.csv' in file:
                    scenario_csv = os.path.join(root1, file)
                    csv_df = pd.read_csv(scenario_csv)
                    location_id = index_df.iat[count, 2]
                    bias = bias_df[(bias_df['id'] == location_id)].iat[0, 1]
                    csv_df['y'] = bias - csv_df['y'] - 1.05
                    csv_df.to_csv(scenario_csv, index=None)
    break """

""" # TODO：将车辆模型文件osgb复制到每个双车场景文件夹中
des_root = os.path.abspath('../OpenSCENARIO/scenario_2ego')
osgb_path = os.path.abspath('../OpenSCENARIO/car_white.osgb')
for root, dirs, files in os.walk(des_root):
    for name in dirs:
        des_path = os.path.join(root, name)
        fpath, fname = os.path.split(osgb_path)
        shutil.copy(osgb_path, des_path + './')
    break """

""" # TODO：将NDS_Shanghai场景数据文件进行重构并保存
data_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))
des_root = os.path.join(data_root, 'NDS_Shanghai/scenarios')
scenario_root = os.path.join(data_root, 'NDS_Shanghai/交付件汇总/11.5交付场景-危险+标准+碰撞')
for root, dirs, files in os.walk(scenario_root):
    for type in dirs:
        type_root = os.path.join(root, type)
        for root1, dirs1, files1 in os.walk(type_root):
            for name in dirs1:
                scenario_path = os.path.join(root1, name)
                if type == 'crash':
                    des_path = os.path.join(des_root, 'crash' + name)
                    shutil.copytree(scenario_path, des_path)
                else:
                    des_path = os.path.join(des_root, name)
                    shutil.copytree(scenario_path, des_path)
    break """

""" # TODO：选取400个上海NDS单主车场景
data_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))
scenario_root = os.path.join(data_root, 'NDS_Shanghai/scenarios')
des_root = os.path.join(data_root, 'NDS_Shanghai/NDS_for_EKT')
follow_count = 0
cutin_count = 0
lanechanging_count = 0
for root, dirs, files in os.walk(scenario_root):
    for name in dirs:
        if '1follow' in name and follow_count < 180:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.csv', '*.osgb', '*.xml'))
            follow_count += 1
        elif '1cutin' in name and cutin_count < 108:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.csv', '*.osgb', '*.xml'))
            cutin_count += 1
        elif '1lanechange' in name and lanechanging_count < 112:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.csv', '*.osgb', '*.xml'))
            lanechanging_count += 1
    break """

""" a = [1 for _ in range(50)]
b = [2 for _ in range(50)]
c = [3 for _ in range(50)]
d = [4 for _ in range(50)]
data = np.empty((2, 50, 2), dtype=np.float64)
for i in range(2):
    temp_array = np.empty((50, 2), dtype=np.float64)
    for j in range(50):
        temp_array[j, 0] = a[i]
        temp_array[j, 1] = b[i]
    data[i] = temp_array

x = np.load(os.path.abspath("../VAE_sample/follow2.npy"))
print(x.shape) """

""" nds_path = "E:\\Vertiacl_project\\HAV_virtual_testing\\Data\\NDS_Shanghai\\NDS_for_EKT\\1cutin1\\1cutin1.xodr"
nds_data = open(nds_path).read()
xodr = ET.fromstring(nds_data)
xodr.find('road').set('length', '3000')
xodr.write(nds_path) """

""" nds_path = "E:\\Horizontal_project\\亿咖通\\交付件\\NDS_for_EKT"
for root, dirs, files in os.walk(nds_path):
    for dir_name in dirs:
        dir_path = os.path.join(root, dir_name)
        for root1, dirs1, files1 in os.walk(dir_path):
            for scenario_name in dirs1:
                scenario_path = os.path.join(root1, scenario_name)
                for root2, dirs2, files2 in os.walk(scenario_path):
                    for file_name in files2:
                        if '.xml' in file_name:
                            del_file = os.path.join(root2, file_name)
                            os.remove(del_file) """
def downSample(scene_length, x, y):
    t = np.arange(0, scene_length, 0.04)
    df = pd.DataFrame({
        'time_in_seconds': t,
        'x': x,
        'y': y
    })
    output_x = (
        df.set_index(pd.to_timedelta(df['time_in_seconds'], unit='s'))
        ['x']
        .resample('100ms')
        .mean()
    ).to_list()
    output_y = (
        df.set_index(pd.to_timedelta(df['time_in_seconds'], unit='s'))
        ['y']
        .resample('100ms')
        .mean()
    ).to_list()
    return output_x, output_y

plt.plot(x, y, 'bo')
plt.plot(output_x, output_y, 'r*')
plt.show()
