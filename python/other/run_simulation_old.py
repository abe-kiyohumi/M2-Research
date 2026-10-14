import numpy as np
import random
import math
import pandas as pd
import os
import time
import zipfile
import io
import sys
import re

# ==========================================
# 0. 引数の受け取りと設定
# ==========================================
# 引数: typePATTERN, PATTERN, datePATTERN, omega, Z
if len(sys.argv) > 5:
    typePATTERN = sys.argv[1]
    PATTERN = sys.argv[2]
    datePATTERN = sys.argv[3]
    omega = float(sys.argv[4])
    Z = int(sys.argv[5])
else:
    # デフォルト設定 (単体テスト用)
    typePATTERN = "image"
    PATTERN = "+0.6+0.2-0.6-0.2+1+0.6"
    datePATTERN = "imageデータ"
    omega = 0.1
    Z = 50

print(f"🔧 [設定] type: {typePATTERN} | pattern: {PATTERN} | date: {datePATTERN} | omega: {omega} | Z: {Z}")

def parse_pattern(pattern_str):
    """PATTERNから6つの数値を抽出し、絶対値のリストを返す"""
    numbers = [abs(float(x)) for x in re.findall(r'[+-]?\d+(?:\.\d+)?', pattern_str)]
    if len(numbers) != 6:
        raise ValueError(f"PATTERN のフォーマットが不正です（6つの数値が必要です）: {pattern_str}")
    return numbers

p_vals = parse_pattern(PATTERN)
print("パターン",p_vals)

# 定数設定
L = 100
G = 5
R = 3.0
K = 0.5
alpha = 0.1
beta = 1.0
num_steps = 10000

OUTPUT_DIR        = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}"   
OUTPUT_DIR_C      = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/C"
OUTPUT_DIR_PC     = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/PC"
OUTPUT_DIR_D      = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/D"
OUTPUT_DIR_PUNISH = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Punish"
OUTPUT_DIR_PAYOFF = f"../../{datePATTERN}/Z_b_change報酬罰/{PATTERN}/Payoff"

OUTPUT_DIRS = [OUTPUT_DIR, OUTPUT_DIR_C, OUTPUT_DIR_PC, OUTPUT_DIR_D, OUTPUT_DIR_PUNISH, OUTPUT_DIR_PAYOFF]

