import os
import pywt
import numpy as np
import pandas as pd
from tqdm import tqdm
from gekko import GEKKO
import matplotlib.pyplot as plt

# TODO Q1:基于速度的位置等指标计算是否存在问题，代码中不包含
# TODO Q2:为何将vehicle_id为1的车辆提取出来作为cut_in车辆, 还是说是使用的data_procession中讲全部车辆的轨迹对都进行了处理之后，再进行的GAN_sample
# TODO Q3:论文里写小波滤波的最大分解层数是4，我看代码里最大分解层数的确定是通过数据的长度，与db6的滤波器长度（消失炬为6）通过公式：[log2(data_len/(filter_len-1))],小波滤波器的长度（支撑长度）为2*n-1


def plot_outlier_adjacent_trj(series_in, outlier_pos_in, first_pos_in, last_pos_in, segment_id_in, veh_id_in, start_time_in, comparison_label, flag):
    """绘制一段时间窗口内，轨迹的累计位移，速度，加速度曲线"""
    # plot the adjacent trajectory of the outlier (20 points)
    correctness_dir = ['_x', '_y']
    outlier_time = round(start_time_in + outlier_pos_in * 0.04, 2)  # 离群点时间
    included_index = np.arange(first_pos_in, last_pos_in + 1, dtype=int)  # 时间窗口索引范围
    outlier_trj = series_in.loc[included_index, :]  # 把时间窗口中的部分提取出来
    outlier_trj.loc[:, 'local_time'] = np.array(included_index) * 0.04 + start_time_in  # 增加时间列
    plt.subplot(3, 1, 1)  # 第一幅子图累计位移
    plt.plot(outlier_trj['local_time'], outlier_trj[('cumu_dis' + correctness_dir[flag])], '-*k', linewidth=0.25, label='Original', markersize=1.5)
    if comparison_label == 1:
        plt.plot(outlier_trj['local_time'], outlier_trj[('remove_outlier_cumu_dis' + correctness_dir[flag])], '-m', linewidth=0.25, label='Outliers Removed')
        plt.legend(prop={'size': 6})
        trj_title = 'Scenario ' + str(int(segment_id_in)) + ' Vehicle' + str(
            int(veh_id_in)) + ' Direction' + correctness_dir[flag] + ' Outlier at Time ' + str(outlier_time) + ' Removing'
    else:
        trj_title = 'Scenario ' + str(int(segment_id_in)) + ' Vehicle' + str(
            int(veh_id_in)) + ' Direction' + correctness_dir[flag] + ' Outlier at Time ' + str(outlier_time) + ' Pattern'
    plt.ylabel('Position (m)')  # 纵坐标为横向位移
    plt.title(trj_title)  # 轨迹标题
    plt.subplot(3, 1, 2)  # 第二幅子图速度
    plt.plot(outlier_trj['local_time'], outlier_trj[('speed' + correctness_dir[flag])], '-*k', linewidth=0.5, label='Original', markersize=1.5)
    if comparison_label == 1:
        plt.plot(outlier_trj['local_time'], outlier_trj[('remove_outlier_speed' + correctness_dir[flag])], '-m', linewidth=0.5, label='Outliers Removed')
        plt.legend(prop={'size': 6})
    plt.ylabel('Speed (m/s)')
    if not flag:
        plt.ylim([0, 50])
    else:
        plt.ylim([-10, 10])
    plt.subplot(3, 1, 3)  # 第三幅子图加速度
    plt.plot(outlier_trj['local_time'], outlier_trj[('accer' + correctness_dir[flag])], '-*k', linewidth=0.5, label='Original', markersize=1.5)
    if comparison_label == 1:
        plt.plot(outlier_trj['local_time'], outlier_trj[('remove_outlier_accer' + correctness_dir[flag])], '-m', linewidth=0.5, label='Outliers Removed')
        plt.legend(prop={'size': 6})
    plt.xlabel('Time (s)')
    plt.ylabel('Acceleration (m/s2)')
    if not flag:
        plt.ylim([-15, 15])
    else:
        plt.ylim([-3, 3])
    if not os.path.exists('figure_save/trajectory_process/outlier_pattern_and_removing'):
        os.makedirs('figure_save/trajectory_process/outlier_pattern_and_removing')
    trj_save_title = 'figure_save/trajectory_process/outlier_pattern_and_removing/' + trj_title + '.png'
    plt.savefig(trj_save_title, dpi=600)
    plt.close('all')  # test


def before_and_after_remove_outlier_plot(trj_in):
    """绘制去除离群点前后，横纵向轨迹的对比图"""
    current_seg_id = trj_in['segment_id'].iloc[0]
    follower_id_in = trj_in['local_veh_id'].iloc[0]
    correctness_dir = ['_x', '_y']
    for i in range(2):
        plt.subplot(3, 1, 1)
        plt.plot(trj_in['local_time'], trj_in['position' + correctness_dir[i]], '--k', linewidth=0.25, label='Original')
        plt.plot(trj_in['local_time'], trj_in['remove_outlier_pos' + correctness_dir[i]], '-m', linewidth=0.25, label='Outliers Removed')
        plt.ylabel('Position (m)')
        plt.legend(prop={'size': 6})
        trj_title = 'Scenario ' + str(int(current_seg_id)) + ' Vehicle' + str(
            int(follower_id_in)) + ' Direction' + correctness_dir[i] + ' Before and After Removing Outliers'
        plt.title(trj_title)
        plt.subplot(3, 1, 2)
        plt.plot(trj_in['local_time'], trj_in['speed' + correctness_dir[i]], '--k', linewidth=0.5, label='Original')
        plt.plot(trj_in['local_time'], trj_in['remove_outlier_speed' + correctness_dir[i]], '-m', linewidth=0.5, label='Outliers Removed')
        plt.ylabel('Speed (m/s)')
        plt.legend(prop={'size': 6})
        if not i:
            plt.ylim([0, 50])
        else:
            plt.ylim([-10, 10])
        plt.subplot(3, 1, 3)
        plt.plot(trj_in['local_time'], trj_in['accer' + correctness_dir[i]], '--k', linewidth=0.5, label='Original')
        plt.plot(trj_in['local_time'], trj_in['remove_outlier_accer' + correctness_dir[i]], '-m', linewidth=0.5, label='Outliers Removed')
        plt.legend(prop={'size': 6})
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (m/s2)')
        if not i:
            plt.ylim([-15, 15])
        else:
            plt.ylim([-5, 5])
        if not os.path.exists('figure_save/trajectory_process/before_and_after_remove_outlier_plot'):
            os.makedirs('figure_save/trajectory_process/before_and_after_remove_outlier_plot')
        trj_save_title = 'figure_save/trajectory_process/before_and_after_remove_outlier_plot/' + trj_title + '.png'
        plt.savefig(trj_save_title, dpi=600)
        plt.close('all')


