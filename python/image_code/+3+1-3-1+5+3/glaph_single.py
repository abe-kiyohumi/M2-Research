import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
import zipfile
import io
import sys

# 引数の受け取り (第1引数: omega, 第2引数: カンマ区切りZリスト)
if len(sys.argv) > 1:
    omega = float(sys.argv[1])
else:
    omega = 0.1

if len(sys.argv) > 2:
    target_z_list = [int(z) for z in sys.argv[2].split(',')]
else:
    target_z_list = [50, 60, 70, 80, 90, 95, 98]

#PATTERN = "+3+1-3-1+5+3"
PATTERN = "+0.6+0.2-0.6-0.2+1+0.6"
datePATTERN = "imageデータ"
glaphPATTERN = "imageグラフ"
modelPATTERN = "image"

def file_select(Z):
    OUTPUT_DIR = f"../../../{datePATTERN}/Z_change_協力率変遷/{PATTERN}"
    INPUT_DIR  = f"../../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}"
    bs = ['0','0.2','0.4','0.6','0.8','1.0']

    INPUT_FILE = f"{modelPATTERN}10000協力率_まとめ_Z={Z}_r=3.0_omega={omega}.png"
    ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/{modelPATTERN}_Z={Z}_r=3.0_{PATTERN}_omega={omega}.zip"
    file_names = [f'{modelPATTERN}_Z={Z}_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    return OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names

def create_and_save_graph(Z):
    OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names = file_select(Z)
    
    os.makedirs(INPUT_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))

    print(f"ZIPファイルを解凍中: {ZIP_FILE}")
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for file_name in file_names:
                if file_name in zf.namelist():
                    with zf.open(file_name) as file:
                        data = pd.read_csv(file)
                        ax.plot(data.index, data['Cooperation Rate'])
                else:
                    print(f"❌ エラー: ZIP内に {file_name} が見つかりません。")

    except FileNotFoundError:
        print(f"❌ エラー: ZIPファイルが見つかりません: {ZIP_FILE}")
        plt.close(fig)
        return
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        plt.close(fig)
        return

    ax.set_xlabel("MCS", fontsize=20)
    ax.set_ylabel("Ρc", fontsize=20)
    ax.set_ylim(0, 1)
    ax.set_xscale('log')
    ax.set_xlim(left=1, right=100000)
    ax.set_title(f"Z={Z} r=3.0 ω={omega}", fontsize=20)
    ax.set_xticks([10**2, 10**3, 10**4, 10**5])
    ax.set_xticklabels(['10', '100', '1000', '10000'])
    ax.legend(labels=['b=0', 'b=0.2', 'b=0.4', 'b=0.6', 'b=0.8', 'b=1.0'], fontsize=20)
    ax.grid(True)

    file_path = os.path.join(INPUT_DIR, INPUT_FILE)
    plt.savefig(file_path, bbox_inches='tight')
    print(f"✅ 画像を保存しました: {file_path}")

    plt.show(block=False)
    plt.pause(0.1)
    plt.close(fig)

for Z in target_z_list:
    create_and_save_graph(Z)