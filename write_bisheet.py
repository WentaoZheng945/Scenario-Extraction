import pandas as pd
import os
from tqdm import tqdm
import xlrd


def get_info(vals, xlsx_path):
    info = xlrd.open_workbook(xlsx_path).sheets()[0]
    vals[0].append(info.cell(1, 1).value)
    vals[1].append(info.cell(3, 1).value)
    vals[2].append(info.cell(3, 2).value)
    vals[3].append(info.cell(3, 4).value)
    vals[4].append(info.cell(3, 6).value)
    vals[5].append(info.cell(5, 1).value)
    vals[6].append(info.cell(5, 2).value)
    vals[7].append(info.cell(6, 1).value)
    vals[8].append(info.cell(8, 1).value)
    vals[9].append(info.cell(8, 2).value)
    vals[10].append(info.cell(8, 3).value)
    vals[11].append(info.cell(8, 4).value)
    vals[12].append(info.cell(8, 5).value)
    vals[13].append(info.cell(8, 6).value)
    vals[14].append(info.cell(8, 7).value)
    return


xlsx_path = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\400_NDS\15_NDS_demo\original\1cutin1\1cutin1info.xlsx"
info = xlrd.open_workbook(xlsx_path).sheets()[0]
vals = [[] for _ in range(15)]
tag = ['场景ID']
tag.append(info.cell(1, 0).value)
tag.append(info.cell(2, 1).value)
tag.append(info.cell(2, 2).value)
tag.append(info.cell(2, 4).value)
tag.append(info.cell(2, 6).value)
tag.append(info.cell(4, 1).value)
tag.append(info.cell(4, 2).value)
tag.append(info.cell(6, 0).value)
tag.append(info.cell(7, 1).value)
tag.append(info.cell(7, 2).value)
tag.append(info.cell(7, 3).value)
tag.append(info.cell(7, 4).value)
tag.append(info.cell(7, 5).value)
tag.append(info.cell(7, 6).value)
tag.append(info.cell(7, 7).value)

ans = []
nds_root = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\NDS"
for root, dirs, files in os.walk(nds_root):
    for name in tqdm(dirs):
        ans.append(str(name))
        scenario_path = os.path.join(root, name)
        for root1, dirs1, files1 in os.walk(scenario_path):
            for file in files1:
                if '.xlsx' in file:
                    test_file = os.path.join(root1, file)
                    get_info(vals, test_file)
    break

df = pd.DataFrame(columns=tag)
df['场景ID'] = ans
for i in range(len(vals)):
    df[str(tag[i + 1])] = vals[i]
target_path = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\NDS_info.csv"
df.to_csv(target_path, index=None, encoding='gbk')