def before_and_after_filtering_plot(trj_in):
    """绘制原始轨迹、去除离群点轨迹以及去噪后的轨迹对比图"""
    current_seg_id = trj_in['segment_id'].iloc[0]
    follower_id_in = trj_in['local_veh_id'].iloc[0]
    correctness_dir = ['_x', '_y']
    for i in range(2):
        plt.subplot(3, 1, 1)
        plt.plot(trj_in['local_time'], trj_in['position' + correctness_dir[i]], '--k', linewidth=0.25, label='Original')
        plt.plot(trj_in['local_time'], trj_in['remove_outlier_pos' + correctness_dir[i]], '-m', linewidth=0.25, label='Outliers Removed')
        plt.plot(trj_in['local_time'], trj_in['filter_pos' + correctness_dir[i]], '-*g', linewidth=0.25, label='Outliers Removed + Filtering', markersize=0.5)
        plt.ylabel('Position (m)')
        plt.legend(prop={'size': 6})
        trj_title = 'Scenario ' + str(int(current_seg_id)) + ' Vehicle' + str(
            int(follower_id_in)) + ' Direction' + correctness_dir[i] + ' Before and After Filtering'
        plt.title(trj_title)
        plt.subplot(3, 1, 2)
        plt.plot(trj_in['local_time'], trj_in['speed' + correctness_dir[i]], '--k', linewidth=0.25, label='Original')
        plt.plot(trj_in['local_time'], trj_in['remove_outlier_speed' + correctness_dir[i]], '-m', linewidth=0.25, label='Outliers Removed')
        plt.plot(trj_in['local_time'], trj_in['filter_speed' + correctness_dir[i]], '-*g', linewidth=0.25, label='Outliers Removed + Filtering', markersize=0.5)
        plt.ylabel('Speed (m/s)')
        plt.legend(prop={'size': 6})
        if not i:
            plt.ylim([0, 50])
        else:
            plt.ylim([-10, 10])
        plt.subplot(3, 1, 3)
        plt.plot(trj_in['local_time'], trj_in['accer' + correctness_dir[i]], '--k', linewidth=0.25, label='Original')
        plt.plot(trj_in['local_time'], trj_in['remove_outlier_accer' + correctness_dir[i]], '-m', linewidth=0.25, label='Outliers Removed')
        plt.plot(trj_in['local_time'], trj_in['filter_accer' + correctness_dir[i]], '-*g', linewidth=0.25, label='Outliers Removed + Filtering', markersize=0.5)
        plt.legend(prop={'size': 6})
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (m/s2)')
        if not i:
            plt.ylim([-15, 15])
        else:
            plt.ylim([-5, 5])
        if not os.path.exists('figure_save/trajectory_process/before_and_after_filtering_plot'):
            os.makedirs('figure_save/trajectory_process/before_and_after_filtering_plot')
        trj_save_title = 'figure_save/trajectory_process/before_and_after_filtering_plot/' + trj_title + '.png'
        plt.savefig(trj_save_title, dpi=600)
        plt.close('all')


def cf_paired_trj_plot(leader_trj_in, follower_trj_in, av_label):
    """
    此函数用于绘制两辆车的轨迹（位置、速度、加速度）图像
    """
    # av_label is to determine whether av is leader or follower (0 for follower, 1 for leader, 2 for non-av)
    # the format of the trajectory is pandas dataframe
    # for av_label: 0 means AV-HV, 1 means HV-AV, 2 means HV-HV
    current_segment_id = int(leader_trj_in['segment_id'].iloc[0])  # 场景号
    current_leader_id = int(leader_trj_in['local_veh_id'].iloc[0])  # 主车id
    current_follower_id = int(follower_trj_in['local_veh_id'].iloc[0])  # 前车id
    if av_label == 0:
        follower_line = '-r'  # 主车轨迹设置为红色
        leader_line = '--b'  # 对手车轨迹设置为蓝色
        follower_label = 'Cutin Challenger ' + str(current_follower_id)
        leader_label = 'Ego ' + str(current_leader_id)
        # trj_title = 'Cutin Scenario ' + str(current_segment_id)
        # trj_save_title = 'figure_save/trajectory_process/position_time_plot/' + 'Segment_' + str(
        #     current_segment_id) + '_' + trj_title + '_position_time_plot.png'
    else:
        follower_line = '-b'
        leader_line = '--b'
        follower_label = 'HV Follower'
        leader_label = 'HV Leader'
        trj_title = 'HV' + str(current_follower_id) + '-HV' + str(current_leader_id)
        if not os.path.exists('figure_save/trajectory_process/position_time_plot'):
            os.makedirs('figure_save/trajectory_process/position_time_plot')
        trj_save_title = 'figure_save/trajectory_process/position_time_plot/' + 'Segment_' + str(
            current_segment_id) + '_' + trj_title + '_position_time_plot.png'
    correctness_dir = ['_x', '_y']
    for i in range(2):
        plt.subplot(3, 1, 1)
        plt.plot(follower_trj_in['local_time'], follower_trj_in['filter_pos' + correctness_dir[i]], follower_line, linewidth=0.5, label=follower_label)
        plt.plot(leader_trj_in['local_time'], leader_trj_in['filter_pos' + correctness_dir[i]], leader_line, linewidth=0.5, label=leader_label)
        plt.ylabel('Position (m)')
        plt.legend(prop={'size': 6})
        trj_title = 'Cutin Scenario ' + str(current_segment_id) + ' Direction' + correctness_dir[i]
        trj_save_title = 'figure_save/trajectory_process/position_time_plot/' + trj_title + '_position_time_plot.png'
        plt.title(trj_title)
        plt.subplot(3, 1, 2)
        plt.plot(follower_trj_in['local_time'], follower_trj_in['filter_speed' + correctness_dir[i]], follower_line, linewidth=0.5, label=follower_label)
        plt.plot(leader_trj_in['local_time'], leader_trj_in['filter_speed' + correctness_dir[i]], leader_line, linewidth=0.5, label=leader_label)
        plt.ylabel('Speed (m/s)')
        plt.legend(prop={'size': 6})
        if not i:
            plt.ylim([0, 50])
        else:
            plt.ylim([-10, 10])
        plt.subplot(3, 1, 3)
        plt.plot(follower_trj_in['local_time'], follower_trj_in['filter_accer' + correctness_dir[i]], follower_line, linewidth=0.5, label=follower_label)
        plt.plot(leader_trj_in['local_time'], leader_trj_in['filter_accer' + correctness_dir[i]], leader_line, linewidth=0.5, label=leader_label)
        plt.legend(prop={'size': 6})
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (m/s2)')
        if not i:
            plt.ylim([-8, 5])
        else:
            plt.ylim([-5, 5])
        plt.savefig(trj_save_title, dpi=600)
        plt.close('all')


def update_speed_and_accer(series_in, filter_label):
    '''基于位置信息差分得到速度、加速度及加加速度信息'''
    # this function calculate the speed, accelearation, jerk based on position
    # series_in is the same format as  coord_series_in
    # output is series_in with updated speed and accer

    # 输出模式（对应的表头）——0:原始位置信息差分；1:滤波后的位置信息差分；2:离群点剔除后的位置信息差分
    if filter_label == 1:
        current_cumu_dis_x = 'filter_cumu_dis_x'
        current_speed_x = 'filter_speed_x'
        current_accer_x = 'filter_accer_x'
        current_cumu_dis_y = 'filter_cumu_dis_y'
        current_speed_y = 'filter_speed_y'
        current_accer_y = 'filter_accer_y'
    elif filter_label == 0:
        current_cumu_dis_x = 'cumu_dis_x'
        current_speed_x = 'speed_x'
        current_accer_x = 'accer_x'
        current_jerk_x = 'jerk_x'
        current_cumu_dis_y = 'cumu_dis_y'
        current_speed_y = 'speed_y'
        current_accer_y = 'accer_y'
        current_jerk_y = 'jerk_y'
    elif filter_label == 2:
        current_cumu_dis_x = 'remove_outlier_cumu_dis_x'
        current_speed_x = 'remove_outlier_speed_x'
        current_accer_x = 'remove_outlier_accer_x'
        current_jerk_x = 'remove_outlier_jerk_x'
        current_cumu_dis_y = 'remove_outlier_cumu_dis_y'
        current_speed_y = 'remove_outlier_speed_y'
        current_accer_y = 'remove_outlier_accer_y'
        current_jerk_y = 'remove_outlier_jerk_y'

    # 差分计算速度（由前后两个点差分得到——中心差分）
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_speed_x] = float(
                series_in.at[i + 2, current_cumu_dis_x] - series_in.at[i, current_cumu_dis_x]) / (float(0.08))
            series_in.at[i, current_speed_y] = float(
                series_in.at[i + 2, current_cumu_dis_y] - series_in.at[i, current_cumu_dis_y]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_speed_x] = float(
                series_in.at[i, current_cumu_dis_x] - series_in.at[i - 2, current_cumu_dis_x]) / (float(0.08))
            series_in.at[i, current_speed_y] = float(
                series_in.at[i, current_cumu_dis_y] - series_in.at[i - 2, current_cumu_dis_y]) / (float(0.08))
        else:
            series_in.at[i, current_speed_x] = float(
                series_in.at[i + 1, current_cumu_dis_x] - series_in.at[i - 1, current_cumu_dis_x]) / (float(0.08))
            series_in.at[i, current_speed_y] = float(
                series_in.at[i + 1, current_cumu_dis_y] - series_in.at[i - 1, current_cumu_dis_y]) / (float(0.08))

    # 差分计算加速度（由前后两个点差分得到）
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_accer_x] = float(
                series_in.at[i + 2, current_speed_x] - series_in.at[i, current_speed_x]) / (float(0.08))
            series_in.at[i, current_accer_y] = float(
                series_in.at[i + 2, current_speed_y] - series_in.at[i, current_speed_y]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_accer_x] = float(
                series_in.at[i, current_speed_x] - series_in.at[i - 2, current_speed_x]) / (float(0.08))
            series_in.at[i, current_accer_y] = float(
                series_in.at[i, current_speed_y] - series_in.at[i - 2, current_speed_y]) / (float(0.08))
        else:
            series_in.at[i, current_accer_x] = float(
                series_in.at[i + 1, current_speed_x] - series_in.at[i - 1, current_speed_x]) / (float(0.08))
            series_in.at[i, current_accer_y] = float(
                series_in.at[i + 1, current_speed_y] - series_in.at[i - 1, current_speed_y]) / (float(0.08))

    # 差分计算加加速度（由前后两个点差分得到）
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_jerk_x] = float(
                series_in.at[i + 2, current_accer_x] - series_in.at[i, current_accer_x]) / (float(0.08))
            series_in.at[i, current_jerk_y] = float(
                series_in.at[i + 2, current_accer_y] - series_in.at[i, current_accer_y]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_jerk_x] = float(
                series_in.at[i, current_accer_x] - series_in.at[i - 2, current_accer_x]) / (float(0.08))
            series_in.at[i, current_jerk_y] = float(
                series_in.at[i, current_accer_y] - series_in.at[i - 2, current_accer_y]) / (float(0.08))
        else:
            series_in.at[i, current_jerk_x] = float(
                series_in.at[i + 1, current_accer_x] - series_in.at[i - 1, current_accer_x]) / (float(0.08))
            series_in.at[i, current_jerk_y] = float(
                series_in.at[i + 1, current_accer_y] - series_in.at[i - 1, current_accer_y]) / (float(0.08))
    return series_in


