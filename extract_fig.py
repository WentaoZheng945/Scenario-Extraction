import zipfile
from PIL import Image
import os
from tqdm import tqdm


def get_fig(test_file, img_name):
    new_file = test_file.replace(".xlsx", ".zip")
    os.rename(test_file, new_file)
    number = 1
    saveDir = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\Scenarios_for_EKT0512\NDS_fig"
    azip = zipfile.ZipFile(new_file)
    namelist = (azip.namelist())
    # print(namelist)
    for idx in range(0, len(namelist)):
        if 'media' in namelist[idx] and ('png' in namelist[idx] or 'temp' in namelist[idx]):
            img_name = os.path.join(saveDir, img_name) + '.png'
            f = azip.open(namelist[idx])
            img = Image.open(f)
            img = img.convert("RGB")
            img.save(img_name)
            number += 1
    azip.close()
    return


if __name__ == '__main__':
    nds_root = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\NDS"
    fig_root = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\NDS_fig"
    ans, figs, scenario = [], [], []
    for root, dirs, files in os.walk(fig_root):
        for fig in files:
            figs.append(fig)
            # figs.append(fig.split('.')[0])
        break
    for root, dirs, files in os.walk(nds_root):
        for i in dirs:
            scenario.append(i + '.png')
        break
    print(len(figs), len(scenario), len(list(set(figs))))
    print([i for i in figs if i not in scenario])
    for name in tqdm(ans):
        scenario_path = os.path.join(nds_root, name)
        for root1, dirs1, files1 in os.walk(scenario_path):
            for file in files1:
                if '.xlsx' in file:
                    test_file = os.path.join(root1, file)
                    get_fig(test_file, name)
    
