import xml.etree.ElementTree as ET


# TODO：进行TREE的美化，即对根节点下的每个子节点进行相应的换行与缩进操作
def pretty_xml(element, indent, newline, level=0):  # elemnt为传进来的Elment类，参数indent用于缩进，newline用于换行
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


def road_2lanes(road, x, y, h, length):
    '''
    自动补齐OpenD文件下road节点下的路段信息（不涉及交叉口）
    输入road节点、路段参考线的xyhl
    '''
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
    geo.attrib = {'s': '%.16e' % 0, 'x': '%.16e' % x, 'y': '%.16e' % y, 'hdg': '%.16e' % h, 'length': '%.16e' % length}
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
    '''左侧两条行车道'''
    left_lane3 = ET.SubElement(left, 'lane')
    left_lane3.attrib = {'id': '2', 'type': 'driving', 'level': 'false'}
    left_lane2 = ET.SubElement(left, 'lane')
    left_lane2.attrib = {'id': '1', 'type': 'driving', 'level': 'false'}
    '''道路中线（参考线）'''
    center_lane0 = ET.SubElement(center, 'lane')
    center_lane0.attrib = {'id': '0', 'type': 'driving', 'level': 'false'}
    '''右侧两条行车道'''
    right_lane2 = ET.SubElement(right, 'lane')
    right_lane2.attrib = {'id': '-1', 'type': 'driving', 'level': 'false'}
    right_lane3 = ET.SubElement(right, 'lane')
    right_lane3.attrib = {'id': '-2', 'type': 'driving', 'level': 'false'}
    # lane下第二层目录构建（各条车道具体属性设置）——Level 7
    # ***core，需要涉及到highD路段信息手工处理，即根据recodingMeta中的车道边界坐标计算出各车道宽度***
    '''所有车道均含link属性，highD路网中不涉及link连接，故为空'''
    link = ET.Element('link', {})
    left_lane3.append(link)
    left_lane2.append(link)
    center_lane0.append(link)
    right_lane2.append(link)
    right_lane3.append(link)
    '''行车道(含中央分隔带部分）需设置width与roadMark，左车道为左边界，右车道为右边界'''
    left_width3 = ET.SubElement(left_lane3, 'width')
    left_width3.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark3 = ET.SubElement(left_lane3, 'roadMark')
    left_mark3.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    left_width2 = ET.SubElement(left_lane2, 'width')
    left_width2.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    left_mark2 = ET.SubElement(left_lane2, 'roadMark')
    left_mark2.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width2 = ET.SubElement(right_lane2, 'width')
    right_width2.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark2 = ET.SubElement(right_lane2, 'roadMark')
    right_mark2.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'broken', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.15, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    right_width3 = ET.SubElement(right_lane3, 'width')
    right_width3.attrib = {'sOffset': '%.16e' % 0, 'a': '%.16e' % 3, 'b': '%.16e' % 0, 'c': '%.16e' % 0, 'd': '%.16e' % 0}
    right_mark3 = ET.SubElement(right_lane3, 'roadMark')
    right_mark3.attrib = {
        'sOffset': '%.16e' % 0, 'type': 'solid', 'weight': 'standard', 'color': 'standard', 'width': '%.16e' % 0.3, 'laneChange': 'none', 'height': '%.16e' % 0.02}
    # laneMark下第二层目录（标线线型属性设置）——Level 8
    left_line3 = ET.SubElement(left_mark3, 'line')
    left_line3.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}
    left_line2 = ET.SubElement(left_mark2, 'line')
    left_line2.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}
    right_line2 = ET.SubElement(right_mark2, 'line')
    right_line2.attrib = {'length': '%.16e' % 6, 'space': '%.16e' % 12, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.15}
    right_line3 = ET.SubElement(right_mark3, 'line')
    right_line3.attrib = {'length': '%.16e' % 0, 'space': '%.16e' % 0, 'tOffset': '%.16e' % 0, 'sOffset': '%.16e' % 0, 'rule': '', 'width': '%.16e' % 0.3}


def cidas_xodr(output_path):
    '''
    该方法实现了针对CIDAS数据集场景地图的生成
    原OpenDRIVE文件，esmini无法读取，需进行标准化重写；完成重写后OpenD坐标系与OpenS坐标系不一致，需通过轨迹数据反推
    KEY：道路参考线航向角h的反推——当前车道车辆轨迹起点O与终点D之间的航向角（视x坐标小的为起点），利用math.atan2(yd-yo, xd-xo)
    求得航向角
    最后，参考线x=x0, y=y0, h=math.atan(yd-yo, xd-xo)

    Input：行车道标线的y坐标(6个)，OpenDrive输出路径（命名规则，HighD文件夹编号_路网y轴偏移量）
    Output：None
    '''
    root = ET.Element('OpenDRIVE')  # .xodr的根节点
    # TODO：添加子节点，方法二
    # root下第一层目录的构建——Level 2
    header = ET.SubElement(root, 'header')  # root下的子节点header
    header.attrib = {
        'revMajor': '1', 'revMinor': '4', 'name': 'cidas', 'version': '1.00', 'date': '2021-12-23T16:02:00',
        'north': '%.16e' % 0, 'south': '%.16e' % 0, 'east': '%.16e' % 0, 'west': '%.16e' % 0}
    road1 = ET.SubElement(root, 'road')
    road1.attrib = {'name': '', 'length': '%.16e' % 200, 'id': '1', 'junction': '-1'}
    road_2lanes(road1, 19.404439329100114, 22, 0.9730774560827665, 200)
    road2 = ET.SubElement(root, 'road')
    road2.attrib = {'name': '', 'length': '%.16e' % 200, 'id': '2', 'junction': '-1'}
    road_2lanes(road2, 36.449299999999994, 39.79049999999995, -0.59771887071213, 100)

    tree = ET.ElementTree(root)
    pretty_xml(root, '\t', '\n')  # 执行美化方法
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    return


if __name__ == '__main__':
    cidas_xodr('3302170094PCM.xodr')
