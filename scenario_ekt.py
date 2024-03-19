import os
import shutil
import pandas as pd


# TODO：选取200个HighD单主车场景
scenario_root = os.path.abspath('../OpenSCENARIO/scenario_V2')
des_root = os.path.abspath('../OpenSCENARIO/200_for_EKT')
follow_count = 0
cutin_count = 0
lanechanging_count = 0
for root, dirs, files in os.walk(scenario_root):
    for name in dirs:
        if 'follow' in name and follow_count < 100:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.csv'))
            follow_count += 1
        elif 'cutin' in name and cutin_count < 50:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.csv'))
            cutin_count += 1
        elif 'lanechanging' in name and lanechanging_count < 50:
            origin_path = os.path.join(root, name)
            des_path = os.path.join(des_root, name)
            shutil.copytree(origin_path, des_path, ignore=shutil.ignore_patterns('*.csv'))
            lanechanging_count += 1
    break

# TODO：将EKT交付场景中.csv中的信息仅保留前四列
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
                    df1.to_csv(csv_path, index=None)

# TODO：将HighD数据集中的车辆轨迹进行坐标修正
bias_csv = os.path.abspath('../OpenSCENARIO/bias.csv')
index_csv = os.path.abspath('../OpenSCENARIO/index_EKT.csv')
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