def speed_based_update_distance_and_accer(series_in):
    '''基于速度数据积分得到位置，差分得到加速度与加加速度'''
    # this function calculate the distance, acceleration and jerk based on speed (for speed-based data)
    # series_in is the same format as  coord_series_in
    # output is series_in with updated speed and accer

    # 表头标签
    current_cumu_dis_x = 'speed_based_cumu_dis_x'
    current_speed_x = 'speed_based_speed_x'
    current_accer_x = 'speed_based_accer_x'
    current_jerk_x = 'speed_based_jerk_x'
    current_cumu_dis_y = 'speed_based_cumu_dis_y'
    current_speed_y = 'speed_based_speed_y'
    current_accer_y = 'speed_based_accer_y'
    current_jerk_y = 'speed_based_jerk_y'

    # 积分得到车辆的累计位移（弹道方案——加速度恒定），一帧的位移为首尾速度围成的梯形面积
    for i in range(1, len(series_in['global_center_x'])):
        if i == 1:
            series_in.loc[0, current_cumu_dis_x] = 0
            series_in.loc[i, current_cumu_dis_x] = series_in.loc[i - 1, current_cumu_dis_x] + (
                series_in.loc[i, current_speed_x] + series_in.loc[i - 1, current_speed_x]) * 0.5 * 0.04
            series_in.loc[0, current_cumu_dis_y] = 0
            series_in.loc[i, current_cumu_dis_y] = series_in.loc[i - 1, current_cumu_dis_y] + (
                series_in.loc[i, current_speed_y] + series_in.loc[i - 1, current_speed_y]) * 0.5 * 0.04
        else:
            series_in.loc[i, current_cumu_dis_x] = series_in.loc[i - 1, current_cumu_dis_x] + (
                series_in.loc[i, current_speed_x] + series_in.loc[i - 1, current_speed_x]) * 0.5 * 0.04
            series_in.loc[i, current_cumu_dis_y] = series_in.loc[i - 1, current_cumu_dis_y] + (
                series_in.loc[i, current_speed_y] + series_in.loc[i - 1, current_speed_y]) * 0.5 * 0.04

    # 差分得到车辆加速度（前后两个点差分）
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_accer_x] = float(
                series_in.at[i + 2, current_speed_x] - series_in.at[i, current_speed_x]) / (float(0.08))
            series_in.at[i, current_accer_y] = float(
                series_in.at[i + 2, current_speed_y] - series_in.at[i, current_speed_y]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_accer_x] = float(
                series_in.at[i, current_speed_x] - series_in.at[i - 2, current_speed_x]) / (float(0.08))
            series_in.at[i, current_accer_y] = float(
                series_in.at[i, current_speed_y] - series_in.at[i - 2, current_speed_y]) / (float(0.08))
        else:
            series_in.at[i, current_accer_x] = float(
                series_in.at[i + 1, current_speed_x] - series_in.at[i - 1, current_speed_x]) / (float(0.08))
            series_in.at[i, current_accer_y] = float(
                series_in.at[i + 1, current_speed_y] - series_in.at[i - 1, current_speed_y]) / (float(0.08))

    # 差分得到车辆加加速度（前后两个点差分）
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_jerk_x] = float(
                series_in.at[i + 2, current_accer_x] - series_in.at[i, current_accer_x]) / (float(0.08))
            series_in.at[i, current_jerk_y] = float(
                series_in.at[i + 2, current_accer_y] - series_in.at[i, current_accer_y]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_jerk_x] = float(
                series_in.at[i, current_accer_x] - series_in.at[i - 2, current_accer_x]) / (float(0.08))
            series_in.at[i, current_jerk_y] = float(
                series_in.at[i, current_accer_y] - series_in.at[i - 2, current_accer_y]) / (float(0.08))
        else:
            series_in.at[i, current_jerk_x] = float(
                series_in.at[i + 1, current_accer_x] - series_in.at[i - 1, current_accer_x]) / (float(0.08))
            series_in.at[i, current_jerk_y] = float(
                series_in.at[i + 1, current_accer_y] - series_in.at[i - 1, current_accer_y]) / (float(0.08))
    return series_in


