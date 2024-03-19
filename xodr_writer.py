# -*- coding: utf-8 -*-
# @Time    : 2021.10.31
# @Author  : Syh
# @Version : 1.0
# @Descrip : 实现对highD数据集路网的OpenDRIVE格式解析，XML格式编写，保存为.xdor
#            目前针对highD数据中的location 2进行编写，路段宽度需在主函数中手动修改

'''
该代码完成了highD数据集中location2的OpenDRIVE路网格式解析
值得注意的是，该路网的坐标轴原点位于道路参考线（中线）的起点位置，而非highD数据集所参照的图片左上角
且OpenDRIVE中的全局坐标系，y轴朝上，与highD相反，故在进行场景的OpenSCENARIO解析时，
车辆坐标需要相应进行坐标轴变换，用OpenDRIVE中左侧道路宽度减去原y坐标，x坐标保持不变
在本例中，对于位于location2中的车辆，y坐标更新公式：y' = 18.175 - y
'''
import xml.etree.ElementTree as ET


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


'''
XML的解析——ET将XML解析为树结构
tree = ET.parse('.xml')  # 读取xml文件
root = tree.getroot()  # 获取树结构的根节点（XML有且只有一个根节点）
* 根节点及其子节点均为Element类型，但可以通过类似列表的方式读取Element[i][j]
* 对于每个节点，包含tag（标签）、attib（属性），可通过Element.tag读取
for nodes_1 in root:  # 第一层子节点遍历
    print(nodes_1)
for nodes_2 in root[index]:  # 第二层子节点遍历
    print(nodes_2)
* 通过上述循环能够大致了解所需编辑的XML文件的基本结构
'''

""" # TODO：添加子节点，方法1
* 方法二适合从零开始构建整个XML树，方法一适合对已有XML进行节点的增加（从操作复杂性角度而言）
road = ET.Element('road', {'name': '', 'length': '%.16e' % 1000, 'id': '1', 'junction': '-1'})
link = ET.Element('link', {})
type = ET.Element('type', {'s': '%.16e' % 0, 'type': 'motorway'})
road.append(link, type)
root.append(road) """


