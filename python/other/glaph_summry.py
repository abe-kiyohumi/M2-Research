import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time

OUTPUT_DIR = "../imageデータ/Z_b_change/+5+1-5-1+8+3"
INPUT_DIR = "../imageグラフ/Z_b_change_罰入り/+5+1-5-1+8+3"
INPUT_FILE1 = "image協力率_まとめ_1000間隔_Z=50.png"
INPUT_FILE2 = "image協力率_まとめ_1000間隔_Z=60.png"
INPUT_FILE3 = "image協力率_まとめ_1000間隔_Z=70.png"
INPUT_FILE4 = "image協力率_まとめ_1000間隔_Z=80.png"
INPUT_FILE5 = "image協力率_まとめ_1000間隔_Z=90.png"
INPUT_FILE6 = "image協力率_まとめ_1000間隔_Z=95.png"
INPUT_FILE7 = "image協力率_まとめ_1000間隔_Z=98.png" 

INPUT_FILE8 = "image協力率_まとめ_1000間隔_b=0.png"
INPUT_FILE9 = "image協力率_まとめ_1000間隔_b=0.2.png"
INPUT_FILE10 = "image協力率_まとめ_1000間隔_b=0.4.png"
INPUT_FILE11 = "image協力率_まとめ_1000間隔_b=0.6.png"
INPUT_FILE12 = "image協力率_まとめ_1000間隔_b=0.8.png"
INPUT_FILE13 = "image協力率_まとめ_1000間隔_b=1.0.png"

file_names1 = ['image10000協力率変遷_Z=50_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=50_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=50_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=50_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=50_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=50_b=1.0_+5+1-5-1+8+3.csv'] 
file_names2 = ['image10000協力率変遷_Z=60_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=60_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=1.0_+5+1-5-1+8+3.csv'] 
file_names3 = ['image10000協力率変遷_Z=70_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=70_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=1.0_+5+1-5-1+8+3.csv'] 
file_names4 = ['image10000協力率変遷_Z=80_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=80_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=1.0_+5+1-5-1+8+3.csv'] 
file_names5 = ['image10000協力率変遷_Z=90_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=90_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=90_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=90_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=90_b=1.0_+5+1-5-1+8+3.csv'] 
file_names6 = ['image10000協力率変遷_Z=95_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=95_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=1.0_+5+1-5-1+8+3.csv'] 
file_names7 = ['image10000協力率変遷_Z=98_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=98_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=1.0_+5+1-5-1+8+3.csv'] 

file_names8 = ['image10000協力率変遷_Z=50_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0_+5+1-5-1+8+3.csv'] 
file_names9 = ['image10000協力率変遷_Z=50_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.2_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.2_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.2_+5+1-5-1+8+3.csv'] 
file_names10 = ['image10000協力率変遷_Z=50_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.4_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.4_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.4_+5+1-5-1+8+3.csv'] 
file_names11 = ['image10000協力率変遷_Z=50_b=0.6_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.6_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.6_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.6_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=0.6_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.6_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.6_+5+1-5-1+8+3.csv'] 
file_names12 = ['image10000協力率変遷_Z=50_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=0.8_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=0.8_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=0.8_+5+1-5-1+8+3.csv'] 
file_names13 = ['image10000協力率変遷_Z=50_b=1.0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=60_b=1.0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=70_b=1.0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=80_b=1.0_+5+1-5-1+8+3.csv'
              ,'image10000協力率変遷_Z=90_b=1.0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=95_b=1.0_+5+1-5-1+8+3.csv', 'image10000協力率変遷_Z=98_b=1.0_+5+1-5-1+8+3.csv'] 