def outlier_removing_optimization_model(initial_state_in, last_state_in, num_points_in):
    '''syh:针对离群点剔除的非线性规划模型
       zwt:以某一时间窗口内的边界位置、速度、加速度为约束
           中间的位置、速度、加速度为变量，通过动力学约束建立联系
           目标函数为：最大加速度与最小加速度的差值最小'''
    # 传入轨迹相关定义，其中对于插值，仅针对于除首尾轨迹之外的其他轨迹点
    max_acc = 5
    min_acc = -8
    total_steps = num_points_in
    first_pos_in = initial_state_in[0]
    first_speed_in = initial_state_in[1]
    first_acc_in = initial_state_in[2]
    last_pos_in = last_state_in[0]
    last_speed_in = last_state_in[1]
    last_acc_in = last_state_in[2]

    # 传入轨迹的时间颗粒度（采样率倒数）
    time_interval = 0.04

    # ##### TODO: 构建优化模型 ######
    '''初始化模型'''
    model = GEKKO(remote=False)
    # ## 使用IPOPT（非线性优化求解器）
    model.options.SOLVER = 3  # 选择IPOPT求解器
    model.options.SCALING = 2  # 针对每个变量单独设置缩放比例（使起始值为1，保证模型收敛性）
    model.options.MAX_MEMORY = 5  # 求解过程中方程的稀疏元素上限为10^5（不够会报错，然后修改该参数直至不报错）
    # model.options.IMODE = 2  # Steady state optimization
    '''初始化模型变量（每帧下的位置、速度、加速度单独定义变量，通过动力学约束建立联系）'''
    acc = [None] * total_steps  # simulated acceleration
    velocity = [None] * total_steps  # simulated velocity
    pos = [None] * total_steps  # simulated position
    for i in range(total_steps):
        pos[i] = model.Var()
        velocity[i] = model.Var()
        velocity[i].lower = 0
        acc[i] = model.Var(lb=min_acc, ub=max_acc)
    min_sim_acc = model.Var()  # 辅助变量，用于构造目标函数
    max_sim_acc = model.Var()
    '''构建模型约束'''
    # 时间窗边界状态需与输入状态一致
    model.Equation(pos[0] == first_pos_in)
    model.Equation(velocity[0] == first_speed_in)
    model.Equation(acc[0] == first_acc_in)
    model.Equation(pos[total_steps - 1] == last_pos_in)
    model.Equation(velocity[total_steps - 1] == last_speed_in)
    model.Equation(acc[total_steps - 1] == last_acc_in)
    # 时间窗中间状态基于动力学更新（弹道方案，假设相邻帧之间加速度恒定）
    # v:0, 1固定；2变化
    # pos:0, 1固定；2变化，
    # a:0固定；1变化
    for i in range(total_steps):
        if 1 <= i <= total_steps - 1:
            model.Equation(velocity[i] == velocity[i - 1] + acc[i - 1] * time_interval)  # 约束：下一帧的速度要等于上一帧速度+上一帧的a*t
            model.Equation(pos[i] == pos[i - 1] + 0.5 * (velocity[i] + velocity[i - 1]) * time_interval)  # 约束：下一帧的位置要等于上一帧的位置+梯形面积
    # 辅助变量需覆盖加速度曲线
    for i in range(total_steps):
        model.Equation(min_sim_acc <= acc[i])  # 加速度最小值
        model.Equation(max_sim_acc >= acc[i])  # 加速度最大值
    '''构建目标函数（默认最小化）——最小化窗口内的加速度极差'''
    model.Obj(max_sim_acc - min_sim_acc)
    '''求解模型'''
    try:
        model.solve(disp=False)
    except Exception:
        return False
    # solve_time = model.options.SOLVETIME
    # extract values from Gekko type variables
    '''导出求解结果'''
    acc_value = np.zeros(total_steps)
    velocity_value = np.zeros(total_steps)
    pos_value = np.zeros(total_steps)
    for i in range(total_steps):
        acc_value[i] = acc[i].value[0]
        velocity_value[i] = velocity[i].value[0]
        pos_value[i] = pos[i].value[0]
    return pos_value, velocity_value, acc_value


def optimization_based_outlier_removing(series_in, first_pos_in, last_pos_in, min_acc_in, max_acc_in, flag):
    '''syh:基于优化模型的离群点剔除——在加速度曲线上识别，速度曲线上优化
       zwt:基于优化模型的离群点剔除——在加速度曲线上识别，在累计位置曲线上优化，随后利用差分得到速度、加速度、jerk
    '''
    # 确定修正方向
    if flag == 0:
        series_status = ['remove_outlier_cumu_dis_x', 'remove_outlier_speed_x', 'remove_outlier_accer_x']
    else:
        series_status = ['remove_outlier_cumu_dis_y', 'remove_outlier_speed_y', 'remove_outlier_accer_y']
    # 待优化轨迹的窗口边界状态
    first_point_pos = first_pos_in  # 窗口开始索引
    last_point_pos = last_pos_in  # 窗口结束索引
    first_point_cumu_dis = series_in.at[first_point_pos, series_status[0]]  # 窗口开始处的累计位移
    first_point_speed = series_in.at[first_point_pos, series_status[1]]  # 窗口开始处的速度

    # 限定窗口边界符合加速度约束
    if series_in.at[first_point_pos, series_status[2]] <= min_acc_in:
        first_point_acc = min_acc_in  # 低于下界用下界修正
    elif series_in.at[first_point_pos, series_status[2]] >= max_acc_in:
        first_point_acc = max_acc_in  # 高于上界用上界修正
    else:
        first_point_acc = series_in.at[first_point_pos, series_status[2]]
    first_point_state = [first_point_cumu_dis, first_point_speed, first_point_acc]
    last_point_cumu_dis = series_in.at[last_point_pos, series_status[0]]  # 窗口结束处的累计位移
    last_point_speed = series_in.at[last_point_pos, series_status[1]]  # 窗口结束处的速度
    if series_in.at[last_point_pos, series_status[2]] <= min_acc_in:
        last_point_acc = min_acc_in
    elif series_in.at[last_point_pos, series_status[2]] >= max_acc_in:
        last_point_acc = max_acc_in
    else:
        last_point_acc = series_in.at[last_point_pos, series_status[2]]
    last_point_state = [last_point_cumu_dis, last_point_speed, last_point_acc]

    # 得到窗口长度，执行优化模型
    actual_total_related_points = last_point_pos - first_point_pos + 1
    if outlier_removing_optimization_model(first_point_state, last_point_state, actual_total_related_points):
        pos_result, speed_result, acc_result = outlier_removing_optimization_model(first_point_state, last_point_state, actual_total_related_points)
    else:
        return pd.DataFrame()
    series_in.loc[first_point_pos:last_point_pos, series_status[0]] = pos_result
    # 完成x向及y向的轨迹修正后，统一进行position_based数据的反推
    series_in = update_speed_and_accer(series_in, 2)
    return series_in


def wavefilter(data):
    '''syh:小波变换——多贝西6，高频分量全部置零
       zwt:使用小波变换去除一维数据的噪声
    '''
    # We will use the Daubechies(6) wavelet
    daubechies_num = 6
    wname = "db" + str(daubechies_num)  # 使用db6作为小波基
    datalength = data.shape[0]
    wavelet = pywt.Wavelet(wname)
    max_level = pywt.dwt_max_level(datalength, wavelet.dec_len)  # 计算最大有用分解级别
    # print('maximun level is: %s' % max_level)
    # Initialize the container for the filtered data
    # Decompose the signal
    # coeff[0] is approximation coeffs, coeffs[1] is nth level detail coeff, coeff[-1] is first level detail coeffs
    # pywt.wavedec包含四个输入分别为：数据、小波基、分离模式和进行多少层分解
    # 输出为小波系数，第一个值为approximation coeffs， 后面分别为每一层的detail(高频成分)
    # 具体参考：https://zhuanlan.zhihu.com/p/157540476中的树状图，阈值选择其实就是对detail系数做处理，最后重构得到去噪后的信号
    coeffs = pywt.wavedec(data, wname, mode='smooth', level=max_level)
    # thresholding
    for j in range(max_level):
        coeffs[-j - 1] = np.zeros_like(coeffs[-j - 1])  # 将高频信号的系数置为0，只保留A一组系数
    # Reconstruct the signal and save it
    filter_data = pywt.waverec(coeffs, wname, mode='smooth')
    fdata = filter_data[0:datalength]
    return fdata