def xodr_2lanes(upper_marking, lower_marking, output_path):
    '''
    该方法实现了针对HighD数据集中双向四车道场景的OpenDrive格式地图的自动生成
    其间场景划分为11条车道，left（绿化带，应急车道，行车道1，行车道2，中央分隔带），center（道路参考线），right（中央分隔带，行车道3，行车道4，应急车道，绿化带）
    其中，应急车道固定3m，绿化带宽度up1-3，行车道1宽度up2-up1，中央分隔带(down1-up3)/2，以此类推

    Input：行车道标线的y坐标(6个)，OpenDrive输出路径（命名规则，HighD文件夹编号_路网y轴偏移量）
    Output：None
    '''
    up1 = upper_marking[0]
    up2 = upper_marking[1]
    up3 = upper_marking[2]
    down1 = lower_marking[0]
    down2 = lower_marking[1]
    down3 = lower_marking[2]

    root = ET.Element('OpenDRIVE')  # .xodr的根节点
    # TODO：添加子节点，方法二
    # root下第一层目录的构建——Level 2
    header = ET.SubElement(root, 'header')  # root下的子节点header
    header.attrib = {
        'revMajor': '1', 'revMinor': '4', 'name': 'highD', 'version': '1.00', 'date': '2021-10-31T21:02:00',
        'north': '%.16e' % 0, 'south': '%.16e' % 0, 'east': '%.16e' % 0, 'west': '%.16e' % 0}
    road = ET.SubElement(root, 'road')
    road.attrib = {'name': '', 'length': '%.16e' % 4000, 'id': '1', 'junction': '-1'}
    # root下第二层目录的构建（road下第一层目录的构建）——Level 3
    link = ET.SubElement(road, 'link')
    link.attrib = {}
    type = ET.SubElement(road, 'type')
    type.attrib = {'s': '%.16e' % 0, 'type': 'motorway'}
    planView = ET.SubElement(road, 'planView')
    planView.attrib = {}
    ele = ET.SubElement(road, 'elevationProfile')
    ele.attrib = {}
    lateral = ET.SubElement(road, 'lateralProfile')
    lateral.attrib = {}
    lanes = ET.SubElement(road, 'lanes')
    lanes.attrib = {}
    # root下第三层目录的构建（road的第二层目录）——Level 4
    geo = ET.SubElement(planView, 'geometry')  # 路段参考线
    geo.attrib = {'s': '%.16e' % 0, 'x': '%.16e' % -2000, 'y': '%.16e' % 0, 'hdg': '%.16e' % 0, 'length': '%.16e' % 4000}
    elevation = ET.SubElement(ele, 'elevation')
    elevation.attrib = {'s': '%.16e' % 0, 'a': '%.16e' % 0, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    laneSec = ET.SubElement(lanes, 'laneSection')
    laneSec.attrib = {'s': '%.16e' % 0}
    # root下第四层/road下的第三层/lanes下第二层/laneSection下第一层目录构建——Level 5
    left = ET.SubElement(laneSec, 'left')
    left.attrib = {}
    center = ET.SubElement(laneSec, 'center')
    center.attrib = {}
    right = ET.SubElement(laneSec, 'right')
    right.attrib = {}
    line = ET.SubElement(geo, 'line')
    line.attrib = {}
    # laneSection下第二层目录构建（即路段左中右个车道布置，core）——Level 6
    '''最左侧（相较于路段参考线而言）绿化带'''
    left_lane5 = ET.SubElement(left, 'lane')
    left_lane5.attrib = {'id': '5', 'type': 'border', 'level': 'false'}
    '''左侧应急车道'''
    left_lane4 = ET.SubElement(left, 'lane')
    left_lane4.attrib = {'id': '4', 'type': 'stop', 'level': 'false'}
    '''左侧两条行车道'''
    left_lane3 = ET.SubElement(left, 'lane')
    left_lane3.attrib = {'id': '3', 'type': 'driving', 'level': 'false'}
    left_lane2 = ET.SubElement(left, 'lane')
    left_lane2.attrib = {'id': '2', 'type': 'driving', 'level': 'false'}
    '''左侧中央分隔带'''
    left_lane1 = ET.SubElement(left, 'lane')
    left_lane1.attrib = {'id': '1', 'type': 'border', 'level': 'false'}
    '''道路中线（参考线）'''
    center_lane0 = ET.SubElement(center, 'lane')
    center_lane0.attrib = {'id': '0', 'type': 'driving', 'level': 'false'}
    '''右侧中央分隔带'''
    right_lane1 = ET.SubElement(right, 'lane')
    right_lane1.attrib = {'id': '-1', 'type': 'border', 'level': 'false'}
    '''右侧两条行车道'''
    right_lane2 = ET.SubElement(right, 'lane')
    right_lane2.attrib = {'id': '-2', 'type': 'driving', 'level': 'false'}
    right_lane3 = ET.SubElement(right, 'lane')
    right_lane3.attrib = {'id': '-3', 'type': 'driving', 'level': 'false'}
    '''右侧应急车道'''
    right_lane4 = ET.SubElement(right, 'lane')
    right_lane4.attrib = {'id': '-4', 'type': 'stop', 'level': 'false'}
    '''最右侧绿化带'''
    right_lane5 = ET.SubElement(right, 'lane')
    right_lane5.attrib = {'id': '-5', 'type': 'border', 'level': 'false'}
    # lane下第二层目录构建（各条车道具体属性设置）——Level 7
    # ***core，需要涉及到highD路段信息手工处理，即根据recodingMeta中的车道边界坐标计算出各车道宽度***
    '''所有车道均含link属性，highD路网中不涉及link连接，故为空'''
    link = ET.Element('link', {})
    left_lane5.append(link)
    left_lane4.append(link)
    left_lane3.append(link)
    left_lane2.append(link)
    left_lane1.append(link)
    center_lane0.append(link)
    right_lane1.append(link)
    right_lane2.append(link)
    right_lane3.append(link)
    right_lane4.append(link)
    right_lane5.append(link)
    '''非行车道仅需设置width'''
    left_width5 = ET.SubElement(left_lane5, 'width')  # 宽度变化由多项式表示Width (ds) = a + b*ds + c*ds² + d*ds³
    left_width5.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up1 - 3), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_width4 = ET.SubElement(left_lane4, 'width')
    left_width4.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_width4 = ET.SubElement(right_lane4, 'width')
    right_width4.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_width5 = ET.SubElement(right_lane5, 'width')
    right_width5.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up1 - 3), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    '''行车道(含中央分隔带部分）需设置width与roadMark，左车道为左边界，右车道为右边界'''
    left_width3 = ET.SubElement(left_lane3, 'width')
    left_width3.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up2 - up1), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark3 = ET.SubElement(left_lane3, 'roadMark')
    left_mark3.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    left_width2 = ET.SubElement(left_lane2, 'width')
    left_width2.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up3 - up2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark2 = ET.SubElement(left_lane2, 'roadMark')
    left_mark2.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    left_width1 = ET.SubElement(left_lane1, 'width')
    left_width1.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % ((down1 - up3) / 2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark1 = ET.SubElement(left_lane1, 'roadMark')
    left_mark1.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width1 = ET.SubElement(right_lane1, 'width')
    right_width1.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % ((down1 - up3) / 2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark1 = ET.SubElement(right_lane1, 'roadMark')
    right_mark1.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width2 = ET.SubElement(right_lane2, 'width')
    right_width2.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (down2 - down1), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark2 = ET.SubElement(right_lane2, 'roadMark')
    right_mark2.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width3 = ET.SubElement(right_lane3, 'width')
    right_width3.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (down3 - down2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark3 = ET.SubElement(right_lane3, 'roadMark')
    right_mark3.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    # laneMark下第二层目录（标线线型属性设置）——Level 8
    left_line3 = ET.SubElement(left_mark3, 'line')
    left_line3.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}
    left_line2 = ET.SubElement(left_mark2, 'line')
    left_line2.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}
    left_line1 = ET.SubElement(left_mark1, 'line')
    left_line1.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}
    right_line1 = ET.SubElement(right_mark1, 'line')
    right_line1.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}
    right_line2 = ET.SubElement(right_mark2, 'line')
    right_line2.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}
    right_line3 = ET.SubElement(right_mark3, 'line')
    right_line3.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}

    tree = ET.ElementTree(root)
    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return


