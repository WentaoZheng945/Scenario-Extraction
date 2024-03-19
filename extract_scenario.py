import os
import argparse
import zipfile
import pandas as pd
import numpy as np
# TODO: Q1:除去重复帧时为何不对主车（ego_2）去除，这在一个主车时不会出现问题，但双主车时可能出现主车重复的现象？
#       Q2:提取关键参数时，似乎存在前后车帧数不对应的情况？

# TODO: 保存highD三种数据表的路径
def create_args(input_path, input_static_path, input_meta_path):
    # 创建解析对象
    parser = argparse.ArgumentParser(description="ParameterOptimizer")
    # --- Input paths ---
    # 向解析对象parser中添加属性（'--'表示可选参数），并定义其默认值及帮助文档等
    parser.add_argument('--input_path', default=input_path, type=str,
                        help='CSV file of the tracks')  # 轨迹文件位置
    parser.add_argument('--input_static_path', default=input_static_path, type=str,
                        help='Static meta data file for each track')  # 静态信息文件位置
    parser.add_argument('--input_meta_path', default=input_meta_path, type=str,
                        help='Static meta data file for the whole video')  # 摄像头位置信息
    # --- Settings ---
    parser.add_argument('--visualize', default=True, type=lambda x: (str(x).lower() == 'true'),
                        help='True if you want to visualize the data.')  # 是否进行可视化
    parser.add_argument('--background_image', default="E:/科研/智能车虚拟测试自动化/数据/highD数据/highD-dataset-v1.0/data/01_highway.png", type=str,
                        help='Optional: you can specify the correlating background image.')  # 可视化时选择具体的照片作为背景图
    # parser.parse_args()将添加的所有属性返回至子类实例中，vars()将实例按照dict进行解析（属性及对应的属性默认值）
    parsed_arguments = vars(parser.parse_args())
    return parsed_arguments  # 返回dict对象


# TODO：根据ego片段获取其周围八辆车对应片段
def extract_nonego(df, ego_df, highrisk_startframe, highrisk_endframe):
    '''
    zwt:依据已知的主车轨迹信息，提取时间域上重叠的背景车信息（以前后左右8个属性为参考）
        返回dataframe，返回的dataframe中只包含背景车的信息（不包含主车信息）
        总结来说，此函数实现了论文里吹牛的8车模型
    syh:该方法用来对识别出的危险场景进行场景参与者扩充（填入ego相关车辆的轨迹片段）

    :param arguments：所有车轨迹dataFrame、ego轨迹dataFrame、ego轨迹起始帧、ego轨迹结束帧
    :return：相关参与者对应轨迹片段dataFrame
    '''
    scenario_df = pd.DataFrame()
    # 危险场景中的前车部分precedingId
    pre_id = ego_df['precedingId'].unique()  # 获得场景中ego所有的前车
    for id in pre_id:
        if id != 0:
            frame_df = df[(df['id'] == id)]['frame']  # 背景车的frame
            # TODO 三种情况：
            #  （1）主车时间为背景车时间子集，将背景车时间以主车时间起始点为截点切片
            #  （2）背景车起始时间早于主车，但终止时间也早于主车，切片时只考虑大于初始帧的片段
            #  （3）背景车的初始时间晚于主车，但终止时间也晚于主车，切片时同样只考虑小于终止帧的片段
            #  （4）背景车为主车时间子集，将背景车全部时间切去出来

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
    follow_id = ego_df['followingId'].unique()  # 获得场景中ego所有的后车
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
    leftpre_id = ego_df['leftPrecedingId'].unique()  # 获得场景中ego所有的左前车
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
    leftalong_id = ego_df['leftAlongsideId'].unique()  # 获得场景中ego所有的左侧车
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
    leftfollow_id = ego_df['leftFollowingId'].unique()  # 获得场景中ego所有的左后侧车
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
    rightpre_id = ego_df['rightPrecedingId'].unique()  # 获得场景中ego所有的右前车
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
    rightalong_id = ego_df['rightAlongsideId'].unique()  # 获得场景中ego所有的右侧车
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
    rightfollow_id = ego_df['rightFollowingId'].unique()  # 获得场景中ego所有的右后车
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
    return scenario_df


