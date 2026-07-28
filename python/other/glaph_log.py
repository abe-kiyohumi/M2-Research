import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
import zipfile
import io

OUTPUT_DIR = "../imageデータ/Z_change_協力率変遷/+3+1-3-1+5+3"
INPUT_DIR = "../imageグラフ/Z_change_協力率変遷/+3+1-3-1+5+3"
INPUT_FILE = "image10000協力率_まとめ_Z=50_r=3.0.png"
ZIP_FILE = "../imageデータ/Z_b_change報酬罰/+3+1-3-1+5+3/image_Z=50_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.zip"
file_names = ['image_Z=50_b=0_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv','image_Z=50_b=0.2_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv','image_Z=50_b=0.4_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv',
              'image_Z=50_b=0.6_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv','image_Z=50_b=0.6_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv','image_Z=50_b=0.8_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv',
              'image_Z=50_b=1_r=3.0_α=0.1_β=1.0_+3+1-3-1+5+3_omega.csv'] 

"""OUTPUT_DIR = "../shunningデータ/Z_change_協力率変遷"
INPUT_DIR = "../shunningグラフ/Z_change_協力率変遷"
INPUT_FILE = "shunning15000協力率_まとめ_100間隔.png"
file_names = ['shunning15000協力率変遷_traditional.csv','shunning15000協力率_douki_Z=60.csv', 'shunning15000協力率_douki_Z=70.csv', 'shunning15000協力率_douki_Z=80.csv', 'shunning15000協力率_douki_Z=90.csv'] """

"""OUTPUT_DIR = "../simpleデータ/Z_change_協力率変遷"
INPUT_DIR = "../simpleグラフ/Z_change_協力率変遷"
INPUT_FILE = "simple15000協力率_まとめ_1000間隔.png"
file_names = ['simple15000協力率変遷_traditional.csv','simple15000協力率_douki_Z=60.csv', 'simple15000協力率_douki_Z=70.csv', 'simple15000協力率_douki_Z=80.csv', 'simple15000協力率_douki_Z=90.csv'] """

"""OUTPUT_DIR = "../sternデータ/Z_change_協力率変遷"
INPUT_DIR = "../sternグラフ/Z_change_協力率変遷"
INPUT_FILE = "stern15000協力率_まとめ_1000間隔.png"
file_names = ['stern15000協力率変遷_traditional.csv','stern15000協力率_douki_Z=60.csv', 'stern15000協力率_douki_Z=70.csv', 'stern15000協力率_douki_Z=80.csv', 'stern15000協力率_douki_Z=90.csv']  """

"""OUTPUT_DIR = "../報酬_罰_データ/Z_change_協力率変遷"
INPUT_DIR = "../報酬_罰_グラフ/b_change_協力率変遷"
INPUT_FILE = f"報酬_罰_b_change_Z=98_r=3.0_θかける_KDnasi.png"
ZIP_FILE = "../報酬_罰_データ/Z_change_協力率変遷/punish_reawrd_Z=98_r=3.0_α=0.1_β=1.0_θかける_KDnasi.zip"
file_names = ['punish_reward_Z=98_b=0.2_r=3.0_α=0.1_β=1.0.csv', 
              'punish_reward_Z=98_b=0.4_r=3.0_α=0.1_β=1.0.csv', 
              'punish_reward_Z=98_b=0.6_r=3.0_α=0.1_β=1.0.csv', 
              'punish_reward_Z=98_b=0.8_r=3.0_α=0.1_β=1.0.csv', 
              'punish_reward_Z=98_b=1.0_r=3.0_α=0.1_β=1.0.csv'] """

#OUTPUT_FILE = "image50000協力率_douki_Z=90.csv"
#INPUT_FILE = "shunning15000協力率_まとめ_1000間隔.png"

# ファイル名リスト
#file_names = ['shunning15000協力率変遷_traditional.csv','shunning15000協力率変遷_douki_Z=60.csv', 'shunning15000協力率変遷_douki_Z=70.csv', 'shunning15000協力率変遷_douki_Z=80.csv', 'shunning15000協力率変遷_douki_Z=90.csv']

