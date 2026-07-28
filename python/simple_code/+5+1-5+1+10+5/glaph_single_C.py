import numpy as np
import random
import math
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
import zipfile
import io

#PATTERN = "+5+1-5+1+10+5"
PATTERN = "+1+0.2-1+0.2+2+1"
datePATTERN = "simpleデータ"
glaphPATTERN = "simpleグラフ"
modelPATTERN = "simple"

omega = 0.1

def file_select(Z):
    OUTPUT_DIR = f"../../../{datePATTERN}/Z_change_協力率変遷/{PATTERN}/C"
    INPUT_DIR  = f"../../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}/C"

    bs = ['0','0.2','0.4','0.6','0.8','1.0']

    if Z == 50:
        print("Z=50を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=50_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=50_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=50_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    elif Z == 60:
        print("Z=60を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=60_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=60_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=60_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    elif Z == 70:
        print("Z=70を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=70_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=70_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=70_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    elif Z == 80:
        print("Z=80を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=80_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=80_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=80_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    elif Z == 90:
        print("Z=90を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=90_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=90_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=90_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    elif Z == 95:
        print("Z=95を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=95_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=95_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=95_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    elif Z == 98:
        print("Z=98を選択しました。")
        INPUT_FILE = f"{modelPATTERN}10000協力率_C_まとめ_Z=98_r=3.0_{PATTERN}_omega={omega}.png"
        ZIP_FILE   = f"../../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C/{modelPATTERN}_C_Z=98_r=3.0_{PATTERN}_omega={omega}.zip"
        file_names = [f'{modelPATTERN}_C_Z=98_b={b}_r=3.0_{PATTERN}_omega={omega}.csv' for b in bs]

    return OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names


def create_and_save_graph(Z):
    # 1. パスとファイル名の取得
    OUTPUT_DIR, INPUT_DIR, INPUT_FILE, ZIP_FILE, file_names = file_select(Z)
    
    # 保存先ディレクトリがなければ作成
    os.makedirs(INPUT_DIR, exist_ok=True)
    
    # 2. 【重要】ループの最初に新しいキャンバス（フィギュア）を用意する
    fig, ax = plt.subplots(figsize=(10, 6))

    # 3. ZIPファイルからデータを読み込んでプロット
    print(f"ZIPファイルを解凍中: {ZIP_FILE}")
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for file_name in file_names:
                if file_name in zf.namelist():
                    print(file_name, "を読み込んでいます...")
                    with zf.open(file_name) as file:
                        # 3. ファイルを読み込み、DataFrameに変換
                        data = pd.read_csv(file)
                        ax.plot(data.index, data['C Rate'])
                else:
                    print(f"❌ エラー: ZIPファイル内に {file_name} が見つかりません。")
                    print(f"ファイルリスト: {zf.namelist()}")

    except FileNotFoundError:
        print(f"❌ エラー: ZIPファイルが見つかりません。パスを確認してください: {ZIP_FILE}")
        plt.close(fig)
        return
    except Exception as e:
        print(f"❌ その他のエラーが発生しました: {e}")
        plt.close(fig)
        return

    # 4. グラフの装飾（axに対して設定）
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

    # 5. 【重要】保存を最初に行う（showやcloseの前）
    file_path = os.path.join(INPUT_DIR, INPUT_FILE)
    plt.savefig(file_path, bbox_inches='tight')
    print(f"✅ 画像を保存しました: {file_path}")

    # 6. 表示して1秒待ってから閉じる
    plt.show(block=False)
    plt.pause(0.1)
    plt.close(fig)  # このループで開いたキャンバスだけをしっかり破棄


# --- メイン実行処理 ---
for Z in [50, 60, 70, 80, 90, 95, 98]:
    create_and_save_graph(Z)