def wavelet_filter(series_in, flag):
    '''基于小波变换的去噪——对完成离群点剔除的序列进行滤波'''
    filter_status = ['wavelet_filter_speed', 'wavelet_filter_cumu_dis', 'wavelet_filter_accer', 'wavelet_filter_jerk']
    # 确定滤波方向(x/y)
    if flag == 0:
        # TODO: 对完成离群点剔除的速度序列（position_based）进行滤波
        remove_outlier_speed_signal = series_in.loc[:, 'remove_outlier_speed_x'].to_numpy()
        # filter_status = ['wavelet_filter_speed_x', 'wavelet_filter_cumu_dis_x', 'wavelet_filter_accer_x', 'wavelet_filter_jerk_x']
    else:
        # TODO: 对完成离群点剔除的速度序列（position_based）进行滤波
        remove_outlier_speed_signal = series_in.loc[:, 'remove_outlier_speed_y'].to_numpy()
        # filter_status = ['wavelet_filter_speed_y', 'wavelet_filter_cumu_dis_y', 'wavelet_filter_accer_y', 'wavelet_filter_jerk_y']
    wavelet_filter_speed = wavefilter(remove_outlier_speed_signal)  # 基于小波变换去除一维噪声

    # TODO: 基于完成滤波的速度，更新累计位移、加速度、加加速度
    series_in.loc[:, filter_status[0]] = wavelet_filter_speed
    series_in.loc[:, filter_status[1]] = None
    series_in.loc[:, filter_status[2]] = None
    series_in.loc[:, filter_status[3]] = None
    # 累计位移
    for i in range(len(series_in['global_center_x'])):
        if i == 0:
            # start from the filtered value
            series_in.loc[i, filter_status[1]] = 0  # initial pos should be 0
        else:
            series_in.loc[i, filter_status[1]] = series_in.loc[i - 1, filter_status[1]] + (
                series_in.loc[i - 1, filter_status[0]] + series_in.loc[i, filter_status[0]]) * 0.5 * 0.04
    # 加速度
    current_speed = filter_status[0]
    current_accer = filter_status[2]
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_accer] = float(
                series_in.at[i + 2, current_speed] - series_in.at[i, current_speed]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_accer] = float(
                series_in.at[i, current_speed] - series_in.at[i - 2, current_speed]) / (float(0.08))
        else:
            series_in.at[i, current_accer] = float(
                series_in.at[i + 1, current_speed] - series_in.at[i - 1, current_speed]) / (float(0.08))
    # 加加速度
    current_jerk = filter_status[3]
    for i in range(0, len(series_in['global_center_x'])):
        if i == 0:
            series_in.at[i, current_jerk] = float(
                series_in.at[i + 2, current_accer] - series_in.at[i, current_accer]) / (float(0.08))
        elif i == len(series_in['global_center_x']) - 1:
            series_in.at[i, current_jerk] = float(
                series_in.at[i, current_accer] - series_in.at[i - 2, current_accer]) / (float(0.08))
        else:
            series_in.at[i, current_jerk] = float(
                series_in.at[i + 1, current_accer] - series_in.at[i - 1, current_accer]) / (float(0.08))
    return series_in


def trajectory_correctness(coord_series_in, segment_id_in, veh_id_in, start_time_in, all_outlier_record):
    '''基于一维化的数据，完成轨迹增强，涉及到xy两个方向轨迹的分别增强'''
    # this function remove outliers and filter the trajectory
    # input coord_series_in: ['global_center_x', 'global_center_y', 'cumu_dis', 'speed', 'accer']
    # output coord_series_in: ['global_center_x', 'global_center_y', 'cumu_dis', 'speed', 'accer', 'filter_cumu_dis', 'filter_speed', 'filter_accer']

    # 离群点剔除的相关参数（加速度边界、平滑窗口长度）
    minimum_accer = -8
    maximum_accer = 5
    total_related_points = 50  # 滑动窗口长度，离群点前后各50帧
    coord_series_in.reset_index(inplace=True, drop=True)
    # global all_outlier_record

    # remove outliers in acceleration, note that cubic spline interpolation is implemented on distance
    # 初始化离群点剔除——赋初值
    coord_series_in.loc[:, 'remove_outlier_cumu_dis_x'] = coord_series_in.loc[:, 'cumu_dis_x']
    coord_series_in.loc[:, 'remove_outlier_speed_x'] = coord_series_in.loc[:, 'speed_x']
    coord_series_in.loc[:, 'remove_outlier_accer_x'] = coord_series_in.loc[:, 'accer_x']
    coord_series_in.loc[:, 'remove_outlier_cumu_dis_y'] = coord_series_in.loc[:, 'cumu_dis_y']
    coord_series_in.loc[:, 'remove_outlier_speed_y'] = coord_series_in.loc[:, 'speed_y']
    coord_series_in.loc[:, 'remove_outlier_accer_y'] = coord_series_in.loc[:, 'accer_y']

    # 轨迹优化方向（x向/y向）
    correctness_dir = ['remove_outlier_accer_x', 'remove_outlier_accer_y']

    # 多次执行离群点剔除动作，直至整条轨迹没有离群点
    for flag in range(2):  # flag用于标识此时修正的方向(0 for x, 1 for y)
        outlier_label = 1
        while outlier_label:
            outlier_label = 0
            for m in range(len(coord_series_in['global_center_x'])):
                # 基于边界识别离群点
                if coord_series_in.at[m, correctness_dir[flag]] >= maximum_accer or coord_series_in.at[m, correctness_dir[flag]] <= minimum_accer:
                    '''
                    print('Outlier info: Current segment: %s, vehicle id: %s, time: %s, position: %s' % (
                        segment_id_in, veh_id_in, round(m * 0.04 + start_time_in, 1), m))
                    '''
                    # 记录离群点信息
                    single_outlier_record = pd.DataFrame(np.zeros((1, 3)), columns=['segment_id', 'local_veh_id', 'outlier_time'])
                    single_outlier_record.loc[0, 'segment_id'] = segment_id_in
                    single_outlier_record.loc[0, 'local_veh_id'] = veh_id_in
                    single_outlier_record.loc[0, 'outlier_time'] = start_time_in + 0.04 * m
                    all_outlier_record = all_outlier_record.append(single_outlier_record)  # 列表中的元素为dataframe
                    # 确定平滑窗口边界（超过轨迹首尾的，截至首尾）
                    first_point_pos = int(max(0, m - total_related_points / 2))  # 首端
                    last_point_pos = int(min(len(coord_series_in.loc[:, correctness_dir[flag]]) - 1, m + total_related_points / 2))  # 尾端
                    if first_point_pos == 0:
                        last_point_pos = first_point_pos + total_related_points  # 前半部分不够，通过后半部分补全
                    if last_point_pos == len(coord_series_in.loc[:, correctness_dir[flag]]) - 1:
                        first_point_pos = last_point_pos - total_related_points  # 后半部分不够，通过前半部分补全
                    # 绘制剔除离群点之前的轨迹
                    plot_outlier_adjacent_trj(coord_series_in, m, first_point_pos, last_point_pos, segment_id_in, veh_id_in, start_time_in, 0, flag)
                    # 执行基于优化模型的离群点剔除
                    coord_series_in = optimization_based_outlier_removing(coord_series_in, first_point_pos, last_point_pos, minimum_accer,
                                                                          maximum_accer, flag)
                    if coord_series_in.empty:
                        return pd.DataFrame()
                    # 绘制剔除离群点之后的轨迹
                    plot_outlier_adjacent_trj(coord_series_in, m, first_point_pos, last_point_pos, segment_id_in, veh_id_in, start_time_in, 1, flag)
                    outlier_label = 0  # outlier still exsit in this loop
        # 完成离群点剔除后，对轨迹进行小波变换增强
        coord_series_in = wavelet_filter(coord_series_in, flag)
        # 更新滤波后的轨迹结果
        if flag == 0:
            filter_status = ['filter_cumu_dis_x', 'filter_speed_x', 'filter_accer_x', 'filter_jerk_x']
        else:
            filter_status = ['filter_cumu_dis_y', 'filter_speed_y', 'filter_accer_y', 'filter_jerk_y']
        coord_series_in.loc[:, filter_status[0]] = coord_series_in.loc[:, 'wavelet_filter_cumu_dis'].to_numpy()
        coord_series_in.loc[:, filter_status[1]] = coord_series_in.loc[:, 'wavelet_filter_speed'].to_numpy()
        coord_series_in.loc[:, filter_status[2]] = coord_series_in.loc[:, 'wavelet_filter_accer'].to_numpy()
        coord_series_in.loc[:, filter_status[3]] = coord_series_in.loc[:, 'wavelet_filter_jerk'].to_numpy()
    return coord_series_in


