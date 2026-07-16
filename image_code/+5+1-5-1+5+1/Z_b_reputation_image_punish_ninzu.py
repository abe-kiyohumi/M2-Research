import numpy as np
import random
import math
import pandas as pd
import os
import time
import zipfile
import io
import shutil

# 定数設定
L = 100
G = 5
R = 3.0
K = 0.5
alpha = 0.1
beta = 1.0
num_steps = 10000

PATTERN = "+1+0.2-1-0.2+1+0.2"
typePATTERN = "image"
datePATTERN = "imageデータ"

OUTPUT_DIR = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}"   
OUTPUT_DIR_C = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C"
OUTPUT_DIR_CP = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/CP"
OUTPUT_DIR_D = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/D"
OUTPUT_DIR_PUNISH = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish"
OUTPUT_DIR_PAYOFF = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Payoff"

OUTPUT_DIRS = [OUTPUT_DIR, OUTPUT_DIR_C, OUTPUT_DIR_CP, OUTPUT_DIR_D, OUTPUT_DIR_PUNISH, OUTPUT_DIR_PAYOFF]

def initialize_grid():
    values = np.ones(L * L)
    values[L * L // 2:] = -1
    values[:L * L // 4] = 2
    np.random.shuffle(values)
    grid = values.reshape(L, L)
    return grid

def initialize_reputationgrid():
    return np.random.randint(1, 101, size=(L, L)).astype(np.float64)

def cal_f(Z, reputationgrid, b, i, j):
    rep_val = reputationgrid[i, j]
    if rep_val < Z:
        return ((Z - rep_val) / Z) ** b
    return 0.0

def cal_KD(grid, i, j, my_neighbors, reputationgrid, Z):
    # D（-1）かつ低評判（< Z）の近傍をカウント
    NBD = 0
    for n in my_neighbors:
        if grid[n] == -1 and reputationgrid[n] < Z:
            NBD += 1
    return NBD if grid[i, j] == 2 else 0

def game(i, j, Nc, NPc, R, grid, reputationgrid, my_neighbors, count_punish, Z, b):
    # pointx や pointy の計算を分離して高速化
    g_val = grid[i, j]
    base_payoff = (R * (Nc + NPc)) / G
    if g_val == 1:
        return base_payoff - 1.0, count_punish
    elif g_val == 2:
        KD = cal_KD(grid, i, j, my_neighbors, reputationgrid, Z)
        return base_payoff - 1.0 - (alpha * KD), count_punish
    else:
        # D の場合
        f = cal_f(Z, reputationgrid, b, i, j)
        if random.random() < f:
            sita = NPc
            count_punish += 1
        else:
            sita = 0
        return base_payoff - (beta * sita), count_punish

def cal_point(i, j, R, grid, reputationgrid, count_punish, Z, b):
    # 近傍の座標リストを事前に展開
    im1, ip1 = (i-1) % L, (i+1) % L
    jm1, jp1 = (j-1) % L, (j+1) % L
    
    my_neighbors = [(im1, j), (ip1, j), (i, jm1), (i, jp1), (i, j)]     
    
    # 近傍のC(1)とCP(2)をキャッシュして、ループ内でのカウントを高速化
    # 隣接プレイヤー(5箇所分)の各近傍内のC, CP数を計算してgameを適用
    point = 0.0
    for index, (ni, nj) in enumerate(my_neighbors):
        nim1, nip1 = (ni-1) % L, (ni+1) % L
        njm1, njp1 = (nj-1) % L, (nj+1) % L
        neighbors_of_neighbor = [(nim1, nj), (nip1, nj), (ni, njm1), (ni, njp1), (ni, nj)]
        
        Nc, NPc = 0, 0
        for pos in neighbors_of_neighbor:
            val = grid[pos]
            if val == 1:
                Nc += 1
            elif val == 2:
                NPc += 1
                
        p, count_punish = game(i, j, Nc, NPc, R, grid, reputationgrid, neighbors_of_neighbor, count_punish, Z, b)
        point += p  
    return point, count_punish

def update_reputation(reputationgrid, grid, i, j, ni, nj, Z):
    g_val = grid[i, j]
    rep_nj = reputationgrid[ni, nj]
    rep_ij = reputationgrid[i, j]
    
    # 複雑な分岐を整理して判定を削減
    cond_nj = rep_nj >= Z
    cond_ij = rep_ij >= Z
    
    if g_val == 1:
        diff = 1 if cond_nj else 0.2
    elif g_val == -1:
        diff = -1 if cond_nj else -0.2
    else:
        diff = 1 if cond_nj else 0.2
        
    reputationgrid[i, j] = np.clip(rep_ij + diff, 0.0, 100.0)
    return reputationgrid

# モンテカルロステップ
def simulation(record_index, omega_copy, Z, b):
    grid = initialize_grid()
    reputationgrid = initialize_reputationgrid()
    
    # 一度だけ生成し使い回す
    indices = np.array([[i, j] for i in range(L) for j in range(L)])
    check = 0
    rast = 0
    
    # 近傍選択用の乱数をあらかじめ1MCSごとに高速に引けるようにする
    # random.randint は遅いため、1MCSあたりの選択を1つの乱数配列で事前に準備
    for mcsstep in range(num_steps):
        mcs_punish_X = 0
        mcs_punish_Y = 0
        np.random.shuffle(indices)
        
        # 1MCS分(10000回分)の近傍選択インデックス(0~3)を一括生成してPythonの乱数呼び出しを激減させる
        neighbor_choices = np.random.randint(0, 4, size=L*L)
        for _ in range(L*L):
            if check == 0:
                i, j = indices[_]
                im1, ip1 = (i-1) % L, (i+1) % L
                jm1, jp1 = (j-1) % L, (j+1) % L
                
                # neighbor_choices から素早く取得
                choice = neighbor_choices[_]
                if choice == 0: ni, nj = im1, j
                elif choice == 1: ni, nj = ip1, j
                elif choice == 2: ni, nj = i, jm1
                else: ni, nj = i, jp1
                
                if grid[i, j] == grid[ni, nj]:
                    reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj, Z)
                    
                    # ⚠️ 毎ステップ np.sum(grid) を呼ぶのをやめ、1000回に1回記録するときだけ計算するように変更
                    if _ % 1000 == 0 and mcsstep < 10000:
                        grid_is_1 = (grid == 1)
                        grid_is_2 = (grid == 2)
                        grid_is_m1 = (grid == -1)
                        count_C_CP = np.sum(grid_is_1) + np.sum(grid_is_2)
                        rate = count_C_CP / (L*L)
                        
                        if rate == 0: check = 1; rast = mcsstep
                        if rate == 1.0: check = 2; rast = mcsstep
                        
                        high_rep = (reputationgrid >= Z)
                        low_rep = (reputationgrid < Z)
                        
                        C_high_rate = np.sum(grid_is_1 & high_rep) / (L*L)
                        C_low_rate  = np.sum(grid_is_1 & low_rep) / (L*L)
                        CP_high_rate = np.sum(grid_is_2 & high_rep) / (L*L)
                        CP_low_rate  = np.sum(grid_is_2 & low_rep) / (L*L)
                        D_high_rate = np.sum(grid_is_m1 & high_rep) / (L*L)
                        D_low_rate  = np.sum(grid_is_m1 & low_rep) / (L*L)
                        
                        rates_array[record_index] = rate
                        Crates_array[record_index] = C_high_rate + C_low_rate
                        CPrates_array[record_index] = CP_high_rate + CP_low_rate
                        Drates_array[record_index] = D_high_rate + D_low_rate
                        rate_high_rates_array[record_index] = C_high_rate + CP_high_rate
                        rate_low_rates_array[record_index] = C_low_rate + CP_low_rate
                        C_high_rates_array[record_index] = C_high_rate
                        C_low_rates_array[record_index] = C_low_rate
                        CP_high_rates_array[record_index] = CP_high_rate
                        CP_low_rates_array[record_index] = CP_low_rate
                        D_high_rates_array[record_index] = D_high_rate
                        D_low_rates_array[record_index] = D_low_rate
                        record_index += 1 
                    continue
                
                count_punishX = 0
                count_punishY = 0
                pointx, count_punishX = cal_point(i, j, R, grid, reputationgrid, count_punishX, Z, b)
                pointy, count_punishY = cal_point(ni, nj, R, grid, reputationgrid, count_punishY, Z, b)
                
                mcs_punish_X += count_punishX
                mcs_punish_Y += count_punishY
                
                omega = 1.0 if reputationgrid[ni, nj] >= Z else omega_copy
                    
                if random.random() < omega * (1 / (1 + math.exp((pointx - pointy) / K))):
                    grid[i, j] = grid[ni, nj]
                    
                reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj, Z)
                
                if _ % 1000 == 0 and mcsstep < 10000:
                    grid_is_1 = (grid == 1)
                    grid_is_2 = (grid == 2)
                    grid_is_m1 = (grid == -1)
                    count_C_CP = np.sum(grid_is_1) + np.sum(grid_is_2)
                    rate = count_C_CP / (L*L)
                    
                    if rate == 0: check = 1; rast = mcsstep
                    if rate == 1.0: check = 2; rast = mcsstep
                    
                    high_rep = (reputationgrid >= Z)
                    low_rep = (reputationgrid < Z)
                    
                    C_high_rate = np.sum(grid_is_1 & high_rep) / (L*L)
                    C_low_rate  = np.sum(grid_is_1 & low_rep) / (L*L)
                    CP_high_rate = np.sum(grid_is_2 & high_rep) / (L*L)
                    CP_low_rate  = np.sum(grid_is_2 & low_rep) / (L*L)
                    D_high_rate = np.sum(grid_is_m1 & high_rep) / (L*L)
                    D_low_rate  = np.sum(grid_is_m1 & low_rep) / (L*L)
                    
                    rates_array[record_index] = rate
                    Crates_array[record_index] = C_high_rate + C_low_rate
                    CPrates_array[record_index] = CP_high_rate + CP_low_rate
                    Drates_array[record_index] = D_high_rate + D_low_rate
                    rate_high_rates_array[record_index] = C_high_rate + CP_high_rate
                    rate_low_rates_array[record_index] = C_low_rate + CP_low_rate
                    C_high_rates_array[record_index] = C_high_rate
                    C_low_rates_array[record_index] = C_low_rate
                    CP_high_rates_array[record_index] = CP_high_rate
                    CP_low_rates_array[record_index] = CP_low_rate
                    D_high_rates_array[record_index] = D_high_rate
                    D_low_rates_array[record_index] = D_low_rate
                    record_index += 1 
            else:
                if _ % 1000 == 0 and mcsstep < 10000:
                    rates_array[record_index] = rate
                    Crates_array[record_index] = C_high_rate + C_low_rate
                    CPrates_array[record_index] = CP_high_rate + CP_low_rate
                    Drates_array[record_index] = D_high_rate + D_low_rate
                    rate_high_rates_array[record_index] = C_high_rate + CP_high_rate
                    rate_low_rates_array[record_index] = C_low_rate + CP_low_rate
                    C_high_rates_array[record_index] = C_high_rate
                    C_low_rates_array[record_index] = C_low_rate
                    CP_high_rates_array[record_index] = CP_high_rate
                    CP_low_rates_array[record_index] = CP_low_rate
                    D_high_rates_array[record_index] = D_high_rate
                    D_low_rates_array[record_index] = D_low_rate
                    record_index += 1
                break
                
        if mcsstep < num_steps:
            punish_X_time_series[mcsstep] = mcs_punish_X
            punish_Y_time_series[mcsstep] = mcs_punish_Y
            
            all_payoffs = np.zeros((L, L))
            temporary_punish = 0  
            for x in range(L):
                for y in range(L):
                    all_payoffs[x, y], temporary_punish = cal_point(x, y, R, grid, reputationgrid, temporary_punish, Z, b)
            
            mask_C = (grid == 1)
            mask_D = (grid == -1)
            mask_PC = (grid == 2)
            
            payoff_history_all[mcsstep] = np.mean(all_payoffs)
            payoff_history_C[mcsstep] = np.mean(all_payoffs[mask_C]) if np.any(mask_C) else 0.0
            payoff_history_D[mcsstep] = np.mean(all_payoffs[mask_D]) if np.any(mask_D) else 0.0
            payoff_history_PC[mcsstep] = np.mean(all_payoffs[mask_PC]) if np.any(mask_PC) else 0.0

        if mcsstep % 1000 == 0:
            print(f"ステップ数 {mcsstep} 協力率 {rate:.4f} | 罰回数 i: {mcs_punish_X}, j: {mcs_punish_Y}")
        if check != 0: break
            
    print("0または1になったステップ数", rast)
    return (rates_array, Crates_array, CPrates_array, Drates_array,
            rate_high_rates_array, rate_low_rates_array,
            C_high_rates_array, C_low_rates_array, 
            CP_high_rates_array, CP_low_rates_array, 
            D_high_rates_array, D_low_rates_array)