# TODO：提取危险场景(单主车)
def extract_scenario(ego_id, highrisk_startframe, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath):
    """
    syh:该方法用来将识别出来的危险场景提取至相应的csv中，并单独存入根目录下的对应文件夹中
    zwt:从原始high_d数据中提取特定id作为主车，给定初始帧和事件时长，提取对应的dataframe,
        同时依据extract_nonego(8车模型)从中提取背景车，最后将主车和背景车拼接写入对应文件夹下的对应csv中
        总结来说，实现由原始csv到事件参与者csv的转换(其中主车id的选取，以及初始帧和事件时长的选取问题尚未解决)

    :param arguments: 本车id、危险场景起始帧、危险场景总帧数、场景位于的highD数据路径、场景类型、类型编号、输出场景的根目录
    :return: None
    """
    new_dir = os.path.join(scenario_rootpath + '/' + str(scenario_type) + str(scenario_index))  # 文件夹
    if not os.path.isdir(new_dir):
        os.mkdir(new_dir)  # 不存在则新建
        output_path = os.path.join(new_dir + '/' + str(scenario_type) + str(scenario_index) + '.csv')  # 提取出的轨迹文件
        df = pd.read_csv(input_path)  # pd读取csv，输出dataframe格式'df'，读取high_d的原始csv
        highrisk_endframe = highrisk_startframe + scenario_len
        # 危险场景中的ego部分
        ego_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]  # 提取主车的dataframe
        # 将ego部分场景加入危险场景中
        scenario_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        nonego_df = extract_nonego(df, ego_df, highrisk_startframe, highrisk_endframe)  # 提取8车模型的背景车
        scenario_df = pd.concat([scenario_df, nonego_df])  # 把主车和8车模型提取的背景车拼接起来
        '''
        syh:由于df以ego为参考依次将其周围八辆车的信息纳入df，可能存在同一辆车的帧数跳跃现象，需要对df中每辆车帧数进行排序
        zwt:这里描述的调整或许是因为某一辆车可能初始时为主车前车，后为8车模型其他位置的车辆，因此被提取两次，这里去除多提取的内容，
            方法为groupby后去除重复帧数
        '''
        groups = scenario_df.groupby('id')  # 将df按车辆id进行分组
        final_scenario = pd.DataFrame(columns=list(scenario_df))  # 用于储存清洗完成后的新df
        for group_id, rows in groups:  # 保证df中第一辆车为ego
            if group_id == ego_id:
                final_scenario = pd.concat([final_scenario, rows])
        for group_id, rows in groups:
            if group_id != ego_id:
                # 删除同一车辆中相同帧数(subset表示按这一列去重， first表示不第一次出现不标记为重复，其余标记为重复，true表示直接在源数据上修改)
                rows.drop_duplicates(subset='frame', keep='first', inplace=True)  # 删除同一车辆中相同帧数
                rows = rows.sort_values(by="frame", ascending=True)  # 对同一辆车按帧数升序排序
                final_scenario = pd.concat([final_scenario, rows])
        # 将危险场景输出至对应文件夹中的.csv中
        final_scenario.to_csv(output_path, index=False)
    return


