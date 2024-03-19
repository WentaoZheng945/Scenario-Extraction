import matplotlib.pyplot as plt
from xml.etree.ElementTree import ElementTree


class ParseXodr:
    '''对OpenDRIVER文件进行解析，实现路网绘制'''
    def __init__(self, input_path):
        '''初始化，读取road根节点'''
        tree = ElementTree()
        tree.parse(input_path)
        root = tree.getroot()
        self.road = root.find('road')       

    def getReferline(self):
        '''获取参考线信息
        以字典形式储存至self.referline'''
        referline = self.road.find('planView')
        geoInfo = referline.find('geometry')
        referline = geoInfo.attrib
        return referline

    def getLanes(self):
        '''获取车道信息
        以列表形式储存各车道Element'''
        lanes = self.road.find('lanes')
        laneSection = lanes.find('laneSection')
        leftLanes = laneSection.find('left')
        # 左车道组倒序，从中心线向外排序
        lanes = leftLanes.findall('lane')
        lanes.reverse()
        rightLanes = laneSection.find('right')
        # 右车道正序即可，从中心线向外
        lanes.extend(rightLanes.findall('lane'))
        return lanes


def plotOpenD(input_path):
    xodr = ParseXodr(input_path)
    # 获取参考线属性
    referline = xodr.getReferline()
    x_start = eval(referline['x'])
    x_end = eval(referline['length']) + x_start
    # 获取各车道信息
    ids, info, width, left, right = [], [], [], 0, 0
    lanes = xodr.getLanes()
    for item in lanes:
        infos = item.attrib
        if infos['type'] == 'driving':
            info.append(1)
        else:
            info.append(infos['type'])
        ids.append(int(infos['id']))
        if int(infos['id']) > 0:  # 左车道组
            w = eval(item.find('width').attrib['a'])
            width.append(left + w)
            left += w
        else:  # 右车道组
            w = eval(item.find('width').attrib['a'])
            width.append(right - w)
            right -= w
    # 绘制道路
    plt.figure(1)
    for i in range(len(width)):
        if info[i] != 1:
            plt.axhline(width[i], c='black', ls='-')
            if info[i] == 'border' and ids[i] > 0:
                if ids[i] == 1:  # 中间分隔带
                    plt.axhspan(ymin=0, ymax=width[i], facecolor="g", alpha=0.3)
                else:  # 绿化带
                    plt.axhspan(ymin=width[i - 1], ymax=width[i], facecolor="g", alpha=0.3)
            elif info[i] == 'border' and ids[i] < 0:
                if ids[i] == -1:
                    plt.axhspan(ymin=width[i], ymax=0, facecolor="g", alpha=0.3)
                else:
                    plt.axhspan(ymin=width[i], ymax=width[i - 1], facecolor="g", alpha=0.3)
        else:
            if info[i + 1] == 1:  # 行车道
                plt.axhline(width[i], c='black', ls='--')
            else:  # 紧急车道
                plt.axhline(width[i], c='black', ls='-')
    plt.xlim(x_start, x_end)
    plt.show()
    return


if __name__ == '__main__':
    plotOpenD('highD_1.xodr')