# ==========================================
# 2. メイン処理（データの定義と保存）
# ==========================================
start = time.time()
for omega in [0.1, 0.01]:
    # R は上部で定義された R = 3.0 を使用
    print("R=", R)
    for Z in [50, 60, 70, 80, 90, 95, 98]: 
        print("現在のZ値:", Z, "OUTPUT_DIR:", OUTPUT_DIR)
        
        ZIP_NAME = f"{typePATTERN}_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
        ZIP_NAME_C = f"{typePATTERN}_C_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
        ZIP_NAME_CP = f"{typePATTERN}_CP_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
        ZIP_NAME_D = f"{typePATTERN}_D_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
        ZIP_NAME_PUNISH = f"punish_history_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
        ZIP_NAME_PAYOFF = f"payoff_history_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip" 
        
        zip_buffer = io.BytesIO()
        zip_buffer_C = io.BytesIO()
        zip_buffer_CP = io.BytesIO()
        zip_buffer_D = io.BytesIO()
        zip_buffer_P = io.BytesIO()
        zip_buffer_payoff = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf, \
             zipfile.ZipFile(zip_buffer_C, 'w', zipfile.ZIP_DEFLATED) as zf_C, \
             zipfile.ZipFile(zip_buffer_CP, 'w', zipfile.ZIP_DEFLATED) as zf_CP, \
             zipfile.ZipFile(zip_buffer_D, 'w', zipfile.ZIP_DEFLATED) as zf_D, \
             zipfile.ZipFile(zip_buffer_P, 'w', zipfile.ZIP_DEFLATED) as zf_P, \
             zipfile.ZipFile(zip_buffer_payoff, 'w', zipfile.ZIP_DEFLATED) as zf_payoff:
                 
            for b in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
                expected_size = 100000
                
                # 記録用配列の初期化
                rates_array = np.zeros(expected_size, dtype=np.float32)
                Crates_array = np.zeros(expected_size, dtype=np.float32)
                CPrates_array = np.zeros(expected_size, dtype=np.float32)
                Drates_array = np.zeros(expected_size, dtype=np.float32)
                
                rate_high_rates_array = np.zeros(expected_size, dtype=np.float32)
                rate_low_rates_array = np.zeros(expected_size, dtype=np.float32)
                C_high_rates_array = np.zeros(expected_size, dtype=np.float32)
                C_low_rates_array = np.zeros(expected_size, dtype=np.float32)
                CP_high_rates_array = np.zeros(expected_size, dtype=np.float32)
                CP_low_rates_array = np.zeros(expected_size, dtype=np.float32)
                D_high_rates_array = np.zeros(expected_size, dtype=np.float32)
                D_low_rates_array = np.zeros(expected_size, dtype=np.float32)
                
                punish_X_time_series = np.zeros(num_steps, dtype=np.int32)
                punish_Y_time_series = np.zeros(num_steps, dtype=np.int32)
                payoff_history_all = np.zeros(num_steps, dtype=np.float32)
                payoff_history_C = np.zeros(num_steps, dtype=np.float32)
                payoff_history_D = np.zeros(num_steps, dtype=np.float32)
                payoff_history_PC = np.zeros(num_steps, dtype=np.float32)
                
                print("現在のb値:", b)
                record_index = 0
                
                # 【修正】引数に Z と b を渡すように変更
                (rates_array, Crates_array, CPrates_array, Drates_array,
                 rate_high_rates_array, rate_low_rates_array,
                 C_high_rates_array, C_low_rates_array, 
                 CP_high_rates_array, CP_low_rates_array, 
                 D_high_rates_array, D_low_rates_array) = simulation(record_index, omega, Z, b)
                
                # 1. 全体協力率データの保存
                csv_buf = io.StringIO()
                pd.DataFrame({
                    "Cooperation Rate": rates_array,
                    "Cooperation Rate High": rate_high_rates_array,
                    "Cooperation Rate Low": rate_low_rates_array
                }).to_csv(csv_buf, index=False)
                zf.writestr(f"{typePATTERN}_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf.getvalue())
                
                # 2. Cデータ保存
                csv_buf_C = io.StringIO()
                pd.DataFrame({
                    "C Rate": Crates_array,
                    "C Rate High": C_high_rates_array,
                    "C Rate Low": C_low_rates_array
                }).to_csv(csv_buf_C, index=False)
                zf_C.writestr(f"{typePATTERN}_C_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_C.getvalue())
                
                # 3. CPデータ保存
                csv_buf_CP = io.StringIO()
                pd.DataFrame({
                    "CP Rate": CPrates_array,
                    "CP Rate High": CP_high_rates_array,
                    "CP Rate Low": CP_low_rates_array
                }).to_csv(csv_buf_CP, index=False)
                zf_CP.writestr(f"{typePATTERN}_CP_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_CP.getvalue())  
                
                # 4. Dデータ保存
                csv_buf_D = io.StringIO()
                pd.DataFrame({
                    "D Rate": Drates_array,
                    "D Rate High": D_high_rates_array,
                    "D Rate Low": D_low_rates_array
                }).to_csv(csv_buf_D, index=False)
                zf_D.writestr(f"{typePATTERN}_D_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_D.getvalue())

                # 5. 罰履歴データ保存
                csv_buf_P = io.StringIO()
                punish_df = pd.DataFrame({
                    "MCS_Step": np.arange(num_steps),
                    "Punish_Count_i": punish_X_time_series,
                    "Punish_Count_j": punish_Y_time_series
                })
                punish_df.to_csv(csv_buf_P, index=False)
                zf_P.writestr(f"punish_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_P.getvalue())

                # 6. ペイオフデータ保存
                csv_buf_Payoff = io.StringIO()
                payoff_df = pd.DataFrame({
                    "MCS_Step": np.arange(num_steps),
                    "Avg_Payoff_Total": payoff_history_all,
                    "Avg_Payoff_C": payoff_history_C,
                    "Avg_Payoff_D": payoff_history_D,
                    "Avg_Payoff_PC": payoff_history_PC
                })
                payoff_df.to_csv(csv_buf_Payoff, index=False)
                zf_payoff.writestr(f"payoff_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_Payoff.getvalue())
                
                # メモリ解放
                del rates_array, Crates_array, CPrates_array, Drates_array, \
                    rate_high_rates_array, rate_low_rates_array, \
                    C_high_rates_array, C_low_rates_array, CP_high_rates_array, CP_low_rates_array, \
                    D_high_rates_array, D_low_rates_array, \
                    punish_X_time_series, punish_Y_time_series, payoff_history_all, payoff_history_C, payoff_history_D, payoff_history_PC

        # 保存先ディレクトリの作成とファイル出力
        for d in OUTPUT_DIRS: 
            os.makedirs(d, exist_ok=True)
        
        save_files = [
            (zip_buffer, ZIP_NAME, OUTPUT_DIRS[0]),
            (zip_buffer_C, ZIP_NAME_C, OUTPUT_DIRS[1]),
            (zip_buffer_CP, ZIP_NAME_CP, OUTPUT_DIRS[2]),
            (zip_buffer_D, ZIP_NAME_D, OUTPUT_DIRS[3]),
            (zip_buffer_P, ZIP_NAME_PUNISH, OUTPUT_DIRS[4]),
            (zip_buffer_payoff, ZIP_NAME_PAYOFF, OUTPUT_DIRS[5])
        ]
        for buf, filename, target_dir in save_files:
            local_path = os.path.join(target_dir, filename)
            with open(local_path, 'wb') as f:
                f.write(buf.getvalue())
            print(f"{filename}が{local_path}に保存されました") 
            buf.close()  
        
        del csv_buf, csv_buf_C, csv_buf_CP, csv_buf_D, csv_buf_P, csv_buf_Payoff

end = time.time()
print("実行時間:", end - start, "秒")