# TODO：提取危险场景(双主车)
def extract_scenario_2ego(ego_id, highrisk_startframe, highrisk_frame, scenario_len, input_path, scenario_type, scenario_index, scenario_rootpath):
    """
    syh:该方法用来将识别出来的双主车危险场景提取至相应的csv中，并单独存入根目录下的对应文件夹中
    zwt:提取双主车场景，与但主车几乎一致，在此基础上将最危险帧的前车作为ego_2的操作

    :param arguments: 本车id、危险场景起始帧、最危险帧数、危险场景总帧数、场景位于的highD数据路径、场景类型、类型编号、输出场景的根目录
    :return: None
    """
    new_dir = os.path.join(scenario_rootpath + '/' + str(scenario_type) + str(scenario_index))  # 文件夹位置
    if not os.path.isdir(new_dir):
        os.mkdir(new_dir)  # 不存在则新建
        output_path = os.path.join(new_dir + '/' + str(scenario_type) + str(scenario_index) + '.csv')  # 输出csv位置
        df = pd.read_csv(input_path)  # pd读取csv，输出dataframe格式'df'
        highrisk_endframe = highrisk_startframe + scenario_len
        # 危险场景中的ego部分
        ego_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]  # 主车dataframe
        # 第二辆车为最危险场面时主车的前车
        # 确定危险场景中的第二辆ego的id
        ego2_ids = ego_df[(df['frame'] == highrisk_frame)]['precedingId']  # 返回series
        for i in ego2_ids.index:
            ego2_id = ego2_ids.get(i)  # 其实只有一个值
        # 将ego部分场景加入危险场景中
        scenario_df = df[(df['id'] == ego_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]  # 主车部分
        # 将ego2部分场景加入危险场景中，提取方式与其余背景车一致
        ego2_frame = df[(df['id'] == ego2_id)]['frame']
        if ego2_frame.min() <= highrisk_startframe and ego2_frame.max() >= highrisk_endframe:
            ego2_df = df[(df['id'] == ego2_id) & (df['frame'] <= highrisk_endframe) & (df['frame'] >= highrisk_startframe)]
        elif ego2_frame.min() <= highrisk_startframe and ego2_frame.max() < highrisk_endframe:  # 结束帧缺失（无需处理，直接取至最后帧）
            ego2_df = df[(df['id'] == ego2_id) & (df['frame'] >= highrisk_startframe)]
        elif ego2_frame.min() > highrisk_startframe and ego2_frame.max() >= highrisk_endframe:  # 起始帧缺失（轨迹倒推——写入xosc时的工作）
            ego2_df = df[(df['id'] == ego2_id) & (df['frame'] <= highrisk_endframe)]
        elif ego2_frame.min() > highrisk_startframe and ego2_frame.max() < highrisk_endframe:  # 起始帧与结束帧均丢失
            ego2_df = df[(df['id'] == ego2_id)]
        scenario_df = pd.concat([scenario_df, ego2_df])
        # 分别提取两个主车的周围8车
        # ego_1
        noneego_df = extract_nonego(df, ego_df, highrisk_startframe, highrisk_endframe)
        scenario_df = pd.concat([scenario_df, noneego_df])
        # ego_2
        nonego2_df = extract_nonego(df, ego2_df, highrisk_startframe, highrisk_endframe)
        scenario_df = pd.concat([scenario_df, nonego2_df])
        '''
        syh:由于df以ego为参考依次将其周围八辆车的信息纳入df，可能存在同一辆车的帧数跳跃现象，需要对df中每辆车帧数进行排序
        zwt:先后把两个主车的周围8车提取出来，会出现重复提取的现象，这个进行去重
        '''
        groups = scenario_df.groupby('id')  # 将df按车辆id进行分组
        final_scenario = pd.DataFrame(columns=list(scenario_df))  # 用于储存清洗完成后的新df
        for group_id, rows in groups:  # 保证df中第一辆车为ego
            if group_id == ego_id:
                final_scenario = pd.concat([final_scenario, rows])
        for group_id, rows in groups:  # 保证df中第二辆车为ego2
            if group_id == ego2_id:
                final_scenario = pd.concat([final_scenario, rows])
        for group_id, rows in groups:
            if group_id != ego_id:
                rows.drop_duplicates(subset='frame', keep='first', inplace=True)  # 删除同一车辆中相同帧数
                rows = rows.sort_values(by="frame", ascending=True)  # 对同一辆车按帧数升序排序
                final_scenario = pd.concat([final_scenario, rows])
        # 将危险场景输出至对应文件夹中的.csv中
        final_scenario.to_csv(output_path, index=None)
    return


# TODO：对所有场景形成对应的索引文件（包括场景类型、参与者个数等标签）
def scenario_flag(scenario_rootpath, index_output_path, location, lane, danger, crash):
    """
    syh:该方法用来将识别出来的所有危险场景的场景标签（任务类型、参与者个数）输入到一个单独的索引文档中
    zwt:实现对提取出的场景打标签的功能

    :param arguments: 储存危险场景的根目录、场景索引文档路径
    :return: None
    """
    scenario_path = []  # 场景路径
    scenario_name = []  # 场景名称（与储存场景的文件夹名对应）
    scenario_task = []  # 场景对应的任务类型
    scenario_cars = []  # 场景包含的车辆个数
    # 获取储存场景根目录下的所有场景csv文件路径
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for filename in filenames:
            if '.csv' in filename:
                name = filename.split('.')[0]  # csv文件名
                scenario_name.append(name)
                scenario_path.append(os.path.join(filepath, filename))  # 存放csv文件路径
                if 'follow' in name:
                    scenario_task.append("紧密跟驰")
                elif 'cutin' in name:
                    scenario_task.append("换道插入")
                elif 'lanechanging' in name:
                    scenario_task.append('侧方插入')
    for path in scenario_path:
        df = pd.read_csv(path)
        id_df = df['id']  # 取出场景csv中id对应的列，dataframe
        id_array = np.array(id_df)  # 将dataframe转换为array
        id_list = id_array.tolist()  # 将array转换为list【id_df.values.tolist()同样效果】
        num_cars = len(set(id_list))  # 去重，统计车辆个数
        scenario_cars.append(num_cars)
    danger_norm = [round((4 - i) / 4, 2) for i in danger]  # 危险程度评价（最值归一化），MTTC范围0-4
    crash = [round(i) for i in crash]
    flag_list = [scenario_name, scenario_task, location, lane, scenario_cars, danger_norm, crash]
    df_name = ['名称', '任务', '地点编号', '车道数', '参与者个数', '危险程度_MTTC', '危险程度_CI']
    flag_df = pd.DataFrame(columns=df_name, data=list(zip(*flag_list)))  # 对flag_list进行转置，按[(a,b,c),..,(a1,b1.c1)]进行重组，每个元素对应df中的一行
    # *list将list中每个可迭代元素取出，zip将多个list按照索引打包成一个个元组并组成一个新的list
    flag_df.to_csv(index_output_path, index=False, encoding='gbk')
    return


# TODO：将每个场景对应的文件（轨迹数据及openX数据）分别进行压缩
def scenario_zip(scenario_rootpath, scenario_zippath):
    """
    syh:该方法用来将识别出来的所有危险场景进行批量压缩
    zwt:该函数能实现将scenario_rootpath下的每一个文件夹分别打包到scenario_zippath下
        ps:scenario_rootpath下只能有文件夹，不能有文件，不然会报错

    :param arguments: 储存危险场景的根目录、各场景压缩储存的根目录
    :return: None
    """
    dirs = os.listdir(scenario_rootpath)
    for dir_name in dirs:
        zippath = os.path.join(scenario_zippath, dir_name) + '.zip'
        zf = zipfile.ZipFile(zippath, mode='w')
        filepath = os.path.join(scenario_rootpath, dir_name)
        scenario_files = os.listdir(filepath)
        for scenario_file in scenario_files:
            file = os.path.join(filepath, scenario_file)
            print(file)
            zf.write(file, scenario_file)
        zf.close()
    return


def df_to_list(path, attribute):
    """
    该方法用来读取csv，并将特定属性的数据列以list输出

    :param arguments: csv路径、需提取的属性
    :return: 属性对应的数据list
    """
    df = pd.read_csv(path)
    attribute_df = df[attribute]
    attribute_list = attribute_df.values.tolist()  # .value变成ndarray，tolist变成列表
    return attribute_list


# TODO：将所有场景转换为GAN所需要的样本格式（仅提取关键属性的时间序列）
def GAN_sample(scenario_rootpath, GANsample_rootpath):
    """
    zwt:将之前提取出的csv文件中关键背景车的关键参数提取出来
    syh:该方法用来将识别出来的所有危险场景转换为GAN派生所需的样本，即提取场景关键属性值
        跟驰场景：本车速度、前车速度、相对距离
        换道场景：参考华骏IEEE中对cutin场景的定义————
            目标车道（ego插入）：1.following car——2.ego car——3.preceding car
            目标车道（ego被插入）：1.ego car——2.following car——3.preceding car
            总共包含六个参数：v3, delta_v32, delta_v21, delta_x32, delta_x21, delta_y21

    :param arguments: 储存危险场景的根目录、GAN样本库储存的根目录
    :return: None
    """
    scenario_path = []  # 存放csv文件位置
    scenario_name = []  # 场景名
    for filepath, dirnames, filenames in os.walk(scenario_rootpath):
        for filename in filenames:
            if '.csv' in filename:
                name = filename.split('.')[0]
                scenario_path.append(os.path.join(filepath, filename))
                scenario_name.append(name)
    for i, path in enumerate(scenario_path):
        id_list = df_to_list(path, 'id')
        ego_id = id_list[0]  # 主车id
        pre_list = df_to_list(path, 'precedingId')  # 前车
        follow_list = df_to_list(path, 'followingId')  # 后车
        v_list = df_to_list(path, 'xVelocity')  # 横向速度
        x_list = df_to_list(path, 'x')  # 横向坐标
        lane_list = df_to_list(path, 'laneId')  # 车道id
        sample_output_path = os.path.join(GANsample_rootpath, scenario_name[i]) + '_gan.csv'  # 输出文件位置
        if 'follow' in path:  # 跟驰场景
            ego_v = []
            pre_v = []
            delta_dis = []
            pre_id = pre_list[0]
            index_pre = [x for (x, m) in enumerate(id_list) if m == pre_id]  # ego前车对应的索引集合
            for index, id in enumerate(id_list):
                if id == ego_id:  # ego
                    ego_v.append(v_list[index])
                    pre_v.append(v_list[index_pre[index]])
                    delta_x = abs(x_list[index] - x_list[index_pre[index]])
                    delta_dis.append(delta_x)
            sample_list = [ego_v, pre_v, delta_dis]
            df_name = ['本车速度', '前车速度', '相对距离']
            sample_df = pd.DataFrame(columns=df_name, data=list(zip(*sample_list)))
            sample_df.to_csv(sample_output_path, index=False, encoding='gbk')
        else:  # 换道场景（ego危险cutin、ego被危险cutin）
            index_ego = [x for (x, m) in enumerate(id_list) if m == ego_id]
            ego_lane = lane_list[index_ego[0]:index_ego[-1]]  # 主车所在车道
            scenario_df = pd.read_csv(path)
            groups = scenario_df.groupby('id')
            if len(set(ego_lane)) == 2:  # ego危险cutin
                base1 = follow_list[index_ego[-1]]  # 换道场景中，三个基本要素中的目标车道上ego的上游跟驰车辆id(1号车)
                base3 = pre_list[index_ego[-1]]  # 换道场景中，三个基本要素中目标车道上ego的下游被跟驰车辆id(3号车)
                if base1 != 0 and base3 != 0:  # 去除掉场景内不足三辆车的情况
                    for group_id, rows in groups:
                        if group_id == ego_id:
                            base1_df = rows[
                                (rows['precedingId'] == base1) | (rows['followingId'] == base1)
                                | (rows['leftPrecedingId'] == base1) | (rows['leftAlongsideId'] == base1)
                                | (rows['leftFollowingId'] == base1) | (rows['rightPrecedingId'] == base1)
                                | (rows['rightAlongsideId'] == base1) | (rows['rightFollowingId'] == base1)]  # ego插入场景中，1号车在ego(2号车)中出现的所有帧
                            base3_df = rows[
                                (rows['precedingId'] == base3) | (rows['followingId'] == base3)
                                | (rows['leftPrecedingId'] == base3) | (rows['leftAlongsideId'] == base3)
                                | (rows['leftFollowingId'] == base3) | (rows['rightPrecedingId'] == base3)
                                | (rows['rightAlongsideId'] == base3) | (rows['rightFollowingId'] == base3)]
                    base1_frames = base1_df['frame'].values.tolist()  # 换道场景中，1号车对应的帧数列表
                    base3_frames = base3_df['frame'].values.tolist()
                    min_frame = max(min(base1_frames), min(base3_frames))
                    max_frame = min(max(base1_frames), max(base3_frames))
                    for group_id, rows in groups:
                        if group_id == ego_id:
                            data2_df = rows[['x', 'y', 'xVelocity']][(rows['frame'] <= max_frame) & (rows['frame'] >= min_frame)]
                        elif group_id == base1:
                            data1_df = rows[['x', 'y', 'xVelocity']][(rows['frame'] <= max_frame) & (rows['frame'] >= min_frame)]
                        elif group_id == base3:
                            data3_df = rows[['x', 'y', 'xVelocity']][(rows['frame'] <= max_frame) & (rows['frame'] >= min_frame)]
                    data1_df.reset_index(drop=True, inplace=True)  # dataframe根据条件筛选出的新df，其index依旧是原df，需要重置index
                    data2_df.reset_index(drop=True, inplace=True)
                    data3_df.reset_index(drop=True, inplace=True)
                    param_df = pd.DataFrame()
                    param_df['v3'] = data3_df['xVelocity']
                    param_df['delta_v32'] = data3_df['xVelocity'] - data2_df['xVelocity']  # 按照index对应计算，若对应不上则填充为空值NAN
                    param_df['delta_v21'] = data2_df['xVelocity'] - data1_df['xVelocity']
                    param_df['delta_x32'] = data3_df['x'] - data2_df['x']
                    param_df['delta_x21'] = data2_df['x'] - data1_df['x']
                    param_df['delta_y21'] = data2_df['y'] - data1_df['y']
                    param_df.to_csv(sample_output_path, index=False, encoding='gbk')
            else:  # ego被插入
                for group_id, rows in groups:
                    if group_id == ego_id:
                        pre_df = rows.drop_duplicates(subset='precedingId', keep='first', inplace=False)
                        pre_id = pre_df['precedingId'].values.tolist()
                        base2 = pre_id[-1]  # 插入的车辆id为ego最后跟驰的车辆
                        base3 = pre_id[-2]  # 被插入前ego跟驰的车辆id位次为倒数第二
                        base2_df = rows[
                            (rows['precedingId'] == base2) | (rows['followingId'] == base2)
                            | (rows['leftPrecedingId'] == base2) | (rows['leftAlongsideId'] == base2)
                            | (rows['leftFollowingId'] == base2) | (rows['rightPrecedingId'] == base2)
                            | (rows['rightAlongsideId'] == base2) | (rows['rightFollowingId'] == base2)]  # ego被插入场景中，2号车在ego(2号车)中出现的所有帧
                        base3_df = rows[
                            (rows['precedingId'] == base3) | (rows['followingId'] == base3)
                            | (rows['leftPrecedingId'] == base3) | (rows['leftAlongsideId'] == base3)
                            | (rows['leftFollowingId'] == base3) | (rows['rightPrecedingId'] == base3)
                            | (rows['rightAlongsideId'] == base3) | (rows['rightFollowingId'] == base3)]
                if base2 != 0 and base3 != 0:
                    base2_frames = base2_df['frame'].values.tolist()  # ego被插入场景中，2号车对应的帧数列表
                    base3_frames = base3_df['frame'].values.tolist()
                    min_frame = max(min(base2_frames), min(base3_frames))
                    max_frame = min(max(base2_frames), max(base3_frames))
                    for group_id, rows in groups:
                        if group_id == ego_id:
                            data1_df = rows[['x', 'y', 'xVelocity']][(rows['frame'] <= max_frame) & (rows['frame'] >= min_frame)]
                        elif group_id == base2:
                            data2_df = rows[['x', 'y', 'xVelocity']][(rows['frame'] <= max_frame) & (rows['frame'] >= min_frame)]
                        elif group_id == base3:
                            data3_df = rows[['x', 'y', 'xVelocity']][(rows['frame'] <= max_frame) & (rows['frame'] >= min_frame)]
                    data1_df.reset_index(drop=True, inplace=True)  # dataframe根据条件筛选出的新df，其index依旧是原df，需要重置index
                    data2_df.reset_index(drop=True, inplace=True)
                    data3_df.reset_index(drop=True, inplace=True)
                    param_df = pd.DataFrame()
                    param_df['v3'] = data3_df['xVelocity']
                    param_df['delta_v32'] = data3_df['xVelocity'] - data2_df['xVelocity']
                    param_df['delta_v21'] = data2_df['xVelocity'] - data1_df['xVelocity']
                    param_df['delta_x32'] = data3_df['x'] - data2_df['x']
                    param_df['delta_x21'] = data2_df['x'] - data1_df['x']
                    param_df['delta_y21'] = data2_df['y'] - data1_df['y']
                    param_df.to_csv(sample_output_path, index=False, encoding='gbk')
    return