files = [file_names1, file_names2, file_names3, file_names4, file_names5, file_names6, file_names7,
         file_names8, file_names9, file_names10, file_names11, file_names12, file_names13] 

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
INPUT_DIR = "../報酬_罰_グラフ/Z_change_協力率変遷"
INPUT_FILE = "報酬_罰_15000協力率_まとめ_1000間隔_r=2.0.png"
file_names = ['image10000協力率変遷_douki_Z=30_r=2.0.csv','image10000協力率変遷_douki_Z=50_r=2.0_個別.csv', 
              'image10000協力率変遷_douki_Z=70_r=2.0.csv', 'image10000協力率変遷_douki_Z=90_r=2.0.csv', 'image10000協力率変遷_douki_Z=95_r=2.0.csv', 'image10000協力率変遷_douki_Z=98_r=2.0.csv'] """

#OUTPUT_FILE = "image50000協力率_douki_Z=90.csv"
#INPUT_FILE = "shunning15000協力率_まとめ_1000間隔.png"

# ファイル名リスト
#file_names = ['shunning15000協力率変遷_traditional.csv','shunning15000協力率変遷_douki_Z=60.csv', 'shunning15000協力率変遷_douki_Z=70.csv', 'shunning15000協力率変遷_douki_Z=80.csv', 'shunning15000協力率変遷_douki_Z=90.csv']

# グラフの設定

# 各ファイルのデータを読み込み、プロット
sample_inierval = 1000
i = 1
for file_names in files:
    plt.figure(figsize=(10, 6))
    for file_name in file_names:
        # フルパスを作成
        print(file_name)
        file_path = os.path.join(OUTPUT_DIR, file_name)
        data = pd.read_csv(file_path, dtype={'Cooperation Rate': np.float32})
        sample_data = data.iloc[::sample_inierval, :]
        plt.plot(sample_data.index, sample_data['Cooperation Rate'])
    

    # グラフの装飾
    #plt.title("Cooperation Rate Comparison")
    plt.xlabel("MCS",fontsize=20)
    plt.ylabel("Ρc",fontsize=20)
    plt.ylim(0, 1)
    plt.xscale('log')
    #plt.xticks([1, 10**2, 10**3, 10**4, 10**5, 10**6],
    #           ['1', '10^2', '10^3', '10^4', '10^5', '10^6'])
    plt.xticks([10000, 10**5, 10**6, 10**7,10**8],
            ['1', '10', '100', '1000','10000'])
    plt.xlim(left=100)
    if file_names == files[0]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=50")
        FILE_NAME = f"Z=50_r=3.6"
    elif file_names == files[1]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=60")
        FILE_NAME = f"Z=60_r=3.6"
    elif file_names == files[2]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=70")
        FILE_NAME = f"Z=70_r=3.6"
    elif file_names == files[3]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=80")
        FILE_NAME = f"Z=80_r=3.6"
    elif file_names == files[4]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=90")
        FILE_NAME = f"Z=90_r=3.6"
    elif file_names == files[5]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=95")
        FILE_NAME = f"Z=95_r=3.6"
    elif file_names == files[6]:
        plt.legend(labels=['b=0','b=0.2','b=0.4','b=0.6','b=0.8','b=1.0'],fontsize=20)
        plt.title("Z=98")
        FILE_NAME = f"Z=98_r=3.6"
    elif file_names == files[7]:
        plt.legend(labels=['Z=50','Z=60','Z=70','Z=80','Z=90','Z=95','Z=98'],fontsize=20)
        plt.title("b=0")
        FILE_NAME = f"b=0_r=3.6"
    elif file_names == files[8]:
        plt.legend(labels=['Z=50','Z=60','Z=70','Z=80','Z=90','Z=95','Z=98'],fontsize=20)
        plt.title("b=0.2")
        FILE_NAME = f"b=02_r=3.6"
    elif file_names == files[9]:
        plt.legend(labels=['Z=50','Z=60','Z=70','Z=80','Z=90','Z=95','Z=98'],fontsize=20)
        plt.title("b=0.4")
        FILE_NAME = f"b=04_r=3.6"
    elif file_names == files[10]:
        plt.legend(labels=['Z=50','Z=60','Z=70','Z=80','Z=90','Z=95','Z=98'],fontsize=20)
        plt.title("b=0.6")
        FILE_NAME = f"b=06_r=3.6"
    elif file_names == files[11]:
        plt.legend(labels=['Z=50','Z=60','Z=70','Z=80','Z=90','Z=95','Z=98'],fontsize=20)
        plt.title("b=0.8")
        FILE_NAME = f"b=08_r=3.6"
    elif file_names == files[12]:
        plt.legend(labels=['Z=50','Z=60','Z=70','Z=80','Z=90','Z=95','Z=98'],fontsize=20)
        plt.title("b=1.0")
        FILE_NAME = f"b=1_r=3.6"
    #plt.title("image scoring reputation model",fontsize=20)
    #plt.legend(labels=['β = 2.5','β = 2', 'β = 1.5'],fontsize=20)
    #plt.legend(labels=['α = 0.1','α = 0.2', 'α = 0.3'],fontsize=20)
    #plt.legend(labels=['R = 3.5','R = 4', 'R = 4.5'],fontsize=20)
    #plt.legend(labels=['normal','only punish', 'only reward', 'only reward random','reward punish', 'reward punish random', '8neighbors'])
    plt.grid(True)

    # グラフを保存
    #os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
    #FILE_NAME = f"INPUT_FILE{i}"
    file_path = os.path.join(INPUT_DIR, FILE_NAME)
    #plt.show()
    plt.savefig(file_path)  # 保存
    i += 1
        #data = pd.read_csv(file_path)
        #plt.plot(data.index, data['Cooperation Rate'])

        #data_plot = data.sample(frac=0.001, random_state=42)
        #plt.plot(data_plot.index,data_plot['Cooperation Rate'])


"""for file_name in file_names:
    # フルパスを作成
    print(file_name)
    file_path = os.path.join(OUTPUT_DIR, file_name)
    data = pd.read_csv(file_path, dtype={'Cooperation Rate': np.float32})
    sample_data = data.iloc[::sample_inierval, :]
    plt.plot(sample_data.index, sample_data['Cooperation Rate']) """

    #data = pd.read_csv(file_path)
    #plt.plot(data.index, data['Cooperation Rate'])

    #data_plot = data.sample(frac=0.001, random_state=42)
    #plt.plot(data_plot.index,data_plot['Cooperation Rate'])
"""if os.path.exists(file_path):  # ファイルが存在するか確認
        data = pd.read_csv(OUTPUT_DIR, file_name, header=None)  # ステップ数がないため、列名なしで読み込む
        data.columns = ['Cooperation Rate']  # 列名を設定
        plt.plot(data.index, data['Cooperation Rate'], label=file_name.split('.')[0])
    else:
        print(f"ファイル {file_name} が見つかりません。")"""
"""# グラフの装飾
#plt.title("Cooperation Rate Comparison")
plt.xlabel("MCS",fontsize=20)
plt.ylabel("Ρc",fontsize=20)
plt.ylim(0, 1)
plt.xscale('log')
#plt.xticks([1, 10**2, 10**3, 10**4, 10**5, 10**6],
#           ['1', '10^2', '10^3', '10^4', '10^5', '10^6'])
plt.xticks([10000, 10**5, 10**6, 10**7,10**8],
           ['1', '10', '100', '1000','10000'])
plt.xlim(left=100)
plt.legend(labels=['Z=30','Z=50','Z=70','Z=90','Z=95','Z=98'],fontsize=20)
plt.title("r=2.0")
#plt.title("image scoring reputation model",fontsize=20)
#plt.legend(labels=['β = 2.5','β = 2', 'β = 1.5'],fontsize=20)
#plt.legend(labels=['α = 0.1','α = 0.2', 'α = 0.3'],fontsize=20)
#plt.legend(labels=['R = 3.5','R = 4', 'R = 4.5'],fontsize=20)
#plt.legend(labels=['normal','only punish', 'only reward', 'only reward random','reward punish', 'reward punish random', '8neighbors'])
plt.grid(True)

# グラフを保存
#os.makedirs(folder_name, exist_ok=True)  # フォルダが存在しない場合は作成
file_path = os.path.join(INPUT_DIR, INPUT_FILE)
#plt.show()
plt.savefig(file_path)  # 保存

# グラフの表示
#plt.show()
#plt.close() """
