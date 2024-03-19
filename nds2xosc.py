# -*- coding: utf-8 -*-
# @Time    : 2021.12.01
# @Author  : Syh
# @Version : 1.0
# @Descrip : 实现对现有上海NDS数据向OpenSCENARIO格式转换


'''
上海NDS数据中xml文件采用航点WayPoint描述车辆路径，不包含时间信息
拟采用AcquirePositionAction以表现车辆动作
'''

import xml.etree.ElementTree as ET

from numpy.core.arrayprint import SubArrayFormat


# TODO：进行TREE的美化，即对根节点下的每个子节点进行相应的换行与缩进操作
def pretty_xml(element, indent, newline, level=0):  # elemnt为传进来的Elment类，参数indent用于缩进，newline用于换行
    '''
    该部分的美化操作，置于整个tree构建完成后，进行统一美化
    :param arguments: 传进来的Elment类，缩进参数，换行参数
    :return: None

    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write('.xdor')  # 美化完成后将XML写入.xdor
    '''
    if element:  # 判断element是否有子元素
        if (element.text is None) or element.text.isspace():  # 如果element的text没有内容
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
            # else:  # 此处两行如果把注释去掉，Element的text也会另起一行
            # element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * level
    temp = list(element)  # 将element转成list
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素，说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
        pretty_xml(subelement, indent, newline, level=level + 1)  # 对子元素进行递归操作


