import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
OUTPUT_DIR = "../imageデータ/Z_change_協力率変遷"
INPUT_DIR = "../../../../OneDrive/ドキュメント/ゼミ/M1"
OUTPUT_FILE = "image50000協力率_douki_Z=90.csv"
INPUT_FILE = "image50000協力率_douki_Z=90.png"

# CSVファイルの読み込み
file_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
data = pd.read_csv(file_path)

# DataFrameの中身を確認（必要に応じてコメントアウト）

print(len(data))

"""if len(data) < 100000000:
    #dataに100000000行まで0を追加
    additional_rows = 100000000 - len(data)
    additional_data = pd.DataFrame(0, index=np.arange(additional_rows), columns=data.columns)
    data = pd.concat([data, additional_data], ignore_index=True)"""


# グラフの作成
plt.figure(figsize=(10, 6))
plt.plot(data.index, data['Cooperation Rate'], linestyle='-', color='b')
#plt.plot(data.index, linestyle='-', color='b')


# グラフの装飾
#plt.title("Cooperation Rate Over Time")
plt.xlabel("MCS", fontsize = 15)
plt.ylabel("Ρc",fontsize=15)
plt.ylim(0.0, 1.0)  # y軸の範囲を設定
plt.xscale('log')
plt.xticks([100, 1000, 10000, 10**5, 10**6, 10**7,10**8],
           ['10^-2', '10^-1', '1', '10', '100', '1000','10000'])
#plt.xticks([400, 4000, 40000, 400000, 4000000, 40000000],
#           ['10^-2', '10^-1', '1', '10', '10^2', '10^3'])
plt.xlim(left=100)
#plt.legend(labels=['normal', 'only punish', 'only reward','reward punish'])
plt.grid(True)
# グラフを保存
os.makedirs(INPUT_DIR, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(INPUT_DIR, INPUT_FILE)
plt.savefig(file_path)  # 保存

# グラフの表示
plt.show()

"""
# DataFrameの中身を確認（必要に応じてコメントアウト）
#print(data.head())
alpha_values = [0.2, 0.3, 0.4, 0.5]
beta_values  = [1, 1.5, 2, 2.5, 3]
tau_values = [1, 2, 3]
R_values = [round(i, 3) for i in np.arange(2.75, 5.25, 0.25)]
for alpha in alpha_values:
    folder_name = "データ8"  # フォルダ名
    file_name = f"格子アルファ{alpha}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    dataa = pd.read_csv(file_path)

    #plt.plot(R_values,data, label = f"group_alpha={alpha}")

    folder_name = "データ8"  # フォルダ名
    file_name = f"個人アルファ{alpha}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    datab = pd.read_csv(file_path)

    plt.plot(R_values,dataa, label = f"Individual_alpha={alpha}")
    plt.plot(R_values,datab, label = f"Individual_alpha={alpha}")
# グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="α Values")
folder_name = "グラフ8"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, 'アルファ合体.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for beta in beta_values:
    folder_name = "データ8"  # フォルダ名
    file_name = f"個人ベータ{beta}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)
    plt.plot(R_values, data, label = f"beta={beta}")
    # グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="β Values")
folder_name = "グラフ8"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '個人ベータ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for tau in tau_values:
    folder_name = "データ8"  # フォルダ名
    file_name = f"個人タウ{tau}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)

    plt.plot(R_values, data, label = f"tau={tau}")
    # グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="τ Values")
folder_name = "グラフ8"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '個人タウ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for alpha in alpha_values:
    folder_name = "データ5"  # フォルダ名
    file_name = f"格子罰は罰アルファ{alpha}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)

    plt.plot(R_values,data, label = f"alpha={alpha}")
# グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="α Values")
folder_name = "グラフ5"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '格子罰は罰アルファ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for beta in beta_values:
    folder_name = "データ4"  # フォルダ名
    file_name = f"格子全員にベータ{beta}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)
    plt.plot(R_values, data, label = f"beta={beta}")
    # グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="β Values")
folder_name = "グラフ4"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '格子ベータ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for beta in beta_values:
    folder_name = "データ5"  # フォルダ名
    file_name = f"格子全員に罰は罰ベータ{beta}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)

    plt.plot(R_values, data, label = f"beta={beta}")
    # グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="β Values")
folder_name = "グラフ5"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '格子罰は罰ベータ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for tau in tau_values:
    folder_name = "データ4"  # フォルダ名
    file_name = f"格子全員にタウ{tau}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)

    plt.plot(R_values, data, label = f"tau={tau}")
    # グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="τ Values")
folder_name = "グラフ4"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '格子タウ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""

"""for tau in tau_values:
    folder_name = "データ5"  # フォルダ名
    file_name = f"0.3格子全員に罰は罰タウ{tau}.csv"  # ファイル名
    # フルパスを作成
    file_path = os.path.join(folder_name, file_name)
    #file_path = '8neighbors10000回_R3.5_a0.1_b2.5_t2_G8.csv'  # ファイル名を指定
    data = pd.read_csv(file_path)

    plt.plot(R_values, data, label = f"tau={tau}")
    # グラフの装飾
plt.xlabel("R", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
plt.legend(title="τ Values")
folder_name = "グラフ5"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '0.3格子全員に罰は罰タウ.png')
plt.savefig(file_path)  # 保存
plt.show(block=False)
time.sleep(1)
plt.close()"""


"""plt.plot(R_values,data)
# グラフの装飾
plt.xlabel("τ", fontsize=12)
plt.ylabel("Cooperation Rate (ρc)", fontsize=12)
plt.title("Cooperation Rate vs τ", fontsize=14)
plt.ylim(0, 1)  # 協力率の範囲
plt.grid(True)
folder_name = "グラフ2"
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, '修正3Rのみ_α0.3_β2.5_τ2.png')
plt.savefig(file_path)  # 保存
plt.show()"""


"""# グラフの作成
plt.figure(figsize=(10, 6))
plt.plot(data.index, data['Cooperation Rate'], linestyle='-', color='b', label='Cooperation Rate')