# ==========================================
# 1. 共通関数 & 増減表に基づく評判更新
# ==========================================
def initialize_grid():
    values = np.ones(L * L)
    values[L * L // 2:] = -1
    values[:L * L // 4] = 2
    np.random.shuffle(values)
    return values.reshape(L, L)

def initialize_reputationgrid():
    return np.random.randint(1, 101, size=(L, L)).astype(np.float64)

def cal_f(Z, reputationgrid, b, i, j):
    rep_val = reputationgrid[i, j]
    return ((Z - rep_val) / Z) ** b if rep_val < Z else 0.0

def cal_KD(grid, i, j, my_neighbors, reputationgrid, Z):
    if grid[i, j] != 2:
        return 0
    return sum(1 for n in my_neighbors if grid[n] == -1 and reputationgrid[n] < Z)

def game(i, j, Nc, NPc, R, grid, reputationgrid, my_neighbors, count_punish, Z, b):
    g_val = grid[i, j]
    base_payoff = (R * (Nc + NPc)) / G
    if g_val == 1:
        return base_payoff - 1.0, count_punish
    elif g_val == 2:
        KD = cal_KD(grid, i, j, my_neighbors, reputationgrid, Z)
        return base_payoff - 1.0 - (alpha * KD), count_punish
    else:
        f = cal_f(Z, reputationgrid, b, i, j)
        if random.random() < f:
            sita = NPc
            count_punish += 1
        else:
            sita = 0
        return base_payoff - (beta * sita), count_punish

def cal_point(i, j, R, grid, reputationgrid, count_punish, Z, b):
    im1, ip1 = (i-1) % L, (i+1) % L
    jm1, jp1 = (j-1) % L, (j+1) % L
    my_neighbors = [(im1, j), (ip1, j), (i, jm1), (i, jp1), (i, j)]     
    
    point = 0.0
    for ni, nj in my_neighbors:
        nim1, nip1 = (ni-1) % L, (ni+1) % L
        njm1, njp1 = (nj-1) % L, (nj+1) % L
        neighbors_of_neighbor = [(nim1, nj), (nip1, nj), (ni, njm1), (ni, njp1), (ni, nj)]
        
        Nc, NPc = 0, 0
        for pos in neighbors_of_neighbor:
            val = grid[pos]
            if val == 1: Nc += 1
            elif val == 2: NPc += 1
                
        p, count_punish = game(i, j, Nc, NPc, R, grid, reputationgrid, neighbors_of_neighbor, count_punish, Z, b)
        point += p  
    return point, count_punish

def update_reputation(reputationgrid, grid, i, j, ni, nj, Z, typePATTERN, p_vals):
    v1, v2, v3, v4, v5, v6 = p_vals
    g_val = grid[i, j]
    rep_nj = reputationgrid[ni, nj]
    rep_ij = reputationgrid[i, j]
    
    cond_nj = rep_nj >= Z
    cond_ij = rep_ij >= Z
    
    diff = 0.0

    if typePATTERN == "image":
        if g_val == 1:     diff = v1 if cond_nj else v2
        elif g_val == -1:  diff = -v3 if cond_nj else -v4
        elif g_val == 2:   diff = v5 if cond_nj else v6

    elif typePATTERN == "shunning":
        if g_val == 1:     diff = v1 if cond_nj else -v2
        elif g_val == -1:
            if cond_nj:    diff = -v3
            else:          diff = v4 if cond_ij else -v4
        elif g_val == 2:   diff = v5 if cond_nj else -v6

    elif typePATTERN == "stern":
        if g_val == 1:
            if cond_nj:    diff = v1
            else:          diff = v2 if cond_ij else -v2
        elif g_val == -1:
            if cond_nj:    diff = -v3
            else:          diff = v4 if cond_ij else -v4
        elif g_val == 2:
            if cond_nj:    diff = v5
            else:          diff = v6 if cond_ij else -v6

    elif typePATTERN == "simple":
        if g_val == 1:     diff = v1 if cond_nj else v2
        elif g_val == -1:
            if cond_nj:    diff = -v3
            else:          diff = v4 if cond_ij else -v4
        elif g_val == 2:   diff = v5 if cond_nj else v6

    reputationgrid[i, j] = np.clip(rep_ij + diff, 0.0, 100.0)
    return reputationgrid

# モンテカルロステップ
def simulation(record_index, omega_copy, Z, b):
    grid = initialize_grid()
    reputationgrid = initialize_reputationgrid()
    indices = np.array([[i, j] for i in range(L) for j in range(L)])
    check = 0
    rast = 0
    
    for mcsstep in range(num_steps):
        mcs_punish_X = 0
        mcs_punish_Y = 0
        np.random.shuffle(indices)
        neighbor_choices = np.random.randint(0, 4, size=L*L)
        
        for _ in range(L*L):
            if check == 0:
                i, j = indices[_]
                im1, ip1 = (i-1) % L, (i+1) % L
                jm1, jp1 = (j-1) % L, (j+1) % L
                
                choice = neighbor_choices[_]
                if choice == 0: ni, nj = im1, j
                elif choice == 1: ni, nj = ip1, j
                elif choice == 2: ni, nj = i, jm1
                else: ni, nj = i, jp1
                
                if grid[i, j] == grid[ni, nj]:
                    reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj, Z, typePATTERN, p_vals)
                    if _ % 1000 == 0 and mcsstep < 10000:
                        grid_is_1 = (grid == 1)
                        grid_is_2 = (grid == 2)
                        grid_is_m1 = (grid == -1)
                        count_C_PC = np.sum(grid_is_1) + np.sum(grid_is_2)
                        rate = count_C_PC / (L*L)
                        
                        if rate == 0: check = 1; rast = mcsstep
                        if rate == 1.0: check = 2; rast = mcsstep
                        
                        high_rep = (reputationgrid >= Z)
                        low_rep = (reputationgrid < Z)
                        
                        C_high_rate = np.sum(grid_is_1 & high_rep) / (L*L)
                        C_low_rate  = np.sum(grid_is_1 & low_rep) / (L*L)
                        PC_high_rate = np.sum(grid_is_2 & high_rep) / (L*L)
                        PC_low_rate  = np.sum(grid_is_2 & low_rep) / (L*L)
                        D_high_rate = np.sum(grid_is_m1 & high_rep) / (L*L)
                        D_low_rate  = np.sum(grid_is_m1 & low_rep) / (L*L)
                        
                        rates_array[record_index] = rate
                        Crates_array[record_index] = C_high_rate + C_low_rate
                        PCrates_array[record_index] = PC_high_rate + PC_low_rate
                        Drates_array[record_index] = D_high_rate + D_low_rate
                        rate_high_rates_array[record_index] = C_high_rate + PC_high_rate
                        rate_low_rates_array[record_index] = C_low_rate + PC_low_rate
                        C_high_rates_array[record_index] = C_high_rate
                        C_low_rates_array[record_index] = C_low_rate
                        PC_high_rates_array[record_index] = PC_high_rate
                        PC_low_rates_array[record_index] = PC_low_rate
                        D_high_rates_array[record_index] = D_high_rate
                        D_low_rates_array[record_index] = D_low_rate
                        record_index += 1 
                    continue
                
                count_punishX, count_punishY = 0, 0
                pointx, count_punishX = cal_point(i, j, R, grid, reputationgrid, count_punishX, Z, b)
                pointy, count_punishY = cal_point(ni, nj, R, grid, reputationgrid, count_punishY, Z, b)
                
                mcs_punish_X += count_punishX
                mcs_punish_Y += count_punishY
                
                current_omega = 1.0 if reputationgrid[ni, nj] >= Z else omega_copy
                    
                if random.random() < current_omega * (1 / (1 + math.exp((pointx - pointy) / K))):
                    grid[i, j] = grid[ni, nj]
                    
                reputationgrid = update_reputation(reputationgrid, grid, i, j, ni, nj, Z, typePATTERN, p_vals)
                
                if _ % 1000 == 0 and mcsstep < 10000:
                    grid_is_1 = (grid == 1)
                    grid_is_2 = (grid == 2)
                    grid_is_m1 = (grid == -1)
                    count_C_PC = np.sum(grid_is_1) + np.sum(grid_is_2)
                    rate = count_C_PC / (L*L)
                    
                    if rate == 0: check = 1; rast = mcsstep
                    if rate == 1.0: check = 2; rast = mcsstep
                    
                    high_rep = (reputationgrid >= Z)
                    low_rep = (reputationgrid < Z)
                    
                    C_high_rate = np.sum(grid_is_1 & high_rep) / (L*L)
                    C_low_rate  = np.sum(grid_is_1 & low_rep) / (L*L)
                    PC_high_rate = np.sum(grid_is_2 & high_rep) / (L*L)
                    PC_low_rate  = np.sum(grid_is_2 & low_rep) / (L*L)
                    D_high_rate = np.sum(grid_is_m1 & high_rep) / (L*L)
                    D_low_rate  = np.sum(grid_is_m1 & low_rep) / (L*L)
                    
                    rates_array[record_index] = rate
                    Crates_array[record_index] = C_high_rate + C_low_rate
                    PCrates_array[record_index] = PC_high_rate + PC_low_rate
                    Drates_array[record_index] = D_high_rate + D_low_rate
                    rate_high_rates_array[record_index] = C_high_rate + PC_high_rate
                    rate_low_rates_array[record_index] = C_low_rate + PC_low_rate
                    C_high_rates_array[record_index] = C_high_rate
                    C_low_rates_array[record_index] = C_low_rate
                    PC_high_rates_array[record_index] = PC_high_rate
                    PC_low_rates_array[record_index] = PC_low_rate
                    D_high_rates_array[record_index] = D_high_rate
                    D_low_rates_array[record_index] = D_low_rate
                    record_index += 1 
            else:
                if _ % 1000 == 0 and mcsstep < 10000:
                    rates_array[record_index] = rate
                    Crates_array[record_index] = C_high_rate + C_low_rate
                    PCrates_array[record_index] = PC_high_rate + PC_low_rate
                    Drates_array[record_index] = D_high_rate + D_low_rate
                    rate_high_rates_array[record_index] = C_high_rate + PC_high_rate
                    rate_low_rates_array[record_index] = C_low_rate + PC_low_rate
                    C_high_rates_array[record_index] = C_high_rate
                    C_low_rates_array[record_index] = C_low_rate
                    PC_high_rates_array[record_index] = PC_high_rate
                    PC_low_rates_array[record_index] = PC_low_rate
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
    return

# ==========================================
# 2. メイン実行処理
# ==========================================
if __name__ == "__main__":
    start = time.time()
    
    ZIP_NAME        = f"{typePATTERN}_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
    ZIP_NAME_C      = f"{typePATTERN}_C_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
    ZIP_NAME_PC     = f"{typePATTERN}_PC_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
    ZIP_NAME_D      = f"{typePATTERN}_D_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
    ZIP_NAME_PUNISH = f"punish_history_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip"
    ZIP_NAME_PAYOFF = f"payoff_history_Z={Z}_r={R}_{PATTERN}_omega={omega}.zip" 
    
    zip_buffer = io.BytesIO()
    zip_buffer_C = io.BytesIO()
    zip_buffer_PC = io.BytesIO()
    zip_buffer_D = io.BytesIO()
    zip_buffer_P = io.BytesIO()
    zip_buffer_payoff = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf, \
         zipfile.ZipFile(zip_buffer_C, 'w', zipfile.ZIP_DEFLATED) as zf_C, \
         zipfile.ZipFile(zip_buffer_PC, 'w', zipfile.ZIP_DEFLATED) as zf_PC, \
         zipfile.ZipFile(zip_buffer_D, 'w', zipfile.ZIP_DEFLATED) as zf_D, \
         zipfile.ZipFile(zip_buffer_P, 'w', zipfile.ZIP_DEFLATED) as zf_P, \
         zipfile.ZipFile(zip_buffer_payoff, 'w', zipfile.ZIP_DEFLATED) as zf_payoff:
             
        # b のループのみ内部で行う
        for b in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            expected_size = 100000
            
            rates_array = np.zeros(expected_size, dtype=np.float32)
            Crates_array = np.zeros(expected_size, dtype=np.float32)
            PCrates_array = np.zeros(expected_size, dtype=np.float32)
            Drates_array = np.zeros(expected_size, dtype=np.float32)
            
            rate_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            rate_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            C_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            C_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            PC_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            PC_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            D_high_rates_array = np.zeros(expected_size, dtype=np.float32)
            D_low_rates_array = np.zeros(expected_size, dtype=np.float32)
            
            punish_X_time_series = np.zeros(num_steps, dtype=np.int32)
            punish_Y_time_series = np.zeros(num_steps, dtype=np.int32)
            payoff_history_all = np.zeros(num_steps, dtype=np.float32)
            payoff_history_C = np.zeros(num_steps, dtype=np.float32)
            payoff_history_D = np.zeros(num_steps, dtype=np.float32)
            payoff_history_PC = np.zeros(num_steps, dtype=np.float32)
            print(f"現在のb値: {b} (omega={omega}, Z={Z})")
            
            simulation(0, omega, Z, b)
            
            # CSV書き込み (io.StringIO使用)
            csv_buf = io.StringIO()
            pd.DataFrame({"Cooperation Rate": rates_array, "Cooperation Rate High": rate_high_rates_array, "Cooperation Rate Low": rate_low_rates_array}).to_csv(csv_buf, index=False)
            zf.writestr(f"{typePATTERN}_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf.getvalue())
            
            csv_buf_C = io.StringIO()
            pd.DataFrame({"C Rate": Crates_array, "C Rate High": C_high_rates_array, "C Rate Low": C_low_rates_array}).to_csv(csv_buf_C, index=False)
            zf_C.writestr(f"{typePATTERN}_C_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_C.getvalue())
            
            csv_buf_PC = io.StringIO()
            pd.DataFrame({"PC Rate": PCrates_array, "PC Rate High": PC_high_rates_array, "PC Rate Low": PC_low_rates_array}).to_csv(csv_buf_PC, index=False)
            zf_PC.writestr(f"{typePATTERN}_PC_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_PC.getvalue())  
            
            csv_buf_D = io.StringIO()
            pd.DataFrame({"D Rate": Drates_array, "D Rate High": D_high_rates_array, "D Rate Low": D_low_rates_array}).to_csv(csv_buf_D, index=False)
            zf_D.writestr(f"{typePATTERN}_D_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_D.getvalue())

            csv_buf_P = io.StringIO()
            pd.DataFrame({"MCS_Step": np.arange(num_steps), "Punish_Count_i": punish_X_time_series, "Punish_Count_j": punish_Y_time_series}).to_csv(csv_buf_P, index=False)
            zf_P.writestr(f"punish_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_P.getvalue())

            csv_buf_Payoff = io.StringIO()
            pd.DataFrame({"MCS_Step": np.arange(num_steps), "Avg_Payoff_Total": payoff_history_all, "Avg_Payoff_C": payoff_history_C, "Avg_Payoff_D": payoff_history_D, "Avg_Payoff_PC": payoff_history_PC}).to_csv(csv_buf_Payoff, index=False)
            zf_payoff.writestr(f"payoff_Z={Z}_b={b}_r={R}_{PATTERN}_omega={omega}.csv", csv_buf_Payoff.getvalue())

    # 保存処理
    for d in OUTPUT_DIRS: 
        os.makedirs(d, exist_ok=True)
    
    save_files = [
        (zip_buffer, ZIP_NAME, OUTPUT_DIRS[0]),
        (zip_buffer_C, ZIP_NAME_C, OUTPUT_DIRS[1]),
        (zip_buffer_PC, ZIP_NAME_PC, OUTPUT_DIRS[2]),
        (zip_buffer_D, ZIP_NAME_D, OUTPUT_DIRS[3]),
        (zip_buffer_P, ZIP_NAME_PUNISH, OUTPUT_DIRS[4]),
        (zip_buffer_payoff, ZIP_NAME_PAYOFF, OUTPUT_DIRS[5])
    ]
    
    for buf, filename, target_dir in save_files:
        local_path = os.path.join(target_dir, filename)
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        print(f"✅ 保存完了: {local_path}") 
        buf.close()  

    end = time.time()
    print("実行時間:", end - start, "秒")