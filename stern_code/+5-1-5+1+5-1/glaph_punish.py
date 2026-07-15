import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import zipfile

PATTERN = "+5-1-5+1+5-1"
datePATTERN = "sternデータ"
glaphPATTERN = "sternグラフ"
modelPATTERN = "stern"

def file_select(Z):
    OUTPUT_DIR = f"../../{datePATTERN}/Z_change_協力率変遷/{PATTERN}/Punish"
    INPUT_DIR  = f"../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}/Punish"

    bs = ['0','0.2','0.4','0.6','0.8','1.0']

    if Z == 50:
        print("Z=50を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=50_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=50_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    elif Z == 60:
        print("Z=60を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=60_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=60_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    elif Z == 70:
        print("Z=70を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=70_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=70_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    elif Z == 80:
        print("Z=80を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=80_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=80_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    elif Z == 90:
        print("Z=90を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=90_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=90_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    elif Z == 95:
        print("Z=95を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=95_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=95_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    elif Z == 98:
        print("Z=98を選択しました。")
        ZIP_FILE   = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z=98_r=3.0_{PATTERN}_omega=0.1.zip"
        file_names = [f'punish_Z=98_b={b}_r=3.0_{PATTERN}_omega=0.1.csv' for b in bs]
    else:
        raise ValueError(f"未対応のZ値です: {Z}")

    return OUTPUT_DIR, INPUT_DIR, ZIP_FILE, file_names


def last_nonzero_step(series_x, series_y):
    """0でない最後のMCS_Stepを返す。全部0なら先頭のステップを返す。"""
    nonzero_idx = series_y[series_y != 0].index
    if len(nonzero_idx) == 0:
        return series_x.iloc[0]
    return series_x.iloc[nonzero_idx[-1]]


def extract_and_plot(INPUT_DIR, ZIP_FILE, file_names, Z):
    b_labels = ['b=0', 'b=0.2', 'b=0.4', 'b=0.6', 'b=0.8', 'b=1.0']

    datasets = []
    print(f"ZIPファイルを解凍中: {ZIP_FILE}")
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for file_name in file_names:
                if file_name in zf.namelist():
                    print(f"{file_name} を読み込んでいます...")
                    with zf.open(file_name) as f:
                        data = pd.read_csv(f)
                        datasets.append(data)
                else:
                    print(f"❌ エラー: ZIPファイル内に {file_name} が見つかりません。")
                    print(f"ファイルリスト: {zf.namelist()}")
    except FileNotFoundError:
        print(f"❌ エラー: ZIPファイルが見つかりません: {ZIP_FILE}")
        return
    except Exception as e:
        print(f"❌ その他のエラー: {e}")
        return

    if not datasets:
        print("❌ 読み込めたデータがありません。終了します。")
        return

    # 全b値・i/j両方を通じてX軸右端の最大値を求める
    xlim_right = max(
        max(last_nonzero_step(d['MCS_Step'], d['Punish_Count_i']) for d in datasets),
        max(last_nonzero_step(d['MCS_Step'], d['Punish_Count_j']) for d in datasets)
    )
    print(f"X軸右端: {xlim_right}")

    os.makedirs(INPUT_DIR, exist_ok=True)

    for col, suffix in [('Punish_Count_i', '_punish_i'), ('Punish_Count_j', '_punish_j')]:
        fig, ax = plt.subplots(figsize=(10, 6))

        for data, label in zip(datasets, b_labels):
            ax.plot(data['MCS_Step'], data[col], label=label)

        ax.set_xlabel("MCS", fontsize=20)
        ax.set_ylabel(col, fontsize=20)
        ax.set_xlim(left=0, right=xlim_right)
        ax.set_title(f"Z={Z} r=3.0 {col} ω=0.1", fontsize=16)
        ax.legend(fontsize=14)
        ax.grid(True)
        plt.tight_layout()

        out_path = os.path.join(INPUT_DIR, f"{modelPATTERN}罰の回数グラフ_Z={Z}_r=3.0{suffix}_omega=0.1.png")
        plt.savefig(out_path)
        print(f"保存しました: {out_path}")
        plt.show()


# メイン処理
Z = int(input("Zを入力してください: "))
OUTPUT_DIR, INPUT_DIR, ZIP_FILE, file_names = file_select(Z)
extract_and_plot(INPUT_DIR, ZIP_FILE, file_names, Z)