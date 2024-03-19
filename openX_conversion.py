# %%
import os
from tqdm import tqdm
import shutil
import pandas as pd
import xodr_writer as openD
import xosc_writer as openS
import xodr_changer as openD_C


# %%
# TODO：以HighD数据集单个文件夹为单位（每个文件夹的坐标系偏移均不同）完成各场景的OpenX标准文件生成
# PS：可直接进行覆盖写入
scenario_rootpath = os.path.abspath('../OpenSCENARIO/HighD_V3')
highD_meta = os.path.abspath('../OpenSCENARIO/recording.csv')
df_recording = pd.read_csv(highD_meta)
flag = 0  # 用于区分当前转换的场景是否为双主车（默认为单主车）
if '2ego' in scenario_rootpath:
    flag = 1
for root, dirs, files in os.walk(scenario_rootpath):
    for highD_index in tqdm(dirs):
        # print(highD_index)
        highD_path = os.path.join(root, highD_index)  # highD数据集单个文件夹路径
        if int(highD_index) < 10:
            tracksMeta_path = os.path.join("../highD-dataset-v1.0/data/0" + str(highD_index) + "_tracksMeta.csv")
        else:
            tracksMeta_path = os.path.join("../highD-dataset-v1.0/data/" + str(highD_index) + "_tracksMeta.csv")
        # TODO：完成该文件夹对应OpenDrive路网的绘制
        upper_marking = str(df_recording[df_recording['id'] == int(highD_index)]['upperLaneMarkings'][int(highD_index) - 1]).split(';')
        upper_marking = [float(i) for i in upper_marking]
        lower_marking = str(df_recording[df_recording['id'] == int(highD_index)]['lowerLaneMarkings'][int(highD_index) - 1]).split(';')
        lower_marking = [float(i) for i in lower_marking]
        y_bias = upper_marking[-1] + (lower_marking[0] - upper_marking[-1]) / 2
        df_tracksMeta = pd.read_csv(tracksMeta_path)
        xodr_name = 'highD_' + highD_index + '.xodr'
        marking = upper_marking + lower_marking
        '''
        output_path_xodr = os.path.join(highD_path, xodr_name)
        if len(upper_marking) == 3:
            openD.xodr_2lanes(upper_marking, lower_marking, output_path_xodr)
        else:
            openD.xodr_3lanes(upper_marking, lower_marking, output_path_xodr)
        '''
        # TODO：完成该文件夹所包含所有场景的OpenScenario格式转换（OpenScenario保存到对应文件夹并复制OpenDrive到对应文件夹）
        '''
        重新输出经过数据增强后的*_exam.xosc
        **遇到坐标于地图不匹配的情况——初步排查为*.csv与*_test.csv坐标不一致所导致
        *_test.csv的y坐标已经经过了一次y_bias的纠偏，若输入xosc_write_V5中将重复纠偏

        *****************已解决
        针对*_exam.xosc的数据增强输出的具体步骤：
        1. 通过data_processioon.py对所有*_test.csv文件进行数据增强，输出*_test_processed.csv
        2. 基于输出的*_test_processed.csv，利用xosc_writer_V6()进行新的*_exam.xosc的输出
        '''
        for root1, dirs1, files1 in os.walk(highD_path):
            for scenario_name in dirs1:
                scenario_path = os.path.join(root1, scenario_name)  # 危险场景对应文件夹路径
                csv_name = scenario_name + '_test_processed.csv'
                csv_path = os.path.join(scenario_path, csv_name)
                test_name = scenario_name + '_test.csv'
                test_path = os.path.join(scenario_path, test_name)  # 测试用的场景试卷路径
                xosc_name = scenario_name + '_exam.xosc'
                output_path_xosc = os.path.join(scenario_path, xosc_name)
                # 针对text.csv存在的重复纠偏，重写了xosc_writer_V6()，删除了纠偏动作
                openS.xosc_write_V6(csv_path, xodr_name, output_path_xosc, y_bias, marking, df_tracksMeta, flag)
                # write_test(csv_path, test_path, df_xlist, df_ylist)
                destination = scenario_path + '\\'
                # shutil.copy(output_path_xodr, destination)
    break


# %%
# TODO：将NDS_Shanghai的各场景数据进行OpenSCENARIO转换
# PS：可以直接进行覆盖写入
data_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))
scenario_root = os.path.join(data_root, 'NDS_Shanghai/NDS_for_EKT/original')
for root, dirs, files in os.walk(scenario_root):
    for name in tqdm(dirs):
        scenario_path = os.path.join(root, name)
        for root1, dirs1, files1 in os.walk(scenario_path):
            for file in files1:
                if '.xodrs' in file:
                    xodr_path = os.path.join(root1, file)
                    xodr = openD_C.read_xml(xodr_path)
                    xodr.find('road').set('length', '3000')
                    xodr.write(xodr_path, xml_declaration=True)
            nds_path = os.path.join(root1, name) + '.xml'
            output_path = os.path.join(root1, name) + '.xosc'
            xodr_path = name + '.xodr'
            openS.nds2xosc(nds_path, xodr_path, output_path)
    break

# %%
# TODO：将HighD各个文件夹中所包含的场景集中保存
# PS：无法进行覆盖，如有修改，需要删掉des_root中的所有场景文件夹
openS_rootpath = os.path.abspath('../OpenSCENARIO/HighD_V3')
des_root = os.path.abspath('../OpenSCENARIO/scenario_for_evaluation')
for root, dirs, files in os.walk(openS_rootpath):
    for i in tqdm(dirs):
        origin_root = os.path.join(root, i)
        for root1, dirs1, files1 in os.walk(origin_root):
            for name in dirs1:
                origin_path = os.path.join(root1, name)
                des_path = os.path.join(des_root, name)
                shutil.copytree(origin_path, des_path)
    break

# %%
# TODO：利用python调用CMD，实现esmini对osc的自动播放
esmini_path = os.path.abspath('../OpenSCENARIO/esmini-demo/bin')
# scenario_root = os.path.abspath('../OpenSCENARIO/scenario_2ego')  # HighD场景库
scenario_root = os.path.join(os.path.abspath(os.path.join(os.getcwd(), "../..")), 'NDS_Shanghai/scenarios')  # 上海NDS场景库
for root, dirs, files in os.walk(scenario_root):
    for name in dirs:
        if 'cutin' in name:
            scenario_path = os.path.join(root, name)
            osc_path = os.path.join(scenario_path, name) + '.xosc'
            path_cmd = 'cd ' + esmini_path
            play_cmd = 'esmini.exe --window 60 60 1200 1000  --osc ' + osc_path
            cmd = "e: && " + path_cmd + ' && ' + play_cmd
            os.popen(cmd).read()
        # break

# %%