def cumulated_dis_cal(coord_series_in, segment_id_in, veh_id_in, start_time_in, all_outlier_record):
    '''基于车辆轨迹的累计位移，完成数据增强
    :param coord_series_in: 传入的车辆坐标序列 -> ['global_center_x', 'global_center_y', 'speed_x', 'speed_y']
    :param segment_id_in: 场景id
    :param veh_id_in: 主车id
    :param start_time_in: 初始帧
    :param all_outlier_record: 记录离群点的列表

    '''
    # this function calculate the cumulated distance based on the given  global coordinates,
    # input coord_series_in: ['global_center_x', 'global_center_y', 'speed_x', 'speed_y']
    # output coord_series_in: ['global_center_x', 'global_center_y', 'speed_x', 'speed_y', 'cumu_dis', 'speed', 'accer', 'filter_cumu_dis',
    # 'filter_speed', 'filter_accer', 'speed_based_cumu_dis', 'speed_based_speed', 'speed_based_accer', 'speed_based_filter_cumu_dis',
    # 'speed_based_filter_speed', 'speed_based_accer']

    # 重置当前df的索引，并删除原始索引
    coord_series_in.reset_index(drop=True, inplace=True)

    # 新增列，分别对应position_based与speed_based
    coord_series_in.loc[:, 'cumu_dis_x'] = float(0)  # 累计x
    coord_series_in.loc[:, 'cumu_dis_y'] = float(0)  # 累计y
    coord_series_in.loc[:, 'speed_x'] = float(0)
    coord_series_in.loc[:, 'speed_y'] = float(0)
    coord_series_in.loc[:, 'accer_x'] = float(0)
    coord_series_in.loc[:, 'accer_y'] = float(0)
    coord_series_in.loc[:, 'jerk_x'] = float(0)
    coord_series_in.loc[:, 'jerk_y'] = float(0)
    coord_series_in.loc[:, 'speed_based_cumu_dis_x'] = float(0)
    coord_series_in.loc[:, 'speed_based_cumu_dis_y'] = float(0)
    coord_series_in.loc[:, 'speed_based_speed_x'] = float(0)
    coord_series_in.loc[:, 'speed_based_speed_y'] = float(0)
    coord_series_in.loc[:, 'speed_based_accer_x'] = float(0)
    coord_series_in.loc[:, 'speed_based_accer_y'] = float(0)
    coord_series_in.loc[:, 'speed_based_jerk_x'] = float(0)
    coord_series_in.loc[:, 'speed_based_jerk_y'] = float(0)

    # 基于xy坐标计算累计位移'cumu_dis'
    for i in range(1, len(coord_series_in['global_center_x'])):
        pre_x = coord_series_in['global_center_x'].iloc[i - 1]
        pre_y = coord_series_in['global_center_y'].iloc[i - 1]
        post_x = coord_series_in['global_center_x'].iloc[i]
        post_y = coord_series_in['global_center_y'].iloc[i]
        single_dis_x = post_x - pre_x
        single_dis_y = post_y - pre_y
        coord_series_in.loc[i, 'cumu_dis_x'] = coord_series_in.loc[i - 1, 'cumu_dis_x'] + single_dis_x
        coord_series_in.loc[i, 'cumu_dis_y'] = coord_series_in.loc[i - 1, 'cumu_dis_y'] + single_dis_y

    # 分别基于位置与速度得到两种参考系下(position_base, speed_based)的位置、速度、加速度信息
    coord_series_in = update_speed_and_accer(coord_series_in, 0)
    coord_series_in = speed_based_update_distance_and_accer(coord_series_in)
    # 轨迹修正
    # 初始化修正完成后的表头
    coord_series_in.loc[:, 'filter_cumu_dis_x'] = coord_series_in.loc[:, 'cumu_dis_x'].to_numpy()
    coord_series_in.loc[:, 'filter_speed_x'] = coord_series_in.loc[:, 'speed_x'].to_numpy()
    coord_series_in.loc[:, 'filter_accer_x'] = coord_series_in.loc[:, 'accer_x'].to_numpy()
    coord_series_in.loc[:, 'filter_jerk_x'] = 0
    coord_series_in.loc[:, 'filter_cumu_dis_y'] = coord_series_in.loc[:, 'cumu_dis_y'].to_numpy()
    coord_series_in.loc[:, 'filter_speed_y'] = coord_series_in.loc[:, 'speed_y'].to_numpy()
    coord_series_in.loc[:, 'filter_accer_y'] = coord_series_in.loc[:, 'accer_y'].to_numpy()
    coord_series_in.loc[:, 'filter_jerk_y'] = 0
    coord_series_in = trajectory_correctness(coord_series_in, segment_id_in, veh_id_in, start_time_in, all_outlier_record)  # 数据增强：基于优化的去除离群点，以及基于小波变换的方法进行去噪
    return coord_series_in


