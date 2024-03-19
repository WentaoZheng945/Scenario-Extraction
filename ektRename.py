import os
from tqdm import tqdm


nds_rootpath = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\Scenarios_for_EKT0512\400_NDS"
highD_rootpath = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\Scenarios_for_EKT0512\200_highD"
fig_rootpath = r"C:\Users\15251\Desktop\Scenarios_for_EKT_20220214\Scenarios_for_EKT0512\NDS_fig"
for filepath1, dirnames1, filenames1 in os.walk(fig_rootpath):
    for filename in tqdm(filenames1):
        if '.png' in filename:
            oldName = filename
            newName = oldName[:-4]
            olddir = os.path.join(filepath1, oldName)
            newdir = os.path.join(filepath1, newName)
            os.rename(olddir, newdir)

for filepath, dirnames, filenames in os.walk(highD_rootpath):
    for name in tqdm(dirnames):
        oldname = name
        newname = oldname
        oldDir = os.path.join(filepath, name)
        newDir = os.path.join(filepath, newname)
        os.rename(oldDir, newDir)
        for filepath1, dirnames1, filenames1 in os.walk(newDir):
            for filename in filenames1:
                if '.xosc' in filename:
                    oldName = filename
                    newName = oldName
                    olddir = os.path.join(filepath1, oldName)
                    newdir = os.path.join(filepath1, newName)
                    os.rename(olddir, newdir)
    break