def xosc_write(nds_path, xodr_path, output_path):
    '''
    该方法用于自动化实现上海NDS场景数据XML文件到OpenSCENARIO格式的转换
    转换思路：将每辆车的轨迹按照轨迹逐帧记录storyBoard中的Event中（NDS轨迹采样率为10HZ）

    Input：NDS场景XML文件、OpenDrive文件路径、输出的OpenScenario文件路径
    Output：None
    '''
    root = ET.Element('OpenSCENARIO')
    # root下第一层目录构建——Level 1
    header = ET.SubElement(root, 'FileHeader')
    header.attrib = {'revMajor': '1', 'revMinor': '0', 'date': '2021-12-04T16:15:00', 'description': 'scenario_NDS', 'author': 'OnSite_TOPS'}
    pareDecl = ET.SubElement(root, 'ParameterDeclarations')
    pareDecl.attrib = {}
    catalog = ET.SubElement(root, 'CatalogLocations')
    catalog.attrib = {}
    roadNet = ET.SubElement(root, 'RoadNetwork')
    roadNet.attrib = {}
    entity = ET.SubElement(root, 'Entities')
    entity.attrib = {}
    storyboard = ET.SubElement(root, 'Storyboard')
    storyboard.attrib = {}

    # root下第二层目录构建——Level 2
    logic = ET.SubElement(roadNet, 'LogicFile')
    logic.attrib = {'filepath': xodr_path}
    init = ET.SubElement(storyboard, 'Init')
    init.attrib = {}
    story = ET.SubElement(storyboard, 'Story')
    story.attrib = {'name': 'Cutin'}
    stoptrigger = ET.SubElement(storyboard, 'StopTrigger')
    stoptrigger.attrib = {}

    # root下第三层目录构建——Level 3
    actions = ET.SubElement(init, 'Actions')
    actions.attrib = {}
    paramDecl = ET.SubElement(story, 'ParameterDeclarations')
    paramDecl.attrib = {}

    # Level 4及以下，以模块为单位进行树结构构建
    '''Init-Action下的GlobalAction块'''
    globalaction = ET.Element('GlobalAction', {})
    actions.append(globalaction)
    environmentaction = ET.Element('EnvironmentAction', {})
    globalaction.append(environmentaction)
    environment = ET.Element('Environment', {})
    environmentaction.append(environment)
    ''''读取场景cvs后，自动化完成车辆初始化及轨迹设置'''
    nds_data = open(nds_path).read()
    nds_root = ET.fromstring(nds_data)
    sample = 1 / 10  # 上海NDS场景的轨迹采样率（阅读YD师姐编写XML文件的C语言代码）
    count = 0  # 用于区分主车及编号
    speed_list = []
    for speed in nds_root.iter('Speed'):
        speed_list.append(float(speed.attrib['Value']))
    for path in nds_root.iter('PathShape'):
        x_list, y_list, z_list, h_list, p_list, r_list = [[] for i in range(6)]
        for waypoint in path:
            x_list.append(float(waypoint.attrib['X']))
            y_list.append(float(waypoint.attrib['Y']))
            z_list.append(float(waypoint.attrib['Z']))
            h_list.append(float(waypoint.attrib['Yaw']))
            p_list.append(float(waypoint.attrib['Pitch']))
            r_list.append(float(waypoint.attrib['Roll']))
        if count == 0:  # ego
            x_stop = x_list[-1]
            y_stop = y_list[-1]
            z_stop = z_list[-1]
            h_stop = h_list[-1]
            p_stop = p_list[-1]
            r_stop = r_list[-1]
            # 申明Entities及对应属性
            scenObj = ET.SubElement(entity, 'ScenarioObject')
            scenObj.attrib = {'name': 'Ego'}
            veh = ET.SubElement(scenObj, 'Vehicle')
            veh.attrib = {'name': 'Default_car', 'vehicleCategory': 'car'}
            boundingbox = ET.SubElement(veh, 'BoundingBox')  # 车辆边框属性设置
            center = ET.SubElement(boundingbox, 'Center')  # 车辆中心在【车辆坐标系】中的坐标
            center.attrib = {'x': '%.16e' % 1.5, 'y': '%.16e' % 0, 'z': '%.16e' % 0.9}
            dimension = ET.SubElement(boundingbox, 'Dimensions')
            dimension.attrib = {'width': '%.16e' % 2.1, 'length': '%.16e' % 4.5, 'height': '%.16e' % 1.8}
            controller = ET.SubElement(scenObj, 'ObjectController')
            controller.attrib = {}
            # Init部分对车辆的属性设置
            private = ET.Element('Private', {'entityRef': 'Ego'})  # 申明专属对象
            actions.append(private)

            privateAction1_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作1（速度）
            privateAction1_init.attrib = {}
            longitAction = ET.SubElement(privateAction1_init, 'LongitudinalAction')
            longitAction.attrib = {}
            speedAction = ET.SubElement(longitAction, 'SpeedAction')
            speedAction.attrib = {}
            speedAcDy = ET.SubElement(speedAction, 'SpeedActionDynamics')
            speedAcDy.attrib = {'dynamicsShape': 'step', 'value': '0', 'dynamicsDimension': 'time'}
            speedAcTar = ET.SubElement(speedAction, 'SpeedActionTarget')
            speedAcTar.attrib = {}
            absTarSpeed = ET.SubElement(speedAcTar, 'AbsoluteTargetSpeed')
            absTarSpeed.attrib = {'value': '%.16e' % speed_list[0]}

            privateAction2_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作2（位置）
            privateAction2_init.attrib = {}
            telepAction = ET.SubElement(privateAction2_init, 'TeleportAction')
            telepAction.attrib = {}
            position_init = ET.SubElement(telepAction, 'Position')
            position_init.attrib = {}
            worldPos_init = ET.SubElement(position_init, 'WorldPosition')  # 采用全局世界坐标对车辆进行定位
            worldPos_init.attrib = {
                'x': '%.16e' % x_list[0], 'y': '%.16e' % y_list[0], 'z': '%.16e' % z_list[0], 'h': '%.16e' % h_list[0], 'p': '%.16e' % p_list[0], 'r': '%.16e' % r_list[0]}
            # Stroy部分对车辆动作（位置获取）的设置
            '''
            OpenSCENARIO中通过StoryBoard展现场景的机制：
            story下设置各个车辆的动作集Act，每个Act下定义车辆对应的操作集ManeuverGroup及其触发器StartTrigger
            ManeuverGroup下定义该操作集的执行者Actor及对应的事件Event
            Event下定义具体的车辆动作Action及其触发器StartTrigger
            【对于一个Action，只有动作集Act的触发器触发并且对应Event的触发器也触发，才会执行该动作Action】
            【Act的触发要早于Event，否则仿真将出错，故下面Act的触发时间为0，Event触发时间后移一帧0.05】
            '''
            act = ET.SubElement(story, 'Act')
            act.attrib = {'name': 'Act_Ego'}
            '''车辆操作组ManeuverGroup设置'''
            maneuGroup = ET.SubElement(act, 'ManeuverGroup')
            maneuGroup.attrib = {'maximumExecutionCount': '1', 'name': 'Sequence_Ego'}
            actor = ET.SubElement(maneuGroup, 'Actors')  # 操作执行者设置
            actor.attrib = {'selectTriggeringEntities': 'false'}
            entityRef = ET.SubElement(actor, 'EntityRef')
            entityRef.attrib = {'entityRef': 'Ego'}
            maneuver = ET.SubElement(maneuGroup, 'Maneuver')  # 具体操作设置（通过事件Event的触发）
            maneuver.attrib = {'name': 'Maneuver1'}
            event = ET.SubElement(maneuver, 'Event')
            event.attrib = {'name': 'Event1', 'priority': 'overwrite'}
            action = ET.SubElement(event, 'Action')  # Event下定义的具体车辆动作
            action.attrib = {'name': 'Action1'}
            privateAction_story = ET.SubElement(action, 'PrivateAction')
            privateAction_story.attrib = {}
            routAction = ET.SubElement(privateAction_story, 'RoutingAction')
            routAction.attrib = {}
            followTraAction = ET.SubElement(routAction, 'FollowTrajectoryAction')  # 路径行为模型为轨迹跟随
            followTraAction.attrib = {}
            trajectory = ET.SubElement(followTraAction, 'Trajectory')  # 轨迹跟随的具体轨迹设置
            trajectory.attrib = {'name': 'Trajectory_Ego', 'closed': 'false'}
            shape = ET.SubElement(trajectory, 'Shape')  # 轨迹线型设置（轨迹点之间相连的方式）
            shape.attrib = {}
            polyline = ET.SubElement(shape, 'Polyline')  # 直线相连，上海NDS轨迹为10HZ的采样
            polyline.attrib = {}
            for i in range(len(x_list) - 1):  # 批量填充csv场景中的轨迹点（去除掉初始化点）
                vertex = ET.SubElement(polyline, 'Vertex')
                vertex.attrib = {'time': str(sample * (i))}
                position_story = ET.SubElement(vertex, 'Position')
                position_story.attrib = {}
                worldPos_story = ET.SubElement(position_story, 'WorldPosition')
                worldPos_story.attrib = {
                    'x': '%.16e' % x_list[i + 1], 'y': '%.16e' % y_list[i + 1], 'z': '%.16e' % z_list[i + 1], 'h': '%.16e' % h_list[i + 1], 'p': '%.16e' % p_list[i + 1], 'r': '%.16e' % r_list[i + 1]}
            timeRef = ET.SubElement(followTraAction, 'TimeReference')  # 轨迹跟随的时间设置
            timeRef.attrib = {}
            timing = ET.SubElement(timeRef, 'Timing')  # 选择绝对时间，（不能选择相对事件触发的时间，为保证Act先触发，Event触发点延后了0.03秒）
            timing.attrib = {'domainAbsoluteRelative': 'absolute', 'scale': '1.0', 'offset': '0.0'}
            trajecFolloeMode = ET.SubElement(followTraAction, 'TrajectoryFollowingMode')
            trajecFolloeMode.attrib = {'follingMode': 'follow'}
            startTrig_event = ET.SubElement(event, 'StartTrigger')  # Event的触发器StartTrigger
            startTrig_event.attrib = {}
            conditionGroup_event = ET.SubElement(startTrig_event, 'ConditionGroup')
            conditionGroup_event.attrib = {}
            condition_event = ET.SubElement(conditionGroup_event, 'Condition')
            condition_event.attrib = {'name': '', 'delay': '0', 'conditionEdge': 'rising'}  # 触发机制为rising，即condi由0至1时触发
            byValueCondi_event = ET.SubElement(condition_event, 'ByValueCondition')  # 通过变量值判断条件
            byValueCondi_event.attrib = {}
            simulationTimeCondi_event = ET.SubElement(byValueCondi_event, 'SimulationTimeCondition')  # 基于仿真时间触发
            simulationTimeCondi_event.attrib = {'value': '0.01', 'rule': 'greaterThan'}
            '''车辆动作集Act的触发器设置'''
            startTrig_act = ET.SubElement(act, 'StartTrigger')  # 动作集Act触发器设置
            startTrig_act.attrib = {}
            conditionGroup_act = ET.SubElement(startTrig_act, 'ConditionGroup')
            conditionGroup_act.attrib = {}
            condition_act = ET.SubElement(conditionGroup_act, 'Condition')
            condition_act.attrib = {'name': '', 'delay': '', 'conditionEdge': 'rising'}
            byValueCondi_act = ET.SubElement(condition_act, 'ByValueCondition')
            byValueCondi_act.attrib = {}
            simulationTimeCondi_act = ET.SubElement(byValueCondi_act, 'SimulationTimeCondition')
            simulationTimeCondi_act.attrib = {'value': '0', 'rule': 'greaterThan'}
        else:  # 非ego
            # 申明Entities及对应属性
            scenObj = ET.SubElement(entity, 'ScenarioObject')
            scenObj.attrib = {'name': str('A' + str(count))}
            veh = ET.SubElement(scenObj, 'Vehicle')
            veh.attrib = {'name': 'Default_car', 'vehicleCategory': 'car'}
            boundingbox = ET.SubElement(veh, 'BoundingBox')  # 车辆边框属性设置
            center = ET.SubElement(boundingbox, 'Center')  # 车辆中心在【车辆坐标系】中的坐标
            center.attrib = {'x': '%.16e' % 1.5, 'y': '%.16e' % 0, 'z': '%.16e' % 0.9}
            dimension = ET.SubElement(boundingbox, 'Dimensions')
            dimension.attrib = {'width': '%.16e' % 2.1, 'length': '%.16e' % 4.5, 'height': '%.16e' % 1.8}
            controller = ET.SubElement(scenObj, 'ObjectController')
            controller.attrib = {}
            # Init部分对车辆的初始化
            private = ET.Element('Private', {'entityRef': str('A' + str(count))})  # 申明专属对象
            actions.append(private)

            privateAction1_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作1（速度）
            privateAction1_init.attrib = {}
            longitAction = ET.SubElement(privateAction1_init, 'LongitudinalAction')
            longitAction.attrib = {}
            speedAction = ET.SubElement(longitAction, 'SpeedAction')
            speedAction.attrib = {}
            speedAcDy = ET.SubElement(speedAction, 'SpeedActionDynamics')
            speedAcDy.attrib = {'dynamicsShape': 'step', 'value': '0', 'dynamicsDimension': 'time'}
            speedAcTar = ET.SubElement(speedAction, 'SpeedActionTarget')
            speedAcTar.attrib = {}
            absTarSpeed = ET.SubElement(speedAcTar, 'AbsoluteTargetSpeed')
            absTarSpeed.attrib = {'value': '%.16e' % speed_list[count]}

            privateAction2_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作2（位置）
            privateAction2_init.attrib = {}
            telepAction = ET.SubElement(privateAction2_init, 'TeleportAction')
            telepAction.attrib = {}
            position_init = ET.SubElement(telepAction, 'Position')
            position_init.attrib = {}
            worldPos_init = ET.SubElement(position_init, 'WorldPosition')  # 采用全局世界坐标对车辆进行定位
            worldPos_init.attrib = {
                'x': '%.16e' % x_list[0], 'y': '%.16e' % y_list[0], 'z': '%.16e' % z_list[0], 'h': '%.16e' % h_list[0], 'p': '%.16e' % p_list[0], 'r': '%.16e' % r_list[0]}
            # Stroy部分对车辆动作（轨迹跟随）的设置
            act = ET.SubElement(story, 'Act')
            act.attrib = {'name': str('Act_' + 'A' + str(count))}
            '''车辆操作组ManeuverGroup设置'''
            maneuGroup = ET.SubElement(act, 'ManeuverGroup')
            maneuGroup.attrib = {'maximumExecutionCount': '1', 'name': str('Squence_' + 'A' + str(count))}
            actor = ET.SubElement(maneuGroup, 'Actors')  # 操作执行者设置
            actor.attrib = {'selectTriggeringEntities': 'false'}
            entityRef = ET.SubElement(actor, 'EntityRef')
            entityRef.attrib = {'entityRef': str('A' + str(count))}
            maneuver = ET.SubElement(maneuGroup, 'Maneuver')  # 具体操作设置（通过事件Event的触发）
            maneuver.attrib = {'name': 'Maneuver1'}
            event = ET.SubElement(maneuver, 'Event')
            event.attrib = {'name': 'Event1', 'priority': 'overwrite'}
            action = ET.SubElement(event, 'Action')  # Event下定义的具体车辆动作
            action.attrib = {'name': 'Action1'}
            privateAction_story = ET.SubElement(action, 'PrivateAction')
            privateAction_story.attrib = {}
            routAction = ET.SubElement(privateAction_story, 'RoutingAction')
            routAction.attrib = {}
            followTraAction = ET.SubElement(routAction, 'FollowTrajectoryAction')  # 路径行为模型为轨迹跟随
            followTraAction.attrib = {}
            trajectory = ET.SubElement(followTraAction, 'Trajectory')  # 轨迹跟随的具体轨迹设置
            trajectory.attrib = {'name': 'Trajectory_Ego', 'closed': 'false'}
            shape = ET.SubElement(trajectory, 'Shape')  # 轨迹线型设置（轨迹点之间相连的方式）
            shape.attrib = {}
            polyline = ET.SubElement(shape, 'Polyline')  # 直线相连，上海NDS轨迹为10HZ的采样
            polyline.attrib = {}
            for i in range(len(x_list) - 1):  # 批量填充csv场景中的轨迹点（去除掉初始化点）
                vertex = ET.SubElement(polyline, 'Vertex')
                vertex.attrib = {'time': str(sample * (i))}
                position_story = ET.SubElement(vertex, 'Position')
                position_story.attrib = {}
                worldPos_story = ET.SubElement(position_story, 'WorldPosition')
                worldPos_story.attrib = {
                    'x': '%.16e' % x_list[i + 1], 'y': '%.16e' % y_list[i + 1], 'z': '%.16e' % z_list[i + 1], 'h': '%.16e' % h_list[i + 1], 'p': '%.16e' % p_list[i + 1], 'r': '%.16e' % r_list[i + 1]}
            timeRef = ET.SubElement(followTraAction, 'TimeReference')  # 轨迹跟随的时间设置
            timeRef.attrib = {}
            timing = ET.SubElement(timeRef, 'Timing')  # 选择绝对时间，（不能选择相对事件触发的时间，为保证Act先触发，Event触发点延后了0.03秒）
            timing.attrib = {'domainAbsoluteRelative': 'absolute', 'scale': '1.0', 'offset': '0.0'}
            trajecFolloeMode = ET.SubElement(followTraAction, 'TrajectoryFollowingMode')
            trajecFolloeMode.attrib = {'follingMode': 'follow'}
            startTrig_event = ET.SubElement(event, 'StartTrigger')  # Event的触发器StartTrigger
            startTrig_event.attrib = {}
            conditionGroup_event = ET.SubElement(startTrig_event, 'ConditionGroup')
            conditionGroup_event.attrib = {}
            condition_event = ET.SubElement(conditionGroup_event, 'Condition')
            condition_event.attrib = {'name': '', 'delay': '0', 'conditionEdge': 'rising'}  # 触发机制为rising，即condi由0至1时触发
            byValueCondi_event = ET.SubElement(condition_event, 'ByValueCondition')  # 通过变量值判断条件
            byValueCondi_event.attrib = {}
            simulationTimeCondi_event = ET.SubElement(byValueCondi_event, 'SimulationTimeCondition')  # 基于仿真时间触发
            simulationTimeCondi_event.attrib = {'value': '0.01', 'rule': 'greaterThan'}
            '''车辆动作集Act的触发器设置'''
            startTrig_act = ET.SubElement(act, 'StartTrigger')  # 动作集Act触发器设置
            startTrig_act.attrib = {}
            conditionGroup_act = ET.SubElement(startTrig_act, 'ConditionGroup')
            conditionGroup_act.attrib = {}
            condition_act = ET.SubElement(conditionGroup_act, 'Condition')
            condition_act.attrib = {'name': '', 'delay': '', 'conditionEdge': 'rising'}
            byValueCondi_act = ET.SubElement(condition_act, 'ByValueCondition')
            byValueCondi_act.attrib = {}
            simulationTimeCondi_act = ET.SubElement(byValueCondi_act, 'SimulationTimeCondition')
            simulationTimeCondi_act.attrib = {'value': '0', 'rule': 'greaterThan'}
        count += 1

    # 设置整个StoryBoard的停止器StopTrigger
    conditionGroup_stop = ET.SubElement(stoptrigger, 'ConditionGroup')
    conditionGroup_stop.attrib = {}
    condition_stop = ET.SubElement(conditionGroup_stop, 'Condition')
    condition_stop.attrib = {'name': '', 'delay': '0', 'conditionEdge': 'rising'}  # 触发机制为rising，即condi由0至1时触发
    byEntityCondi_stop = ET.SubElement(condition_stop, 'ByEntityCondition')  # 通过参与对象判断条件
    byEntityCondi_stop.attrib = {}
    triggerEntity = ET.SubElement(byEntityCondi_stop, 'TriggeringEntities')
    triggerEntity.attrib = {'TriggeringEntitiesRule': 'all'}
    entityRef = ET.SubElement(triggerEntity, 'EntityRef')
    entityRef.attrib = {'entityRef': 'Ego'}
    entityCondi = ET.SubElement(byEntityCondi_stop, 'EntityCondition')
    entityCondi.attrib = {}
    reachPositionCondi_stop = ET.SubElement(entityCondi, 'ReachPositionCondition')  # 基于Ego位置触发
    reachPositionCondi_stop.attrib = {'tolerance': '%.16e' % 0.1}  # 设置触发点半径，小于tolerance则触发
    position_stop = ET.SubElement(reachPositionCondi_stop, 'Position')
    position_stop.attrib = {}
    worldPos_stop = ET.SubElement(position_stop, 'WorldPosition')
    worldPos_stop.attrib = {
        'x': '%.16e' % x_stop, 'y': '%.16e' % y_stop, 'z': '%.16e' % z_stop, 'h': '%.16e' % h_stop, 'p': '%.16e' % p_stop, 'r': '%.16e' % r_stop}

    tree = ET.ElementTree(root)
    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return