def pair_cf_coord_cal(leader_id, leader_trj_in, follower_id, follower_trj_in, av_label, all_outlier_record):
    '''
    zwt:
    :param leader_id: 主车id
    :param leader_trj_in: 主车轨迹dataframe
    :param follower_id: 前车(cutin车辆)的id
    :param follower_trj_in: 前车(cutin车辆)的dataframe
    :param av_label: 默认值为0
    :param all_outlier_record: 用来记录离群点的列表
    syh：
    传入场景参与者轨迹，并将其一维化（坐标转换为累计位移）
    :param leader_id                 : 前车ID，cutin场景中指代主车ID
    :param leader_trj_in             : 传入的前车轨迹df
    :param follower_id               : 后车ID，cutin场景中指代对手车ID
    :param follower_trj_in           : 传入的后车轨迹df

    ####为尽可能减少对waymo版数据修复代码及highD版场景生成泛化代码的修改，采用修改列表名的方式，实现代码复用
    即读取highD场景数据，修改对应列表名，与waymo版数据修复代码的输入要求对齐
    完成数据修复后，修改输出的列表名，与highD版场景生成泛化代码的输入要求对齐
    ####

    *************传入轨迹df的关键属性说明*****************
    :df_attri local_time_stamp       : 时间戳，对应highD中的frame
    :df_attri segment_id             : 场景片段id，highD中无该字段，读取文件时添加对应场景id为替代
    :df_attri veh_id                 : 车辆id，对应highD中的id
    :df_attri length                 : 车辆长度，对应highD中的width
    :df_attri global_center_x        : 车辆中心的全局x坐标，对应highD中的x
    :df_attri global_center_y        : 车辆中心的全局y坐标，对应highD中的y
    :df_attri speed_x                : 车辆的x向速度，对应highD中的xVelocity
    :df_attri speed_y                : 车辆的y向速度，对应highD中的yVelocity

    *************传出轨迹df的关键属性说明*****************
    :df_attri filter_positon_x       : 完成数据增强后的车辆x向累计位移
    :df_attri filter_position_y      : 完成数据增强后的车辆y向累计位移
    :df_attri filter_speed_x         : 完成数据增强后的车辆x向速度
    :df_attri filter_speed_y         : 完成数据增强后的车辆y向速度
    :df_attri filter_accer_x         : 完成数据增强后的车辆x向加速度
    :df_attri filter_accer_y         : 完成数据增强后的车辆y向加速度
    '''
    # convert 2-d coordinates to 1-d longitudinal coordinates
    # note that the leader and follower interacts with each other
    # av_label is to determine whether av is leader or follower (0 for follower, 1 for leader, 2 for non-av pair)
    all_seg_paired_cf_trj_final = pd.DataFrame()
    # all_seg_paired_cf_trj_with_comparison = pd.DataFrame()
    # 提取出每个场景参与者轨迹
    min_local_time = max(leader_trj_in['local_time_stamp'].min(), follower_trj_in['local_time_stamp'].min())  # 取主车和前车重合时段的最小时间
    max_local_time = min(leader_trj_in['local_time_stamp'].max(), follower_trj_in['local_time_stamp'].max())  # 取主车和前车重合时段的最大时间
    leader_trj_in = leader_trj_in.loc[leader_trj_in['local_time_stamp'] >= min_local_time, :]  # 取出主车中和前车的时间重叠的部分
    leader_trj_in = leader_trj_in.loc[leader_trj_in['local_time_stamp'] <= max_local_time, :]
    follower_trj_in = follower_trj_in.loc[follower_trj_in['local_time_stamp'] >= min_local_time, :]  # 取出前车中和主车的时间重叠的部分
    follower_trj_in = follower_trj_in.loc[follower_trj_in['local_time_stamp'] <= max_local_time, :]
    # 提取到的轨迹按照时间戳重排序
    leader_trj_in = leader_trj_in.sort_values(['local_time_stamp'])  # 主车dataframe按时间戳排序
    follower_trj_in = follower_trj_in.sort_values(['local_time_stamp'])  # 前车dataframe按时间戳排序
    # 初始化输出格式
    out_leader_trj = pd.DataFrame(leader_trj_in[['segment_id', 'veh_id', 'length', 'local_time_stamp']].to_numpy(),
                                  columns=['segment_id', 'local_veh_id', 'length', 'local_time'])
    out_leader_trj.loc[:, 'follower_id'] = follower_id
    out_leader_trj.loc[:, 'leader_id'] = leader_id
    out_follower_trj = pd.DataFrame(follower_trj_in[['segment_id', 'veh_id', 'length', 'local_time_stamp']].to_numpy(),
                                    columns=['segment_id', 'local_veh_id', 'length', 'local_time'])
    out_follower_trj.loc[:, 'follower_id'] = follower_id
    out_follower_trj.loc[:, 'leader_id'] = leader_id
    # cf_paired_trj_plot(out_leader_trj, out_follower_trj, av_label)
    # 修正传入的车辆轨迹
    temp_current_segment_id = out_follower_trj['segment_id'].iloc[0]  # 场景id
    temp_start_time = out_follower_trj['local_time'].iloc[0]  # 初始帧
    leader_cumu_dis = cumulated_dis_cal(
        leader_trj_in.loc[:, ['global_center_x', 'global_center_y', 'speed_x', 'speed_y']], temp_current_segment_id, leader_id, temp_start_time, all_outlier_record)
    follower_cumu_dis = cumulated_dis_cal(
        follower_trj_in.loc[:, ['global_center_x', 'global_center_y', 'speed_x', 'speed_y']], temp_current_segment_id, follower_id, temp_start_time, all_outlier_record)
    if leader_cumu_dis.empty or follower_cumu_dis.empty:
        print('Scenario %s has no feasible solution' % str(temp_current_segment_id))
        return pd.DataFrame()
    '''由于每个参与者的轨迹单独修正，并且都将轨迹初始点归一化至原点，故需要将参与者间的相对关系进行还原'''
    # 计算各参与者初始状态
    pre_x_1 = leader_trj_in['global_center_x'].iloc[0]
    pre_y_1 = leader_trj_in['global_center_y'].iloc[0]
    post_x_1 = follower_trj_in['global_center_x'].iloc[0]
    post_y_1 = follower_trj_in['global_center_y'].iloc[0]
    initial_dis = [post_x_1 - pre_x_1, post_y_1 - pre_y_1]
    # 还原两组轨迹数据
    # ======基于位置的轨迹数据======
    tags = ['_x', '_y']
    for i in range(2):
        # 记录前车相对于主车的相对坐标
        out_follower_trj.loc[:, 'position' + tags[i]] = follower_cumu_dis['cumu_dis' + tags[i]].to_numpy() + initial_dis[i]  # 原始位移
        out_follower_trj.loc[:, 'remove_outlier_pos' + tags[i]] = follower_cumu_dis['remove_outlier_cumu_dis' + tags[i]].to_numpy() + initial_dis[i]  # 去除离群点之后的位移
        out_follower_trj.loc[:, 'filter_pos' + tags[i]] = follower_cumu_dis['filter_cumu_dis' + tags[i]].to_numpy() + initial_dis[i]  # 去噪之后的位移
        # out_follower_trj.loc[:, 'wavelet_filter_pos' + tags[i]] = follower_cumu_dis['wavelet_filter_cumu_dis' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'speed' + tags[i]] = follower_cumu_dis['speed' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'remove_outlier_speed' + tags[i]] = follower_cumu_dis['remove_outlier_speed' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'filter_speed' + tags[i]] = follower_cumu_dis['filter_speed' + tags[i]].to_numpy()
        # out_follower_trj.loc[:, 'wavelet_filter_speed' + tags[i]] = follower_cumu_dis['wavelet_filter_speed' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'accer' + tags[i]] = follower_cumu_dis['accer' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'remove_outlier_accer' + tags[i]] = follower_cumu_dis['remove_outlier_accer' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'filter_accer' + tags[i]] = follower_cumu_dis['filter_accer' + tags[i]].to_numpy()
        # out_follower_trj.loc[:, 'wavelet_filter_accer' + tags[i]] = follower_cumu_dis['wavelet_filter_accer' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'jerk' + tags[i]] = follower_cumu_dis['jerk' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'filter_jerk' + tags[i]] = follower_cumu_dis['filter_jerk' + tags[i]].to_numpy()
        # out_follower_trj.loc[:, 'wavelet_filter_jerk' + tags[i]] = follower_cumu_dis['wavelet_filter_jerk' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'position' + tags[i]] = leader_cumu_dis['cumu_dis' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'remove_outlier_pos' + tags[i]] = leader_cumu_dis['remove_outlier_cumu_dis' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'filter_pos' + tags[i]] = leader_cumu_dis['filter_cumu_dis' + tags[i]].to_numpy()
        # out_leader_trj.loc[:, 'wavelet_filter_pos' + tags[i]] = leader_cumu_dis['wavelet_filter_cumu_dis' + tags[i]].to_numpy() + initial_dis[i]
        out_leader_trj.loc[:, 'speed' + tags[i]] = leader_cumu_dis['speed' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'remove_outlier_speed' + tags[i]] = leader_cumu_dis['remove_outlier_speed' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'filter_speed' + tags[i]] = leader_cumu_dis['filter_speed' + tags[i]].to_numpy()
        # out_leader_trj.loc[:, 'wavelet_filter_speed' + tags[i]] = leader_cumu_dis['wavelet_filter_speed' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'accer' + tags[i]] = leader_cumu_dis['accer' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'remove_outlier_accer' + tags[i]] = leader_cumu_dis['remove_outlier_accer' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'filter_accer' + tags[i]] = leader_cumu_dis['filter_accer' + tags[i]].to_numpy()
        # out_leader_trj.loc[:, 'wavelet_filter_accer' + tags[i]] = leader_cumu_dis['wavelet_filter_accer' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'jerk' + tags[i]] = leader_cumu_dis['jerk' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'filter_jerk' + tags[i]] = leader_cumu_dis['filter_jerk' + tags[i]].to_numpy()
        # out_leader_trj.loc[:, 'wavelet_filter_jerk' + tags[i]] = leader_cumu_dis['wavelet_filter_jerk' + tags[i]].to_numpy()
        # ======基于速度的轨迹数据======
        out_follower_trj.loc[:, 'speed_based_position' + tags[i]] = follower_cumu_dis['speed_based_cumu_dis' + tags[i]].to_numpy() + initial_dis[i]
        out_follower_trj.loc[:, 'speed_based_speed' + tags[i]] = follower_cumu_dis['speed_based_speed' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'speed_based_accer' + tags[i]] = follower_cumu_dis['speed_based_accer' + tags[i]].to_numpy()
        out_follower_trj.loc[:, 'speed_based_jerk' + tags[i]] = follower_cumu_dis['speed_based_jerk' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'speed_based_position' + tags[i]] = leader_cumu_dis['speed_based_cumu_dis' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'speed_based_speed' + tags[i]] = leader_cumu_dis['speed_based_speed' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'speed_based_accer' + tags[i]] = leader_cumu_dis['speed_based_accer' + tags[i]].to_numpy()
        out_leader_trj.loc[:, 'speed_based_jerk' + tags[i]] = leader_cumu_dis['speed_based_jerk' + tags[i]].to_numpy()
    # plot speed and acc figure
    before_and_after_remove_outlier_plot(out_follower_trj)
    before_and_after_remove_outlier_plot(out_leader_trj)
    before_and_after_filtering_plot(out_follower_trj)
    before_and_after_filtering_plot(out_leader_trj)
    # save cf paired trj
    # all_seg_paired_cf_trj = pd.concat([all_seg_paired_cf_trj, pd.concat([out_leader_trj, out_follower_trj])])
    # all_seg_paired_cf_trj_with_comparison = pd.concat([out_leader_trj, out_follower_trj])
    out_follower_trj_final = out_follower_trj.loc[
        :, ['segment_id', 'local_veh_id', 'length', 'local_time', 'follower_id', 'leader_id',
            'filter_pos_x', 'filter_speed_x', 'filter_accer_x', 'filter_pos_y', 'filter_speed_y', 'filter_accer_y']]
    out_follower_trj_final.columns = [
        'segment_id', 'local_veh_id', 'length', 'local_time', 'follower_id', 'leader_id',
        'filter_pos_x', 'filter_speed_x', 'filter_accer_x', 'filter_pos_y', 'filter_speed_y', 'filter_accer_y']
    out_leader_trj_final = out_leader_trj.loc[
        :, ['segment_id', 'local_veh_id', 'length', 'local_time', 'follower_id', 'leader_id',
            'filter_pos_x', 'filter_speed_x', 'filter_accer_x', 'filter_pos_y', 'filter_speed_y', 'filter_accer_y']]
    out_leader_trj_final.columns = [
        'segment_id', 'local_veh_id', 'length', 'local_time', 'follower_id', 'leader_id',
        'filter_pos_x', 'filter_speed_x', 'filter_accer_x', 'filter_pos_y', 'filter_speed_y', 'filter_accer_y']
    all_seg_paired_cf_trj_final = pd.concat([out_leader_trj_final, out_follower_trj_final])
    # plot the car following trj of both follower and leader
    cf_paired_trj_plot(out_leader_trj_final, out_follower_trj_final, av_label)
    return all_seg_paired_cf_trj_final