# グラフの装飾
plt.title("Cooperation Rate Over Time")
plt.xlabel("Index (Step)")
plt.ylabel("Cooperation Rate")
plt.ylim(0.0, 1.0)  # y軸の範囲を設定
#plt.xscale('log')
#plt.xticks([4, 40, 400, 4000],
#           ['10^-1','1', '10^1', '10^2'])
#plt.xticks([400, 4000, 40000, 200000, 2000000, 20000000],
#           ['10^-2', '10^-1', '1', '10', '10^2', '10^3'])
#plt.xlim(left=400)
plt.legend()
plt.grid(True)
folder_name = "グラフc言語" #  フォルダ名
file_name = "フリーネットワーク　1000ステップ　pg.png"  # ファイル名   
os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(folder_name, file_name)
plt.savefig(file_path)  # 保存
plt.show()"""




"""import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# CSVファイルの読み込み
file_path = 'cooperation_rate_data_reward1000回.csv'  # ファイル名を指定
data = pd.read_csv(file_path)

# ステップ数を新たに列として追加
data['Step'] = data.index + 1

# 対数間隔でサンプリングするステップ数を生成
log_steps = np.unique(np.logspace(-2, 3, num=100, base=10).astype(int))

# サンプリングデータを抽出
sampled_data = data[data['Step'].isin(log_steps)]

# グラフの作成
plt.figure(figsize=(10, 6))
plt.plot(sampled_data['Step'], sampled_data['Cooperation Rate'], marker='o', linestyle='-', color='b', label='Cooperation Rate')

# x軸を対数スケールに設定
plt.xscale('log')

# グラフの装飾
plt.title("Cooperation Rate Over Logarithmic Steps")
plt.xlabel("Steps (log scale)")
plt.ylabel("Cooperation Rate")
plt.ylim(0.0, 1.0)  # y軸の範囲を設定
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.legend()
plt.savefig('glaph_reward1000.png')

# グラフを表示
plt.show()"""



"""import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# CSVファイルの読み込み
file_path = 'cooperation_rate_data_reward1000回.csv'  # ファイル名を指定
data = pd.read_csv(file_path)

# ステップの指定
steps = [400, 4000, 40000, 400000, 4000000]

# 各ステップに対応するデータを抽出
selected_data = data.iloc[np.array(steps) - 1]  # インデックスを1-basedに合わせるため、1を引く

# X軸の値（指定されたステップ）
x_values = steps

# グラフの作成
plt.figure(figsize=(10, 6))
plt.plot(x_values, selected_data['Cooperation Rate'], linestyle='-', color='b', label='Cooperation Rate')

# グラフの装飾
plt.title("Cooperation Rate at Selected Steps")
plt.xlabel("Steps")
plt.ylabel("Cooperation Rate")
plt.ylim(0.0, 1.0)  # y軸の範囲を設定
plt.grid(True, linestyle="--", linewidth=0.5)
plt.legend()
plt.xscale('log')
plt.savefig('glaph_reward1000.png')

# グラフを表示
plt.show()"""
