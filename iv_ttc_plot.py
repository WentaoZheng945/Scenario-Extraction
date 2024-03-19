import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

""" with open('ttc.txt', 'r') as f:
    str = f.read().splitlines()
ttc = []
mttc = []
for i in str:
    list = i.split(',')
    mttc.append(round(float(list[0]), 1))
    ttc.append(float(list[-1]))
mttc = [i-0.01 for i in mttc]
plt.hist(mttc, 25, range=[0, 10], alpha=0.5, edgecolor='black', label='MTTC')
plt.hist(ttc, 25, range=[0, 10], alpha=0.5, edgecolor='black', label='TTC')
plt.legend()
plt.savefig('../ttc.png', dpi=600)
plt.show() """

df = pd.read_csv('index.csv')
grouped_task = df.groupby(['task'], sort=False)
for group_id, rows in grouped_task:
    if group_id == 'car_following':
        num_follow = rows['num'].values.tolist()
    elif group_id == 'cut_in':
        num_cut = rows['num'].values.tolist()
    elif group_id == 'lane_changing':
        num_change = rows['num'].values.tolist()
""" plt.hist(num_follow, 13, range=[2, 14], alpha=0.3, edgecolor='black', density=True, label='Car_following')
plt.hist(num_cut, 13, range=[2, 14], alpha=0.3, edgecolor='black', density=True, label='Cut_in')
plt.hist(num_change, 13, range=[2, 14], alpha=0.3, edgecolor='black', density=True, label='Lane_changing')
plt.legend()
plt.show() """
sns.kdeplot(data=num_follow, label="Car_following", shade=True)
sns.kdeplot(data=num_cut, label="Cut_in", shade=True)
sns.kdeplot(data=num_change, label="Lane_changing", shade=True)
plt.legend()
plt.savefig('../num.png', dpi=600)
plt.show()