def csv_plot(oldcsv_path, newcsv_path, ego_id, cutin_id, scene_id):
    '''对场景CSV文件进行可视化'''
    def getPos(csv_path, ego_id, cutin_id):
        df = pd.read_csv(csv_path)
        df_ego = df[df['id'] == ego_id]
        df_cutin = df[df['id'] == cutin_id]
        x1, y1 = df_ego['x'].tolist(), df_ego['y'].tolist()
        x2, y2 = df_cutin['x'].tolist(), df_cutin['y'].tolist()
        min_x = min(min(x1), min(x2)) - 10
        max_x = max(max(x1), max(x2)) + 10
        min_y = min(min(y1), min(y2)) - 10
        max_y = max(max(y1), max(y2)) + 10
        return x1, y1, x2, y2, min_x, max_x, min_y, max_y

    oldPos = getPos(oldcsv_path, ego_id, cutin_id)
    newPos = getPos(newcsv_path, ego_id, cutin_id)

    plt.ion()
    for i in range(len(newPos[0])):
        plt.subplot(2, 1, 1)
        plt.xlim(oldPos[4], oldPos[5])
        plt.ylim(oldPos[6], oldPos[7])
        plt.scatter(oldPos[0][i], oldPos[1][i], c='r')
        plt.scatter(oldPos[2][i], oldPos[3][i], c='b')
        plt.title('Scenario ' + str(scene_id) + ' GIF' + ' Before and After Data Processing')
        plt.subplot(2, 1, 2)
        plt.xlim(newPos[4], newPos[5])
        plt.ylim(newPos[6], newPos[7])
        plt.scatter(newPos[0][i], newPos[1][i], c='r')
        plt.scatter(newPos[2][i], newPos[3][i], c='b')
        plt.pause(1e-7)
        plt.clf()
    plt.ioff()


if __name__ == '__main__':
    pd.set_option('mode.chained_assignment', None)  # 更改dataframe显示的设置，这里是去掉潜在出现的dataframe警告

    scene_rootpath = os.path.abspath('../OpenSCENARIO/HighD_V3')
    scenario_path = []  # 添加需要处理的csv文件路径
    for filepath, dirnames, filenames in os.walk(scene_rootpath):
        for dirname in dirnames:
            dir_path = os.path.join(filepath, dirname)
            for filepath1, dirnames1, filenames1 in os.walk(dir_path):
                for filename in filenames1:
                    if 'test.csv' in filename and 'processed.csv' not in filename:
                        scenario_path.append(os.path.join(filepath1, filename))
    noSolution_count = 0
    pbar_iteration = tqdm(total=len(scenario_path), desc='[scenarios]')
    for i in range(len(scenario_path)):
        scene_path = scenario_path[i]
        df_scene = pd.read_csv(scene_path)
        # 与Waymo代码对齐，增加一列segment_id，取值为场景id，并修改相关列名
        scene_id = scene_path.split('\\')[-1][:4]  # 场景名的前4个字符
        df_scene['segment_id'] = [scene_id] * df_scene.shape[0]  # 填充为1列
        df_scene.rename(columns={
            'frame': 'local_time_stamp', 'id': 'veh_id', 'width': 'length', 'x': 'global_center_x', 'y': 'global_center_y',
            'xVelocity': 'speed_x', 'yVelocity': 'speed_y', 'precedingId': 'precedingId'}, inplace=True)  # 调整部分列名
        ego_id = df_scene.loc[0, 'veh_id']  # 主车id
        df_ego = df_scene[df_scene['veh_id'] == ego_id]  # 取出主车的dataframe
        ego_preIds = df_ego['precedingId'].tolist()  # 取出主车的前车list
        ego_preId = list(set(ego_preIds))  # 去重
        ego_preId.sort(key=ego_preIds.index)  # 这里是按出现前后排序
        for i in range(len(ego_preId) - 1, -1, -1):
            if ego_preId[i]:
                cutin_id = ego_preId[i]  # 最后一个前车作为对手车辆
                break
        df_cutin = df_scene[df_scene['veh_id'] == 1]  # 车辆id为1的提出出来作为cutin_df

        # 进行上下行方向的统一
        if df_ego.loc[0, 'global_center_x'] > df_ego.loc[len(df_ego) - 1, 'global_center_x']:  # 上行需调整
            df_ego.loc[:, 'global_center_x'] = df_ego.loc[:, 'global_center_x'] * -1  # x直接*-1
            df_ego.loc[:, 'global_center_y'] = df_ego.loc[:, 'global_center_y'] * -1  # y直接*-1
            df_ego.loc[:, 'speed_x'] = df_ego.loc[:, 'speed_x'] * -1  # x速度*-1
            df_ego.loc[:, 'speed_y'] = df_ego.loc[:, 'speed_y'] * -1  # y速度*-1
            df_cutin.loc[:, 'global_center_x'] = df_cutin.loc[:, 'global_center_x'] * -1  # cutin车辆做一样的操作
            df_cutin.loc[:, 'global_center_y'] = df_cutin.loc[:, 'global_center_y'] * -1
            df_cutin.loc[:, 'speed_x'] = df_cutin.loc[:, 'speed_x'] * -1
            df_cutin.loc[:, 'speed_y'] = df_cutin.loc[:, 'speed_y'] * -1

        all_outlier_record = pd.DataFrame()  # 记录离群点
        out_trj = pd.DataFrame()
        out_trj = pair_cf_coord_cal(ego_id, df_ego, cutin_id, df_cutin, 0, all_outlier_record)
        if not out_trj.empty:
            df_final = out_trj.loc[:, ['local_veh_id', 'length', 'local_time', 'filter_pos_x', 'filter_speed_x',
                                   'filter_accer_x', 'filter_pos_y', 'filter_speed_y', 'filter_accer_y']]
            df_final.rename(columns={
                'local_veh_id': 'id', 'length': 'width', 'local_time': 'frame', 'filter_pos_x': 'x', 'filter_pos_y': 'y', 'filter_speed_x': 'xVelocity',
                'filter_speed_y': 'yVelocity', 'filter_accer_x': 'xAcceleration', 'filter_accer_y': 'yAcceleration'}, inplace=True)
            output_path = scene_path.split('.')[0] + '_processed.csv'
            df_final.to_csv(output_path, index=None)
            # csv_plot(scene_path, output_path, ego_id, cutin_id, scene_id)
        else:
            noSolution_count += 1
        pbar_iteration.update(1)
    pbar_iteration.write('[*] Finish Data Processing')
    pbar_iteration.close()
    print(noSolution_count)