def xodr_3lanes(upper_marking, lower_marking, output_path):
    '''
    该方法实现了针对HighD数据集中双向六车道场景的OpenDrive格式地图的自动生成
    其间场景划分为13条车道，left（绿化带，应急车道，行车道1，行车道2，行车道3，中央分隔带），center（道路参考线），right（中央分隔带，行车道4，行车道5，行车道 6，应急车道，绿化带）
    其中，应急车道固定3m，绿化带宽度up1-3，行车道1宽度up2-up1，中央分隔带(down1-up3)/2，以此类推

    Input：行车道标线的y坐标(8个)，OpenDrive输出路径（命名规则，HighD文件夹编号_路网y轴偏移量）
    Output：None
    '''
    up1 = upper_marking[0]
    up2 = upper_marking[1]
    up3 = upper_marking[2]
    up4 = upper_marking[3]
    down1 = lower_marking[0]
    down2 = lower_marking[1]
    down3 = lower_marking[2]
    down4 = lower_marking[3]
    root = ET.Element('OpenDRIVE')  # .xodr的根节点
    # TODO：添加子节点，方法二
    # root下第一层目录的构建——Level 2
    header = ET.SubElement(root, 'header')  # root下的子节点header
    header.attrib = {
        'revMajor': '1', 'revMinor': '4', 'name': 'highD', 'version': '1.00', 'date': '2021-10-31T21:02:00',
        'north': '%.16e' % 0, 'south': '%.16e' % 0, 'east': '%.16e' % 0, 'west': '%.16e' % 0}
    road = ET.SubElement(root, 'road')
    road.attrib = {'name': '', 'length': '%.16e' % 4000, 'id': '1', 'junction': '-1'}
    # root下第二层目录的构建（road下第一层目录的构建）——Level 3
    link = ET.SubElement(road, 'link')
    link.attrib = {}
    type = ET.SubElement(road, 'type')
    type.attrib = {'s': '%.16e' % 0, 'type': 'motorway'}
    planView = ET.SubElement(road, 'planView')
    planView.attrib = {}
    ele = ET.SubElement(road, 'elevationProfile')
    ele.attrib = {}
    lateral = ET.SubElement(road, 'lateralProfile')
    lateral.attrib = {}
    lanes = ET.SubElement(road, 'lanes')
    lanes.attrib = {}
    # root下第三层目录的构建（road的第二层目录）——Level 4
    geo = ET.SubElement(planView, 'geometry')  # 路段参考线
    geo.attrib = {'s': '%.16e' % 0, 'x': '%.16e' % -2000, 'y': '%.16e' % 0, 'hdg': '%.16e' % 0, 'length': '%.16e' % 4000}
    elevation = ET.SubElement(ele, 'elevation')
    elevation.attrib = {'s': '%.16e' % 0, 'a': '%.16e' % 0, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    laneSec = ET.SubElement(lanes, 'laneSection')
    laneSec.attrib = {'s': '%.16e' % 0}
    # root下第四层/road下的第三层/lanes下第二层/laneSection下第一层目录构建——Level 5
    left = ET.SubElement(laneSec, 'left')
    left.attrib = {}
    center = ET.SubElement(laneSec, 'center')
    center.attrib = {}
    right = ET.SubElement(laneSec, 'right')
    right.attrib = {}
    line = ET.SubElement(geo, 'line')
    line.attrib = {}
    # laneSection下第二层目录构建（即路段左中右个车道布置，core）——Level 6
    '''最左侧（相较于路段参考线而言）绿化带'''
    left_lane6 = ET.SubElement(left, 'lane')
    left_lane6.attrib = {'id': '6', 'type': 'border', 'level': 'false'}
    '''左侧应急车道'''
    left_lane5 = ET.SubElement(left, 'lane')
    left_lane5.attrib = {'id': '5', 'type': 'stop', 'level': 'false'}
    '''左侧三条行车道'''
    left_lane4 = ET.SubElement(left, 'lane')
    left_lane4.attrib = {'id': '4', 'type': 'driving', 'level': 'false'}
    left_lane3 = ET.SubElement(left, 'lane')
    left_lane3.attrib = {'id': '3', 'type': 'driving', 'level': 'false'}
    left_lane2 = ET.SubElement(left, 'lane')
    left_lane2.attrib = {'id': '2', 'type': 'driving', 'level': 'false'}
    '''左侧中央分隔带'''
    left_lane1 = ET.SubElement(left, 'lane')
    left_lane1.attrib = {'id': '1', 'type': 'border', 'level': 'false'}
    '''道路中线（参考线）'''
    center_lane0 = ET.SubElement(center, 'lane')
    center_lane0.attrib = {'id': '0', 'type': 'driving', 'level': 'false'}
    '''右侧中央分隔带'''
    right_lane1 = ET.SubElement(right, 'lane')
    right_lane1.attrib = {'id': '-1', 'type': 'border', 'level': 'false'}
    '''右侧三条行车道'''
    right_lane2 = ET.SubElement(right, 'lane')
    right_lane2.attrib = {'id': '-2', 'type': 'driving', 'level': 'false'}
    right_lane3 = ET.SubElement(right, 'lane')
    right_lane3.attrib = {'id': '-3', 'type': 'driving', 'level': 'false'}
    right_lane4 = ET.SubElement(right, 'lane')
    right_lane4.attrib = {'id': '-4', 'type': 'driving', 'level': 'false'}
    '''右侧应急车道'''
    right_lane5 = ET.SubElement(right, 'lane')
    right_lane5.attrib = {'id': '-5', 'type': 'stop', 'level': 'false'}
    '''最右侧绿化带'''
    right_lane6 = ET.SubElement(right, 'lane')
    right_lane6.attrib = {'id': '-6', 'type': 'border', 'level': 'false'}
    # lane下第二层目录构建（各条车道具体属性设置）——Level 7
    # ***core，需要涉及到highD路段信息手工处理，即根据recodingMeta中的车道边界坐标计算出各车道宽度***
    '''所有车道均含link属性，highD路网中不涉及link连接，故为空'''
    link = ET.Element('link', {})
    left_lane6.append(link)
    left_lane5.append(link)
    left_lane4.append(link)
    left_lane3.append(link)
    left_lane2.append(link)
    left_lane1.append(link)
    center_lane0.append(link)
    right_lane1.append(link)
    right_lane2.append(link)
    right_lane3.append(link)
    right_lane4.append(link)
    right_lane5.append(link)
    right_lane6.append(link)
    '''非行车道仅需设置width'''
    left_width6 = ET.SubElement(left_lane6, 'width')  # 宽度变化由多项式表示Width (ds) = a + b*ds + c*ds² + d*ds³
    left_width6.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up1 - 3), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_width5 = ET.SubElement(left_lane5, 'width')
    left_width5.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_width5 = ET.SubElement(right_lane5, 'width')
    right_width5.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_width6 = ET.SubElement(right_lane6, 'width')
    right_width6.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up1 - 3), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    '''行车道(含中央分隔带部分）需设置width与roadMark，左车道为左边界，右车道为右边界'''
    left_width4 = ET.SubElement(left_lane4, 'width')
    left_width4.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up2 - up1), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark4 = ET.SubElement(left_lane4, 'roadMark')
    left_mark4.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    left_width3 = ET.SubElement(left_lane3, 'width')
    left_width3.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up3 - up2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark3 = ET.SubElement(left_lane3, 'roadMark')
    left_mark3.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    left_width2 = ET.SubElement(left_lane2, 'width')
    left_width2.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (up4 - up3), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark2 = ET.SubElement(left_lane2, 'roadMark')
    left_mark2.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    left_width1 = ET.SubElement(left_lane1, 'width')
    left_width1.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % ((down1 - up4) / 2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark1 = ET.SubElement(left_lane1, 'roadMark')
    left_mark1.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width1 = ET.SubElement(right_lane1, 'width')
    right_width1.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % ((down1 - up4) / 2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark1 = ET.SubElement(right_lane1, 'roadMark')
    right_mark1.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width2 = ET.SubElement(right_lane2, 'width')
    right_width2.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (down2 - down1), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark2 = ET.SubElement(right_lane2, 'roadMark')
    right_mark2.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width3 = ET.SubElement(right_lane3, 'width')
    right_width3.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (down3 - down2), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark3 = ET.SubElement(right_lane3, 'roadMark')
    right_mark3.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width4 = ET.SubElement(right_lane4, 'width')
    right_width4.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % (down4 - down3), 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark4 = ET.SubElement(right_lane4, 'roadMark')
    right_mark4.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    # laneMark下第二层目录（标线线型属性设置）——Level 8
    left_line4 = ET.SubElement(left_mark4, 'line')
    left_line4.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}  # 实线
    left_line3 = ET.SubElement(left_mark3, 'line')
    left_line3.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}  # 虚线
    left_line2 = ET.SubElement(left_mark2, 'line')
    left_line2.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}  # 虚线
    left_line1 = ET.SubElement(left_mark1, 'line')
    left_line1.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}
    right_line1 = ET.SubElement(right_mark1, 'line')
    right_line1.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}
    right_line2 = ET.SubElement(right_mark2, 'line')
    right_line2.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}
    right_line3 = ET.SubElement(right_mark3, 'line')
    right_line3.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}
    right_line4 = ET.SubElement(right_mark4, 'line')
    right_line4.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}

    tree = ET.ElementTree(root)
    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return