# グラフの設定
plt.figure(figsize=(10, 6))

# 各ファイルのデータを読み込み、プロット
"""
sample_interval = 10
for file_name in file_names:
    # フルパスを作成
    print(file_name)
    file_path = os.path.join(OUTPUT_DIR, file_name)
    data = pd.read_csv(file_path, dtype={'Cooperation Rate': np.float32})
    #sample_data = data.iloc[::sample_interval, :]
    #plt.plot(sample_data.index, sample_data['Cooperation Rate'])
    plt.plot(data.index, data['Cooperation Rate'])

    #data = pd.read_csv(file_path)
    #plt.plot(data.index, data['Cooperation Rate']) 

    #data_plot = data.sample(frac=0.001, random_state=42)
    #plt.plot(data_plot.index,data_plot['Cooperation Rate']) """
"""    if os.path.exists(file_path):  # ファイルが存在するか確認
        data = pd.read_csv(OUTPUT_DIR, file_name, header=None)  # ステップ数がないため、列名なしで読み込む
        data.columns = ['Cooperation Rate']  # 列名を設定
        plt.plot(data.index, data['Cooperation Rate'], label=file_name.split('.')[0])
    else:
        print(f"ファイル {file_name} が見つかりません。") """

#ZIPファイル解凍
sample_inierval = 1000
try:
    # 1. zipfile.ZipFile を 'r' (読み込み) モードで開く
    with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
        # 2. ZIPファイル内に目的のファイルが存在するかチェック
        for file_name in file_names:
            if file_name in zf.namelist():
                print(file_name)
                with zf.open(file_name) as file:
                    # 3. ファイルを読み込み、DataFrameに変換
                    data = pd.read_csv(file)
                    plt.plot(data.index, data['Cooperation Rate'])
                
            else:
                print(f"❌ エラー: ZIPファイル内に {file_name} が見つかりません。")
                print(f"ファイルリスト: {zf.namelist()}")

except FileNotFoundError:
    print(f"❌ エラー: ZIPファイルが見つかりません。パスを確認してください: {ZIP_FILE}")
except Exception as e:
    print(f"❌ その他のエラーが発生しました: {e}")

# グラフの装飾
#plt.title("Cooperation Rate Comparison")
plt.xlabel("MCS",fontsize=20)
plt.ylabel("Ρc",fontsize=20)
plt.ylim(0, 1)
plt.xlim(right=100000)
plt.xscale('log')
plt.title("Z=50 r=3.0",fontsize=20)
#plt.xticks([1, 10**2, 10**3, 10**4, 10**5, 10**6],
#           ['1', '10^2', '10^3', '10^4', '10^5', '10^6'])
#plt.xticks([100, 1000, 10000, 10**5, 10**6, 10**7,10**8],
#           ['10^-2', '10^-1', '1', '10', '100', '1000','10000'])
plt.xticks([10**5, 10**6, 10**7, 10**8],
           ['10','100', '1000', '10000'])
plt.xlim(left=1)
#plt.legend(labels=['Z=50','Z=60','Z=70','Z=80', 'Z=90','Z=95', 'Z=98'],fontsize=20)
plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6', 'b=0.8','b=1.0'],fontsize=20)
#plt.title("image scoring reputation model",fontsize=25)
#plt.legend(labels=['β = 2.5','β = 2', 'β = 1.5'],fontsize=25)
#plt.legend(labels=['α = 0.1','α = 0.2', 'α = 0.3'],fontsize=20)
#plt.legend(labels=['R = 3.5','R = 4', 'R = 4.5'],fontsize=20)
#plt.legend(labels=['normal','only punish', 'only reward', 'only reward random','reward punish', 'reward punish random', '8neighbors'])
plt.grid(True)

# グラフを保存
#os.makedirs(INPUT_DIR, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(INPUT_DIR, INPUT_FILE)
#plt.show()
plt.savefig(file_path)  # 保存
plt.show()

# グラフの表示
#plt.show()
#plt.close()
