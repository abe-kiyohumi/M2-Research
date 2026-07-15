import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
import zipfile
import io

PATTERN = "+5-1-5+1+8-3"
datePATTERN = "sternデータ"
glaphPATTERN = "sternグラフ"
modelPATTERN = "stern"

def file_select(Z):
    OUTPUT_DIR = f"../../{datePATTERN}/Z_change_協力率変遷/{PATTERN}/C"
    INPUT_DIR  = f"../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}/C"

    bs = ['0','0.2','0.4','0.6','0.8','1.0']

    if Z == 50:
        print("Z=50を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=50_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=50_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=50_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 60:
        print("Z=60を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=60_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=60_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=60_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 70:
        print("Z=70を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=70_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=70_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=70_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 80:
        print("Z=80を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=80_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=80_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=80_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 90:
        print("Z=90を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=90_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=90_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=90_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 95:
        print("Z=95を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=95_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=95_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=95_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    elif Z == 98:
        print("Z=98を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=98_r=3.0_{PATTERN}_omega=0.1.png"
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=98_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'{modelPATTERN}_C_Z=98_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]

    return OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names

def extract_zip_files(OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names):
    #ZIPファイル解凍
    print(f"ZIPファイルを解凍中: {ZIP_FILE}")
    sample_inierval = 1000
    try:
        # 1. zipfile.ZipFile を 'r' (読み込み) モードで開く
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            # 2. ZIPファイル内に目的のファイルが存在するかチェック
            for file_name in file_names:
                if file_name in zf.namelist():
                    print(file_name,"を読み込んでいます...")
                    with zf.open(file_name) as file:
                        # 3. ファイルを読み込み、DataFrameに変換
                        data = pd.read_csv(file)
                        plt.plot(data.index, data['C Rate'])
                    
                else:
                    print(f"❌ エラー: ZIPファイル内に {file_name} が見つかりません。")
                    print(f"ファイルリスト: {zf.namelist()}")

    except FileNotFoundError:
        print(f"❌ エラー: ZIPファイルが見つかりません。パスを確認してください: {ZIP_FILE}")
    except Exception as e:
        print(f"❌ その他のエラーが発生しました: {e}")

# グラフの設定
plt.figure(figsize=(10, 6))
Z=int(input("Zを入力してください: "))
OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names = file_select(Z)
extract_zip_files(OUTPUT_DIR,INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names)

# グラフの装飾
#plt.title("Cooperation Rate Comparison")
plt.xlabel("MCS",fontsize=20)
plt.ylabel("Ρc",fontsize=20)
plt.ylim(0, 1)
plt.xlim(right=100000)
plt.xscale('log')
plt.title(f"C Z={Z} r=3.0 ω=0.1",fontsize=20)
#plt.xticks([1, 10**2, 10**3, 10**4, 10**5, 10**6],
#           ['1', '10^2', '10^3', '10^4', '10^5', '10^6'])
#plt.xticks([100, 1000, 10000, 10**5, 10**6, 10**7,10**8],
#           ['10^-2', '10^-1', '1', '10', '100', '1000','10000'])
plt.xticks([10**2, 10**3, 10**4, 10**5],
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