def xosc_write_followTra(nds_path, xodr_path, output_path):
    '''
    该方法用于自动化实现上海NDS数据中XML场景数据到openScenario格式的自动转换
    转换思路：上海NDS中的XML数据中只有车辆轨迹的航点Waypoint，并没有时间戳信息，故
    在Event下的车辆路径选择设置中，采用忽略时间信息的position轨迹跟踪模型
    【RoutingAction.FollowTrajectoryAction---TimeReference=None, TrajectoryFollowMode=position】

    Input：轨迹XML文本路径、OpenDrive文件路径、输出的OpenScenario文件路径
    Output：None
    '''
    root = ET.Element('OpenSCENARIO')
    # root下第一层目录构建——Level 1
    header = ET.SubElement(root, 'FileHeader')
    header.attrib = {'revMajor': '1', 'revMinor': '0', 'date': '2021-11-02T16:20:00', 'description': 'scenario_highD', 'author': 'OnSite_TOPS'}
    pareDecl = ET.SubElement(root, 'ParameterDeclarations')
    pareDecl.attrib = {}
    catalog = ET.SubElement(root, 'CatalogLocations')
    catalog.attrib = {}
    roadNet = ET.SubElement(root, 'RoadNetwork')
    roadNet.attrib = {}
    entity = ET.SubElement(root, 'Entities')
    entity.attrib = {}
    storyboard = ET.SubElement(root, 'Storyboard')
    storyboard.attrib = {}

    # root下第二层目录构建——Level 2
    logic = ET.SubElement(roadNet, 'LogicFile')
    logic.attrib = {'filepath': xodr_path}
    init = ET.SubElement(storyboard, 'Init')
    init.attrib = {}
    story = ET.SubElement(storyboard, 'Story')
    story.attrib = {'name': 'Cutin'}
    stoptrigger = ET.SubElement(storyboard, 'StopTrigger')
    stoptrigger.attrib = {}

    # root下第三层目录构建——Level 3
    actions = ET.SubElement(init, 'Actions')
    actions.attrib = {}
    paramDecl = ET.SubElement(story, 'ParameterDeclarations')
    paramDecl.attrib = {}

    # Level 4及以下，以模块为单位进行树结构构建
    '''Init-Action下的GlobalAction块'''
    globalaction = ET.Element('GlobalAction', {})
    actions.append(globalaction)
    environmentaction = ET.Element('EnvironmentAction', {})
    globalaction.append(environmentaction)
    environment = ET.Element('Environment', {})
    environmentaction.append(environment)
    ''''读取场景cvs后，自动化完成车辆初始化及轨迹设置'''
    nds_data = open(nds_path).read()
    nds_root = ET.fromstring(nds_data)
    count = 0  # 用于区分主车及编号
    speed_list = []
    for speed in nds_root.iter('Speed'):
        speed_list.append(float(speed.attrib['Value']))
    for path in nds_root.iter('PathShape'):
        x_list, y_list, z_list, h_list, p_list, r_list = [[] for i in range(6)]
        for waypoint in path:
            x_list.append(float(waypoint.attrib['X']))
            y_list.append(float(waypoint.attrib['Y']))
            z_list.append(float(waypoint.attrib['Z']))
            h_list.append(float(waypoint.attrib['Yaw']))
            p_list.append(float(waypoint.attrib['Pitch']))
            r_list.append(float(waypoint.attrib['Roll']))
        if count == 0:  # ego
            x_stop = x_list[-1]
            y_stop = y_list[-1]
            z_stop = z_list[-1]
            h_stop = h_list[-1]
            p_stop = p_list[-1]
            r_stop = r_list[-1]
            # 申明Entities及对应属性
            scenObj = ET.SubElement(entity, 'ScenarioObject')
            scenObj.attrib = {'name': 'Ego'}
            veh = ET.SubElement(scenObj, 'Vehicle')
            veh.attrib = {'name': 'Default_car', 'vehicleCategory': 'car'}
            boundingbox = ET.SubElement(veh, 'BoundingBox')  # 车辆边框属性设置
            center = ET.SubElement(boundingbox, 'Center')  # 车辆中心在【车辆坐标系】中的坐标
            center.attrib = {'x': '%.16e' % 1.5, 'y': '%.16e' % 0, 'z': '%.16e' % 0.9}
            dimension = ET.SubElement(boundingbox, 'Dimensions')
            dimension.attrib = {'width': '%.16e' % 2.1, 'length': '%.16e' % 4.5, 'height': '%.16e' % 1.8}
            controller = ET.SubElement(scenObj, 'ObjectController')
            controller.attrib = {}
            # Init部分对车辆的属性设置
            private = ET.Element('Private', {'entityRef': 'Ego'})  # 申明专属对象
            actions.append(private)

            privateAction1_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作1（速度）
            privateAction1_init.attrib = {}
            longitAction = ET.SubElement(privateAction1_init, 'LongitudinalAction')
            longitAction.attrib = {}
            speedAction = ET.SubElement(longitAction, 'SpeedAction')
            speedAction.attrib = {}
            speedAcDy = ET.SubElement(speedAction, 'SpeedActionDynamics')
            speedAcDy.attrib = {'dynamicsShape': 'step', 'value': '0', 'dynamicsDimension': 'time'}
            speedAcTar = ET.SubElement(speedAction, 'SpeedActionTarget')
            speedAcTar.attrib = {}
            absTarSpeed = ET.SubElement(speedAcTar, 'AbsoluteTargetSpeed')
            absTarSpeed.attrib = {'value': '%.16e' % speed_list[0]}

            privateAction2_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作2（位置）
            privateAction2_init.attrib = {}
            telepAction = ET.SubElement(privateAction2_init, 'TeleportAction')
            telepAction.attrib = {}
            position_init = ET.SubElement(telepAction, 'Position')
            position_init.attrib = {}
            worldPos_init = ET.SubElement(position_init, 'WorldPosition')  # 采用全局世界坐标对车辆进行定位
            worldPos_init.attrib = {
                'x': '%.16e' % x_list[0], 'y': '%.16e' % y_list[0], 'z': '%.16e' % z_list[0], 'h': '%.16e' % h_list[0], 'p': '%.16e' % p_list[0], 'r': '%.16e' % r_list[0]}
            # Stroy部分对车辆动作（轨迹跟随）的设置
            '''
            OpenSCENARIO中通过StoryBoard展现场景的机制：
            story下设置各个车辆的动作集Act，每个Act下定义车辆对应的操作集ManeuverGroup及其触发器StartTrigger
            ManeuverGroup下定义该操作集的执行者Actor及对应的事件Event
            Event下定义具体的车辆动作Action及其触发器StartTrigger
            【对于一个Action，只有动作集Act的触发器触发并且对应Event的触发器也触发，才会执行该动作Action】
            【Act的触发要早于Event，否则仿真将出错，故下面Act的触发时间为0，Event触发时间后移一帧0.01】
            '''
            act = ET.SubElement(story, 'Act')
            act.attrib = {'name': 'Act_Ego'}
            '''车辆操作组ManeuverGroup设置'''
            maneuGroup = ET.SubElement(act, 'ManeuverGroup')
            maneuGroup.attrib = {'maximumExecutionCount': '1', 'name': 'Sequence_Ego'}
            actor = ET.SubElement(maneuGroup, 'Actors')  # 操作执行者设置
            actor.attrib = {'selectTriggeringEntities': 'false'}
            entityRef = ET.SubElement(actor, 'EntityRef')
            entityRef.attrib = {'entityRef': 'Ego'}
            maneuver = ET.SubElement(maneuGroup, 'Maneuver')  # 具体操作设置（通过事件Event的触发）
            maneuver.attrib = {'name': 'Maneuver1'}
            event = ET.SubElement(maneuver, 'Event')
            event.attrib = {'name': 'Event1', 'priority': 'overwrite'}
            action = ET.SubElement(event, 'Action')  # Event下定义的具体车辆动作
            action.attrib = {'name': 'Action1'}
            privateAction_story = ET.SubElement(action, 'PrivateAction')
            privateAction_story.attrib = {}
            routAction = ET.SubElement(privateAction_story, 'RoutingAction')
            routAction.attrib = {}
            followTraAction = ET.SubElement(routAction, 'FollowTrajectoryAction')  # 路径行为模型为轨迹跟随
            followTraAction.attrib = {}
            trajectory = ET.SubElement(followTraAction, 'Trajectory')  # 轨迹跟随的具体轨迹设置
            trajectory.attrib = {'name': str('Trajectory_' + 'A' + str(count)), 'closed': 'false'}
            shape = ET.SubElement(trajectory, 'Shape')  # 轨迹线型设置（轨迹点之间相连的方式）
            shape.attrib = {}
            polyline = ET.SubElement(shape, 'Polyline')  # 直线相连，highD轨迹为25HZ的采样
            polyline.attrib = {}
            for i in range(len(x_list) - 1):  # 批量填充csv场景中的轨迹点（去除掉初始化点）
                vertex = ET.SubElement(polyline, 'Vertex')
                vertex.attrib = {}
                position_story = ET.SubElement(vertex, 'Position')
                position_story.attrib = {}
                worldPos_story = ET.SubElement(position_story, 'WorldPosition')
                worldPos_story.attrib = {
                    'x': '%.16e' % x_list[i + 1], 'y': '%.16e' % y_list[i + 1], 'z': '%.16e' % z_list[i + 1], 'h': '%.16e' % h_list[i + 1], 'p': '%.16e' % p_list[i + 1], 'r': '%.16e' % r_list[i + 1]}
            timeRef = ET.SubElement(followTraAction, 'TimeReference')  # 轨迹跟随的时间参考为None，即跟随轨迹时忽略时间信息
            timeRef.attrib = {}
            trajecFolloeMode = ET.SubElement(followTraAction, 'TrajectoryFollowingMode')  # 轨迹跟随模式为按照位置移动行动者
            trajecFolloeMode.attrib = {'follingMode': 'position'}
            startTrig_event = ET.SubElement(event, 'StartTrigger')  # Event的触发器StartTrigger
            startTrig_event.attrib = {}
            conditionGroup_event = ET.SubElement(startTrig_event, 'ConditionGroup')
            conditionGroup_event.attrib = {}
            condition_event = ET.SubElement(conditionGroup_event, 'Condition')
            condition_event.attrib = {'name': '', 'delay': '0', 'conditionEdge': 'rising'}  # 触发机制为rising，即condi由0至1时触发
            byValueCondi_event = ET.SubElement(condition_event, 'ByValueCondition')  # 通过变量值判断条件
            byValueCondi_event.attrib = {}
            simulationTimeCondi_event = ET.SubElement(byValueCondi_event, 'SimulationTimeCondition')  # 基于仿真时间触发
            simulationTimeCondi_event.attrib = {'value': '0.01', 'rule': 'greaterThan'}
            '''车辆动作集Act的触发器设置'''
            startTrig_act = ET.SubElement(act, 'StartTrigger')  # 动作集Act触发器设置
            startTrig_act.attrib = {}
            conditionGroup_act = ET.SubElement(startTrig_act, 'ConditionGroup')
            conditionGroup_act.attrib = {}
            condition_act = ET.SubElement(conditionGroup_act, 'Condition')
            condition_act.attrib = {'name': '', 'delay': '', 'conditionEdge': 'rising'}
            byValueCondi_act = ET.SubElement(condition_act, 'ByValueCondition')
            byValueCondi_act.attrib = {}
            simulationTimeCondi_act = ET.SubElement(byValueCondi_act, 'SimulationTimeCondition')
            simulationTimeCondi_act.attrib = {'value': '0', 'rule': 'greaterThan'}
        else:  # 非ego
            # 申明Entities及对应属性
            scenObj = ET.SubElement(entity, 'ScenarioObject')
            scenObj.attrib = {'name': str('A' + str(count))}
            veh = ET.SubElement(scenObj, 'Vehicle')
            veh.attrib = {'name': 'Default_car', 'vehicleCategory': 'car'}
            boundingbox = ET.SubElement(veh, 'BoundingBox')  # 车辆边框属性设置
            center = ET.SubElement(boundingbox, 'Center')  # 车辆中心在【车辆坐标系】中的坐标
            center.attrib = {'x': '%.16e' % 1.5, 'y': '%.16e' % 0, 'z': '%.16e' % 0.9}
            dimension = ET.SubElement(boundingbox, 'Dimensions')
            dimension.attrib = {'width': '%.16e' % 2.1, 'length': '%.16e' % 4.5, 'height': '%.16e' % 1.8}
            controller = ET.SubElement(scenObj, 'ObjectController')
            controller.attrib = {}
            # Init部分对车辆的初始化
            private = ET.Element('Private', {'entityRef': str('A' + str(count))})  # 申明专属对象
            actions.append(private)

            privateAction1_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作1（速度）
            privateAction1_init.attrib = {}
            longitAction = ET.SubElement(privateAction1_init, 'LongitudinalAction')
            longitAction.attrib = {}
            speedAction = ET.SubElement(longitAction, 'SpeedAction')
            speedAction.attrib = {}
            speedAcDy = ET.SubElement(speedAction, 'SpeedActionDynamics')
            speedAcDy.attrib = {'dynamicsShape': 'step', 'value': '0', 'dynamicsDimension': 'time'}
            speedAcTar = ET.SubElement(speedAction, 'SpeedActionTarget')
            speedAcTar.attrib = {}
            absTarSpeed = ET.SubElement(speedAcTar, 'AbsoluteTargetSpeed')
            absTarSpeed.attrib = {'value': '%.16e' % speed_list[count]}

            privateAction2_init = ET.SubElement(private, 'PrivateAction')  # 初始化专属动作2（位置）
            privateAction2_init.attrib = {}
            telepAction = ET.SubElement(privateAction2_init, 'TeleportAction')
            telepAction.attrib = {}
            position_init = ET.SubElement(telepAction, 'Position')
            position_init.attrib = {}
            worldPos_init = ET.SubElement(position_init, 'WorldPosition')  # 采用全局世界坐标对车辆进行定位
            worldPos_init.attrib = {
                'x': '%.16e' % x_list[0], 'y': '%.16e' % y_list[0], 'z': '%.16e' % z_list[0], 'h': '%.16e' % h_list[0], 'p': '%.16e' % p_list[0], 'r': '%.16e' % r_list[0]}
            # Stroy部分对车辆动作（轨迹跟随）的设置
            act = ET.SubElement(story, 'Act')
            act.attrib = {'name': str('Act_' + 'A' + str(count))}
            '''车辆操作组ManeuverGroup设置'''
            maneuGroup = ET.SubElement(act, 'ManeuverGroup')
            maneuGroup.attrib = {'maximumExecutionCount': '1', 'name': str('Squence_' + 'A' + str(count))}
            actor = ET.SubElement(maneuGroup, 'Actors')  # 操作执行者设置
            actor.attrib = {'selectTriggeringEntities': 'false'}
            entityRef = ET.SubElement(actor, 'EntityRef')
            entityRef.attrib = {'entityRef': str('A' + str(count))}
            maneuver = ET.SubElement(maneuGroup, 'Maneuver')  # 具体操作设置（通过事件Event的触发）
            maneuver.attrib = {'name': 'Maneuver1'}
            event = ET.SubElement(maneuver, 'Event')
            event.attrib = {'name': 'Event1', 'priority': 'overwrite'}
            action = ET.SubElement(event, 'Action')  # Event下定义的具体车辆动作
            action.attrib = {'name': 'Action1'}
            privateAction_story = ET.SubElement(action, 'PrivateAction')
            privateAction_story.attrib = {}
            routAction = ET.SubElement(privateAction_story, 'RoutingAction')
            routAction.attrib = {}
            followTraAction = ET.SubElement(routAction, 'FollowTrajectoryAction')  # 路径行为模型为轨迹跟随
            followTraAction.attrib = {}
            trajectory = ET.SubElement(followTraAction, 'Trajectory')  # 轨迹跟随的具体轨迹设置
            trajectory.attrib = {'name': str('Trajectory_' + 'A' + str(count)), 'closed': 'false'}
            shape = ET.SubElement(trajectory, 'Shape')  # 轨迹线型设置（轨迹点之间相连的方式）
            shape.attrib = {}
            polyline = ET.SubElement(shape, 'Polyline')  # 直线相连，highD轨迹为25HZ的采样
            polyline.attrib = {}
            for i in range(len(x_list) - 1):  # 批量填充csv场景中的轨迹点（去除掉初始化点）
                vertex = ET.SubElement(polyline, 'Vertex')
                vertex.attrib = {}
                position_story = ET.SubElement(vertex, 'Position')
                position_story.attrib = {}
                worldPos_story = ET.SubElement(position_story, 'WorldPosition')
                worldPos_story.attrib = {
                    'x': '%.16e' % x_list[i + 1], 'y': '%.16e' % y_list[i + 1], 'z': '%.16e' % z_list[i + 1], 'h': '%.16e' % h_list[i + 1], 'p': '%.16e' % p_list[i + 1], 'r': '%.16e' % r_list[i + 1]}
            timeRef = ET.SubElement(followTraAction, 'TimeReference')  # 轨迹跟随的时间设置
            timeRef.attrib = {}
            trajecFolloeMode = ET.SubElement(followTraAction, 'TrajectoryFollowingMode')
            trajecFolloeMode.attrib = {'follingMode': 'position'}
            startTrig_event = ET.SubElement(event, 'StartTrigger')  # Event的触发器StartTrigger
            startTrig_event.attrib = {}
            conditionGroup_event = ET.SubElement(startTrig_event, 'ConditionGroup')
            conditionGroup_event.attrib = {}
            condition_event = ET.SubElement(conditionGroup_event, 'Condition')
            condition_event.attrib = {'name': '', 'delay': '0', 'conditionEdge': 'rising'}  # 触发机制为rising，即condi由0至1时触发
            byValueCondi_event = ET.SubElement(condition_event, 'ByValueCondition')  # 通过变量值判断条件
            byValueCondi_event.attrib = {}
            simulationTimeCondi_event = ET.SubElement(byValueCondi_event, 'SimulationTimeCondition')  # 基于仿真时间触发
            simulationTimeCondi_event.attrib = {'value': '0.01', 'rule': 'greaterThan'}
            '''车辆动作集Act的触发器设置'''
            startTrig_act = ET.SubElement(act, 'StartTrigger')  # 动作集Act触发器设置
            startTrig_act.attrib = {}
            conditionGroup_act = ET.SubElement(startTrig_act, 'ConditionGroup')
            conditionGroup_act.attrib = {}
            condition_act = ET.SubElement(conditionGroup_act, 'Condition')
            condition_act.attrib = {'name': '', 'delay': '', 'conditionEdge': 'rising'}
            byValueCondi_act = ET.SubElement(condition_act, 'ByValueCondition')
            byValueCondi_act.attrib = {}
            simulationTimeCondi_act = ET.SubElement(byValueCondi_act, 'SimulationTimeCondition')
            simulationTimeCondi_act.attrib = {'value': '0', 'rule': 'greaterThan'}
        count += 1

    # 设置整个StoryBoard的停止器StopTrigger
    conditionGroup_stop = ET.SubElement(stoptrigger, 'ConditionGroup')
    conditionGroup_stop.attrib = {}
    condition_stop = ET.SubElement(conditionGroup_stop, 'Condition')
    condition_stop.attrib = {'name': '', 'delay': '0', 'conditionEdge': 'rising'}  # 触发机制为rising，即condi由0至1时触发
    byEntityCondi_stop = ET.SubElement(condition_stop, 'ByEntityCondition')  # 通过参与对象判断条件
    byEntityCondi_stop.attrib = {}
    triggerEntity = ET.SubElement(byEntityCondi_stop, 'TriggeringEntities')
    triggerEntity.attrib = {'TriggeringEntitiesRule': 'all'}
    entityRef = ET.SubElement(triggerEntity, 'EntityRef')
    entityRef.attrib = {'entityRef': 'Ego'}
    entityCondi = ET.SubElement(byEntityCondi_stop, 'EntityCondition')
    entityCondi.attrib = {}
    reachPositionCondi_stop = ET.SubElement(entityCondi, 'ReachPositionCondition')  # 基于Ego位置触发
    reachPositionCondi_stop.attrib = {'tolerance': '%.16e' % 0.1}  # 设置触发点半径，小于tolerance则触发
    position_stop = ET.SubElement(reachPositionCondi_stop, 'Position')
    position_stop.attrib = {}
    worldPos_stop = ET.SubElement(position_stop, 'WorldPosition')
    worldPos_stop.attrib = {
        'x': '%.16e' % x_stop, 'y': '%.16e' % y_stop, 'z': '%.16e' % z_stop, 'h': '%.16e' % h_stop, 'p': '%.16e' % p_stop, 'r': '%.16e' % r_stop}

    tree = ET.ElementTree(root)
    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return


if __name__ == '__main__':
    '''
    用于测试模块函数，即当该脚本作为一个自定义模块import至其他脚本时，
    _name_变量会在脚本运行时自动变成模块名（如此时nds2xosc），而直接
    运行模块时，其则会变成主函数_main_，并执行下方的测试命令。通过这种
    方式能够防止模块被其他脚本引用时，运行了下方的测试命令
    '''
    nds_path = 'nds.xml'
    xodr_path = 'nds.xodr'
    output_path = 'nds.xosc'
    xosc_write(nds_path, xodr_path, output_path)
