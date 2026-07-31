import numpy as np
import matplotlib
matplotlib.use('Agg')  # 🌟 ウィンドウを描画せずバックグラウンドで処理し、メモリを節約
import matplotlib.pyplot as plt
import pandas as pd
import os
import zipfile
import sys

# ==========================================
# 1. 親プログラム (all_glaph.py) から引数を受け取る
# ==========================================
if len(sys.argv) > 5:
    modelPATTERN = sys.argv[1]
    PATTERN = sys.argv[2]
    datePATTERN = sys.argv[3]
    glaphPATTERN = sys.argv[4]
    omega = float(sys.argv[5])
else:
    # 直接実行した時のためのデフォルト値
    modelPATTERN = "image"
    PATTERN = "+0.6+0.2-0.6-0.2+1+0.6"
    datePATTERN = "imageデータ"
    glaphPATTERN = "imageグラフ"
    omega = 0.1

print(f"🔧 [グラフ設定] model: {modelPATTERN} | pattern: {PATTERN} | omega: {omega}")

# ==========================================
# 2. 協力率変遷グラフ作成関数 (Base, C, CP を統合)[cite: 6, 7, 8]
# ==========================================
def plot_coop(Z, target_type):
    # target_type に応じてパスや参照カラムを切り替え
    if target_type == "Base":
        sub_dir = ""
        prefix = modelPATTERN
        col_name = "Cooperation Rate" #[cite: 6]
        out_file = f"{modelPATTERN}10000協力率_まとめ_Z={Z}_r=3.0_omega={omega}.png" #[cite: 6]
    else:
        sub_dir = f"/{target_type}"
        prefix = f"{modelPATTERN}_{target_type}"
        col_name = f"{target_type} Rate" #[cite: 7, 8]
        out_file = f"{modelPATTERN}10000協力率_{target_type}_まとめ_Z={Z}_r=3.0_omega={omega}.png" #[cite: 7, 8]

    # パス設定[cite: 6, 7, 8]
    INPUT_DIR = f"../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}{sub_dir}"
    ZIP_FILE  = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}{sub_dir}/{prefix}_Z={Z}_r=3.0_{PATTERN}_omega={omega}.zip"
    
    os.makedirs(INPUT_DIR, exist_ok=True)
    bs = ['0','0.2','0.4','0.6','0.8','1.0']
    file_names = [f"{prefix}_Z={Z}_b={b}_r=3.0_{PATTERN}_omega={omega}.csv" for b in bs]

    if not os.path.exists(ZIP_FILE):
        print(f"⚠️ スキップ: {ZIP_FILE} が存在しません。")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for file_name in file_names:
                if file_name in zf.namelist():
                    with zf.open(file_name) as file:
                        data = pd.read_csv(file)
                        ax.plot(data.index, data[col_name])
    except Exception as e:
        print(f"❌ エラー({target_type} Z={Z}): {e}")
        plt.close(fig)
        return

    # グラフ装飾[cite: 6, 7, 8]
    ax.set_xlabel("MCS", fontsize=20)
    ax.set_ylabel("Ρc", fontsize=20)
    ax.set_ylim(0, 1)
    ax.set_xscale('log')
    ax.set_xlim(left=1, right=100000)
    ax.set_title(f"{prefix}_Z={Z} r=3.0 ω={omega}", fontsize=20)
    ax.set_xticks([10**2, 10**3, 10**4, 10**5])
    ax.set_xticklabels(['10', '100', '1000', '10000'])
    ax.legend(labels=[f'b={b}' for b in bs], fontsize=20)
    ax.grid(True)

    file_path = os.path.join(INPUT_DIR, out_file)
    plt.savefig(file_path, bbox_inches='tight')
    plt.close(fig)
    print(f"✅ 保存({target_type}): {file_path}")

# ==========================================
# 3. 罰の回数グラフ作成関数[cite: 5]
# ==========================================
def last_nonzero_step(series_x, series_y):
    nonzero_idx = series_y[series_y != 0].index
    if len(nonzero_idx) == 0:
        return series_x.iloc[0]
    return series_x.iloc[nonzero_idx[-1]]

def plot_punish(Z):
    INPUT_DIR = f"../../{glaphPATTERN}/Z_change_協力率変遷/{PATTERN}/Punish" #[cite: 5]
    ZIP_FILE  = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish/punish_history_Z={Z}_r=3.0_{PATTERN}_omega={omega}.zip" #[cite: 5]
    
    os.makedirs(INPUT_DIR, exist_ok=True)
    bs = ['0','0.2','0.4','0.6','0.8','1.0']
    file_names = [f"punish_Z={Z}_b={b}_r=3.0_{PATTERN}_omega={omega}.csv" for b in bs] #[cite: 5]

    if not os.path.exists(ZIP_FILE):
        print(f"⚠️ スキップ: {ZIP_FILE} が存在しません。")
        return

    datasets = []
    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            for file_name in file_names:
                if file_name in zf.namelist():
                    with zf.open(file_name) as f:
                        datasets.append(pd.read_csv(f))
    except Exception as e:
        print(f"❌ エラー(Punish Z={Z}): {e}")
        return

    if not datasets:
        return

    # X軸右端の最大値を求める処理[cite: 5]
    xlim_right = max(
        max(last_nonzero_step(d['MCS_Step'], d['Punish_Count_i']) for d in datasets),
        max(last_nonzero_step(d['MCS_Step'], d['Punish_Count_j']) for d in datasets)
    )

    for col, suffix in [('Punish_Count_i', '_punish_i'), ('Punish_Count_j', '_punish_j')]: #[cite: 5]
        fig, ax = plt.subplots(figsize=(10, 6))
        for data, label in zip(datasets, [f'b={b}' for b in bs]):
            ax.plot(data['MCS_Step'], data[col], label=label)

        ax.set_xlabel("MCS", fontsize=20)
        ax.set_ylabel(col, fontsize=20)
        ax.set_xlim(left=0, right=xlim_right)
        ax.set_title(f"Z={Z} r=3.0 {col} ω={omega}", fontsize=16)
        ax.legend(fontsize=14)
        ax.grid(True)
        plt.tight_layout()

        out_path = os.path.join(INPUT_DIR, f"{modelPATTERN}罰の回数グラフ_Z={Z}_r=3.0{suffix}_omega={omega}.png") #[cite: 5]
        plt.savefig(out_path)
        plt.close(fig)
        print(f"✅ 保存(Punish {col}): {out_path}")

# ==========================================
# 4. 実行ループ
# ==========================================
if __name__ == "__main__":
    zs = [50, 60, 70, 80, 90, 95, 98] #[cite: 5, 6, 7, 8]
    for Z in zs:
        print(f"\n--- Z={Z} のグラフ作成開始 ---")
        plot_coop(Z, "Base")
        plot_coop(Z, "C")
        plot_coop(Z, "PC")
        plot_punish(Z)
    
    print(f"\n🎉 {modelPATTERN} / {PATTERN} / omega={omega} の全グラフ作成が完了しました！")